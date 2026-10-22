"""Override stacking and confirmation status (SPEC.md 3.5 and 4.2)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta

from .models import EnforcerResult, Override, OverrideKind, OverrideStatus, ResultStatus

# Statuses that no longer change. A failed override is settled but still in force as a decision.
SETTLED = (OverrideStatus.CANCELLED, OverrideStatus.EXPIRED, OverrideStatus.FAILED)


def active(overrides: Iterable[Override], now: datetime, kind: OverrideKind | None = None) -> list[Override]:
	"""Overrides in force at ``now``, oldest first. Ties keep issue order."""
	found = [override for override in overrides if override.active_at(now) and (kind is None or override.kind == kind)]
	return sorted(found, key=lambda override: override.starts_at)


def _decisions(overrides: Iterable[Override], now: datetime, device_id: str | None) -> list[Override]:
	"""Locks and unlocks in force that bear on a device, oldest first.

	Compensating records (``cancels`` set) are not decisions in their own
	right: the override they cancel is already marked cancelled, and they
	must not lift any other lock.
	"""
	return [
		override
		for override in active(overrides, now)
		if override.kind in (OverrideKind.LOCK, OverrideKind.UNLOCK)
		and override.cancels is None
		and override.scope.type in ("all", "device")
		and (device_id is None or override.scope.covers_device(device_id))
	]


def locks_in_force(overrides: Iterable[Override], now: datetime, device_id: str | None = None) -> list[Override]:
	"""Every lock still holding a device, or any device when ``device_id`` is None, oldest first.

	An unlock lifts the locks issued before it that it covers. For one device
	every decision that bears on it covers it. For the whole child a device
	unlock only lifts locks scoped to that device: a lock on every device stays
	in force for the others.
	"""
	held: list[Override] = []
	for decision in _decisions(overrides, now, device_id):
		if decision.kind == OverrideKind.LOCK:
			held.append(decision)
		elif device_id is not None or decision.scope.type == "all":
			held = []
		else:
			held = [lock for lock in held if lock.scope != decision.scope]
	return held


def effective_lock(overrides: Iterable[Override], now: datetime, device_id: str | None = None) -> Override | None:
	"""The lock in force for a device (or the whole child), or None.

	The newest decision wins. A lock issued after an unlock locks again; an
	unlock issued after a lock lifts it. Grants never lift a lock.
	"""
	held = locks_in_force(overrides, now, device_id)
	return held[-1] if held else None


def allowance_today(overrides: Iterable[Override], now: datetime) -> Override | None:
	"""The newest ``allowance_today`` override in force, if any."""
	found = active(overrides, now, OverrideKind.ALLOWANCE_TODAY)
	return found[-1] if found else None


def aggregate_status(
	results: Iterable[EnforcerResult],
	requested_at: datetime,
	confirmation_window: timedelta,
	now: datetime,
) -> OverrideStatus:
	"""Fold per-enforcer results into one override status.

	``confirmed`` needs every asked enforcer to have read back the new state.
	While the window is open and something is still pending the answer is
	``applied``. Once everything has settled, or the window has closed, any
	confirmation gives ``partial`` and none gives ``failed``. An override that
	asked nobody has failed: nothing was enforced.
	"""
	results = list(results)
	if not results:
		return OverrideStatus.FAILED
	statuses = {result.status for result in results}
	if statuses == {ResultStatus.CONFIRMED}:
		return OverrideStatus.CONFIRMED
	pending = statuses & {ResultStatus.REQUESTED, ResultStatus.APPLIED}
	window_open = now < requested_at + confirmation_window
	if pending and window_open:
		return OverrideStatus.APPLIED
	if ResultStatus.CONFIRMED in statuses:
		return OverrideStatus.PARTIAL
	return OverrideStatus.FAILED


def unconfirmed(results: Iterable[EnforcerResult]) -> list[EnforcerResult]:
	return [result for result in results if result.status != ResultStatus.CONFIRMED]
