"""The parent-facing verbs through Home Assistant services, with the guardian check and PIN."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import ServiceValidationError, Unauthorized
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser, async_fire_time_changed

from custom_components.kerb.const import DOMAIN, EVENT_TYPE

from .conftest import BLOCK_PS5, GUARDIAN, PIN, PLUG_XBOX, STRANGER, XBOX_ACTIVE, call, entry_data


async def test_lock_blocks_network_cuts_power_and_asks_the_parent(hass: HomeAssistant, setup, fake_switches) -> None:
	events = []
	hass.bus.async_listen(EVENT_TYPE, lambda event: events.append(event.data["type"]))
	response = await call(hass, "lock", child="alice", duration={"hours": 1}, reason="dinner")
	await hass.async_block_till_done()
	assert hass.states.get(BLOCK_PS5).state == "on"
	assert hass.states.get(PLUG_XBOX).state == "off"
	assert response["status"] == "applied"  # the manual PS5 action is still pending
	assert response["summary"] == [
		"PS5 network blocked (network:input_boolean.block_ps5). PS5 may still run offline games.",
		"PS5 manual action requested (manual:33333333-3333-4333-8333-333333333333). PS5 waiting for a parent to press done. Awaiting confirmation.",
		"Xbox powered off (power:input_boolean.plug_xbox).",
	]
	assert hass.states.get("sensor.alice_status").state == "locked"
	assert hass.states.get("sensor.alice_enforcement").state == "pending"  # the manual step is not a problem yet
	assert hass.states.get("binary_sensor.alice_any_enforcer_degraded").state == "off"
	assert hass.states.get("switch.alice_lock").state == "on"
	assert hass.states.get("switch.alice_lock").attributes["reason"] == "dinner"
	assert "override.applied" in events

	await call(hass, "confirm_manual", child="Alice", device="PS5")
	await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_enforcement").state == "confirmed"
	assert "override.confirmed" in events


async def test_manual_done_button(hass: HomeAssistant, setup) -> None:
	await call(hass, "lock", child="Alice", scope="PS5")
	await hass.services.async_call("button", "press", {"entity_id": "button.alice_ps5_manual_done"}, blocking=True)
	await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_enforcement").state == "confirmed"
	assert hass.states.get("switch.alice_ps5_lock").state == "on"
	assert hass.states.get("switch.alice_xbox_lock").state == "off"


async def test_unlock_releases(hass: HomeAssistant, setup) -> None:
	await call(hass, "lock", child="Alice")
	response = await call(hass, "unlock", child="Alice", reason="homework done")
	await hass.async_block_till_done()
	assert hass.states.get(BLOCK_PS5).state == "off"
	assert hass.states.get(PLUG_XBOX).state == "on"
	assert hass.states.get("sensor.alice_status").state == "free"
	assert response["status"] == "applied"  # manual unlock awaits the parent too
	assert response["summary"] == [
		"PS5 network unblocked (network:input_boolean.block_ps5).",
		"PS5 manual release requested (manual:33333333-3333-4333-8333-333333333333). PS5 waiting for a parent to press done. Awaiting confirmation.",
		"Xbox power restored (power:input_boolean.plug_xbox).",
	]


async def test_grant_and_allowance(hass: HomeAssistant, setup) -> None:
	response = await call(hass, "grant", child="Alice", minutes=20, reason="emptied the dishwasher", source="taskmate")
	assert response["status"] == "confirmed"
	assert response["results"][0]["enforcer"] == "ledger"
	assert hass.states.get("sensor.alice_remaining_today").state == "140"
	assert hass.states.get("sensor.alice_remaining_today").attributes["granted"] == 20
	await call(hass, "set_allowance_today", child="Alice", minutes=60)
	assert hass.states.get("sensor.alice_remaining_today").state == "80"
	assert hass.states.get("number.alice_allowance_today").state == "60"


async def test_unknown_child_or_device(hass: HomeAssistant, setup) -> None:
	with pytest.raises(ServiceValidationError):
		await call(hass, "lock", child="Bob")
	with pytest.raises(ServiceValidationError):
		await call(hass, "lock", child="Alice", scope="Toaster")
	with pytest.raises(ServiceValidationError):
		await call(hass, "confirm_manual", child="Alice", device="Xbox")


async def test_guardian_check(hass: HomeAssistant, setup) -> None:
	with pytest.raises(Unauthorized):
		await call(hass, "lock", child="Alice", context=Context(user_id=STRANGER))
	assert hass.states.get("sensor.alice_status").state == "free"
	response = await call(hass, "lock", child="Alice", context=Context(user_id=GUARDIAN), scope="Xbox")
	assert response["results"][0]["enforcer"] == "power:input_boolean.plug_xbox"
	assert hass.states.get("sensor.alice_status").state == "locked"
	# Entity writes carry the same check.
	with pytest.raises(Unauthorized):
		await hass.services.async_call(
			"switch", "turn_off", {"entity_id": "switch.alice_lock"}, blocking=True, context=Context(user_id=STRANGER)
		)
	await hass.services.async_call(
		"switch", "turn_off", {"entity_id": "switch.alice_lock"}, blocking=True, context=Context(user_id=GUARDIAN)
	)
	await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_status").state == "free"


async def test_pin(hass: HomeAssistant, fake_switches, freezer: FrozenDateTimeFactory) -> None:
	MockUser(id=GUARDIAN, name="Andy", is_owner=True).add_to_hass(hass)
	MockUser(id=STRANGER, name="Alice").add_to_hass(hass)
	entry = MockConfigEntry(domain=DOMAIN, title="Alice", data=entry_data(pin=PIN), entry_id="alice-pin")
	entry.add_to_hass(hass)
	assert await hass.config_entries.async_setup(entry.entry_id)
	await hass.async_block_till_done()
	guardian = Context(user_id=GUARDIAN)
	with pytest.raises(ServiceValidationError):
		await call(hass, "grant", child="Alice", minutes=10)
	with pytest.raises(ServiceValidationError):
		await call(hass, "grant", child="Alice", minutes=10, pin="0000", context=guardian)
	await call(hass, "grant", child="Alice", minutes=10, pin=PIN, context=guardian)
	assert hass.states.get("sensor.alice_remaining_today").state == "130"
	# A blank PIN from a template means none was given.
	with pytest.raises(ServiceValidationError):
		await call(hass, "grant", child="Alice", minutes=10, pin="", context=guardian)

	# Entities cannot carry a PIN, so the dashboard is refused until the guardian enters it.
	with pytest.raises(ServiceValidationError):
		await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.alice_lock"}, blocking=True, context=guardian)
	assert hass.states.get("text.alice_pin").state == ""
	assert hass.states.get("text.alice_pin").attributes["pin_set"] is True
	with pytest.raises(ServiceValidationError):
		await hass.services.async_call(
			"text", "set_value", {"entity_id": "text.alice_pin", "value": "0000"}, blocking=True, context=guardian
		)
	with pytest.raises(Unauthorized):
		await hass.services.async_call(
			"text", "set_value", {"entity_id": "text.alice_pin", "value": PIN}, blocking=True, context=Context(user_id=STRANGER)
		)
	await hass.services.async_call(
		"text", "set_value", {"entity_id": "text.alice_pin", "value": PIN}, blocking=True, context=guardian
	)
	assert hass.states.get("text.alice_pin").state == ""  # the PIN is never kept
	assert hass.states.get("text.alice_pin").attributes["armed"] == [GUARDIAN]
	await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.alice_lock"}, blocking=True, context=guardian)
	await hass.services.async_call(
		"button", "press", {"entity_id": "button.alice_grant_15_minutes"}, blocking=True, context=guardian
	)
	await hass.services.async_call(
		"number", "set_value", {"entity_id": "number.alice_allowance_today", "value": 60}, blocking=True, context=guardian
	)
	await hass.async_block_till_done()
	assert hass.states.get("switch.alice_lock").state == "on"
	assert hass.states.get("sensor.alice_remaining_today").attributes["granted"] == 25
	assert hass.states.get("number.alice_allowance_today").state == "60"
	# Armed guardians may also call the services without repeating the PIN.
	await call(hass, "unlock", child="Alice", context=guardian)
	assert hass.states.get("switch.alice_lock").state == "off"
	# The arming window closes, and the next tick shows it.
	freezer.tick(timedelta(minutes=6))
	async_fire_time_changed(hass)
	await hass.async_block_till_done()
	with pytest.raises(ServiceValidationError):
		await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.alice_lock"}, blocking=True, context=guardian)
	assert hass.states.get("text.alice_pin").attributes["armed"] == []


async def test_confirming_a_manual_step_needs_no_pin(hass: HomeAssistant, fake_switches) -> None:
	MockUser(id=GUARDIAN, name="Andy", is_owner=True).add_to_hass(hass)
	MockUser(id=STRANGER, name="Alice").add_to_hass(hass)
	entry = MockConfigEntry(domain=DOMAIN, title="Alice", data=entry_data(pin=PIN), entry_id="alice-pin")
	entry.add_to_hass(hass)
	assert await hass.config_entries.async_setup(entry.entry_id)
	await hass.async_block_till_done()
	guardian = Context(user_id=GUARDIAN)
	await call(hass, "lock", child="Alice", scope="PS5", pin=PIN, context=guardian)
	assert hass.states.get("sensor.alice_enforcement").state == "pending"
	with pytest.raises(Unauthorized):
		await hass.services.async_call(
			"button", "press", {"entity_id": "button.alice_ps5_manual_done"}, blocking=True, context=Context(user_id=STRANGER)
		)
	await hass.services.async_call(
		"button", "press", {"entity_id": "button.alice_ps5_manual_done"}, blocking=True, context=guardian
	)
	await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_enforcement").state == "confirmed"
	await call(hass, "unlock", child="Alice", scope="PS5", pin=PIN, context=guardian)
	await call(hass, "confirm_manual", child="Alice", device="PS5", context=guardian)
	await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_status").state == "free"


async def test_entities_write_through(hass: HomeAssistant, setup) -> None:
	await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.alice_lock"}, blocking=True)
	await hass.async_block_till_done()
	assert hass.states.get("switch.alice_lock").state == "on"
	assert hass.states.get(BLOCK_PS5).state == "on"
	await hass.services.async_call(
		"number", "set_value", {"entity_id": "number.alice_allowance_today", "value": 45}, blocking=True
	)
	assert hass.states.get("sensor.alice_remaining_today").state == "45"
	await hass.services.async_call("button", "press", {"entity_id": "button.alice_grant_30_minutes"}, blocking=True)
	assert hass.states.get("sensor.alice_remaining_today").state == "75"


async def test_tick_charges_usage_and_expires_locks(hass: HomeAssistant, setup, freezer: FrozenDateTimeFactory) -> None:
	await hass.services.async_call("input_boolean", "turn_on", {"entity_id": XBOX_ACTIVE}, blocking=True)
	await call(hass, "reconcile")
	# The first tick only establishes a baseline; the next two charge a minute each.
	for _ in range(3):
		freezer.tick(timedelta(seconds=60))
		async_fire_time_changed(hass)
		await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_used_today").state == "2.0"
	assert hass.states.get("sensor.alice_remaining_today").state == "118"
	assert hass.states.get("sensor.alice_used_today").attributes["devices_without_per_app_usage"] == ["Xbox"]

	await call(hass, "lock", child="Alice", scope="Xbox", duration={"minutes": 2})
	assert hass.states.get(PLUG_XBOX).state == "off"
	freezer.tick(timedelta(seconds=150))
	async_fire_time_changed(hass)
	await hass.async_block_till_done()
	assert hass.states.get(PLUG_XBOX).state == "on"
	assert hass.states.get("switch.alice_xbox_lock").state == "off"


async def test_state_is_stored_and_restored(hass: HomeAssistant, setup, hass_storage) -> None:
	await call(hass, "grant", child="Alice", minutes=25)
	assert await hass.config_entries.async_unload(setup.entry_id)
	await hass.async_block_till_done()
	assert "kerb.state" in hass_storage
	assert await hass.config_entries.async_setup(setup.entry_id)
	await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_remaining_today").state == "145"
	assert hass.states.get("sensor.alice_remaining_today").attributes["granted"] == 25
