"""Fixtures for the pure-Python core tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from kerb_core.controller import Controller
from kerb_core.enforcer import BaseEnforcer
from kerb_core.models import (
	AgeBand,
	Capabilities,
	Child,
	Device,
	DeviceRef,
	EnforcedState,
	EnforcerResult,
	Health,
	HealthStatus,
	Household,
	Mode,
	Override,
	OverrideKind,
	Platform,
	Policy,
	ResultStatus,
	TimeWindow,
)

TZ = ZoneInfo("Europe/London")
# Wednesday 21 October 2026, 17:00 in London (BST, UTC+1).
START = datetime(2026, 10, 21, 17, 0, tzinfo=TZ)


class Clock:
	def __init__(self, start: datetime = START) -> None:
		self.now = start

	def __call__(self) -> datetime:
		return self.now

	def advance(self, minutes: float = 0, seconds: float = 0) -> datetime:
		self.now += timedelta(minutes=minutes, seconds=seconds)
		return self.now


CAPS = {
	Mode.NETWORK: dict(level=1, lock_now=True, unlock_now=True, network_block=True),
	Mode.POWER: dict(level=1, lock_now=True, unlock_now=True, power_off=True),
	Mode.MANUAL: dict(level=1, lock_now=True, unlock_now=True, manual=True, confirmation_window_s=900),
	Mode.PAUSE: dict(level=3, lock_now=True, unlock_now=True, grant_minutes=True, daily_allowance=True, usage_read=True),
	Mode.ZERO_ALLOWANCE: dict(level=2, lock_emulated=True, daily_allowance=True, request_queue=True),
}


@dataclass
class Call:
	method: str
	kind: OverrideKind
	device_id: str
	override_id: str


class FakeEnforcer(BaseEnforcer):
	"""A configurable enforcer that keeps its own device state.

	``noop`` mimics a vendor that returns 200 and changes nothing.
	``flaky`` raises on apply. ``health`` is what the controller will trust.
	"""

	def __init__(
		self,
		name: str,
		mode: Mode = Mode.NETWORK,
		*,
		noop: bool = False,
		flaky: bool = False,
		health: HealthStatus = HealthStatus.HEALTHY,
		in_use: bool = False,
		readable: bool = True,
		confirmation_window_s: int | None = None,
	) -> None:
		caps = dict(CAPS[mode])
		if confirmation_window_s is not None:
			caps["confirmation_window_s"] = confirmation_window_s
		super().__init__(name, Capabilities(enforcer=name, **caps))
		self.mode = mode
		self.noop = noop
		self.flaky = flaky
		self.health_status = health
		self.in_use = in_use
		self.readable = readable
		self.locked: dict[str, bool] = {}
		self.calls: list[Call] = []
		self.bonus: list[int] = []
		self.allowance: list[int] = []

	async def apply(self, override: Override, device: DeviceRef) -> EnforcerResult:
		self.calls.append(Call("apply", override.kind, device.device_id, override.id))
		if self.flaky:
			raise RuntimeError("vendor said no")
		if override.kind == OverrideKind.GRANT:
			self.bonus.append(override.minutes or 0)
			return self.result(ResultStatus.APPLIED, device, Mode.BONUS, "bonus sent")
		if override.kind == OverrideKind.ALLOWANCE_TODAY:
			self.allowance.append(override.minutes or 0)
			return self.result(ResultStatus.APPLIED, device, Mode.ALLOWANCE, "allowance sent")
		if not self.noop and self.mode != Mode.MANUAL:
			self.locked[device.device_id] = True
		restore = {"allowance": 120} if self.mode == Mode.ZERO_ALLOWANCE else None
		return self.result(ResultStatus.APPLIED, device, self.mode, "sent", restore=restore)

	async def revert(self, override: Override, device: DeviceRef) -> EnforcerResult:
		self.calls.append(Call("revert", override.kind, device.device_id, override.id))
		if self.flaky:
			raise RuntimeError("vendor said no")
		if not self.noop:
			self.locked[device.device_id] = False
		return self.result(ResultStatus.APPLIED, device, self.mode, "released")

	async def read_state(self, device: DeviceRef) -> EnforcedState:
		if not self.readable:
			return EnforcedState(device.device_id, locked=None, detail="cannot read")
		return EnforcedState(device.device_id, locked=self.locked.get(device.device_id, False), in_use=self.in_use)

	async def health(self) -> Health:
		return Health(self.health_status, "" if self.health_status == HealthStatus.HEALTHY else "session lost")

	def mark_done(self, device_id: str) -> None:
		"""For the manual flavour: the parent pressed done."""
		self.locked[device_id] = True


@pytest.fixture
def clock() -> Clock:
	return Clock()


@pytest.fixture
def household() -> Household:
	return Household(time_zone="Europe/London", guardians=["andy"], id="11111111-1111-4111-8111-111111111111")


@pytest.fixture
def alice() -> Child:
	return Child(display_name="Alice", age_band=AgeBand.SEVEN_TO_12, id="22222222-2222-4222-8222-222222222222")


@pytest.fixture
def policy(alice: Child) -> Policy:
	return Policy(
		child_id=alice.id,
		allowance_minutes=[60, 60, 90, 60, 120, 180, 180],
		bedtime=[TimeWindow("20:00", "07:00")] * 5 + [TimeWindow("21:00", "08:00")] * 2,
		grant_cap_minutes_per_day=60,
	)


@pytest.fixture
def controller(clock: Clock, household: Household, alice: Child, policy: Policy) -> Controller:
	controller = Controller(household, clock)
	controller.add_child(alice, policy)
	return controller


def add_device(controller: Controller, name: str, child_id: str, *enforcers: FakeEnforcer, power_opt_in: bool = False) -> Device:
	device = Device(
		display_name=name,
		platform=Platform.PLAYSTATION,
		child_id=child_id,
		enforcer_ids=[enforcer.name for enforcer in enforcers],
		power_off_allowed=power_opt_in,
	)
	for enforcer in enforcers:
		if enforcer.name not in controller.enforcers:
			controller.add_enforcer(enforcer)
	controller.add_device(device)
	return device


@pytest.fixture
def events(controller: Controller) -> list:
	seen: list = []
	controller.listen(seen.append)
	return seen


def today() -> date:
	return START.date()
