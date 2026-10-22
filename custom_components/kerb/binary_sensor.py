"""Any enforcer degraded: the alert hook."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.models import EnforcementStatus
from .entity import KerbChildEntity
from .hub import KerbConfigEntry


async def async_setup_entry(
	hass: HomeAssistant, entry: KerbConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
	async_add_entities([EnforcerDegradedSensor(entry.runtime_data)])


class EnforcerDegradedSensor(KerbChildEntity, BinarySensorEntity):
	_attr_device_class = BinarySensorDeviceClass.PROBLEM

	def __init__(self, coordinator) -> None:
		super().__init__(coordinator, "enforcer_degraded")

	@property
	def is_on(self) -> bool:
		state = self.state_data
		return bool(state.degraded_enforcers) or state.enforcement in (
			EnforcementStatus.PARTIAL,
			EnforcementStatus.DEGRADED,
			EnforcementStatus.UNKNOWN,
		)

	@property
	def extra_state_attributes(self) -> dict[str, Any]:
		return {"degraded_enforcers": self.state_data.degraded_enforcers, "enforcement": str(self.state_data.enforcement)}
