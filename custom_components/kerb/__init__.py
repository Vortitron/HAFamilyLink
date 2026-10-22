"""Kerb: household screen time for Home Assistant.

One config entry per child. All entries share one hub, one controller and
one store. Vendor logins never live here; enforcement goes through existing
HA entities (network switches, smart plugs) or a manual done button.
"""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError, Unauthorized
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
	ATTR_CHILD,
	ATTR_DEVICE,
	ATTR_DURATION,
	ATTR_MINUTES,
	ATTR_MODE,
	ATTR_PIN,
	ATTR_REASON,
	ATTR_SCOPE,
	ATTR_SOURCE,
	CONF_CHILD_ID,
	DOMAIN,
	SERVICE_CONFIRM_MANUAL,
	SERVICE_GRANT,
	SERVICE_LOCK,
	SERVICE_RECONCILE,
	SERVICE_SET_ALLOWANCE_TODAY,
	SERVICE_UNLOCK,
	STORAGE_KEY,
	STORAGE_VERSION,
)
from .core.auth import BadPin, NotAGuardian
from .core.controller import Controller
from .core.ledger import GrantCapExceeded
from .core.models import Override, Scope
from .hub import KerbConfigEntry, KerbHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
	Platform.BINARY_SENSOR,
	Platform.BUTTON,
	Platform.NUMBER,
	Platform.SENSOR,
	Platform.SWITCH,
	Platform.TEXT,
]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

MODES = ("auto", "pause", "zero_allowance", "network", "power", "manual")
# A blank or null PIN from a template means "none given", never a refusal.
PIN_FIELD = vol.Any(None, cv.string)

LOCK_SCHEMA = vol.Schema(
	{
		vol.Required(ATTR_CHILD): cv.string,
		vol.Optional(ATTR_DURATION): cv.time_period,
		vol.Optional(ATTR_SCOPE, default="all"): cv.string,
		vol.Optional(ATTR_MODE, default="auto"): vol.In(MODES),
		vol.Optional(ATTR_REASON, default=""): cv.string,
		vol.Optional(ATTR_PIN): PIN_FIELD,
	}
)
UNLOCK_SCHEMA = vol.Schema(
	{
		vol.Required(ATTR_CHILD): cv.string,
		vol.Optional(ATTR_SCOPE, default="all"): cv.string,
		vol.Optional(ATTR_REASON, default=""): cv.string,
		vol.Optional(ATTR_PIN): PIN_FIELD,
	}
)
GRANT_SCHEMA = vol.Schema(
	{
		vol.Required(ATTR_CHILD): cv.string,
		vol.Required(ATTR_MINUTES): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
		vol.Optional(ATTR_REASON, default=""): cv.string,
		vol.Optional(ATTR_SOURCE): cv.string,
		vol.Optional(ATTR_PIN): PIN_FIELD,
	}
)
ALLOWANCE_SCHEMA = vol.Schema(
	{
		vol.Required(ATTR_CHILD): cv.string,
		vol.Required(ATTR_MINUTES): vol.All(vol.Coerce(int), vol.Range(min=0, max=1440)),
		vol.Optional(ATTR_PIN): PIN_FIELD,
	}
)
CONFIRM_MANUAL_SCHEMA = vol.Schema(
	{vol.Required(ATTR_CHILD): cv.string, vol.Required(ATTR_DEVICE): cv.string, vol.Optional(ATTR_PIN): PIN_FIELD}
)


def get_hub(hass: HomeAssistant) -> KerbHub:
	hub: KerbHub | None = hass.data.get(DOMAIN)
	if hub is None:
		hub = KerbHub(hass)
		hass.data[DOMAIN] = hub
	return hub


def source_for(call: ServiceCall, default: str | None = None) -> str:
	if default:
		return f"integration:{default}"
	if call.context.user_id:
		return f"guardian:{call.context.user_id}"
	return "automation:" + (call.context.parent_id or call.context.id)


