"""The controller end to end against fake enforcers."""

from datetime import datetime

import pytest

from kerb_core.controller import SOURCE_BEDTIME, SOURCE_EXHAUSTED, SOURCE_WINDOW, Controller
from kerb_core.ledger import GrantCapExceeded
from kerb_core.models import (
	ChildStatus,
	Confidence,
	EnforcementStatus,
	HealthStatus,
	Mode,
	OverrideStatus,
	Policy,
	ResultStatus,
	Scope,
	TimeWindow,
)

from .conftest import TZ, Clock, FakeEnforcer, add_device


def types(events) -> list[str]:
	return [event.type for event in events]


async def test_lock_uses_network_and_manual_but_not_power_without_opt_in(controller: Controller, alice, events) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	plug = FakeEnforcer("plug", Mode.POWER)
	manual = FakeEnforcer("manual", Mode.MANUAL)
	add_device(controller, "PS5", alice.id, unifi, plug, manual)
	override = await controller.lock(alice.id, minutes=60, reason="dinner", source="guardian:andy")
	assert {result.enforcer for result in override.results} == {"unifi", "manual"}
	assert list(unifi.locked.values()) == [True]
	assert plug.calls == []
	assert override.status == OverrideStatus.APPLIED  # manual has not been pressed yet
	assert types(events)[:1] == ["override.applied"]
	state = controller.child_state(alice.id)
	assert state.status == ChildStatus.LOCKED
	assert state.enforcement == EnforcementStatus.PENDING  # awaiting the parent, not a problem
	assert state.summary == [
		"PS5 network blocked (unifi). PS5 may still run offline games.",
		"PS5 manual action requested (manual). PS5 waiting for a parent to press done. Awaiting confirmation.",
	]


async def test_power_used_when_the_parent_opted_in(controller: Controller, alice) -> None:
	plug = FakeEnforcer("plug", Mode.POWER)
	add_device(controller, "Xbox", alice.id, plug, power_opt_in=True)
	override = await controller.lock(alice.id, minutes=30)
	assert override.status == OverrideStatus.CONFIRMED
	assert override.results[0].mode == Mode.POWER
	assert controller.summary(override) == ["Xbox powered off (plug)."]


async def test_explicit_mode_filters_enforcers(controller: Controller, alice) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	plug = FakeEnforcer("plug", Mode.POWER)
	add_device(controller, "Xbox", alice.id, unifi, plug, power_opt_in=True)
	override = await controller.lock(alice.id, minutes=30, mode="power")
	assert [result.enforcer for result in override.results] == ["plug"]
	assert unifi.calls == []


async def test_lock_with_nobody_to_ask_fails_honestly(controller: Controller, alice, events) -> None:
	override = await controller.lock(alice.id, minutes=30)
	assert override.status == OverrideStatus.FAILED
	assert "override.failed" in types(events)
	# The decision stands, so the status sensor says locked and enforcement says degraded.
	assert controller.child_state(alice.id).status == ChildStatus.LOCKED
	assert controller.child_state(alice.id).enforcement == EnforcementStatus.DEGRADED


async def test_vendor_200_without_change_is_not_confirmed(controller: Controller, alice, events, clock: Clock) -> None:
	liar = FakeEnforcer("family_safety", Mode.ZERO_ALLOWANCE, noop=True, confirmation_window_s=120)
	add_device(controller, "Xbox", alice.id, liar)
	override = await controller.lock(alice.id, minutes=60)
	assert override.status == OverrideStatus.APPLIED
	assert override.results[0].restore == {"allowance": 120}
	clock.advance(minutes=1)
	await controller.tick()
	assert override.status == OverrideStatus.APPLIED
	clock.advance(minutes=2)
	await controller.tick()
	assert override.status == OverrideStatus.FAILED
	assert "enforcement.unconfirmed" in types(events)
	unconfirmed = next(event for event in events if event.type == "enforcement.unconfirmed")
	assert unconfirmed.payload["enforcer"] == "family_safety"


