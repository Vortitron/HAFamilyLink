"""The household hub: one controller shared by every child entry, plus storage and the tick timer."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
	CONF_AGE_BAND,
	CONF_ALLOWANCE_DAYS,
	CONF_BEDTIME_END,
	CONF_BEDTIME_START,
	CONF_CHILD_ID,
	CONF_CONFIRMATION_WINDOW,
	CONF_DEVICE_ID,
	CONF_DEVICE_NAME,
	CONF_DEVICES,
	CONF_GRACEFUL_OFF,
	CONF_GRANT_CAP,
	CONF_GUARDIANS,
	CONF_IN_USE_ENTITY,
	CONF_LOW_THRESHOLD,
	CONF_MANUAL,
	CONF_NAME,
	CONF_NETWORK_INVERTED,
	CONF_NETWORK_SWITCHES,
	CONF_PIN_HASH,
	CONF_PLATFORM,
	CONF_POWER_DELAY,
	CONF_POWER_OPT_IN,
	CONF_POWER_SWITCH,
	CONF_RETENTION_DAYS,
	DEFAULT_ALLOWANCE,
	DEFAULT_CONFIRMATION_WINDOW,
	DEFAULT_LOW_THRESHOLD,
	DEFAULT_POWER_DELAY,
	DEFAULT_RETENTION_DAYS,
	DOMAIN,
	EVENT_TYPE,
	PIN_ARM_SECONDS,
	STORAGE_KEY,
	STORAGE_VERSION,
	TICK_SECONDS,
)
from .core.auth import authorise, verify_pin
from .core.controller import ChildState, Controller
from .core.models import AgeBand, Child, Device, Event, Household, Platform, Policy, TimeWindow
from .enforcers import ManualEnforcer, NetworkEnforcer, PowerEnforcer, PresenceObserver

_LOGGER = logging.getLogger(__name__)

type KerbConfigEntry = ConfigEntry["KerbChildCoordinator"]


def policy_from_options(child_id: str, options: dict[str, Any]) -> Policy:
	allowance = [int(options.get(key, DEFAULT_ALLOWANCE)) for key in CONF_ALLOWANCE_DAYS]
	start = options.get(CONF_BEDTIME_START)
	end = options.get(CONF_BEDTIME_END)
	bedtime: list[TimeWindow | None] = [None] * 7
	if start and end:
		bedtime = [TimeWindow(start[:5], end[:5])] * 7
	return Policy(
		child_id=child_id,
		allowance_minutes=allowance,
		bedtime=bedtime,
		grant_cap_minutes_per_day=options.get(CONF_GRANT_CAP) or None,
	)


class KerbHub:
	"""Owns the controller, the store and the timer. Created on the first entry, torn down on the last."""

	def __init__(self, hass: HomeAssistant) -> None:
		self.hass = hass
		self.household = Household(time_zone=hass.config.time_zone or "UTC")
		self.controller = Controller(self.household, dt_util.now)
		self.store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, STORAGE_KEY)
		self.coordinators: dict[str, KerbChildCoordinator] = {}
		self.manual: dict[str, ManualEnforcer] = {}
		self.pins: dict[str, str | None] = {}
		self.armed: dict[str, datetime] = {}
		self._unsub_timer: Callable[[], None] | None = None
		self._unsub_events: Callable[[], None] | None = None
		self._loaded = False

	async def async_load(self) -> None:
		if self._loaded:
			return
		data = await self.store.async_load()
		if data:
			self.controller.load(data)
		self._unsub_events = self.controller.listen(self._on_event)
		self._unsub_timer = async_track_time_interval(self.hass, self._tick, timedelta(seconds=TICK_SECONDS))
		self._loaded = True

	async def async_unload(self) -> None:
		if self._unsub_timer:
			self._unsub_timer()
		if self._unsub_events:
			self._unsub_events()
		await self.store.async_save(self.controller.to_dict())

	def add_entry(self, entry: KerbConfigEntry) -> KerbChildCoordinator:
		child_id = entry.data[CONF_CHILD_ID]
		child = Child(display_name=entry.data[CONF_NAME], age_band=AgeBand(entry.data[CONF_AGE_BAND]), id=child_id)
		self.controller.add_child(child, policy_from_options(child_id, dict(entry.options)))
		window = int(entry.options.get(CONF_CONFIRMATION_WINDOW, DEFAULT_CONFIRMATION_WINDOW))
		for spec in entry.data.get(CONF_DEVICES, []):
			self._add_device(child_id, spec, window)
		for user_id in entry.data.get(CONF_GUARDIANS, []):
			if user_id not in self.household.guardians:
				self.household.guardians.append(user_id)
		self.pins[entry.entry_id] = entry.data.get(CONF_PIN_HASH)
		self._refresh_pin()
		self.controller.low_threshold = int(entry.options.get(CONF_LOW_THRESHOLD, DEFAULT_LOW_THRESHOLD))
		self.household.usage_retention_days = int(entry.options.get(CONF_RETENTION_DAYS, DEFAULT_RETENTION_DAYS))
		coordinator = KerbChildCoordinator(self.hass, self, entry, child_id)
		self.coordinators[entry.entry_id] = coordinator
		return coordinator

	def remove_entry(self, entry: KerbConfigEntry) -> None:
		"""Unload a child. Ledgers and overrides stay: this also runs on a reload. See ``async_forget_child``."""
		child_id = entry.data[CONF_CHILD_ID]
		self.coordinators.pop(entry.entry_id, None)
		self.pins.pop(entry.entry_id, None)
		self._refresh_pin()
		self.controller.children.pop(child_id, None)
		self.controller.policies.pop(child_id, None)
		for device in list(self.controller.devices_for(child_id)):
			self.controller.devices.pop(device.id, None)
			for name in device.enforcer_ids:
				if not any(name in other.enforcer_ids for other in self.controller.devices.values()):
					self.controller.enforcers.pop(name, None)
					self.manual.pop(name, None)

	async def async_forget_child(self, child_id: str) -> None:
		"""The entry was deleted: drop everything stored about the child and save now."""
		self.controller.forget_child(child_id)
		await self.store.async_save(self.controller.to_dict())

	def _refresh_pin(self) -> None:
		self.household.pin_hash = next((pin for pin in self.pins.values() if pin), None)

	# Access

	def authorise(self, user_id: str | None, pin: str | None = None, check_pin: bool = True) -> None:
		"""The guardian check and PIN for any write.

		A call with no user is an automation or the owner context and is
		trusted. A guardian who entered the PIN on the dashboard within the
		arming window does not have to send it again.
		"""
		if pin is None and user_id is not None and self.is_armed(user_id):
			check_pin = False
		authorise(self.household, user_id, pin, trusted=user_id is None, check_pin=check_pin)

	def arm(self, user_id: str, pin: str) -> bool:
		"""Check the PIN once and arm the dashboard for this guardian. Never stores the PIN."""
		if not verify_pin(self.household.pin_hash, pin):
			self.armed.pop(user_id, None)
			return False
		self.armed[user_id] = dt_util.utcnow() + timedelta(seconds=PIN_ARM_SECONDS)
		return True

	def is_armed(self, user_id: str) -> bool:
		until = self.armed.get(user_id)
		if until is None:
			return False
		if until <= dt_util.utcnow():
			self.armed.pop(user_id, None)
			return False
		return True

	def armed_until(self, user_id: str) -> datetime | None:
		return self.armed.get(user_id) if self.is_armed(user_id) else None

	def _add_device(self, child_id: str, spec: dict[str, Any], window: int) -> None:
		device = Device(
			id=spec[CONF_DEVICE_ID],
			display_name=spec[CONF_DEVICE_NAME],
			platform=Platform(spec.get(CONF_PLATFORM, "other")),
			child_id=child_id,
			power_off_allowed=bool(spec.get(CONF_POWER_OPT_IN, False)),
		)
		inverted = bool(spec.get(CONF_NETWORK_INVERTED, False))
		for entity_id in spec.get(CONF_NETWORK_SWITCHES, []):
			enforcer = NetworkEnforcer(self.hass, entity_id, inverted, window)
			self.controller.add_enforcer(enforcer)
			device.enforcer_ids.append(enforcer.name)
		if spec.get(CONF_POWER_SWITCH):
			enforcer = PowerEnforcer(
				self.hass,
				spec[CONF_POWER_SWITCH],
				spec.get(CONF_GRACEFUL_OFF) or None,
				int(spec.get(CONF_POWER_DELAY, DEFAULT_POWER_DELAY)),
				window,
			)
			self.controller.add_enforcer(enforcer)
			device.enforcer_ids.append(enforcer.name)
		if spec.get(CONF_IN_USE_ENTITY):
			observer = PresenceObserver(self.hass, spec[CONF_IN_USE_ENTITY])
			self.controller.add_enforcer(observer)
			device.enforcer_ids.append(observer.name)
		if spec.get(CONF_MANUAL):
			manual = ManualEnforcer(self.hass, device.id, device.display_name)
			manual.on_change = lambda: self.hass.async_create_task(self.async_refresh())
			self.controller.add_enforcer(manual)
			self.manual[device.id] = manual
			device.enforcer_ids.append(manual.name)
		self.controller.add_device(device)

	# Runtime

	async def _tick(self, _now=None) -> None:
		try:
			await self.controller.tick()
			self.controller.prune()
		except Exception:  # noqa: BLE001 - a tick must never kill the timer
			_LOGGER.exception("Kerb tick failed")
		await self.async_refresh()

	async def async_refresh(self) -> None:
		"""Push fresh child states to every coordinator and save."""
		for coordinator in self.coordinators.values():
			coordinator.async_set_updated_data(self.controller.child_state(coordinator.child_id))
		self.store.async_delay_save(self.controller.to_dict, 5)

	async def async_confirm_manual(self, device_id: str) -> None:
		manual = self.manual.get(device_id)
		if manual is None:
			raise KeyError(device_id)
		manual.mark_done()
		await self.controller.reconcile()
		await self.async_refresh()

	def child_id_for(self, name: str) -> str | None:
		"""Match a child by display name, case-insensitively, or by id."""
		wanted = name.strip().casefold()
		for child in self.controller.children.values():
			if child.id == name or child.display_name.casefold() == wanted:
				return child.id
		return None

	def device_id_for(self, child_id: str, name: str) -> str | None:
		wanted = name.strip().casefold()
		for device in self.controller.devices_for(child_id):
			if device.id == name or device.display_name.casefold() == wanted:
				return device.id
		return None

	@callback
	def _on_event(self, event: Event) -> None:
		payload = event.to_dict()
		self.hass.bus.async_fire(EVENT_TYPE, payload)
		if event.type == "enforcer.degraded":
			ir.async_create_issue(
				self.hass,
				DOMAIN,
				f"enforcer_{event.payload['enforcer']}",
				is_fixable=False,
				severity=ir.IssueSeverity.WARNING,
				translation_key="enforcer_degraded",
				translation_placeholders={
					"enforcer": event.payload["enforcer"],
					"status": event.payload.get("status", "unknown"),
					"reason": event.payload.get("reason", ""),
				},
			)
		elif event.type == "enforcer.restored":
			ir.async_delete_issue(self.hass, DOMAIN, f"enforcer_{event.payload['enforcer']}")
		if event.type in (
			"override.applied",
			"override.confirmed",
			"override.partial",
			"override.failed",
			"enforcement.unconfirmed",
		):
			_LOGGER.debug("Kerb %s for child %s", event.type, event.child_id)


class KerbChildCoordinator(DataUpdateCoordinator[ChildState]):
	"""Per-child state for the entities. Fed by the hub, no polling of its own."""

	def __init__(self, hass: HomeAssistant, hub: KerbHub, entry: KerbConfigEntry, child_id: str) -> None:
		super().__init__(hass, _LOGGER, name=f"{DOMAIN} {entry.data[CONF_NAME]}", config_entry=entry, update_interval=None)
		self.hub = hub
		self.child_id = child_id
		self.entry = entry

	@property
	def child(self) -> Child:
		return self.hub.controller.children[self.child_id]

	@property
	def controller(self) -> Controller:
		return self.hub.controller

	async def _async_update_data(self) -> ChildState:
		return self.controller.child_state(self.child_id)
