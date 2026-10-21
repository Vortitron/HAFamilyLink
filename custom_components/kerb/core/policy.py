"""Policy evaluation: allowances, windows, bedtime and per-app effects (SPEC.md 3.4)."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, time, timedelta

from .models import EFFECT_RATE, Effect, Policy, TimeWindow

# Most restrictive first. When several tag rules match an app the strictest wins.
EFFECT_STRICTNESS: tuple[Effect, ...] = (
	Effect.BLOCK,
	Effect.REQUIRE_APPROVAL,
	Effect.COUNT_DOUBLE,
	Effect.ALLOW,
	Effect.COUNT_HALF,
	Effect.ALLOW_ALWAYS,
)


def weekday_index(day: date) -> int:
	"""Monday is 0, matching index 0 of every seven-entry policy list."""
	return day.weekday()


def hhmm(moment: datetime) -> str:
	return moment.strftime("%H:%M")


def parse_hhmm(value: str, day: date, tzinfo) -> datetime:
	hour, minute = (int(part) for part in value.split(":"))
	return datetime.combine(day, time(hour, minute), tzinfo=tzinfo)


def end_of_day(moment: datetime) -> datetime:
	"""Midnight at the end of the local day that contains ``moment``."""
	return datetime.combine(moment.date() + timedelta(days=1), time.min, tzinfo=moment.tzinfo)


def allowance_for(policy: Policy, day: date) -> int:
	return policy.allowance_minutes[weekday_index(day)]


def bedtime_for(policy: Policy, moment: datetime) -> TimeWindow | None:
	"""The bedtime window in force at ``moment``, if any.

	A window that runs past midnight belongs to the day it starts on, so the
	early hours check the previous day's window too.
	"""
	now = hhmm(moment)
	today = policy.bedtime[weekday_index(moment.date())]
	if today is not None and today.contains(now):
		if today.start <= today.end or now >= today.start:
			return today
	yesterday = policy.bedtime[weekday_index(moment.date() - timedelta(days=1))]
	if yesterday is not None and yesterday.start > yesterday.end and now < yesterday.end:
		return yesterday
	return None


def in_bedtime(policy: Policy, moment: datetime) -> bool:
	return bedtime_for(policy, moment) is not None


def bedtime_end(policy: Policy, moment: datetime) -> datetime | None:
	"""When the bedtime in force at ``moment`` ends, as an aware datetime."""
	window = bedtime_for(policy, moment)
	if window is None:
		return None
	end = parse_hhmm(window.end, moment.date(), moment.tzinfo)
	if end <= moment:
		end += timedelta(days=1)
	return end


def windows_for(policy: Policy, day: date) -> list[TimeWindow]:
	return policy.windows[weekday_index(day)]


def in_allowed_window(policy: Policy, moment: datetime) -> bool:
	"""No windows configured for the day means the whole day is allowed."""
	windows = windows_for(policy, moment.date())
	if not windows:
		return True
	now = hhmm(moment)
	return any(window.contains(now) for window in windows)


def next_window_start(policy: Policy, moment: datetime) -> datetime:
	"""When screens next open after ``moment``. End of day if no later window today."""
	now = hhmm(moment)
	starts = sorted(window.start for window in windows_for(policy, moment.date()) if window.start > now)
	if starts:
		return parse_hhmm(starts[0], moment.date(), moment.tzinfo)
	return end_of_day(moment)


def strictest(effects: Iterable[Effect]) -> Effect | None:
	ranked = [effect for effect in EFFECT_STRICTNESS if effect in set(effects)]
	return ranked[0] if ranked else None


def effect_for_app(policy: Policy, app: str | None, tags: Iterable[str] = ()) -> tuple[Effect, str]:
	"""Resolve the effect for an app and say which rule produced it.

	A per-app rule beats any tag rule. Among several matching tag rules the
	strictest wins. With no match the effect is ``allow`` from the ``default`` rule.
	"""
	if app is not None and app in policy.app_rules:
		return policy.app_rules[app], f"app:{app}"
	matched = {tag: policy.tag_rules[tag] for tag in tags if tag in policy.tag_rules}
	if matched:
		effect = strictest(matched.values())
		assert effect is not None
		winning = sorted(tag for tag, value in matched.items() if value == effect)[0]
		return effect, f"tag:{winning}"
	return Effect.ALLOW, "default"


def rate_for(effect: Effect) -> float:
	return EFFECT_RATE[effect]
