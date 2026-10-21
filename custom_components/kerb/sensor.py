"""Per-child sensors: remaining, used, status, enforcement."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core.controller import ChildState
from .core.models import ChildStatus, EnforcementStatus
from .entity import KerbChildEntity
from .hub import KerbConfigEntry


@dataclass(frozen=True, kw_only=True)
class KerbSensorDescription(SensorEntityDescription):
	value: Callable[[ChildState], Any]
	attributes: Callable[[ChildState], dict[str, Any]] = lambda state: {}


DESCRIPTIONS: tuple[KerbSensorDescription, ...] = (
	KerbSensorDescription(
		key="remaining_today",
		translation_key="remaining_today",
		native_unit_of_measurement=UnitOfTime.MINUTES,
		device_class=SensorDeviceClass.DURATION,
		state_class=SensorStateClass.MEASUREMENT,
		icon="mdi:timer-sand",
		value=lambda state: state.remaining,
		attributes=lambda state: {"confidence": str(state.confidence), "allowance": state.allowance, "granted": state.granted},
	),
	KerbSensorDescription(
		key="used_today",
		translation_key="used_today",
		native_unit_of_measurement=UnitOfTime.MINUTES,
		device_class=SensorDeviceClass.DURATION,
		state_class=SensorStateClass.TOTAL_INCREASING,
		icon="mdi:timer-outline",
		value=lambda state: state.used,
		attributes=lambda state: {"devices_without_per_app_usage": state.devices_without_per_app_usage},
	),
	KerbSensorDescription(
		key="status",
		translation_key="status",
		device_class=SensorDeviceClass.ENUM,
		options=[str(value) for value in ChildStatus],
		icon="mdi:account-child",
		value=lambda state: str(state.status),
		attributes=lambda state: {
			"lock_reason": state.lock_reason,
			"lock_expires_at": None if state.lock_expires_at is None else state.lock_expires_at.isoformat(),
			"summary": state.summary,
		},
	),
	KerbSensorDescription(
		key="enforcement",
		translation_key="enforcement",
		device_class=SensorDeviceClass.ENUM,
		options=[str(value) for value in EnforcementStatus],
		icon="mdi:shield-check",
		value=lambda state: str(state.enforcement),
		attributes=lambda state: {"degraded_enforcers": state.degraded_enforcers},
	),
)


async def async_setup_entry(
	hass: HomeAssistant, entry: KerbConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
	coordinator = entry.runtime_data
	async_add_entities(KerbSensor(coordinator, description) for description in DESCRIPTIONS)


class KerbSensor(KerbChildEntity, SensorEntity):
	entity_description: KerbSensorDescription

	def __init__(self, coordinator, description: KerbSensorDescription) -> None:
		super().__init__(coordinator, description.key)
		self.entity_description = description

	@property
	def native_value(self) -> Any:
		return self.entity_description.value(self.state_data)

	@property
	def extra_state_attributes(self) -> dict[str, Any]:
		return self.entity_description.attributes(self.state_data)
