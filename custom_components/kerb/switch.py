"""Lock switches: one per child, one per device."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .core import overrides as ov
from .core.models import Device, Scope
from .entity import KerbChildEntity
from .hub import KerbConfigEntry


async def async_setup_entry(
	hass: HomeAssistant, entry: KerbConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
	coordinator = entry.runtime_data
	entities: list[SwitchEntity] = [ChildLockSwitch(coordinator)]
	entities.extend(DeviceLockSwitch(coordinator, device) for device in coordinator.controller.devices_for(coordinator.child_id))
	async_add_entities(entities)


class ChildLockSwitch(KerbChildEntity, SwitchEntity):
	"""On creates a lock that expires at end of day. Off cancels any lock in force."""

	_attr_icon = "mdi:lock-clock"

	def __init__(self, coordinator) -> None:
		super().__init__(coordinator, "lock")

	@property
	def is_on(self) -> bool:
		return self.state_data.lock_id is not None

	@property
	def extra_state_attributes(self) -> dict[str, Any]:
		state = self.state_data
		return {
			"override_id": state.lock_id,
			"reason": state.lock_reason,
			"expires_at": None if state.lock_expires_at is None else state.lock_expires_at.isoformat(),
			"enforcement": str(state.enforcement),
			"summary": state.summary,
		}

	async def async_turn_on(self, **kwargs: Any) -> None:
		self.guard()
		await self.coordinator.controller.lock(self.coordinator.child_id, reason="lock switch", source=self.source())
		await self.coordinator.hub.async_refresh()

	async def async_turn_off(self, **kwargs: Any) -> None:
		self.guard()
		await self.coordinator.controller.unlock(self.coordinator.child_id, reason="lock switch", source=self.source())
		await self.coordinator.hub.async_refresh()


class DeviceLockSwitch(KerbChildEntity, SwitchEntity):
	"""Lock one device only."""

	_attr_icon = "mdi:devices"

	def __init__(self, coordinator, device: Device) -> None:
		super().__init__(coordinator, f"device_lock_{device.id}")
		self._device = device
		self._attr_translation_key = "device_lock"
		self._attr_translation_placeholders = {"device": device.display_name}

	@property
	def is_on(self) -> bool:
		controller = self.coordinator.controller
		return (
			ov.effective_lock(controller.child_overrides(self.coordinator.child_id), controller.now(), self._device.id)
			is not None
		)

	@property
	def extra_state_attributes(self) -> dict[str, Any]:
		controller = self.coordinator.controller
		mode = controller.strongest_mode(self._device)
		return {
			"device_id": self._device.id,
			"platform": str(self._device.platform),
			"enforcers": list(self._device.enforcer_ids),
			"strongest_mode": None if mode is None else str(mode),
		}

	async def async_turn_on(self, **kwargs: Any) -> None:
		self.guard()
		await self.coordinator.controller.lock(
			self.coordinator.child_id,
			scope=Scope("device", device_id=self._device.id),
			reason="device lock switch",
			source=self.source(),
		)
		await self.coordinator.hub.async_refresh()

	async def async_turn_off(self, **kwargs: Any) -> None:
		self.guard()
		await self.coordinator.controller.unlock(
			self.coordinator.child_id,
			scope=Scope("device", device_id=self._device.id),
			reason="device lock switch",
			source=self.source(),
		)
		await self.coordinator.hub.async_refresh()
