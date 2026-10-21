"""Shared entity base: one HA device per child."""

from __future__ import annotations

from homeassistant.core import Context
from homeassistant.exceptions import ServiceValidationError, Unauthorized
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .core.auth import BadPin, NotAGuardian, authorise
from .hub import KerbChildCoordinator


class KerbChildEntity(CoordinatorEntity[KerbChildCoordinator]):
	_attr_has_entity_name = True

	def __init__(self, coordinator: KerbChildCoordinator, key: str) -> None:
		super().__init__(coordinator)
		self._key = key
		self._attr_unique_id = f"{coordinator.child_id}_{key}"
		self._attr_translation_key = key
		self._attr_device_info = DeviceInfo(
			identifiers={(DOMAIN, coordinator.child_id)},
			name=coordinator.child.display_name,
			manufacturer="Kerb",
			model="Child",
		)

	@property
	def state_data(self):
		return self.coordinator.data

	def guard(self, pin: str | None = None) -> None:
		"""Refuse writes from HA users who are not guardians. No user means an automation, which is trusted."""
		context: Context | None = self._context
		user_id = context.user_id if context else None
		try:
			authorise(self.coordinator.hub.household, user_id, pin, trusted=user_id is None)
		except NotAGuardian as err:
			raise Unauthorized(context=context, permission="kerb.guardian") from err
		except BadPin as err:
			raise ServiceValidationError(translation_domain=DOMAIN, translation_key="bad_pin") from err

	def source(self) -> str:
		context: Context | None = self._context
		if context and context.user_id:
			return f"guardian:{context.user_id}"
		return "automation:entity"
