"""Round trips keep unknown and x_ properties, as SPEC.md section 3 promises."""

from datetime import datetime
from zoneinfo import ZoneInfo

from kerb_core.ledger import DayLedger
from kerb_core.models import (
	Effect,
	EnforcerResult,
	LedgerEntry,
	Mode,
	Override,
	OverrideKind,
	Policy,
	RatingClaim,
	ResultStatus,
	Scope,
	TimeWindow,
)

NOW = datetime(2026, 10, 21, 17, 0, tzinfo=ZoneInfo("Europe/London"))
EXTRA = {"x_vendor": {"note": "kept"}, "future_field": 7}


def test_override_round_trip_keeps_extensions() -> None:
	override = Override(
		child_id="c",
		kind=OverrideKind.LOCK,
		source="guardian:andy",
		starts_at=NOW,
		expires_at=NOW,
		scope=Scope("device", device_id="d"),
		results=[EnforcerResult("unifi", ResultStatus.APPLIED, "d", Mode.NETWORK)],
	)
	data = override.to_dict() | EXTRA
	data["scope"] |= {"x_hint": 1}
	data["results"][0] |= {"x_raw": "200 OK"}
	again = Override.from_dict(data)
	assert again.extras == EXTRA
	assert again.to_dict() == data
	assert again.scope == override.scope  # extras never affect equality
	assert again.results[0].to_dict()["x_raw"] == "200 OK"


def test_policy_round_trip_keeps_extensions() -> None:
	policy = Policy(
		child_id="c",
		windows=[[TimeWindow("07:00", "08:30")]] + [[] for _ in range(6)],
		rating_ceiling=RatingClaim("PEGI", "7", "https://pegi.info", "2026-10-21T17:00:00+01:00"),
		app_rules={"steam:1": Effect.COUNT_HALF},
	)
	data = policy.to_dict() | EXTRA | {"profile_ref": "strict_under_10@3"}
	data["rating_ceiling"] |= {"x_foo": True}
	again = Policy.from_dict(data)
	assert again.to_dict() == data
	assert again.rating_ceiling is not None and again.rating_ceiling.extras == {"x_foo": True}
	assert again.app_rules == policy.app_rules


def test_ledger_entry_round_trip_keeps_extensions() -> None:
	entry = LedgerEntry("c", "2026-10-21", "usage", 5, NOW, rate=0.0, app="steam:1", rule="tag:educational")
	data = entry.to_dict() | EXTRA
	again = LedgerEntry.from_dict(data)
	assert again.to_dict() == data
	assert again.rate == 0.0
	ledger = DayLedger.from_dict({"child_id": "c", "date": "2026-10-21", "entries": [data]})
	assert ledger.to_dict()["entries"] == [data]


def test_known_keys_win_over_extras() -> None:
	scope = Scope("all", extras={"type": "device"})
	assert scope.to_dict()["type"] == "all"
