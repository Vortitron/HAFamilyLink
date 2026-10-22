"""The JSON Schemas parse, the examples validate, and the core models emit valid documents."""

from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from jsonschema import Draft202012Validator
import pytest
from referencing import Registry, Resource

from kerb_core.models import (
	AgeBand,
	Capabilities,
	Child,
	Device,
	DeviceRef,
	Effect,
	EnforcedState,
	EnforcerResult,
	Event,
	Health,
	HealthStatus,
	Household,
	LedgerEntry,
	Mode,
	Override,
	OverrideKind,
	Platform,
	Policy,
	RatingClaim,
	Request,
	ResultStatus,
	Scope,
	TimeWindow,
	UsageSample,
)

SCHEMAS = Path(__file__).resolve().parents[1] / "docs" / "schemas"
NOW = datetime(2026, 10, 21, 17, 0, tzinfo=ZoneInfo("Europe/London"))
UUID = "8d0c0b8a-0f8e-4e4f-9d8f-6f8f6b3b2a11"


def load(name: str) -> dict:
	return json.loads((SCHEMAS / f"{name}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registry() -> Registry:
	resources = []
	for path in SCHEMAS.glob("*.json"):
		schema = json.loads(path.read_text(encoding="utf-8"))
		resources.append((schema["$id"], Resource.from_contents(schema)))
	return Registry().with_resources(resources)


def validator(name: str, registry: Registry) -> Draft202012Validator:
	return Draft202012Validator(load(name), registry=registry, format_checker=Draft202012Validator.FORMAT_CHECKER)


@pytest.mark.parametrize("path", sorted(SCHEMAS.glob("*.json")), ids=lambda path: path.stem)
def test_schema_is_valid_2020_12(path: Path) -> None:
	schema = json.loads(path.read_text(encoding="utf-8"))
	Draft202012Validator.check_schema(schema)
	assert schema["$id"] == f"https://kerb.dev/schema/0.1/{path.name}"


@pytest.mark.parametrize("path", sorted((SCHEMAS / "examples").glob("*.json")), ids=lambda path: path.stem)
def test_examples_validate(path: Path, registry: Registry) -> None:
	# examples/<schema>_<label>.json
	name = path.stem.rsplit("_", 1)[0]
	validator(name, registry).validate(json.loads(path.read_text(encoding="utf-8")))


def errors(name: str, registry: Registry, document: dict) -> list[str]:
	return [error.message for error in validator(name, registry).iter_errors(document)]


def test_override_model_validates(registry: Registry) -> None:
	override = Override(
		id=UUID,
		child_id=UUID,
		kind=OverrideKind.LOCK,
		scope=Scope("device", device_id=UUID),
		minutes=60,
		reason="dinner",
		source="guardian:andy",
		starts_at=NOW,
		expires_at=NOW,
		results=[
			EnforcerResult("unifi", ResultStatus.CONFIRMED, UUID, Mode.NETWORK, "blocked", NOW),
			EnforcerResult("family_safety", ResultStatus.APPLIED, UUID, Mode.ZERO_ALLOWANCE, restore={"days": [0] * 7}),
		],
	)
	validator("override", registry).validate(override.to_dict())


def test_policy_model_validates(registry: Registry) -> None:
	policy = Policy(
		id=UUID,
		child_id=UUID,
		allowance_minutes=[60] * 7,
		windows=[[TimeWindow("07:00", "08:30")]] + [[] for _ in range(6)],
		bedtime=[TimeWindow("20:00", "07:00")] + [None] * 6,
		rating_ceiling=RatingClaim("PEGI", "7", "https://pegi.info", "2026-10-21T17:00:00+01:00", "GB"),
		app_rules={"android:com.mojang.minecraftpe": Effect.COUNT_HALF},
		tag_rules={"educational": Effect.ALLOW_ALWAYS},
		grant_cap_minutes_per_day=60,
	)
	validator("policy", registry).validate(policy.to_dict())


def test_other_models_validate(registry: Registry) -> None:
	validator("child", registry).validate(Child("Alice", AgeBand.SEVEN_TO_12, UUID, id=UUID).to_dict())
	validator("device", registry).validate(
		Device(
			"PS5",
			Platform.PLAYSTATION,
			child_id=UUID,
			enforcer_ids=["network:switch.ps5"],
			network={"mac": ["AA:BB:CC:DD:EE:FF"]},
			id=UUID,
		).to_dict()
	)
	validator("household", registry).validate(Household("Europe/London", ["andy"], id=UUID).to_dict())
	validator("ledger_entry", registry).validate(
		LedgerEntry(
			UUID,
			"2026-10-21",
			"usage",
			12.5,
			NOW,
			rate=0.5,
			device_id=UUID,
			app="steam:1",
			rule="tag:educational",
			per_app_usage_available=True,
			id=UUID,
		).to_dict()
	)
	# allow_always use is recorded at rate 0.0: counted, never charged.
	validator("ledger_entry", registry).validate(
		LedgerEntry(UUID, "2026-10-21", "usage", 3, NOW, rate=0.0, device_id=UUID, rule="tag:educational", id=UUID).to_dict()
	)
	validator("usage_sample", registry).validate(UsageSample(UUID, UUID, NOW, NOW, 600, "observer", NOW, app="steam:1").to_dict())
	validator("request", registry).validate(
		Request(UUID, "more_time", NOW, "family_safety", minutes=15, device_id=UUID, id=UUID).to_dict()
	)
	validator("capabilities", registry).validate(
		Capabilities("network", 1, network_block=True, lock_now=True, manual=False).to_dict()
	)
	validator("event", registry).validate(Event("override.confirmed", UUID, NOW, UUID, {"override_id": UUID}).to_dict())


def test_enforcer_interface_models_validate(registry: Registry) -> None:
	validator("device_ref", registry).validate(DeviceRef(UUID, "PS5", Platform.PLAYSTATION, True).to_dict())
	validator("enforced_state", registry).validate(EnforcedState(UUID, locked=None, detail="cannot read").to_dict())
	validator("enforced_state", registry).validate(EnforcedState(UUID, locked=True, in_use=False, observed_at=NOW).to_dict())
	validator("health", registry).validate(Health(HealthStatus.REVOKED, "session lost").to_dict())
	validator("enforcer_result", registry).validate(EnforcerResult("unifi", ResultStatus.APPLIED, UUID, Mode.NETWORK).to_dict())


def test_scope_type_requires_its_target(registry: Registry) -> None:
	base = {
		"id": UUID,
		"child_id": UUID,
		"kind": "lock",
		"source": "guardian:andy",
		"starts_at": "2026-10-21T17:00:00+01:00",
		"expires_at": "2026-10-21T18:00:00+01:00",
		"status": "requested",
	}
	assert errors("override", registry, {**base, "scope": {"type": "device"}}) == ["'device_id' is a required property"]
	assert errors("override", registry, {**base, "scope": {"type": "app"}}) == ["'app' is a required property"]
	assert errors("override", registry, {**base, "scope": {"type": "tag"}}) == ["'tag' is a required property"]
	assert errors("override", registry, {**base, "scope": {"type": "all"}}) == []


def test_grant_and_allowance_today_require_minutes(registry: Registry) -> None:
	base = {
		"id": UUID,
		"child_id": UUID,
		"scope": {"type": "all"},
		"source": "guardian:andy",
		"starts_at": "2026-10-21T17:00:00+01:00",
		"expires_at": "2026-10-22T00:00:00+01:00",
		"status": "confirmed",
	}
	for kind in ("grant", "allowance_today"):
		assert errors("override", registry, {**base, "kind": kind}) == ["'minutes' is a required property"]
		assert errors("override", registry, {**base, "kind": kind, "minutes": 20}) == []
	assert errors("override", registry, {**base, "kind": "unlock"}) == []


def test_timestamps_need_an_explicit_offset(registry: Registry) -> None:
	event = {"type": "override.confirmed", "household_id": UUID, "at": "2026-10-21T17:00:00"}
	assert errors("event", registry, event)
	assert errors("event", registry, {**event, "at": "2026-10-21T17:00:00Z"}) == []
	assert errors("event", registry, {**event, "at": "2026-10-21T17:00:00.123456+01:00"}) == []
	# The models always emit aware datetimes.
	assert errors("event", registry, Event("override.confirmed", UUID, NOW).to_dict()) == []


def test_community_objects_refuse_extra_data(registry: Registry) -> None:
	vote = json.loads((SCHEMAS / "examples" / "tag_vote_educational.json").read_text(encoding="utf-8"))
	assert errors("tag_vote", registry, vote) == []
	assert errors("tag_vote", registry, {**vote, "child_name": "Alice"})
	assert errors("tag_vote", registry, {**vote, "usage_minutes": 40})
	assert errors("tag_vote", registry, {**vote, "x_client_hint": "ok"}) == []
	assert errors("tag_vote", registry, {**vote, "evidence": "https://example.com/screenshot.png"})
	assert errors("tag_vote", registry, {**vote, "household_id": UUID})
	profile = {"id": UUID, "name": "Strict under 10", "version": 1, "age_band": "under_7", "tag_rules": []}
	assert errors("profile", registry, profile) == []
	assert errors("profile", registry, {**profile, "children": ["Alice"]})


def test_policy_has_no_phase_3_fields_yet(registry: Registry) -> None:
	policy = {
		"id": UUID,
		"child_id": UUID,
		"allowance_minutes": [60] * 7,
		"app_rules": [{"app": "steam:1", "effect": "allow", "daily_limit_minutes": 30}],
	}
	assert errors("policy", registry, policy)
	policy["app_rules"] = [{"app": "steam:1", "effect": "allow"}]
	policy["tag_rules"] = [{"tag": "chat_with_strangers", "effect": "block", "windows": [{"start": "19:00", "end": "23:30"}]}]
	assert errors("policy", registry, policy)