async def test_partial_when_one_enforcer_confirms_and_one_does_not(controller: Controller, alice, clock: Clock) -> None:
	good = FakeEnforcer("unifi", Mode.NETWORK)
	bad = FakeEnforcer("plug", Mode.POWER, noop=True, confirmation_window_s=60)
	add_device(controller, "Xbox", alice.id, good, bad, power_opt_in=True)
	override = await controller.lock(alice.id, minutes=60)
	clock.advance(minutes=2)
	await controller.tick()
	assert override.status == OverrideStatus.PARTIAL
	assert controller.child_state(alice.id).enforcement == EnforcementStatus.PARTIAL


async def test_flaky_enforcer_becomes_a_failed_result_not_a_crash(controller: Controller, alice) -> None:
	add_device(controller, "Xbox", alice.id, FakeEnforcer("unifi", Mode.NETWORK, flaky=True))
	override = await controller.lock(alice.id, minutes=10)
	assert override.status == OverrideStatus.FAILED
	assert override.results[0].detail == "vendor said no"
	assert controller.summary(override) == ["Xbox (unifi): failed, vendor said no."]


async def test_unknown_enforcer_means_unknown_never_free(controller: Controller, alice, events) -> None:
	lost = FakeEnforcer("family_link", Mode.PAUSE, health=HealthStatus.REVOKED)
	add_device(controller, "Phone", alice.id, lost)
	await controller.tick()
	assert "enforcer.degraded" in types(events)
	state = controller.child_state(alice.id)
	assert state.status == ChildStatus.UNKNOWN
	assert state.enforcement == EnforcementStatus.UNKNOWN
	assert state.confidence == Confidence.STALE
	assert state.degraded_enforcers == ["family_link"]
	override = await controller.lock(alice.id, minutes=10)
	assert override.results[0].status == ResultStatus.UNKNOWN
	assert override.status == OverrideStatus.FAILED
	lost.health_status = HealthStatus.HEALTHY
	await controller.tick()
	assert "enforcer.restored" in types(events)
	assert controller.child_state(alice.id).status != ChildStatus.UNKNOWN


async def test_grant_raises_remaining_and_is_ledger_only_without_a_vendor(controller: Controller, alice, events) -> None:
	add_device(controller, "PS5", alice.id, FakeEnforcer("unifi", Mode.NETWORK))
	assert controller.child_state(alice.id).remaining == 90  # Wednesday allowance
	override = await controller.grant(alice.id, 20, reason="emptied the dishwasher", source="taskmate")
	assert override.status == OverrideStatus.CONFIRMED
	assert override.results[0].enforcer == "ledger"
	assert controller.child_state(alice.id).remaining == 110
	assert controller.child_state(alice.id).granted == 20
	assert "override.confirmed" in types(events)


async def test_grant_goes_to_vendors_that_take_bonus_minutes(controller: Controller, alice) -> None:
	fl = FakeEnforcer("family_link", Mode.PAUSE)
	add_device(controller, "Phone", alice.id, fl)
	override = await controller.grant(alice.id, 15, source="guardian:andy")
	assert fl.bonus == [15]
	assert override.results[0].mode == Mode.BONUS


async def test_grant_cap_is_enforced(controller: Controller, alice) -> None:
	await controller.grant(alice.id, 60)
	with pytest.raises(GrantCapExceeded):
		await controller.grant(alice.id, 1)


