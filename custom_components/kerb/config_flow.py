"""Config and options flows: a child, their devices as existing HA entities, guardians and a PIN."""

from __future__ import annotations

from typing import Any
import uuid

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
	BooleanSelector,
	EntitySelector,
	EntitySelectorConfig,
	NumberSelector,
	NumberSelectorConfig,
	NumberSelectorMode,
	SelectOptionDict,
	SelectSelector,
	SelectSelectorConfig,
	SelectSelectorMode,
	TextSelector,
	TextSelectorConfig,
	TextSelectorType,
	TimeSelector,
)
import voluptuous as vol

from .const import (
	CONF_ADD_ANOTHER,
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
	CONF_PIN,
	CONF_PIN_HASH,
	CONF_PLATFORM,
	CONF_POWER_DELAY,
	CONF_POWER_OPT_IN,
	CONF_POWER_SWITCH,
	CONF_RETENTION_DAYS,
	CONFIG_VERSION,
	DEFAULT_ALLOWANCE,
	DEFAULT_CONFIRMATION_WINDOW,
	DEFAULT_LOW_THRESHOLD,
	DEFAULT_POWER_DELAY,
	DEFAULT_RETENTION_DAYS,
	DOMAIN,
)
from .core.auth import hash_pin
from .core.models import AgeBand, Platform

CHILD_SCHEMA = vol.Schema(
	{
		vol.Required(CONF_NAME): TextSelector(),
		vol.Required(CONF_AGE_BAND, default=str(AgeBand.SEVEN_TO_12)): SelectSelector(
			SelectSelectorConfig(
				options=[str(band) for band in AgeBand], translation_key="age_band", mode=SelectSelectorMode.DROPDOWN
			)
		),
	}
)

DEVICE_SCHEMA = vol.Schema(
	{
		vol.Required(CONF_DEVICE_NAME): TextSelector(),
		vol.Required(CONF_PLATFORM, default=str(Platform.OTHER)): SelectSelector(
			SelectSelectorConfig(
				options=[str(platform) for platform in Platform], translation_key="platform", mode=SelectSelectorMode.DROPDOWN
			)
		),
		vol.Optional(CONF_NETWORK_SWITCHES, default=[]): EntitySelector(
			EntitySelectorConfig(domain=["switch", "input_boolean"], multiple=True)
		),
		vol.Optional(CONF_NETWORK_INVERTED, default=False): BooleanSelector(),
		vol.Optional(CONF_POWER_SWITCH): EntitySelector(EntitySelectorConfig(domain=["switch", "input_boolean"])),
		vol.Optional(CONF_GRACEFUL_OFF): EntitySelector(EntitySelectorConfig(domain=["remote", "media_player", "switch"])),
		vol.Optional(CONF_POWER_OPT_IN, default=False): BooleanSelector(),
		vol.Optional(CONF_POWER_DELAY, default=DEFAULT_POWER_DELAY): NumberSelector(
			NumberSelectorConfig(min=0, max=600, step=5, unit_of_measurement="s", mode=NumberSelectorMode.BOX)
		),
		vol.Optional(CONF_IN_USE_ENTITY): EntitySelector(
			EntitySelectorConfig(domain=["binary_sensor", "media_player", "device_tracker", "sensor", "switch"])
		),
		vol.Optional(CONF_MANUAL, default=False): BooleanSelector(),
		vol.Optional(CONF_ADD_ANOTHER, default=False): BooleanSelector(),
	}
)


def _minutes(default: int) -> NumberSelector:
	return NumberSelector(NumberSelectorConfig(min=0, max=1440, step=5, unit_of_measurement="min", mode=NumberSelectorMode.BOX))


def options_schema(options: dict[str, Any]) -> vol.Schema:
	fields: dict[Any, Any] = {}
	for key in CONF_ALLOWANCE_DAYS:
		fields[vol.Required(key, default=options.get(key, DEFAULT_ALLOWANCE))] = _minutes(DEFAULT_ALLOWANCE)
	fields[vol.Optional(CONF_BEDTIME_START, description={"suggested_value": options.get(CONF_BEDTIME_START)})] = TimeSelector()
	fields[vol.Optional(CONF_BEDTIME_END, description={"suggested_value": options.get(CONF_BEDTIME_END)})] = TimeSelector()
	fields[vol.Optional(CONF_GRANT_CAP, default=options.get(CONF_GRANT_CAP, 0))] = _minutes(0)
	fields[vol.Required(CONF_CONFIRMATION_WINDOW, default=options.get(CONF_CONFIRMATION_WINDOW, DEFAULT_CONFIRMATION_WINDOW))] = (
		NumberSelector(NumberSelectorConfig(min=10, max=3600, step=10, unit_of_measurement="s", mode=NumberSelectorMode.BOX))
	)
	fields[vol.Required(CONF_LOW_THRESHOLD, default=options.get(CONF_LOW_THRESHOLD, DEFAULT_LOW_THRESHOLD))] = _minutes(
		DEFAULT_LOW_THRESHOLD
	)
	fields[vol.Required(CONF_RETENTION_DAYS, default=options.get(CONF_RETENTION_DAYS, DEFAULT_RETENTION_DAYS))] = NumberSelector(
		NumberSelectorConfig(min=0, max=366, step=1, unit_of_measurement="d", mode=NumberSelectorMode.BOX)
	)
	return vol.Schema(fields)


