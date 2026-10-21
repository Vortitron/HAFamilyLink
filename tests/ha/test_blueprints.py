"""The shipped blueprints parse and pass Home Assistant's blueprint schema."""

from pathlib import Path

from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
from homeassistant.util.yaml import loader
import pytest

BLUEPRINTS = sorted((Path(__file__).resolve().parents[2] / "blueprints" / "automation" / "kerb").glob("*.yaml"))


@pytest.mark.parametrize("path", BLUEPRINTS, ids=lambda path: path.stem)
def test_blueprint_is_valid(path: Path) -> None:
	data = loader.load_yaml(str(path))
	BLUEPRINT_SCHEMA(data["blueprint"])
	assert data["blueprint"]["domain"] == "automation"
	assert "kerb." in str(data["actions"])