async def test_usage_is_charged_and_exhaustion_locks_then_grant_releases(
	controller: Controller, alice, events, clock: Clock
) -> None:
	controller.set_policy(alice.id, Policy(child_id=alice.id, allowance_minutes=[10] * 7))
	unifi = FakeEnforcer("unifi", Mode.NETWORK, in_use=True)
	add_device(controller, "PS5", alice.id, unifi)
	await controller.tick()
	clock.advance(minutes=5)
	await controller.tick()
	assert controller.child_state(alice.id).remaining == 5
	assert controller.child_state(alice.id).used == 5
	assert "usage.reported" in types(events)
	clock.advance(minutes=5)
	await controller.tick()
	state = controller.child_state(alice.id)
	assert state.remaining == 0
	assert state.status == ChildStatus.EXHAUSTED
	assert "allowance.exhausted" in types(events)
	auto = [override for override in controller.overrides if override.source == SOURCE_EXHAUSTED]
	assert len(auto) == 1 and auto[0].status == OverrideStatus.CONFIRMED
	assert unifi.locked[auto[0].results[0].device_id]
	# Locked devices are not charged.
	clock.advance(minutes=5)
	await controller.tick()
	assert controller.child_state(alice.id).used == 10
	await controller.grant(alice.id, 20, source="taskmate")
	assert auto[0].status == OverrideStatus.CANCELLED
	state = controller.child_state(alice.id)
	assert state.status == ChildStatus.FREE
	assert state.remaining == 20
	assert not unifi.locked[auto[0].results[0].device_id]


async def test_low_allowance_event_once_per_day(controller: Controller, alice, events, clock: Clock) -> None:
	controller.set_policy(alice.id, Policy(child_id=alice.id, allowance_minutes=[20] * 7))
	add_device(controller, "PS5", alice.id, FakeEnforcer("unifi", Mode.NETWORK, in_use=True))
	await controller.tick()
	for _ in range(3):
		clock.advance(minutes=3)
		await controller.tick()
	assert types(events).count("allowance.low") == 1


async def test_per_app_rate_uses_tags(controller: Controller, alice, clock: Clock) -> None:
	from kerb_core.models import Effect
	from kerb_core.tags import TagScore, TagSource

	policy = Policy(child_id=alice.id, allowance_minutes=[100] * 7)
	policy.tag_rules["educational"] = Effect.COUNT_HALF
	controller.set_policy(alice.id, policy)
	controller.tags = TagSource([TagScore("steam:252950", "educational", 4)])
	device = add_device(controller, "PC", alice.id, FakeEnforcer("obs", Mode.NETWORK, in_use=True))
	controller.set_now_playing(device.id, "steam:252950")
	await controller.tick()
	clock.advance(minutes=10)
	await controller.tick()
	state = controller.child_state(alice.id)
	assert state.used == 5
	assert state.remaining == 95
	assert state.devices_without_per_app_usage == []
	entry = controller.ledger(alice.id).entries[-1]
	assert entry.rule == "tag:educational" and entry.rate == 0.5


async def test_devices_without_per_app_usage_are_named(controller: Controller, alice, clock: Clock) -> None:
	add_device(controller, "PS5", alice.id, FakeEnforcer("unifi", Mode.NETWORK, in_use=True))
	await controller.tick()
	clock.advance(minutes=1)
	await controller.tick()
	assert controller.child_state(alice.id).devices_without_per_app_usage == ["PS5"]


async def test_lock_expiry_releases_the_network_block(controller: Controller, alice, events, clock: Clock) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	device = add_device(controller, "PS5", alice.id, unifi)
	override = await controller.lock(alice.id, minutes=30)
	assert unifi.locked[device.id]
	clock.advance(minutes=31)
	await controller.tick()
	assert override.status == OverrideStatus.EXPIRED
	assert not unifi.locked[device.id]
	assert "override.expired" in types(events)
	assert controller.child_state(alice.id).status == ChildStatus.FREE


async def test_lock_defaults_to_end_of_day(controller: Controller, alice) -> None:
	override = await controller.lock(alice.id)
	assert override.expires_at == datetime(2026, 10, 22, 0, 0, tzinfo=TZ)


async def test_unlock_reverts_and_relock_wins(controller: Controller, alice) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	device = add_device(controller, "PS5", alice.id, unifi)
	await controller.lock(alice.id)
	unlock = await controller.unlock(alice.id, reason="homework done", source="guardian:andy")
	assert unlock.status == OverrideStatus.CONFIRMED
	assert not unifi.locked[device.id]
	assert controller.child_state(alice.id).status == ChildStatus.FREE
	await controller.lock(alice.id, minutes=5)
	assert unifi.locked[device.id]
	assert controller.child_state(alice.id).status == ChildStatus.LOCKED


