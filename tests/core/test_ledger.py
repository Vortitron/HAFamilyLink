"""The daily ledger."""

import pytest

from kerb_core.ledger import DayLedger, GrantCapExceeded
from kerb_core.models import Override, OverrideKind

from .conftest import START


@pytest.fixture
def ledger() -> DayLedger:
	ledger = DayLedger(child_id="c", date="2026-10-21")
	ledger.add_allowance(90, START, "policy")
	return ledger


def test_remaining_is_allowance_plus_grants_minus_penalties_minus_weighted_usage(ledger: DayLedger) -> None:
	ledger.add_grant(20, START, "taskmate", "emptied the dishwasher")
	ledger.add_penalty(5, START, "guardian:andy", "rude")
	ledger.charge_usage(30, START, rate=1.0, device_id="ps5")
	ledger.charge_usage(
		20, START, rate=0.5, device_id="phone", app="android:x", rule="tag:educational", per_app_usage_available=True
	)
	ledger.charge_usage(10, START, rate=2.0, device_id="phone", app="android:y", per_app_usage_available=True)
	assert ledger.budget == 105
	assert ledger.used_raw == 60
	assert ledger.used_weighted == 60
	assert ledger.remaining == 45


def test_remaining_never_negative(ledger: DayLedger) -> None:
	ledger.charge_usage(500, START)
	assert ledger.remaining == 0


def test_newest_allowance_wins(ledger: DayLedger) -> None:
	ledger.add_allowance(30, START, "guardian:andy")
	assert ledger.allowance == 30


def test_grant_cap(ledger: DayLedger) -> None:
	ledger.add_grant(40, START, "guardian", cap=60)
	with pytest.raises(GrantCapExceeded):
		ledger.add_grant(30, START, "guardian", cap=60)
	assert ledger.granted == 40
	with pytest.raises(ValueError):
		ledger.add_grant(0, START, "guardian")


def test_zero_usage_is_not_recorded(ledger: DayLedger) -> None:
	assert ledger.charge_usage(0, START) is None
	assert len(ledger.entries) == 1


def test_devices_without_per_app_usage(ledger: DayLedger) -> None:
	ledger.charge_usage(5, START, device_id="ps5", per_app_usage_available=False)
	ledger.charge_usage(5, START, device_id="phone", app="a", per_app_usage_available=True)
	assert ledger.devices_without_per_app_usage == ["ps5"]


def test_lock_entry_and_round_trip(ledger: DayLedger) -> None:
	override = Override(
		child_id="c", kind=OverrideKind.LOCK, source="guardian:andy", starts_at=START, expires_at=START, reason="dinner"
	)
	ledger.add_lock(override, START)
	again = DayLedger.from_dict(ledger.to_dict())
	assert again.to_dict() == ledger.to_dict()
	assert again.entries[-1].kind == "lock"
	assert again.entries[-1].reason == "dinner"
