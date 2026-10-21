"""Allowance today: writes an allowance_today override. Mirrors Matter SetScreenDailyTime."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import KerbChildEntity
from .hub import KerbConfigEntry


async def async_setup_entry(
	hass: HomeAssistant, entry: KerbConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
	async_add_entities([AllowanceTodayNumber(entry.runtime_data)])


class AllowanceTodayNumber(KerbChildEntity, NumberEntity):
	_attr_icon = "mdi:calendar-clock"
	_attr_native_min_value = 0
	_attr_native_max_value = 1440
	_attr_native_step = 5
	_attr_native_unit_of_measurement = UnitOfTime.MINUTES
	_attr_mode = NumberMode.BOX

	def __init__(self, coordinator) -> None:
		super().__init__(coordinator, "allowance_today")

	@property
	def native_value(self) -> float:
		return self.state_data.allowance

	async def async_set_native_value(self, value: float) -> None:
		self.guard()
		await self.coordinator.controller.set_allowance_today(self.coordinator.child_id, int(value), source=self.source())
		await self.coordinator.hub.async_refresh()