async def test_unlock_with_nothing_locked_is_confirmed(controller: Controller, alice) -> None:
	unlock = await controller.unlock(alice.id)
	assert unlock.status == OverrideStatus.CONFIRMED
	assert unlock.results[0].detail == "nothing was locked"


async def test_device_scoped_lock(controller: Controller, alice) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	ps5 = add_device(controller, "PS5", alice.id, unifi)
	phone = add_device(controller, "Phone", alice.id, unifi)
	await controller.lock(alice.id, scope=Scope("device", device_id=ps5.id))
	assert unifi.locked.get(ps5.id) is True
	assert phone.id not in unifi.locked


async def test_cancel_grant_writes_a_penalty_and_cancel_lock_reverts(controller: Controller, alice, events) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	device = add_device(controller, "PS5", alice.id, unifi)
	grant = await controller.grant(alice.id, 30)
	assert controller.child_state(alice.id).remaining == 120
	record = await controller.cancel_override(grant.id)
	assert grant.status == OverrideStatus.CANCELLED
	assert record.cancels == grant.id
	assert controller.child_state(alice.id).remaining == 90
	lock = await controller.lock(alice.id)
	await controller.cancel_override(lock.id)
	assert lock.status == OverrideStatus.CANCELLED
	assert not unifi.locked[device.id]
	assert types(events).count("override.cancelled") == 2
	with pytest.raises(KeyError):
		await controller.cancel_override("nope")


async def test_set_allowance_today(controller: Controller, alice) -> None:
	override = await controller.set_allowance_today(alice.id, 30)
	assert override.status == OverrideStatus.CONFIRMED
	assert controller.child_state(alice.id).allowance == 30
	assert controller.child_state(alice.id).remaining == 30
	await controller.cancel_override(override.id)
	assert controller.child_state(alice.id).allowance == 90


async def test_bedtime_locks_until_morning(controller: Controller, alice, clock: Clock) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	add_device(controller, "PS5", alice.id, unifi)
	clock.now = datetime(2026, 10, 21, 20, 0, tzinfo=TZ)
	await controller.tick()
	locks = [override for override in controller.overrides if override.source == SOURCE_BEDTIME]
	assert len(locks) == 1
	assert locks[0].expires_at == datetime(2026, 10, 22, 7, 0, tzinfo=TZ)
	assert controller.child_state(alice.id).status == ChildStatus.BEDTIME
	await controller.tick()
	assert len([override for override in controller.overrides if override.source == SOURCE_BEDTIME]) == 1


async def test_windows_lock_until_next_window(controller: Controller, alice, clock: Clock) -> None:
	policy = Policy(child_id=alice.id)
	policy.windows[2] = [TimeWindow("18:00", "19:00")]
	controller.set_policy(alice.id, policy)
	add_device(controller, "PS5", alice.id, FakeEnforcer("unifi", Mode.NETWORK))
	await controller.tick()
	lock = next(override for override in controller.overrides if override.source == SOURCE_WINDOW)
	assert lock.expires_at == datetime(2026, 10, 21, 18, 0, tzinfo=TZ)
	clock.now = datetime(2026, 10, 21, 18, 30, tzinfo=TZ)
	await controller.tick()
	assert controller.child_state(alice.id).status == ChildStatus.FREE


async def test_state_survives_a_restart(controller: Controller, alice, household, clock: Clock) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK, in_use=True)
	add_device(controller, "PS5", alice.id, unifi)
	await controller.tick()
	clock.advance(minutes=10)
	await controller.tick()
	lock = await controller.lock(alice.id, minutes=60, reason="dinner")
	saved = controller.to_dict()

	again = Controller(household, clock)
	again.add_child(alice, controller.policies[alice.id])
	again.add_device(controller.devices_for(alice.id)[0])
	again.add_enforcer(unifi)
	again.load(saved)
	assert again.child_state(alice.id).status == ChildStatus.UNKNOWN  # nothing polled yet
	await again.reconcile()
	state = again.child_state(alice.id)
	assert state.used == 10
	assert state.lock_id == lock.id
	assert state.lock_reason == "dinner"
	assert state.status == ChildStatus.LOCKED
	assert again.to_dict() == saved


