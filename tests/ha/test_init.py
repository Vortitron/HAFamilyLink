"""Setup, entities and unload."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.kerb.const import DOMAIN

from .conftest import BLOCK_PS5


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