def _clean_options(user_input: dict[str, Any]) -> dict[str, Any]:
	cleaned: dict[str, Any] = {}
	for key, value in user_input.items():
		if key in CONF_ALLOWANCE_DAYS or key in (
			CONF_GRANT_CAP,
			CONF_CONFIRMATION_WINDOW,
			CONF_LOW_THRESHOLD,
			CONF_RETENTION_DAYS,
		):
			cleaned[key] = int(value)
		elif value not in (None, ""):
			cleaned[key] = value
	return cleaned


class KerbConfigFlow(ConfigFlow, domain=DOMAIN):
	VERSION = CONFIG_VERSION

	def __init__(self) -> None:
		self._child: dict[str, Any] = {}
		self._devices: list[dict[str, Any]] = []

	@staticmethod
	@callback
	def async_get_options_flow(config_entry: ConfigEntry) -> KerbOptionsFlow:
		return KerbOptionsFlow()

	async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
		errors: dict[str, str] = {}
		if user_input is not None:
			name = user_input[CONF_NAME].strip()
			if not name:
				errors[CONF_NAME] = "empty_name"
			elif any(entry.data.get(CONF_NAME, "").casefold() == name.casefold() for entry in self._async_current_entries()):
				errors[CONF_NAME] = "duplicate_name"
			else:
				self._child = {CONF_NAME: name, CONF_AGE_BAND: user_input[CONF_AGE_BAND], CONF_CHILD_ID: str(uuid.uuid4())}
				return await self.async_step_device()
		return self.async_show_form(step_id="user", data_schema=CHILD_SCHEMA, errors=errors)

	async def async_step_device(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
		errors: dict[str, str] = {}
		if user_input is not None:
			add_another = user_input.pop(CONF_ADD_ANOTHER, False)
			has_enforcer = (
				bool(user_input.get(CONF_NETWORK_SWITCHES))
				or bool(user_input.get(CONF_POWER_SWITCH))
				or user_input.get(CONF_MANUAL)
			)
			if not user_input[CONF_DEVICE_NAME].strip():
				errors[CONF_DEVICE_NAME] = "empty_name"
			elif not has_enforcer:
				errors["base"] = "no_enforcer"
			else:
				spec = {key: value for key, value in user_input.items() if value not in (None, "", [])}
				spec[CONF_DEVICE_ID] = str(uuid.uuid4())
				spec[CONF_DEVICE_NAME] = user_input[CONF_DEVICE_NAME].strip()
				if CONF_POWER_DELAY in spec:
					spec[CONF_POWER_DELAY] = int(spec[CONF_POWER_DELAY])
				self._devices.append(spec)
				if add_another:
					return await self.async_step_device()
				return await self.async_step_guardians()
		return self.async_show_form(
			step_id="device",
			data_schema=DEVICE_SCHEMA,
			errors=errors,
			description_placeholders={"child": self._child[CONF_NAME], "count": str(len(self._devices))},
		)

	async def async_step_guardians(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
		users = [user for user in await self.hass.auth.async_get_users() if not user.system_generated and user.is_active]
		options = [SelectOptionDict(value=user.id, label=user.name or user.id) for user in users]
		admins = [user.id for user in users if user.is_admin]
		if user_input is not None:
			pin = (user_input.get(CONF_PIN) or "").strip()
			data = {
				**self._child,
				CONF_DEVICES: self._devices,
				CONF_GUARDIANS: list(user_input.get(CONF_GUARDIANS, admins)),
				CONF_PIN_HASH: hash_pin(pin) if pin else None,
			}
			return self.async_create_entry(title=self._child[CONF_NAME], data=data)
		schema: dict[Any, Any] = {}
		if options:
			schema[vol.Optional(CONF_GUARDIANS, default=admins)] = SelectSelector(
				SelectSelectorConfig(options=options, multiple=True, mode=SelectSelectorMode.LIST)
			)
		schema[vol.Optional(CONF_PIN)] = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
		return self.async_show_form(step_id="guardians", data_schema=vol.Schema(schema))


class KerbOptionsFlow(OptionsFlow):
	async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
		if user_input is not None:
			return self.async_create_entry(title="", data=_clean_options(user_input))
		return self.async_show_form(step_id="init", data_schema=options_schema(dict(self.config_entry.options)))
