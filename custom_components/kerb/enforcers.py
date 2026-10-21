"""Phase 1 enforcers that work through existing Home Assistant entities.

Network, power and manual, plus a presence observer that only reports
whether a device is in use. None of them talks to a vendor. See SPEC.md 5.1.
"""

from __future__ import annotations

import asyncio
from datetime import date
import logging

from homeassistant.components import persistent_notification
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DEFAULT_CONFIRMATION_WINDOW, DOMAIN
from .core.enforcer import BaseEnforcer
from .core.models import (
	Capabilities,
	DeviceRef,
	EnforcedState,
	EnforcerResult,
	Health,
	HealthStatus,
	Mode,
	Override,
	OverrideKind,
	ResultStatus,
	UsageSample,
)

_LOGGER = logging.getLogger(__name__)

IN_USE_STATES = {STATE_ON, "playing", "home", "active", "buffering"}


def _entity_health(hass: HomeAssistant, entity_id: str) -> Health:
	state = hass.states.get(entity_id)
	if state is None:
		return Health(HealthStatus.UNKNOWN, f"{entity_id} does not exist")
	if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
		return Health(HealthStatus.UNKNOWN, f"{entity_id} is {state.state}")
	return Health(HealthStatus.HEALTHY)


class HAEnforcer(BaseEnforcer):
	"""Shared plumbing for enforcers bound to HA entities."""

	def __init__(self, hass: HomeAssistant, name: str, capabilities: Capabilities) -> None:
		super().__init__(name, capabilities)
		self.hass = hass

	async def _call(self, service: str, entity_id: str) -> None:
		"""Call the entity's own domain service, so a switch, input_boolean, remote or media player all work."""
		domain = entity_id.split(".", 1)[0]
		await self.hass.services.async_call(domain, service, {ATTR_ENTITY_ID: entity_id}, blocking=True)

	def _state(self, entity_id: str) -> str | None:
		state = self.hass.states.get(entity_id)
		if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
			return None
		return state.state


class NetworkEnforcer(HAEnforcer):
	"""A switch that blocks a device at the router, DNS filter or firewall.

	``on`` means blocked unless ``inverted`` is set, for switches that model
	"allowed" rather than "blocked".
	"""

	def __init__(
		self, hass: HomeAssistant, entity_id: str, inverted: bool = False, window_s: int = DEFAULT_CONFIRMATION_WINDOW
	) -> None:
		super().__init__(
			hass,
			f"network:{entity_id}",
			Capabilities(
				enforcer=f"network:{entity_id}",
				level=1,
				lock_now=True,
				unlock_now=True,
				network_block=True,
				poll_interval_s=60,
				confirmation_window_s=window_s,
				notes="Blocks the device's network access through a Home Assistant switch. Offline games keep running.",
			),
		)
		self.entity_id = entity_id
		self.inverted = inverted

	async def _set_blocked(self, blocked: bool) -> None:
		turn_on = blocked != self.inverted
		await self._call("turn_on" if turn_on else "turn_off", self.entity_id)

	async def apply(self, override: Override, device: DeviceRef) -> EnforcerResult:
		if override.kind != OverrideKind.LOCK:
			return self.unsupported(device, f"apply {override.kind}")
		await self._set_blocked(True)
		return self.result(ResultStatus.APPLIED, device, Mode.NETWORK, f"{self.entity_id} asked to block")

	async def revert(self, override: Override, device: DeviceRef) -> EnforcerResult:
		await self._set_blocked(False)
		return self.result(ResultStatus.APPLIED, device, Mode.NETWORK, f"{self.entity_id} asked to unblock")

	async def read_state(self, device: DeviceRef) -> EnforcedState:
		state = self._state(self.entity_id)
		if state not in (STATE_ON, STATE_OFF):
			return EnforcedState(
				device.device_id, locked=None, detail=f"{self.entity_id} unreadable", observed_at=dt_util.utcnow()
			)
		blocked = (state == STATE_ON) != self.inverted
		return EnforcedState(
			device.device_id,
			locked=blocked,
			detail="client blocked" if blocked else "client allowed",
			observed_at=dt_util.utcnow(),
		)

	async def health(self) -> Health:
		return _entity_health(self.hass, self.entity_id)


