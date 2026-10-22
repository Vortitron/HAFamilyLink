"""Fixtures for the Home Assistant integration tests."""

from __future__ import annotations

from typing import Any

from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry, MockUser

from custom_components.kerb.const import (
	CONF_AGE_BAND,
	CONF_CHILD_ID,
	CONF_DEVICE_ID,
	CONF_DEVICE_NAME,
	CONF_DEVICES,
	CONF_GUARDIANS,
	CONF_IN_USE_ENTITY,
	CONF_MANUAL,
	CONF_NAME,
	CONF_NETWORK_SWITCHES,
	CONF_PIN_HASH,
	CONF_PLATFORM,
	CONF_POWER_DELAY,
	CONF_POWER_OPT_IN,
	CONF_POWER_SWITCH,
	DOMAIN,
)
from custom_components.kerb.core.auth import hash_pin

CHILD_ID = "22222222-2222-4222-8222-222222222222"
PS5_ID = "33333333-3333-4333-8333-333333333333"
XBOX_ID = "44444444-4444-4444-8444-444444444444"
BLOCK_PS5 = "input_boolean.block_ps5"
PLUG_XBOX = "input_boolean.plug_xbox"
XBOX_ACTIVE = "input_boolean.xbox_active"
GUARDIAN = "guardian-user-id"
STRANGER = "stranger-user-id"
PIN = "4321"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
	yield


@pytest.fixture
async def fake_switches(hass: HomeAssistant) -> None:
	"""Real input_boolean entities stand in for a router block switch, a smart plug and an activity sensor."""
	assert await async_setup_component(
		hass, "input_boolean", {"input_boolean": {"block_ps5": {}, "plug_xbox": {"initial": True}, "xbox_active": {}}}
	)
	await hass.async_block_till_done()
	assert hass.states.get(BLOCK_PS5).state == STATE_OFF
	assert hass.states.get(PLUG_XBOX).state == STATE_ON


def entry_data(pin: str | None = None, guardians: list[str] | None = None) -> dict[str, Any]:
	return {
		CONF_NAME: "Alice",
		CONF_AGE_BAND: "7_to_12",
		CONF_CHILD_ID: CHILD_ID,
		CONF_GUARDIANS: [GUARDIAN] if guardians is None else guardians,
		CONF_PIN_HASH: hash_pin(pin) if pin else None,
		CONF_DEVICES: [
			{
				CONF_DEVICE_ID: PS5_ID,
				CONF_DEVICE_NAME: "PS5",
				CONF_PLATFORM: "playstation",
				CONF_NETWORK_SWITCHES: [BLOCK_PS5],
				CONF_MANUAL: True,
			},
			{
				CONF_DEVICE_ID: XBOX_ID,
				CONF_DEVICE_NAME: "Xbox",
				CONF_PLATFORM: "xbox",
				CONF_POWER_SWITCH: PLUG_XBOX,
				CONF_POWER_OPT_IN: True,
				CONF_POWER_DELAY: 0,
				CONF_IN_USE_ENTITY: XBOX_ACTIVE,
			},
		],
	}


@pytest.fixture
def entry(hass: HomeAssistant) -> MockConfigEntry:
	entry = MockConfigEntry(
		domain=DOMAIN, title="Alice", data=entry_data(), options={}, entry_id="alice-entry", unique_id=CHILD_ID
	)
	entry.add_to_hass(hass)
	return entry


@pytest.fixture
async def setup(hass: HomeAssistant, fake_switches, entry: MockConfigEntry) -> MockConfigEntry:
	# The guardian is an admin so HA's own entity permission check lets the call reach Kerb's check.
	MockUser(id=GUARDIAN, name="Andy", is_owner=True).add_to_hass(hass)
	MockUser(id=STRANGER, name="Alice").add_to_hass(hass)
	assert await hass.config_entries.async_setup(entry.entry_id)
	await hass.async_block_till_done()
	return entry


async def call(hass: HomeAssistant, service: str, context=None, **data: Any) -> Any:
	return await hass.services.async_call(
		DOMAIN,
		service,
		data,
		blocking=True,
		context=context,
		return_response=service != "reconcile" and service != "confirm_manual",
	)
