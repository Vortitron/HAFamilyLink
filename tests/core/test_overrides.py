"""Override stacking and status aggregation."""

from datetime import timedelta

import pytest

from kerb_core import overrides as ov
from kerb_core.models import EnforcerResult, Override, OverrideKind, OverrideStatus, ResultStatus, Scope

from .conftest import START


def make(
	kind: OverrideKind, offset_min: int, scope: Scope | None = None, status=OverrideStatus.CONFIRMED, minutes=60
) -> Override:
	start = START + timedelta(minutes=offset_min)
	return Override(
		child_id="c",
		kind=kind,
		source="guardian:andy",
		starts_at=start,
		expires_at=start + timedelta(minutes=minutes),
		scope=scope or Scope(),
		status=status,
	)


def test_newest_lock_wins_over_grant() -> None:
	lock = make(OverrideKind.LOCK, 0)
	grant = make(OverrideKind.GRANT, 5)
	assert ov.effective_lock([grant, lock], START + timedelta(minutes=10)) is lock


def test_unlock_after_lock_lifts_and_lock_after_unlock_locks_again() -> None:
	lock = make(OverrideKind.LOCK, 0)
	unlock = make(OverrideKind.UNLOCK, 5)
	relock = make(OverrideKind.LOCK, 10)
	now = START + timedelta(minutes=7)
	assert ov.effective_lock([lock, unlock], now) is None
	assert ov.effective_lock([lock, unlock, relock], START + timedelta(minutes=12)) is relock


def test_expired_and_cancelled_locks_do_not_count() -> None:
	expired = make(OverrideKind.LOCK, -120, minutes=30)
	cancelled = make(OverrideKind.LOCK, 0, status=OverrideStatus.CANCELLED)
	assert ov.effective_lock([expired, cancelled], START + timedelta(minutes=1)) is None


def test_device_scope_only_covers_that_device() -> None:
	lock = make(OverrideKind.LOCK, 0, Scope("device", device_id="ps5"))
	now = START + timedelta(minutes=1)
	assert ov.effective_lock([lock], now, "ps5") is lock
	assert ov.effective_lock([lock], now, "phone") is None
	# A child-level question still sees a device lock as "something is locked".
	assert ov.effective_lock([lock], now) is lock


def test_device_unlock_leaves_a_child_lock_on_other_devices() -> None:
	lock = make(OverrideKind.LOCK, 0)
	unlock = make(OverrideKind.UNLOCK, 5, Scope("device", device_id="ps5"))
	now = START + timedelta(minutes=6)
	assert ov.effective_lock([lock, unlock], now, "ps5") is None
	assert ov.effective_lock([lock, unlock], now, "xbox") is lock
	assert ov.effective_lock([lock, unlock], now) is lock
	assert ov.locks_in_force([lock, unlock], now, "xbox") == [lock]


def test_cancel_records_do_not_lift_other_locks() -> None:
	first = make(OverrideKind.LOCK, 0)
	second = make(OverrideKind.LOCK, 5)
	first.status = OverrideStatus.CANCELLED
	record = make(OverrideKind.UNLOCK, 10)
	record.cancels = first.id
	assert ov.effective_lock([first, second, record], START + timedelta(minutes=11)) is second


def test_app_scope_never_locks_a_device() -> None:
	lock = make(OverrideKind.LOCK, 0, Scope("app", app="steam:252950"))
	assert ov.effective_lock([lock], START + timedelta(minutes=1), "pc") is None


def test_allowance_today_returns_newest() -> None:
	first = make(OverrideKind.ALLOWANCE_TODAY, 0, minutes=120)
	second = make(OverrideKind.ALLOWANCE_TODAY, 5, minutes=120)
	assert ov.allowance_today([first, second], START + timedelta(minutes=6)) is second


WINDOW = timedelta(seconds=120)


def results(*statuses: ResultStatus) -> list[EnforcerResult]:
	return [EnforcerResult(f"e{index}", status) for index, status in enumerate(statuses)]


@pytest.mark.parametrize(
	("statuses", "elapsed_s", "expected"),
	[
		((), 0, OverrideStatus.FAILED),
		((ResultStatus.CONFIRMED,), 0, OverrideStatus.CONFIRMED),
		((ResultStatus.CONFIRMED, ResultStatus.CONFIRMED), 500, OverrideStatus.CONFIRMED),
		((ResultStatus.APPLIED,), 10, OverrideStatus.APPLIED),
		((ResultStatus.APPLIED, ResultStatus.CONFIRMED), 10, OverrideStatus.APPLIED),
		((ResultStatus.APPLIED, ResultStatus.CONFIRMED), 121, OverrideStatus.PARTIAL),
		((ResultStatus.APPLIED,), 121, OverrideStatus.FAILED),
		((ResultStatus.FAILED, ResultStatus.CONFIRMED), 10, OverrideStatus.PARTIAL),
		((ResultStatus.FAILED,), 10, OverrideStatus.FAILED),
		((ResultStatus.UNKNOWN, ResultStatus.CONFIRMED), 10, OverrideStatus.PARTIAL),
		((ResultStatus.UNKNOWN,), 10, OverrideStatus.FAILED),
	],
)
def test_aggregate_status(statuses, elapsed_s, expected) -> None:
	now = START + timedelta(seconds=elapsed_s)
	assert ov.aggregate_status(results(*statuses), START, WINDOW, now) == expected


def test_unconfirmed_lists_everything_but_confirmed() -> None:
	found = ov.unconfirmed(results(ResultStatus.CONFIRMED, ResultStatus.FAILED, ResultStatus.UNKNOWN))
	assert [result.status for result in found] == [ResultStatus.FAILED, ResultStatus.UNKNOWN]


def test_override_round_trip() -> None:
	override = make(OverrideKind.LOCK, 0)
	override.results.append(EnforcerResult("unifi", ResultStatus.CONFIRMED, device_id="d", confirmed_at=START, restore={"a": 1}))
	again = Override.from_dict(override.to_dict())
	assert again.to_dict() == override.to_dict()
	assert again.results[0].restore == {"a": 1}
