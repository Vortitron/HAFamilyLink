"""The enforcer interface (SPEC.md section 5).

An enforcer declares what it can do, does it, then proves it did it. One
enforcer instance may govern several devices; ``apply`` and ``revert`` are
called once per (enforcer, device) pair and answer for that device alone.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol, runtime_checkable

from .models import (
	Capabilities,
	DeviceRef,
	EnforcedState,
	EnforcerResult,
	Health,
	HealthStatus,
	Mode,
	Override,
	Policy,
	Request,
	ResultStatus,
	UsageSample,
)


@runtime_checkable
class Enforcer(Protocol):
	"""What the controller needs from any enforcer."""

	capabilities: Capabilities

	@property
	def name(self) -> str: ...

	async def discover(self) -> list[DeviceRef]: ...

	async def apply(self, override: Override, device: DeviceRef) -> EnforcerResult: ...

	async def revert(self, override: Override, device: DeviceRef) -> EnforcerResult: ...

	async def read_state(self, device: DeviceRef) -> EnforcedState: ...

	async def usage(self, device: DeviceRef, day: date) -> list[UsageSample]: ...

	async def set_policy(self, device: DeviceRef, policy: Policy) -> EnforcerResult: ...

	async def pending_requests(self) -> list[Request]: ...

	async def respond(self, request_id: str, approve: bool, minutes: int) -> EnforcerResult: ...

	async def health(self) -> Health: ...


class BaseEnforcer:
	"""Sensible defaults so a Level 1 enforcer only writes apply, revert and read_state."""

	capabilities: Capabilities

	def __init__(self, name: str, capabilities: Capabilities) -> None:
		self._name = name
		self.capabilities = capabilities

	@property
	def name(self) -> str:
		return self._name

	def result(
		self,
		status: ResultStatus,
		device: DeviceRef | None = None,
		mode: Mode | None = None,
		detail: str = "",
		confirmed_at: datetime | None = None,
		restore: dict | None = None,
	) -> EnforcerResult:
		return EnforcerResult(
			enforcer=self.name,
			status=status,
			device_id=None if device is None else device.device_id,
			mode=mode,
			detail=detail,
			confirmed_at=confirmed_at,
			restore=restore,
		)

	def unsupported(self, device: DeviceRef | None, what: str) -> EnforcerResult:
		return self.result(ResultStatus.FAILED, device, detail=f"{self.name} cannot {what}")

	async def discover(self) -> list[DeviceRef]:
		return []

	async def apply(self, override: Override, device: DeviceRef) -> EnforcerResult:
		return self.unsupported(device, f"apply {override.kind}")

	async def revert(self, override: Override, device: DeviceRef) -> EnforcerResult:
		return self.unsupported(device, f"revert {override.kind}")

	async def read_state(self, device: DeviceRef) -> EnforcedState:
		return EnforcedState(device_id=device.device_id, locked=None, detail="not readable")

	async def usage(self, device: DeviceRef, day: date) -> list[UsageSample]:
		return []

	async def set_policy(self, device: DeviceRef, policy: Policy) -> EnforcerResult:
		return self.unsupported(device, "set policy")

	async def pending_requests(self) -> list[Request]:
		return []

	async def respond(self, request_id: str, approve: bool, minutes: int) -> EnforcerResult:
		return self.unsupported(None, "respond to requests")

	async def health(self) -> Health:
		return Health(HealthStatus.HEALTHY)
