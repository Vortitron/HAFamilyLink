"""Config and options flows."""

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockUser

from custom_components.kerb.const import (
	CONF_ADD_ANOTHER,
	CONF_AGE_BAND,
	CONF_ALLOWANCE_DAYS,
	CONF_BEDTIME_END,
	CONF_BEDTIME_START,
	CONF_CHILD_ID,
	CONF_CONFIRMATION_WINDOW,
	CONF_DEVICE_NAME,
	CONF_DEVICES,
	CONF_GRANT_CAP,
	CONF_GUARDIANS,
	CONF_LOW_THRESHOLD,
	CONF_MANUAL,
	CONF_NAME,
	CONF_NETWORK_SWITCHES,
	CONF_PIN,
	CONF_PIN_HASH,
	CONF_PLATFORM,
	CONF_RETENTION_DAYS,
	DOMAIN,
)
from custom_components.kerb.core.auth import verify_pin

from .conftest import BLOCK_PS5, GUARDIAN


async def test_full_flow(hass: HomeAssistant, fake_switches) -> None:
	MockUser(id=GUARDIAN, name="Andy", is_owner=True).add_to_hass(hass)
	result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
	assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"

	result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_NAME: " ", CONF_AGE_BAND: "7_to_12"})
	assert result["errors"] == {CONF_NAME: "empty_name"}

	result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_NAME: "Alice", CONF_AGE_BAND: "7_to_12"})
	assert result["step_id"] == "device"

	result = await hass.config_entries.flow.async_configure(
		result["flow_id"], {CONF_DEVICE_NAME: "Toaster", CONF_PLATFORM: "other", CONF_NETWORK_SWITCHES: [], CONF_MANUAL: False}
	)
	assert result["errors"] == {"base": "no_enforcer"}

	result = await hass.config_entries.flow.async_configure(
		result["flow_id"],
		{CONF_DEVICE_NAME: "PS5", CONF_PLATFORM: "playstation", CONF_NETWORK_SWITCHES: [BLOCK_PS5], CONF_ADD_ANOTHER: True},
	)
	assert result["step_id"] == "device"
	assert result["description_placeholders"]["count"] == "1"

	result = await hass.config_entries.flow.async_configure(
		result["flow_id"], {CONF_DEVICE_NAME: "Switch", CONF_PLATFORM: "switch", CONF_MANUAL: True, CONF_ADD_ANOTHER: False}
	)
	assert result["step_id"] == "guardians"

	result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_GUARDIANS: [GUARDIAN], CONF_PIN: "1234"})
	await hass.async_block_till_done()
	assert result["type"] is FlowResultType.CREATE_ENTRY
	assert result["title"] == "Alice"
	data = result["data"]
	assert data[CONF_NAME] == "Alice"
	assert data[CONF_CHILD_ID]
	assert [device[CONF_DEVICE_NAME] for device in data[CONF_DEVICES]] == ["PS5", "Switch"]
	assert data[CONF_DEVICES][1][CONF_MANUAL] is True
	assert data[CONF_GUARDIANS] == [GUARDIAN]
	assert verify_pin(data[CONF_PIN_HASH], "1234")
	assert hass.states.get("sensor.alice_remaining_today").state == "120"


async def test_duplicate_name(hass: HomeAssistant, setup) -> None:
	result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
	result = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_NAME: "alice", CONF_AGE_BAND: "7_to_12"})
	assert result["errors"] == {CONF_NAME: "duplicate_name"}


async def test_options_flow_sets_policy(hass: HomeAssistant, setup) -> None:
	result = await hass.config_entries.options.async_init(setup.entry_id)
	assert result["type"] is FlowResultType.FORM
	user_input = {key: 30 for key in CONF_ALLOWANCE_DAYS}
	user_input.update(
		{
			CONF_BEDTIME_START: "20:00:00",
			CONF_BEDTIME_END: "07:00:00",
			CONF_GRANT_CAP: 45,
			CONF_CONFIRMATION_WINDOW: 60,
			CONF_LOW_THRESHOLD: 10,
			CONF_RETENTION_DAYS: 7,
		}
	)
	result = await hass.config_entries.options.async_configure(result["flow_id"], user_input)
	await hass.async_block_till_done()
	assert result["type"] is FlowResultType.CREATE_ENTRY
	assert setup.options[CONF_GRANT_CAP] == 45
	assert hass.states.get("sensor.alice_remaining_today").state == "30"
	assert hass.states.get("number.alice_allowance_today").state == "30"