async def test_prune_drops_old_days(controller: Controller, alice, clock: Clock) -> None:
	controller.ledger(alice.id)
	clock.advance(minutes=60 * 24 * 40)
	controller.ledger(alice.id)
	controller.prune()
	assert list(controller.ledgers) == [(alice.id, clock.now.date().isoformat())]


async def test_reconcile_refreshes_states_and_health(controller: Controller, alice) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	device = add_device(controller, "PS5", alice.id, unifi)
	unifi.locked[device.id] = True
	await controller.reconcile()
	assert controller.states[("unifi", device.id)].locked is True
	assert controller.health["unifi"].status == HealthStatus.HEALTHY
	assert controller.child_state(alice.id).confidence == Confidence.CONFIRMED


async def test_strongest_mode(controller: Controller, alice) -> None:
	device = add_device(controller, "PS5", alice.id, FakeEnforcer("plug", Mode.POWER), FakeEnforcer("manual", Mode.MANUAL))
	assert controller.strongest_mode(device) == Mode.MANUAL
	device.power_off_allowed = True
	assert controller.strongest_mode(device) == Mode.POWER


async def test_listener_errors_do_not_break_enforcement(controller: Controller, alice) -> None:
	def boom(event) -> None:
		raise RuntimeError("listener broke")

	controller.listen(boom)
	add_device(controller, "PS5", alice.id, FakeEnforcer("unifi", Mode.NETWORK))
	override = await controller.lock(alice.id, minutes=5)
	assert override.status == OverrideStatus.CONFIRMED


async def test_unlock_summary_says_what_was_released(controller: Controller, alice) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	plug = FakeEnforcer("plug", Mode.POWER)
	add_device(controller, "PS5", alice.id, unifi, plug, power_opt_in=True)
	await controller.lock(alice.id)
	unlock = await controller.unlock(alice.id)
	assert controller.summary(unlock) == ["PS5 network unblocked (unifi).", "PS5 power restored (plug)."]


async def test_pending_then_failed_enforcement(controller: Controller, alice, clock: Clock) -> None:
	liar = FakeEnforcer("family_safety", Mode.ZERO_ALLOWANCE, noop=True, confirmation_window_s=120)
	add_device(controller, "Xbox", alice.id, liar)
	await controller.lock(alice.id, minutes=60)
	assert controller.child_state(alice.id).enforcement == EnforcementStatus.PENDING
	clock.advance(minutes=3)
	await controller.tick()
	assert controller.child_state(alice.id).enforcement == EnforcementStatus.DEGRADED


async def test_expiry_of_an_earlier_lock_keeps_a_later_lock_in_force(controller: Controller, alice, events, clock: Clock) -> None:
	controller.set_policy(alice.id, Policy(child_id=alice.id))  # no bedtime, so midnight does not relock
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	plug = FakeEnforcer("plug", Mode.POWER)
	device = add_device(controller, "Xbox", alice.id, unifi, plug, power_opt_in=True)
	hour = await controller.lock(alice.id, minutes=60, reason="dinner")
	clock.advance(minutes=20)
	rest_of_day = await controller.lock(alice.id, reason="lock switch")
	clock.advance(minutes=45)
	await controller.tick()
	assert hour.status == OverrideStatus.EXPIRED
	assert hour.restore["revert"] == []  # nothing was released
	assert unifi.locked[device.id] and plug.locked[device.id]
	assert rest_of_day.status == OverrideStatus.CONFIRMED
	state = controller.child_state(alice.id)
	assert state.status == ChildStatus.LOCKED and state.lock_id == rest_of_day.id
	assert "enforcement.unconfirmed" not in types(events)
	# The surviving lock releases everything when it ends.
	clock.now = rest_of_day.expires_at
	await controller.tick()
	assert not unifi.locked[device.id] and not plug.locked[device.id]


