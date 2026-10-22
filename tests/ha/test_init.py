"""Setup, entities and unload."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.kerb.const import CONF_CHILD_ID, CONF_DEVICES, CONF_NAME, DOMAIN

from .conftest import BLOCK_PS5, CHILD_ID, call, entry_data


async def test_setup_creates_child_entities(hass: HomeAssistant, setup) -> None:
	assert hass.states.get("sensor.alice_remaining_today").state == "120"
	assert hass.states.get("sensor.alice_used_today").state == "0"
	assert hass.states.get("sensor.alice_status").state == "free"
	assert hass.states.get("sensor.alice_enforcement").state == "confirmed"
	assert hass.states.get("switch.alice_lock").state == "off"
	assert hass.states.get("switch.alice_ps5_lock").state == "off"
	assert hass.states.get("switch.alice_xbox_lock").state == "off"
	assert hass.states.get("number.alice_allowance_today").state == "120"
	assert hass.states.get("binary_sensor.alice_any_enforcer_degraded").state == "off"
	assert hass.states.get("button.alice_grant_15_minutes") is not None
	assert hass.states.get("button.alice_ps5_manual_done") is not None
	assert hass.states.get("button.alice_xbox_manual_done") is None
	registry = er.async_get(hass)
	assert registry.async_get("sensor.alice_remaining_today").unique_id.endswith("_remaining_today")
	assert hass.states.get("sensor.alice_remaining_today").attributes["confidence"] == "confirmed"


async def test_services_registered_once(hass: HomeAssistant, setup) -> None:
	for service in ("lock", "unlock", "grant", "set_allowance_today", "reconcile", "confirm_manual"):
		assert hass.services.has_service(DOMAIN, service)


async def test_unload_tears_down_the_hub(hass: HomeAssistant, setup) -> None:
	assert DOMAIN in hass.data
	assert await hass.config_entries.async_unload(setup.entry_id)
	await hass.async_block_till_done()
	assert DOMAIN not in hass.data
	assert hass.states.get("sensor.alice_remaining_today").state == "unavailable"


async def test_missing_switch_makes_the_child_unknown(hass: HomeAssistant, fake_switches, entry) -> None:
	hass.states.async_remove(BLOCK_PS5)
	assert await hass.config_entries.async_setup(entry.entry_id)
	await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_status").state == "unknown"
	assert hass.states.get("sensor.alice_enforcement").state == "unknown"
	assert hass.states.get("binary_sensor.alice_any_enforcer_degraded").state == "on"


def stored_children(hass_storage) -> dict[str, set[str]]:
	data = hass_storage["kerb.state"]["data"]
	return {
		"ledgers": {item["child_id"] for item in data["ledgers"]},
		"overrides": {item["child_id"] for item in data["overrides"]},
	}


async def test_deleting_the_last_child_forgets_their_records(hass: HomeAssistant, setup, hass_storage) -> None:
	await call(hass, "grant", child="Alice", minutes=5)
	await call(hass, "lock", child="Alice", scope="Xbox")
	assert await hass.config_entries.async_remove(setup.entry_id)
	await hass.async_block_till_done()
	assert DOMAIN not in hass.data
	assert stored_children(hass_storage) == {"ledgers": set(), "overrides": set()}


async def test_deleting_one_child_keeps_the_other(hass: HomeAssistant, setup, hass_storage) -> None:
	bob_id = "55555555-5555-4555-8555-555555555555"
	bob = MockConfigEntry(
		domain=DOMAIN,
		title="Bob",
		data={**entry_data(), CONF_NAME: "Bob", CONF_CHILD_ID: bob_id, CONF_DEVICES: []},
		entry_id="bob-entry",
		unique_id=bob_id,
	)
	bob.add_to_hass(hass)
	assert await hass.config_entries.async_setup(bob.entry_id)
	await hass.async_block_till_done()
	await call(hass, "grant", child="Alice", minutes=5)
	await call(hass, "grant", child="Bob", minutes=5)
	await call(hass, "lock", child="Alice", scope="Xbox")
	assert await hass.config_entries.async_remove(setup.entry_id)
	await hass.async_block_till_done()
	assert stored_children(hass_storage) == {"ledgers": {bob_id}, "overrides": {bob_id}}
	assert CHILD_ID not in hass.data[DOMAIN].controller.children
	assert hass.states.get("sensor.bob_remaining_today").state == "125"
