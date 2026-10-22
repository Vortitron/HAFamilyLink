"""Policy evaluation: allowances, bedtime, windows and app effects."""

from datetime import date, datetime

import pytest

from kerb_core import policy as pol
from kerb_core.models import Effect, Policy, TimeWindow

from .conftest import START, TZ


def test_allowance_follows_iso_weekday(policy: Policy) -> None:
	assert pol.allowance_for(policy, date(2026, 10, 19)) == 60  # Monday
	assert pol.allowance_for(policy, date(2026, 10, 21)) == 90  # Wednesday
	assert pol.allowance_for(policy, date(2026, 10, 25)) == 180  # Sunday


def test_policy_rejects_wrong_shapes() -> None:
	with pytest.raises(ValueError):
		Policy(child_id="c", allowance_minutes=[60] * 6)
	with pytest.raises(ValueError):
		Policy(child_id="c", allowance_minutes=[2000] + [60] * 6)


@pytest.mark.parametrize(
	("moment", "expected"),
	[
		(datetime(2026, 10, 21, 19, 59, tzinfo=TZ), False),
		(datetime(2026, 10, 21, 20, 0, tzinfo=TZ), True),
		(datetime(2026, 10, 22, 3, 0, tzinfo=TZ), True),  # early hours belong to Wednesday's window
		(datetime(2026, 10, 22, 7, 0, tzinfo=TZ), False),
		(datetime(2026, 10, 24, 20, 30, tzinfo=TZ), False),  # Saturday starts at 21:00
		(datetime(2026, 10, 25, 7, 30, tzinfo=TZ), True),  # Saturday's window runs to 08:00 Sunday
	],
)
def test_bedtime_handles_midnight(policy: Policy, moment: datetime, expected: bool) -> None:
	assert pol.in_bedtime(policy, moment) is expected


def test_bedtime_end_rolls_to_next_day(policy: Policy) -> None:
	end = pol.bedtime_end(policy, datetime(2026, 10, 21, 22, 0, tzinfo=TZ))
	assert end == datetime(2026, 10, 22, 7, 0, tzinfo=TZ)
	assert pol.bedtime_end(policy, START) is None


def test_windows_default_to_whole_day(policy: Policy) -> None:
	assert pol.in_allowed_window(policy, START)
	assert pol.next_window_start(policy, START) == datetime(2026, 10, 22, 0, 0, tzinfo=TZ)


def test_windows_restrict_and_report_next_start(alice) -> None:
	policy = Policy(child_id=alice.id)
	policy.windows[2] = [TimeWindow("07:00", "08:00"), TimeWindow("18:00", "19:30")]
	assert not pol.in_allowed_window(policy, START)
	assert pol.next_window_start(policy, START) == datetime(2026, 10, 21, 18, 0, tzinfo=TZ)
	assert pol.in_allowed_window(policy, datetime(2026, 10, 21, 18, 30, tzinfo=TZ))
	late = datetime(2026, 10, 21, 20, 0, tzinfo=TZ)
	assert pol.next_window_start(policy, late) == pol.end_of_day(late)


def test_app_rule_beats_tag_rule(alice) -> None:
	policy = Policy(child_id=alice.id)
	policy.app_rules["android:com.mojang.minecraftpe"] = Effect.COUNT_HALF
	policy.tag_rules["chat_with_strangers"] = Effect.BLOCK
	effect, rule = pol.effect_for_app(policy, "android:com.mojang.minecraftpe", {"chat_with_strangers"})
	assert (effect, rule) == (Effect.COUNT_HALF, "app:android:com.mojang.minecraftpe")


def test_strictest_tag_rule_wins(alice) -> None:
	policy = Policy(child_id=alice.id)
	policy.tag_rules["educational"] = Effect.ALLOW_ALWAYS
	policy.tag_rules["chat_with_strangers"] = Effect.BLOCK
	policy.tag_rules["creative"] = Effect.COUNT_HALF
	assert pol.effect_for_app(policy, "steam:1", {"educational", "chat_with_strangers"}) == (
		Effect.BLOCK,
		"tag:chat_with_strangers",
	)
	assert pol.effect_for_app(policy, "steam:1", {"educational", "creative"}) == (Effect.COUNT_HALF, "tag:creative")
	assert pol.effect_for_app(policy, "steam:1", {"educational"}) == (Effect.ALLOW_ALWAYS, "tag:educational")


def test_default_effect_is_allow_at_full_rate(policy: Policy) -> None:
	assert pol.effect_for_app(policy, None) == (Effect.ALLOW, "default")
	assert pol.effect_for_app(policy, "xbox:1", {"solo"}) == (Effect.ALLOW, "default")
	assert pol.rate_for(Effect.ALLOW) == 1.0
	assert pol.rate_for(Effect.COUNT_HALF) == 0.5
	assert pol.rate_for(Effect.COUNT_DOUBLE) == 2.0
	assert pol.rate_for(Effect.ALLOW_ALWAYS) == 0.0


def test_policy_round_trips_through_dict(policy: Policy) -> None:
	policy.app_rules["xbox:1"] = Effect.BLOCK
	policy.tag_rules["educational"] = Effect.ALLOW_ALWAYS
	again = Policy.from_dict(policy.to_dict())
	assert again.to_dict() == policy.to_dict()