def check_access(hub: KerbHub, call: ServiceCall, check_pin: bool = True) -> None:
	"""Automations and the owner context have no user and are trusted. Users must be guardians.

	A PIN, when set, must come in the call or have been entered on the PIN
	entity within the arming window. Confirming a manual step needs no PIN.
	"""
	user_id = call.context.user_id
	pin = call.data.get(ATTR_PIN) or None
	try:
		hub.authorise(user_id, pin, check_pin=check_pin)
	except NotAGuardian as err:
		_LOGGER.warning("Kerb refused %s from user %s: not a guardian", call.service, user_id)
		raise Unauthorized(context=call.context, permission="kerb.guardian") from err
	except BadPin as err:
		_LOGGER.warning("Kerb refused %s from user %s: PIN missing or wrong", call.service, user_id)
		raise ServiceValidationError(translation_domain=DOMAIN, translation_key="bad_pin") from err


def response_for(hub: KerbHub, override: Override) -> ServiceResponse:
	return {
		"override_id": override.id,
		"status": str(override.status),
		"expires_at": override.expires_at.isoformat(),
		"summary": hub.controller.summary(override),
		"results": [result.to_dict() for result in override.results],
	}


def resolve_child(hub: KerbHub, call: ServiceCall) -> str:
	child_id = hub.child_id_for(call.data[ATTR_CHILD])
	if child_id is None:
		raise ServiceValidationError(
			translation_domain=DOMAIN, translation_key="unknown_child", translation_placeholders={"child": call.data[ATTR_CHILD]}
		)
	return child_id


def resolve_scope(hub: KerbHub, child_id: str, raw: str) -> Scope:
	if raw in ("", "all"):
		return Scope()
	device_id = hub.device_id_for(child_id, raw)
	if device_id is None:
		raise ServiceValidationError(
			translation_domain=DOMAIN, translation_key="unknown_device", translation_placeholders={"device": raw}
		)
	return Scope("device", device_id=device_id)


