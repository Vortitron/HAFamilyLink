"""The controller: turns parental decisions into enforcer calls and proves them (SPEC.md 4 to 6).

The controller is host-agnostic. The host (Home Assistant in phase 1) gives
it a clock, a household, children, devices and enforcers, then calls the
verbs and ``tick`` on a timer. Events go to listeners the host registers.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from typing import Any
from zoneinfo import ZoneInfo

from . import overrides as ov
from . import policy as pol
from .enforcer import Enforcer
from .ledger import DayLedger
from .models import (
	MODE_STRENGTH,
	Child,
	ChildStatus,
	Confidence,
	Device,
	EnforcedState,
	EnforcementStatus,
	EnforcerResult,
	Event,
	Health,
	HealthStatus,
	Household,
	Mode,
	Override,
	OverrideKind,
	OverrideStatus,
	Policy,
	ResultStatus,
	Scope,
)
from .tags import TagSource

_LOGGER = logging.getLogger(__name__)

LEDGER_ENFORCER = "ledger"
LOW_THRESHOLD_MINUTES = 15
SOURCE_EXHAUSTED = "controller:exhausted"
SOURCE_BEDTIME = "policy:bedtime"
SOURCE_WINDOW = "policy:window"
AUTO_SOURCES = (SOURCE_EXHAUSTED, SOURCE_BEDTIME, SOURCE_WINDOW)

MODE_VERB: dict[Mode, str] = {
	Mode.PAUSE: "locked",
	Mode.ZERO_ALLOWANCE: "allowance zeroed",
	Mode.NETWORK: "network blocked",
	Mode.POWER: "powered off",
	Mode.MANUAL: "manual action requested",
	Mode.BONUS: "bonus added",
	Mode.ALLOWANCE: "allowance set",
}
MODE_CAVEAT: dict[Mode, str] = {
	Mode.NETWORK: "may still run offline games",
	Mode.ZERO_ALLOWANCE: "schedule will be restored on unlock",
	Mode.MANUAL: "waiting for a parent to press done",
}
RESULT_SUFFIX: dict[ResultStatus, str] = {
	ResultStatus.REQUESTED: "Awaiting confirmation.",
	ResultStatus.APPLIED: "Awaiting confirmation.",
	ResultStatus.CONFIRMED: "",
	ResultStatus.FAILED: "Failed.",
	ResultStatus.UNKNOWN: "State unknown.",
}


@dataclass
class ChildState:
	"""What the per-child entities show."""

	child_id: str
	status: ChildStatus
	enforcement: EnforcementStatus
	remaining: int
	used: float
	allowance: int
	granted: int
	confidence: Confidence
	lock_id: str | None = None
	lock_reason: str = ""
	lock_expires_at: datetime | None = None
	devices_without_per_app_usage: list[str] = field(default_factory=list)
	degraded_enforcers: list[str] = field(default_factory=list)
	summary: list[str] = field(default_factory=list)


class Controller:
	def __init__(self, household: Household, clock: Callable[[], datetime] | None = None) -> None:
		self.household = household
		self.tz = ZoneInfo(household.time_zone)
		self._clock = clock or (lambda: datetime.now(tz=self.tz))
		self.children: dict[str, Child] = {}
		self.policies: dict[str, Policy] = {}
		self.devices: dict[str, Device] = {}
		self.enforcers: dict[str, Enforcer] = {}
		self.overrides: list[Override] = []
		self.ledgers: dict[tuple[str, str], DayLedger] = {}
		self.health: dict[str, Health] = {}
		self.states: dict[tuple[str, str], EnforcedState] = {}
		self.tags = TagSource()
		self.low_threshold = LOW_THRESHOLD_MINUTES
		self._listeners: list[Callable[[Event], None]] = []
		self._last_tick: datetime | None = None
		self._announced: set[tuple[str, str, str]] = set()
		self._now_playing: dict[str, str | None] = {}

	# Setup

	def now(self) -> datetime:
		return self._clock().astimezone(self.tz)

	def add_child(self, child: Child, policy: Policy | None = None) -> None:
		self.children[child.id] = child
		self.policies[child.id] = policy or Policy(child_id=child.id)
		child.policy_id = self.policies[child.id].id

	def set_policy(self, child_id: str, policy: Policy) -> None:
		self.policies[child_id] = policy

	def add_device(self, device: Device) -> None:
		self.devices[device.id] = device

	def add_enforcer(self, enforcer: Enforcer) -> None:
		self.enforcers[enforcer.name] = enforcer
		self.health.setdefault(enforcer.name, Health(HealthStatus.UNKNOWN, "not yet polled"))

	def listen(self, listener: Callable[[Event], None]) -> Callable[[], None]:
		self._listeners.append(listener)
		return lambda: self._listeners.remove(listener)

	def emit(self, type_: str, child_id: str | None = None, **payload: Any) -> Event:
		event = Event(type=type_, household_id=self.household.id, at=self.now(), child_id=child_id, payload=payload)
		for listener in list(self._listeners):
			try:
				listener(event)
			except Exception:  # noqa: BLE001 - a bad listener must not break enforcement
				_LOGGER.exception("Kerb event listener failed")
		return event

	def set_now_playing(self, device_id: str, app: str | None) -> None:
		"""The host tells us which app a device is running, when an observer knows."""
		self._now_playing[device_id] = app

	# Lookups

	def devices_for(self, child_id: str, scope: Scope | None = None) -> list[Device]:
		found = [device for device in self.devices.values() if device.governs(child_id)]
		if scope is not None:
			found = [device for device in found if scope.covers_device(device.id)]
		return sorted(found, key=lambda device: device.display_name)

	def ledger(self, child_id: str, day: datetime | None = None) -> DayLedger:
		moment = day or self.now()
		key = (child_id, moment.date().isoformat())
		if key not in self.ledgers:
			ledger = DayLedger(child_id=child_id, date=key[1])
			allowance_override = ov.allowance_today(self.overrides, moment)
			if allowance_override is not None and allowance_override.child_id == child_id:
				ledger.add_allowance(allowance_override.minutes or 0, moment, allowance_override.source, allowance_override.id)
			else:
				ledger.add_allowance(pol.allowance_for(self.policies[child_id], moment.date()), moment, "policy")
			self.ledgers[key] = ledger
		return self.ledgers[key]

	def child_overrides(self, child_id: str) -> list[Override]:
		return [override for override in self.overrides if override.child_id == child_id]

	def get_override(self, override_id: str) -> Override | None:
		return next((override for override in self.overrides if override.id == override_id), None)

	def _window(self, override: Override) -> timedelta:
		names = {result.enforcer for result in override.results} & set(self.enforcers)
		seconds = max((self.enforcers[name].capabilities.confirmation_window_s for name in names), default=0)
		return timedelta(seconds=seconds)

	def _trusted(self, enforcer_name: str) -> bool:
		return self.health.get(enforcer_name, Health(HealthStatus.UNKNOWN)).trusted

	# Verbs

	async def lock(
		self,
		child_id: str,
		minutes: int | None = None,
		scope: Scope | None = None,
		reason: str = "",
		source: str = "guardian",
		mode: str = "auto",
	) -> Override:
		now = self.now()
		expires = now + timedelta(minutes=minutes) if minutes else pol.end_of_day(now)
		override = Override(
			child_id=child_id,
			kind=OverrideKind.LOCK,
			scope=scope or Scope(),
			reason=reason,
			source=source,
			starts_at=now,
			expires_at=expires,
			minutes=minutes,
		)
		self.overrides.append(override)
		self.ledger(child_id).add_lock(override, now)
		await self._dispatch_lock(override, mode)
		return override

	async def unlock(self, child_id: str, scope: Scope | None = None, reason: str = "", source: str = "guardian") -> Override:
		now = self.now()
		scope = scope or Scope()
		override = Override(
			child_id=child_id,
			kind=OverrideKind.UNLOCK,
			scope=scope,
			reason=reason,
			source=source,
			starts_at=now,
			expires_at=pol.end_of_day(now),
		)
		locks = [
			lock
			for lock in ov.active(self.child_overrides(child_id), now, OverrideKind.LOCK)
			if scope.type == "all" or lock.scope.type == "all" or lock.scope == scope
		]
		self.overrides.append(override)
		for lock in locks:
			await self._revert_lock(lock, record_on=override)
		if not locks:
			override.results.append(
				EnforcerResult(LEDGER_ENFORCER, ResultStatus.CONFIRMED, detail="nothing was locked", confirmed_at=now)
			)
		self._settle(override)
		return override

	async def grant(self, child_id: str, minutes: int, reason: str = "", source: str = "guardian") -> Override:
		now = self.now()
		ledger = self.ledger(child_id)
		policy = self.policies[child_id]
		override = Override(
			child_id=child_id,
			kind=OverrideKind.GRANT,
			minutes=minutes,
			reason=reason,
			source=source,
			starts_at=now,
			expires_at=pol.end_of_day(now),
		)
		ledger.add_grant(minutes, now, source, reason, override.id, cap=policy.grant_cap_minutes_per_day)
		self.overrides.append(override)
		await self._dispatch_simple(override, "grant_minutes", Mode.BONUS)
		if ledger.remaining > 0:
			for lock in ov.active(self.child_overrides(child_id), now, OverrideKind.LOCK):
				if lock.source == SOURCE_EXHAUSTED:
					await self.cancel_override(lock.id, source=source)
			self._announced.discard((child_id, ledger.date, "allowance.exhausted"))
		return override

	async def set_allowance_today(self, child_id: str, minutes: int, source: str = "guardian") -> Override:
		now = self.now()
		override = Override(
			child_id=child_id,
			kind=OverrideKind.ALLOWANCE_TODAY,
			minutes=minutes,
			source=source,
			starts_at=now,
			expires_at=pol.end_of_day(now),
		)
		self.ledger(child_id).add_allowance(minutes, now, source, override.id)
		self.overrides.append(override)
		await self._dispatch_simple(override, "daily_allowance", Mode.ALLOWANCE)
		return override

	async def cancel_override(self, override_id: str, source: str = "guardian") -> Override:
		"""Write a compensating record. The original is marked cancelled, never deleted."""
		original = self.get_override(override_id)
		if original is None:
			raise KeyError(override_id)
		now = self.now()
		record = Override(
			child_id=original.child_id,
			kind=OverrideKind.UNLOCK if original.kind == OverrideKind.LOCK else original.kind,
			scope=original.scope,
			minutes=original.minutes,
			reason=f"cancelled {original.kind}",
			source=source,
			starts_at=now,
			expires_at=pol.end_of_day(now),
			cancels=original.id,
		)
		self.overrides.append(record)
		if original.kind == OverrideKind.LOCK and original.active_at(now):
			await self._revert_lock(original, record_on=record)
		elif original.kind == OverrideKind.GRANT and original.minutes:
			self.ledger(original.child_id).add_penalty(original.minutes, now, source, record.reason, record.id)
			record.results.append(EnforcerResult(LEDGER_ENFORCER, ResultStatus.CONFIRMED, mode=Mode.BONUS, confirmed_at=now))
		elif original.kind == OverrideKind.ALLOWANCE_TODAY:
			policy_minutes = pol.allowance_for(self.policies[original.child_id], now.date())
			self.ledger(original.child_id).add_allowance(policy_minutes, now, "policy", record.id)
			record.results.append(EnforcerResult(LEDGER_ENFORCER, ResultStatus.CONFIRMED, mode=Mode.ALLOWANCE, confirmed_at=now))
		else:
			record.results.append(EnforcerResult(LEDGER_ENFORCER, ResultStatus.CONFIRMED, confirmed_at=now))
		original.status = OverrideStatus.CANCELLED
		self.emit("override.cancelled", original.child_id, override=original.to_dict(), by=record.id)
		self._settle(record)
		return record

	async def reconcile(self, child_id: str | None = None) -> None:
		"""Force a read-back from every enforcer and refresh health."""
		await self._poll_health()
		children = [child_id] if child_id else list(self.children)
		for cid in children:
			for device in self.devices_for(cid):
				for name in device.enforcer_ids:
					enforcer = self.enforcers.get(name)
					if enforcer is None:
						continue
					await self._read(enforcer, device)
		for override in self.overrides:
			if override.status == OverrideStatus.APPLIED:
				await self._confirm(override)

	# Dispatch

	def _enforcers_for(self, device: Device) -> list[Enforcer]:
		return [self.enforcers[name] for name in device.enforcer_ids if name in self.enforcers]

	async def _dispatch_lock(self, override: Override, mode: str) -> None:
		await self._ensure_health()
		asked = False
		for device in self.devices_for(override.child_id, override.scope):
			for enforcer in self._enforcers_for(device):
				lock_mode = enforcer.capabilities.lock_mode
				if lock_mode is None:
					continue
				if mode != "auto" and str(lock_mode) != mode:
					continue
				if lock_mode == Mode.POWER and not device.power_off_allowed:
					continue
				asked = True
				override.results.append(await self._call(enforcer.apply, enforcer, override, device, lock_mode))
		if asked:
			self.emit("override.applied", override.child_id, override=override.to_dict())
			await self._confirm(override)
		else:
			self._settle(override)

	async def _dispatch_simple(self, override: Override, capability: str, mode: Mode) -> None:
		await self._ensure_health()
		now = self.now()
		asked = False
		for device in self.devices_for(override.child_id):
			for enforcer in self._enforcers_for(device):
				if not getattr(enforcer.capabilities, capability):
					continue
				asked = True
				override.results.append(await self._call(enforcer.apply, enforcer, override, device, mode))
		if not asked:
			override.results.append(
				EnforcerResult(LEDGER_ENFORCER, ResultStatus.CONFIRMED, mode=mode, detail="ledger only", confirmed_at=now)
			)
		self._settle(override)

	async def _revert_lock(self, lock: Override, record_on: Override) -> None:
		"""Ask every enforcer that applied a lock to release it.

		When the release belongs to another decision (an unlock or a cancel)
		the results land on that record and are confirmed by read-back. When a
		lock expires the release results are kept under ``restore["revert"]``
		on the lock itself, and a device still locked afterwards raises
		``enforcement.unconfirmed``.
		"""
		await self._ensure_health()
		pairs = []
		for result in list(lock.results):
			enforcer = self.enforcers.get(result.enforcer)
			device = self.devices.get(result.device_id or "")
			if enforcer is None or device is None:
				continue
			pairs.append((enforcer, device, await self._call(enforcer.revert, enforcer, lock, device, result.mode)))
		if record_on is not lock:
			record_on.results.extend(result for _enforcer, _device, result in pairs)
			self.emit("override.applied", record_on.child_id, override=record_on.to_dict())
			await self._confirm(record_on)
			return
		lock.restore["revert"] = [result.to_dict() for _enforcer, _device, result in pairs]
		for enforcer, device, result in pairs:
			state = await self._read(enforcer, device)
			if state.locked is False:
				result.status = ResultStatus.CONFIRMED
				continue
			result.status = ResultStatus.UNKNOWN if state.locked is None else ResultStatus.FAILED
			self.emit(
				"enforcement.unconfirmed",
				lock.child_id,
				override_id=lock.id,
				enforcer=enforcer.name,
				device_id=device.id,
				result=result.to_dict(),
				detail="still locked after expiry",
			)
		lock.restore["revert"] = [result.to_dict() for _enforcer, _device, result in pairs]

	async def _ensure_health(self) -> None:
		"""Poll any enforcer that has never reported health, so a first verb is not refused blindly."""
		if any(health.reason == "not yet polled" for health in self.health.values()):
			await self._poll_health()

	async def _call(self, method, enforcer: Enforcer, override: Override, device: Device, mode: Mode | None) -> EnforcerResult:
		if not self._trusted(enforcer.name):
			return EnforcerResult(
				enforcer.name,
				ResultStatus.UNKNOWN,
				device_id=device.id,
				mode=mode,
				detail=f"enforcer {self.health[enforcer.name].status}: {self.health[enforcer.name].reason}",
			)
		try:
			result = await method(override, device.ref())
		except Exception as err:  # noqa: BLE001 - every enforcer failure becomes a result, never a crash
			_LOGGER.warning("Enforcer %s failed on %s: %s", enforcer.name, device.display_name, err)
			return EnforcerResult(enforcer.name, ResultStatus.FAILED, device_id=device.id, mode=mode, detail=str(err))
		if result.device_id is None:
			result.device_id = device.id
		if result.mode is None:
			result.mode = mode
		# Rule 1: an enforcer may not report confirmed without a read-back. We always do our own.
		if result.status == ResultStatus.CONFIRMED:
			result.status = ResultStatus.APPLIED
		return result

	async def _read(self, enforcer: Enforcer, device: Device) -> EnforcedState:
		try:
			state = await enforcer.read_state(device.ref())
		except Exception as err:  # noqa: BLE001
			_LOGGER.warning("Enforcer %s could not read %s: %s", enforcer.name, device.display_name, err)
			state = EnforcedState(device_id=device.id, locked=None, detail=str(err))
		if not self._trusted(enforcer.name):
			state = EnforcedState(device_id=device.id, locked=None, in_use=state.in_use, detail="enforcer not trusted")
		self.states[(enforcer.name, device.id)] = state
		return state

	async def _confirm(self, override: Override) -> None:
		"""Read back every pending result and settle the override."""
		now = self.now()
		want_locked = override.kind == OverrideKind.LOCK
		for result in override.results:
			if result.status not in (ResultStatus.REQUESTED, ResultStatus.APPLIED):
				continue
			enforcer = self.enforcers.get(result.enforcer)
			device = self.devices.get(result.device_id or "")
			if enforcer is None or device is None:
				continue
			state = await self._read(enforcer, device)
			if state.locked is None:
				if not self._trusted(enforcer.name):
					result.status = ResultStatus.UNKNOWN
					result.detail = state.detail
				continue
			if state.locked == want_locked:
				result.status = ResultStatus.CONFIRMED
				result.confirmed_at = now
				if state.detail:
					result.detail = state.detail
		self._settle(override)

	def _settle(self, override: Override) -> None:
		now = self.now()
		before = override.status
		if before in ov.SETTLED or before == OverrideStatus.CONFIRMED:
			return
		status = ov.aggregate_status(override.results, override.starts_at, self._window(override), now)
		override.status = status
		if status == before:
			return
		if status == OverrideStatus.CONFIRMED:
			self.emit("override.confirmed", override.child_id, override=override.to_dict())
		elif status == OverrideStatus.PARTIAL:
			self.emit("override.partial", override.child_id, override=override.to_dict())
		elif status == OverrideStatus.FAILED:
			self.emit("override.failed", override.child_id, override=override.to_dict())
		if status in (OverrideStatus.PARTIAL, OverrideStatus.FAILED):
			for result in ov.unconfirmed(override.results):
				self.emit(
					"enforcement.unconfirmed",
					override.child_id,
					override_id=override.id,
					enforcer=result.enforcer,
					device_id=result.device_id,
					result=result.to_dict(),
				)

	# Time

	async def _poll_health(self) -> None:
		for name, enforcer in self.enforcers.items():
			try:
				health = await enforcer.health()
			except Exception as err:  # noqa: BLE001
				health = Health(HealthStatus.UNKNOWN, str(err))
			previous = self.health.get(name)
			self.health[name] = health
			if previous is None or previous.reason == "not yet polled":
				if not health.trusted:
					self.emit("enforcer.degraded", enforcer=name, status=str(health.status), reason=health.reason)
				continue
			if previous.trusted and not health.trusted:
				self.emit("enforcer.degraded", enforcer=name, status=str(health.status), reason=health.reason)
			elif not previous.trusted and health.trusted:
				self.emit("enforcer.restored", enforcer=name, status=str(health.status))

	async def tick(self) -> None:
		"""Run once per poll: health, expiry, confirmation, usage, schedules, alerts."""
		now = self.now()
		await self._poll_health()
		for override in list(self.overrides):
			if override.status not in ov.SETTLED and override.expires_at <= now:
				if override.kind == OverrideKind.LOCK and override.results:
					await self._revert_lock(override, record_on=override)
				override.status = OverrideStatus.EXPIRED
				self.emit("override.expired", override.child_id, override=override.to_dict())
			elif override.status == OverrideStatus.APPLIED:
				await self._confirm(override)
		for child_id in self.children:
			for device in self.devices_for(child_id):
				for enforcer in self._enforcers_for(device):
					await self._read(enforcer, device)
		if self._last_tick is not None and self._last_tick.date() == now.date():
			self._charge(self._last_tick, now)
		self._last_tick = now
		for child_id in self.children:
			await self._apply_schedules(child_id, now)
			await self._check_allowance(child_id, now)

	def _charge(self, since: datetime, now: datetime) -> None:
		"""Charge elapsed minutes for devices known to be in use and not locked."""
		elapsed = (now - since).total_seconds() / 60
		if elapsed <= 0:
			return
		for child_id in self.children:
			ledger = self.ledger(child_id, now)
			policy = self.policies[child_id]
			for device in self.devices_for(child_id):
				if ov.effective_lock(self.child_overrides(child_id), since, device.id) is not None:
					continue
				states = [self.states[(name, device.id)] for name in device.enforcer_ids if (name, device.id) in self.states]
				if not any(state.in_use for state in states):
					continue
				app = self._now_playing.get(device.id)
				effect, rule = pol.effect_for_app(policy, app, self.tags.tags_for(app))
				ledger.charge_usage(
					round(elapsed, 3),
					now,
					rate=pol.rate_for(effect),
					device_id=device.id,
					app=app,
					rule=rule,
					per_app_usage_available=app is not None,
					source=",".join(sorted(name for name in device.enforcer_ids if (name, device.id) in self.states)),
				)
				self.emit("usage.reported", child_id, device_id=device.id, minutes=round(elapsed, 3), rate=pol.rate_for(effect))

	async def _apply_schedules(self, child_id: str, now: datetime) -> None:
		policy = self.policies[child_id]
		active_sources = {lock.source for lock in ov.active(self.child_overrides(child_id), now, OverrideKind.LOCK)}
		if pol.in_bedtime(policy, now) and SOURCE_BEDTIME not in active_sources:
			end = pol.bedtime_end(policy, now)
			minutes = max(1, int((end - now).total_seconds() // 60)) if end else None
			await self.lock(child_id, minutes=minutes, reason="bedtime", source=SOURCE_BEDTIME)
		elif not pol.in_allowed_window(policy, now) and SOURCE_WINDOW not in active_sources:
			minutes = max(1, int((pol.next_window_start(policy, now) - now).total_seconds() // 60))
			await self.lock(child_id, minutes=minutes, reason="outside allowed hours", source=SOURCE_WINDOW)

	async def _check_allowance(self, child_id: str, now: datetime) -> None:
		ledger = self.ledger(child_id, now)
		active_sources = {lock.source for lock in ov.active(self.child_overrides(child_id), now, OverrideKind.LOCK)}
		if ledger.remaining <= 0:
			if self._announce(child_id, ledger.date, "allowance.exhausted"):
				self.emit("allowance.exhausted", child_id, remaining=0)
			if SOURCE_EXHAUSTED not in active_sources:
				await self.lock(child_id, reason="allowance used up", source=SOURCE_EXHAUSTED)
		elif ledger.remaining <= self.low_threshold and self._announce(child_id, ledger.date, "allowance.low"):
			self.emit("allowance.low", child_id, remaining=ledger.remaining)

	def _announce(self, child_id: str, day: str, type_: str) -> bool:
		key = (child_id, day, type_)
		if key in self._announced:
			return False
		self._announced.add(key)
		return True

	# Reporting

	def child_state(self, child_id: str) -> ChildState:
		now = self.now()
		ledger = self.ledger(child_id, now)
		policy = self.policies[child_id]
		devices = self.devices_for(child_id)
		bound = {name for device in devices for name in device.enforcer_ids if name in self.enforcers}
		untrusted = sorted(name for name in bound if not self._trusted(name))
		degraded = sorted(
			name for name in bound if self.health.get(name, Health(HealthStatus.UNKNOWN)).status == HealthStatus.DEGRADED
		)
		lock = ov.effective_lock(self.child_overrides(child_id), now)

		if untrusted:
			status = ChildStatus.UNKNOWN
			enforcement = EnforcementStatus.UNKNOWN
		else:
			if lock is not None:
				status = (
					ChildStatus.BEDTIME if lock.source == SOURCE_BEDTIME or pol.in_bedtime(policy, now) else ChildStatus.LOCKED
				)
			elif ledger.remaining <= 0:
				status = ChildStatus.EXHAUSTED
			else:
				status = ChildStatus.FREE
			if lock is not None:
				enforcement = {
					OverrideStatus.CONFIRMED: EnforcementStatus.CONFIRMED,
					OverrideStatus.PARTIAL: EnforcementStatus.PARTIAL,
				}.get(lock.status, EnforcementStatus.DEGRADED)
			elif degraded:
				enforcement = EnforcementStatus.DEGRADED
			else:
				enforcement = EnforcementStatus.CONFIRMED

		if untrusted:
			confidence = Confidence.STALE
		elif any(not self.states.get((name, device.id)) for device in devices for name in device.enforcer_ids if name in bound):
			confidence = Confidence.ASSUMED
		else:
			confidence = Confidence.CONFIRMED

		return ChildState(
			child_id=child_id,
			status=status,
			enforcement=enforcement,
			remaining=ledger.remaining,
			used=round(ledger.used_weighted, 1),
			allowance=ledger.allowance,
			granted=ledger.granted,
			confidence=confidence,
			lock_id=None if lock is None else lock.id,
			lock_reason="" if lock is None else lock.reason,
			lock_expires_at=None if lock is None else lock.expires_at,
			devices_without_per_app_usage=[
				self.devices[device_id].display_name if device_id in self.devices else device_id
				for device_id in ledger.devices_without_per_app_usage
			],
			degraded_enforcers=sorted(set(untrusted) | set(degraded)),
			summary=self.summary(lock) if lock is not None else [],
		)

	def summary(self, override: Override) -> list[str]:
		"""One verbatim line per enforcer result, for the dashboard."""
		lines = []
		for result in override.results:
			device = self.devices.get(result.device_id or "")
			name = device.display_name if device else override.child_id
			if result.enforcer == LEDGER_ENFORCER:
				lines.append(f"{result.detail or 'ledger updated'}.".capitalize())
				continue
			verb = MODE_VERB.get(result.mode, str(result.mode or "updated")) if result.mode else "updated"
			line = f"{name} {verb} ({result.enforcer})."
			caveat = MODE_CAVEAT.get(result.mode) if result.mode else None
			if caveat:
				line += f" {name} {caveat}."
			suffix = RESULT_SUFFIX.get(result.status, "")
			if suffix:
				line += f" {suffix}"
			lines.append(line)
		return lines

	def strongest_mode(self, device: Device) -> Mode | None:
		modes = [enforcer.capabilities.lock_mode for enforcer in self._enforcers_for(device)]
		for mode in MODE_STRENGTH:
			if mode in modes and (mode != Mode.POWER or device.power_off_allowed):
				return mode
		return None

	# Persistence

	def to_dict(self) -> dict[str, Any]:
		return {
			"overrides": [override.to_dict() for override in self.overrides],
			"ledgers": [ledger.to_dict() for ledger in self.ledgers.values()],
			"announced": sorted(list(key) for key in self._announced),
		}

	def load(self, data: dict[str, Any]) -> None:
		self.overrides = [Override.from_dict(item) for item in data.get("overrides", [])]
		self.ledgers = {}
		for item in data.get("ledgers", []):
			ledger = DayLedger.from_dict(item)
			self.ledgers[(ledger.child_id, ledger.date)] = ledger
		self._announced = {tuple(key) for key in data.get("announced", [])}  # type: ignore[misc]

	def prune(self) -> None:
		"""Drop ledgers and overrides older than the retention period."""
		cutoff = (self.now() - timedelta(days=self.household.usage_retention_days)).date().isoformat()
		self.ledgers = {key: ledger for key, ledger in self.ledgers.items() if ledger.date >= cutoff}
		self.overrides = [override for override in self.overrides if override.expires_at.date().isoformat() >= cutoff]


async def gather_states(controller: Controller) -> dict[str, ChildState]:
	"""Convenience for hosts: states for every child."""
	await asyncio.sleep(0)
	return {child_id: controller.child_state(child_id) for child_id in controller.children}