async def test_expiry_releases_an_enforcer_the_later_lock_never_asked(controller: Controller, alice, clock: Clock) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	plug = FakeEnforcer("plug", Mode.POWER)
	device = add_device(controller, "Xbox", alice.id, unifi, plug, power_opt_in=True)
	await controller.lock(alice.id, minutes=30)
	await controller.lock(alice.id, mode="power")
	clock.advance(minutes=31)
	await controller.tick()
	# Power is still held by the second lock; the network block had no other holder and is let go.
	assert plug.locked[device.id]
	assert not unifi.locked[device.id]


async def test_hour_lock_expiring_inside_bedtime_keeps_bedtime(controller: Controller, alice, clock: Clock) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	device = add_device(controller, "PS5", alice.id, unifi)
	clock.now = datetime(2026, 10, 21, 19, 30, tzinfo=TZ)
	await controller.lock(alice.id, minutes=60)
	clock.now = datetime(2026, 10, 21, 20, 0, tzinfo=TZ)
	await controller.tick()  # bedtime lock created
	clock.now = datetime(2026, 10, 21, 20, 35, tzinfo=TZ)
	await controller.tick()  # hour lock expires
	assert unifi.locked[device.id]
	assert controller.child_state(alice.id).status == ChildStatus.BEDTIME


async def test_unlock_ends_every_lock_once(controller: Controller, alice, events) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	device = add_device(controller, "PS5", alice.id, unifi)
	first = await controller.lock(alice.id, minutes=60)
	second = await controller.lock(alice.id)
	unlock = await controller.unlock(alice.id)
	assert first.status == OverrideStatus.CANCELLED and second.status == OverrideStatus.CANCELLED
	assert [call.method for call in unifi.calls] == ["apply", "apply", "revert"]
	assert len(unlock.results) == 1
	assert unlock.status == OverrideStatus.CONFIRMED
	applied = [event for event in events if event.type == "override.applied" and event.payload["override"]["id"] == unlock.id]
	assert len(applied) == 1
	assert not unifi.locked[device.id]
	# Reconcile has nothing pending to confirm on the dead locks.
	await controller.reconcile()
	assert types(events).count("override.confirmed") == 3


async def test_device_unlock_keeps_a_child_lock_on_other_devices(controller: Controller, alice) -> None:
	unifi = FakeEnforcer("unifi", Mode.NETWORK)
	ps5 = add_device(controller, "PS5", alice.id, unifi)
	xbox = add_device(controller, "Xbox", alice.id, unifi)
	lock = await controller.lock(alice.id)
	await controller.unlock(alice.id, scope=Scope("device", device_id=ps5.id))
	assert not unifi.locked[ps5.id]
	assert unifi.locked[xbox.id]
	assert lock.status == OverrideStatus.CONFIRMED  # still in force for the Xbox
	assert controller.child_state(alice.id).lock_id == lock.id


async def test_grant_lifts_exhaustion_but_not_a_parents_lock(controller: Controller, alice, clock: Clock) -> None:
	controller.set_policy(alice.id, Policy(child_id=alice.id, allowance_minutes=[5] * 7))
	unifi = FakeEnforcer("unifi", Mode.NETWORK, in_use=True)
	device = add_device(controller, "PS5", alice.id, unifi)
	await controller.tick()
	clock.advance(minutes=6)
	await controller.tick()
	assert controller.child_state(alice.id).status == ChildStatus.EXHAUSTED
	parent = await controller.lock(alice.id, reason="dinner", source="guardian:andy")
	await controller.grant(alice.id, 30, source="taskmate")
	assert unifi.locked[device.id]
	state = controller.child_state(alice.id)
	assert state.status == ChildStatus.LOCKED and state.lock_id == parent.id
	assert state.remaining == 29
