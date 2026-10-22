"""PIN entry: arms the dashboard for a guardian for a few minutes.

Switches, buttons and numbers cannot carry a PIN. When a PIN is set a
guardian types it here first; the entities then accept their writes until
the arming window closes. The PIN itself is checked once and never stored,
and the entity's state is always empty.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, PIN_ARM_SECONDS
from .entity import KerbChildEntity
from .hub import KerbConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
	hass: HomeAssistant, entry: KerbConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback
) -> None:
	async_add_entities([PinEntry(entry.runtime_data)])


class PinEntry(KerbChildEntity, TextEntity):
	_attr_icon = "mdi:dialpad"
	_attr_mode = TextMode.PASSWORD
	_attr_native_min = 0
	_attr_native_max = 32
	_attr_native_value = ""

	def __init__(self, coordinator) -> None:
		super().__init__(coordinator, "pin")

	@property
	def extra_state_attributes(self) -> dict[str, Any]:
		hub = self.coordinator.hub
		return {
			"pin_set": hub.household.pin_hash is not None,
			"arm_seconds": PIN_ARM_SECONDS,
			"armed": sorted(user_id for user_id in list(hub.armed) if hub.is_armed(user_id)),
		}

	async def async_set_value(self, value: str) -> None:
		self.guard(check_pin=False)
		context = self._context
		user_id = context.user_id if context else None
		if user_id is None:
			# An automation needs no PIN, so there is nobody to arm.
			return
		if not self.coordinator.hub.arm(user_id, value.strip()):
			_LOGGER.warning("Kerb refused a PIN entry from user %s", user_id)
			raise ServiceValidationError(translation_domain=DOMAIN, translation_key="bad_pin")
		self.async_write_ha_state()