def register_services(hass: HomeAssistant) -> None:
	if hass.services.has_service(DOMAIN, SERVICE_LOCK):
		return

	async def handle_lock(call: ServiceCall) -> ServiceResponse:
		hub = get_hub(hass)
		check_access(hub, call)
		child_id = resolve_child(hub, call)
		duration: timedelta | None = call.data.get(ATTR_DURATION)
		minutes = int(duration.total_seconds() // 60) if duration else None
		override = await hub.controller.lock(
			child_id,
			minutes=minutes or None,
			scope=resolve_scope(hub, child_id, call.data[ATTR_SCOPE]),
			reason=call.data[ATTR_REASON],
			source=source_for(call),
			mode=call.data[ATTR_MODE],
		)
		await hub.async_refresh()
		return response_for(hub, override)

	async def handle_unlock(call: ServiceCall) -> ServiceResponse:
		hub = get_hub(hass)
		check_access(hub, call)
		child_id = resolve_child(hub, call)
		override = await hub.controller.unlock(
			child_id,
			scope=resolve_scope(hub, child_id, call.data[ATTR_SCOPE]),
			reason=call.data[ATTR_REASON],
			source=source_for(call),
		)
		await hub.async_refresh()
		return response_for(hub, override)

	async def handle_grant(call: ServiceCall) -> ServiceResponse:
		hub = get_hub(hass)
		check_access(hub, call)
		child_id = resolve_child(hub, call)
		try:
			override = await hub.controller.grant(
				child_id,
				call.data[ATTR_MINUTES],
				reason=call.data[ATTR_REASON],
				source=source_for(call, call.data.get(ATTR_SOURCE)),
			)
		except GrantCapExceeded as err:
			raise ServiceValidationError(
				translation_domain=DOMAIN, translation_key="grant_cap", translation_placeholders={"detail": str(err)}
			) from err
		await hub.async_refresh()
		return response_for(hub, override)

	async def handle_allowance(call: ServiceCall) -> ServiceResponse:
		hub = get_hub(hass)
		check_access(hub, call)
		child_id = resolve_child(hub, call)
		override = await hub.controller.set_allowance_today(child_id, call.data[ATTR_MINUTES], source=source_for(call))
		await hub.async_refresh()
		return response_for(hub, override)

	async def handle_reconcile(call: ServiceCall) -> None:
		hub = get_hub(hass)
		await hub.controller.reconcile()
		await hub.async_refresh()

	async def handle_confirm_manual(call: ServiceCall) -> None:
		hub = get_hub(hass)
		check_access(hub, call, check_pin=False)
		child_id = resolve_child(hub, call)
		device_id = hub.device_id_for(child_id, call.data[ATTR_DEVICE])
		if device_id is None or device_id not in hub.manual:
			raise ServiceValidationError(
				translation_domain=DOMAIN,
				translation_key="unknown_device",
				translation_placeholders={"device": call.data[ATTR_DEVICE]},
			)
		await hub.async_confirm_manual(device_id)

	hass.services.async_register(DOMAIN, SERVICE_LOCK, handle_lock, LOCK_SCHEMA, SupportsResponse.OPTIONAL)
	hass.services.async_register(DOMAIN, SERVICE_UNLOCK, handle_unlock, UNLOCK_SCHEMA, SupportsResponse.OPTIONAL)
	hass.services.async_register(DOMAIN, SERVICE_GRANT, handle_grant, GRANT_SCHEMA, SupportsResponse.OPTIONAL)
	hass.services.async_register(
		DOMAIN, SERVICE_SET_ALLOWANCE_TODAY, handle_allowance, ALLOWANCE_SCHEMA, SupportsResponse.OPTIONAL
	)
	hass.services.async_register(DOMAIN, SERVICE_RECONCILE, handle_reconcile, vol.Schema({}))
	hass.services.async_register(DOMAIN, SERVICE_CONFIRM_MANUAL, handle_confirm_manual, CONFIRM_MANUAL_SCHEMA)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
	register_services(hass)
	return True


async def async_setup_entry(hass: HomeAssistant, entry: KerbConfigEntry) -> bool:
	hub = get_hub(hass)
	await hub.async_load()
	coordinator = hub.add_entry(entry)
	try:
		await hub.controller.reconcile(coordinator.child_id)
	except Exception as err:  # noqa: BLE001
		raise HomeAssistantError(f"Kerb could not read its enforcers: {err}") from err
	await coordinator.async_config_entry_first_refresh()
	entry.runtime_data = coordinator
	await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
	entry.async_on_unload(entry.add_update_listener(_async_options_updated))
	return True


async def _async_options_updated(hass: HomeAssistant, entry: KerbConfigEntry) -> None:
	await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: KerbConfigEntry) -> bool:
	unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
	if unloaded:
		hub = get_hub(hass)
		hub.remove_entry(entry)
		if not hub.coordinators:
			await hub.async_unload()
			hass.data.pop(DOMAIN, None)
	return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: KerbConfigEntry) -> None:
	"""The child was deleted, not just unloaded: forget their ledgers and overrides."""
	child_id = entry.data[CONF_CHILD_ID]
	hub: KerbHub | None = hass.data.get(DOMAIN)
	if hub is not None:
		await hub.async_forget_child(child_id)
		return
	# This was the last child, so the hub is gone. Edit the stored document directly.
	store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
	data = await store.async_load()
	if data:
		await store.async_save(Controller.without_child(data, child_id))


def entry_summary(entry: KerbConfigEntry) -> dict[str, Any]:
	"""Diagnostics helper: what an entry configured, without any PIN hash."""
	data = dict(entry.data)
	data.pop("pin_hash", None)
	return {"data": data, "options": dict(entry.options)}
