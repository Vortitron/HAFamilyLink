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


def effective_lock(overrides: Iterable[Override], now: datetime, device_id: str | None = None) -> Override | None:
	"""The lock in force for a device (or the whole child), or None.

	The newest decision wins. A lock issued after an unlock locks again; an
	unlock issued after a lock lifts it. Grants never lift a lock.
	"""
	decisions = [
		override
		for override in active(overrides, now)
		if override.kind in (OverrideKind.LOCK, OverrideKind.UNLOCK)
		and (device_id is None or override.scope.covers_device(device_id))
		and override.scope.type in ("all", "device")
	]
	if not decisions:
		return None
	newest = decisions[-1]
	return newest if newest.kind == OverrideKind.LOCK else None


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