class PowerEnforcer(HAEnforcer):
	"""A smart plug, with an optional graceful off and a delay before the cut.

	Opt-in per device (``Device.power_off_allowed``) because cutting power
	mid-update can corrupt a console. The controller enforces the opt-in.
	"""

	def __init__(
		self,
		hass: HomeAssistant,
		switch_entity_id: str,
		graceful_off_entity_id: str | None = None,
		delay_s: int = 0,
		window_s: int = DEFAULT_CONFIRMATION_WINDOW,
	) -> None:
		super().__init__(
			hass,
			f"power:{switch_entity_id}",
			Capabilities(
				enforcer=f"power:{switch_entity_id}",
				level=1,
				lock_now=True,
				unlock_now=True,
				power_off=True,
				usage_read=True,
				poll_interval_s=60,
				confirmation_window_s=max(window_s, delay_s + 30),
				notes="Cuts power through a Home Assistant switch after an optional graceful off. Blunt, so opt-in per device.",
			),
		)
		self.switch_entity_id = switch_entity_id
		self.graceful_off_entity_id = graceful_off_entity_id
		self.delay_s = delay_s
		self._pending: asyncio.Task | None = None

	async def _cut(self) -> None:
		if self.delay_s:
			await asyncio.sleep(self.delay_s)
		await self._call("turn_off", self.switch_entity_id)

	async def apply(self, override: Override, device: DeviceRef) -> EnforcerResult:
		if override.kind != OverrideKind.LOCK:
			return self.unsupported(device, f"apply {override.kind}")
		detail = f"{self.switch_entity_id} asked to cut power"
		if self.graceful_off_entity_id:
			await self._call("turn_off", self.graceful_off_entity_id)
			detail = f"{self.graceful_off_entity_id} asked to shut down, then {detail} after {self.delay_s}s"
		if self.delay_s:
			if self._pending is not None and not self._pending.done():
				self._pending.cancel()
			self._pending = self.hass.async_create_background_task(self._cut(), f"{DOMAIN} power cut {device.display_name}")
		else:
			await self._cut()
		return self.result(ResultStatus.APPLIED, device, Mode.POWER, detail)

	async def revert(self, override: Override, device: DeviceRef) -> EnforcerResult:
		if self._pending is not None and not self._pending.done():
			self._pending.cancel()
		await self._call("turn_on", self.switch_entity_id)
		return self.result(ResultStatus.APPLIED, device, Mode.POWER, f"{self.switch_entity_id} asked to restore power")

	async def read_state(self, device: DeviceRef) -> EnforcedState:
		state = self._state(self.switch_entity_id)
		if state not in (STATE_ON, STATE_OFF):
			return EnforcedState(
				device.device_id, locked=None, detail=f"{self.switch_entity_id} unreadable", observed_at=dt_util.utcnow()
			)
		off = state == STATE_OFF
		return EnforcedState(
			device.device_id,
			locked=off,
			detail="power off" if off else "power on",
			observed_at=dt_util.utcnow(),
		)

	async def health(self) -> Health:
		return _entity_health(self.hass, self.switch_entity_id)


class ManualEnforcer(HAEnforcer):
	"""The null enforcer: tell the parent what to do in the vendor app and wait for done.

	Confirmed only when the parent presses done. This gives a PlayStation a
	row in the ledger without pretending it was enforced.
	"""

	def __init__(self, hass: HomeAssistant, device_id: str, device_name: str, window_s: int = 900) -> None:
		super().__init__(
			hass,
			f"manual:{device_id}",
			Capabilities(
				enforcer=f"manual:{device_id}",
				level=1,
				lock_now=True,
				unlock_now=True,
				manual=True,
				poll_interval_s=60,
				confirmation_window_s=window_s,
				notes="Asks a parent to act in the vendor app. Confirmed when the parent presses done.",
			),
		)
		self.device_id = device_id
		self.device_name = device_name
		self.pending: str | None = None  # "lock" | "unlock" | None
		self.confirmed_locked: bool | None = None
		self.on_change = lambda: None

	@property
	def notification_id(self) -> str:
		return f"{DOMAIN}_manual_{self.device_id}"

	def _notify(self, action: str, override: Override) -> None:
		reason = f" ({override.reason})" if override.reason else ""
		persistent_notification.async_create(
			self.hass,
			f"Please {action} {self.device_name} in its own parental controls app{reason}, "
			f"then press the '{self.device_name} manual done' button or call kerb.confirm_manual.",
			title=f"Kerb: {action} {self.device_name}",
			notification_id=self.notification_id,
		)

	async def apply(self, override: Override, device: DeviceRef) -> EnforcerResult:
		if override.kind != OverrideKind.LOCK:
			return self.unsupported(device, f"apply {override.kind}")
		self.pending = "lock"
		self._notify("lock", override)
		self.on_change()
		return self.result(ResultStatus.APPLIED, device, Mode.MANUAL, "parent asked to lock in the vendor app")

	async def revert(self, override: Override, device: DeviceRef) -> EnforcerResult:
		self.pending = "unlock"
		self._notify("unlock", override)
		self.on_change()
		return self.result(ResultStatus.APPLIED, device, Mode.MANUAL, "parent asked to unlock in the vendor app")

	def mark_done(self) -> None:
		"""The parent pressed done."""
		if self.pending is None:
			return
		self.confirmed_locked = self.pending == "lock"
		self.pending = None
		persistent_notification.async_dismiss(self.hass, self.notification_id)
		self.on_change()

	async def read_state(self, device: DeviceRef) -> EnforcedState:
		if self.pending is not None:
			return EnforcedState(
				device.device_id, locked=None, detail=f"waiting for a parent to {self.pending}", observed_at=dt_util.utcnow()
			)
		if self.confirmed_locked is None:
			return EnforcedState(device.device_id, locked=None, detail="never confirmed", observed_at=dt_util.utcnow())
		return EnforcedState(
			device.device_id, locked=self.confirmed_locked, detail="confirmed by a parent", observed_at=dt_util.utcnow()
		)

	async def health(self) -> Health:
		return Health(HealthStatus.HEALTHY)


class PresenceObserver(HAEnforcer):
	"""Level 0: says whether a device is in use from any HA entity. Never locks anything."""

	def __init__(self, hass: HomeAssistant, entity_id: str) -> None:
		super().__init__(
			hass,
			f"observer:{entity_id}",
			Capabilities(
				enforcer=f"observer:{entity_id}",
				level=0,
				usage_read=True,
				poll_interval_s=60,
				confirmation_window_s=0,
				notes="Charges minutes while the entity is on, playing or home.",
			),
		)
		self.entity_id = entity_id

	async def read_state(self, device: DeviceRef) -> EnforcedState:
		state = self._state(self.entity_id)
		in_use = None if state is None else state in IN_USE_STATES
		return EnforcedState(
			device.device_id, locked=None, in_use=in_use, detail=f"{self.entity_id} is {state}", observed_at=dt_util.utcnow()
		)

	async def usage(self, device: DeviceRef, day: date) -> list[UsageSample]:
		return []

	async def health(self) -> Health:
		return _entity_health(self.hass, self.entity_id)
