"""Grant buttons per child, and a done button per manual device."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, GRANT_BUTTONS
from .core.ledger import GrantCapExceeded
from .entity import KerbChildEntity
from .hub import KerbConfigEntry


async def async_setup_entry(
	hass: HomeAssistant, entry: KerbConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
	coordinator = entry.runtime_data
	entities: list[ButtonEntity] = [GrantButton(coordinator, minutes) for minutes in GRANT_BUTTONS]
	for device in coordinator.controller.devices_for(coordinator.child_id):
		if device.id in coordinator.hub.manual:
			entities.append(ManualDoneButton(coordinator, device.id, device.display_name))
	async_add_entities(entities)


class GrantButton(KerbChildEntity, ButtonEntity):
	_attr_icon = "mdi:plus-circle-outline"

	def __init__(self, coordinator, minutes: int) -> None:
		super().__init__(coordinator, f"grant_{minutes}")
		self._minutes = minutes
		self._attr_translation_key = "grant"
		self._attr_translation_placeholders = {"minutes": str(minutes)}

	async def async_press(self) -> None:
		self.guard()
		try:
			await self.coordinator.controller.grant(
				self.coordinator.child_id, self._minutes, reason="grant button", source=self.source()
			)
		except GrantCapExceeded as err:
			raise ServiceValidationError(
				translation_domain=DOMAIN, translation_key="grant_cap", translation_placeholders={"detail": str(err)}
			) from err
		await self.coordinator.hub.async_refresh()


class ManualDoneButton(KerbChildEntity, ButtonEntity):
	_attr_icon = "mdi:check-decagram"

	def __init__(self, coordinator, device_id: str, device_name: str) -> None:
		super().__init__(coordinator, f"manual_done_{device_id}")
		self._device_id = device_id
		self._attr_translation_key = "manual_done"
		self._attr_translation_placeholders = {"device": device_name}

	async def async_press(self) -> None:
		self.guard(check_pin=False)
		await self.coordinator.hub.async_confirm_manual(self._device_id)
