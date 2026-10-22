"""Shared shape for a vendor enforcer that is not implemented yet."""

from __future__ import annotations

from ..enforcer import BaseEnforcer
from ..models import Capabilities, DeviceRef, EnforcedState, EnforcerResult, Health, HealthStatus, Override, ResultStatus


class StubEnforcer(BaseEnforcer):
	"""Declares capabilities, trusts nothing, fails every write with the reason."""

	reason = "not implemented"

	def __init__(self, name: str, capabilities: Capabilities) -> None:
		super().__init__(name, capabilities)

	async def apply(self, override: Override, device: DeviceRef) -> EnforcerResult:
		return self.result(ResultStatus.FAILED, device, self.capabilities.lock_mode, f"{self.name}: {self.reason}")

	async def revert(self, override: Override, device: DeviceRef) -> EnforcerResult:
		return self.result(ResultStatus.FAILED, device, self.capabilities.lock_mode, f"{self.name}: {self.reason}")

	async def read_state(self, device: DeviceRef) -> EnforcedState:
		return EnforcedState(device.device_id, locked=None, detail=f"{self.name}: {self.reason}")

	async def health(self) -> Health:
		# Unknown, never healthy: the controller must not trust a stub.
		return Health(HealthStatus.UNKNOWN, self.reason)
