"""The shipped blueprints parse, pass Home Assistant's blueprint schema, and run."""

from pathlib import Path
import shutil

from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.yaml import loader
import pytest

from .conftest import BLOCK_PS5, PLUG_XBOX

BLUEPRINT_DIR = Path(__file__).resolve().parents[2] / "blueprints" / "automation" / "kerb"
BLUEPRINTS = sorted(BLUEPRINT_DIR.glob("*.yaml"))


@pytest.mark.parametrize("path", BLUEPRINTS, ids=lambda path: path.stem)
def test_blueprint_is_valid(path: Path) -> None:
	data = loader.load_yaml(str(path))
	BLUEPRINT_SCHEMA(data)
	assert data["blueprint"]["domain"] == "automation"
	assert "kerb." in str(data["actions"])


@pytest.fixture
def blueprints_in_config(hass: HomeAssistant, tmp_path: Path) -> Path:
	"""Point the test config dir at a copy of the shipped blueprints, where HA looks for them."""
	target = tmp_path / "blueprints" / "automation" / "kerb"
	shutil.copytree(BLUEPRINT_DIR, target)
	hass.config.config_dir = str(tmp_path)
	return target


async def test_lock_for_duration_blueprint_locks(hass: HomeAssistant, setup, blueprints_in_config) -> None:
	assert await async_setup_component(hass, "input_button", {"input_button": {"no_screens": {}}})
	assert await async_setup_component(
		hass,
		"automation",
		{
			"automation": [
				{
					"alias": "hour",
					"use_blueprint": {
						"path": "kerb/lock_for_duration.yaml",
						"input": {
							"trigger_entity": "input_button.no_screens",
							"child": "Alice",
							"duration": {"hours": 1, "minutes": 0, "seconds": 0},
						},
					},
				}
			]
		},
	)
	await hass.async_block_till_done()
	assert hass.states.get("automation.hour") is not None
	await hass.services.async_call("input_button", "press", {"entity_id": "input_button.no_screens"}, blocking=True)
	await hass.async_block_till_done()
	assert hass.states.get("switch.alice_lock").state == "on"
	assert hass.states.get("switch.alice_lock").attributes["reason"] == "lock button"
	assert hass.states.get(BLOCK_PS5).state == "on"
	assert hass.states.get(PLUG_XBOX).state == "off"


async def test_grant_on_event_blueprint_grants(hass: HomeAssistant, setup, blueprints_in_config) -> None:
	assert await async_setup_component(
		hass,
		"automation",
		{
			"automation": [
				{
					"alias": "dishwasher",
					"use_blueprint": {
						"path": "kerb/grant_on_event.yaml",
						"input": {
							"event_type": "taskmate_task_completed",
							"event_data": {"task": "dishwasher"},
							"child": "Alice",
							"minutes": 20,
							"reason": "emptied the dishwasher",
							"source": "taskmate",
						},
					},
				}
			]
		},
	)
	await hass.async_block_till_done()
	hass.bus.async_fire("taskmate_task_completed", {"task": "bins"})
	await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_remaining_today").state == "120"
	hass.bus.async_fire("taskmate_task_completed", {"task": "dishwasher"})
	await hass.async_block_till_done()
	assert hass.states.get("sensor.alice_remaining_today").state == "140"
