"""The vendor stubs are honest: they declare, they do not pretend."""

import pytest

from kerb_core.models import DeviceRef, HealthStatus, Mode, OverrideKind, OverrideStatus, ResultStatus
from kerb_core.vendors import FamilyLinkEnforcer, FamilySafetyEnforcer, NintendoEnforcer, PlayStationEnforcer

from .conftest import add_device

STUBS = [FamilyLinkEnforcer, FamilySafetyEnforcer, NintendoEnforcer, PlayStationEnforcer]


@pytest.mark.parametrize("cls", STUBS)
async def test_stub_never_claims_health_or_success(cls) -> None:
	stub = cls()
	device = DeviceRef("d", "Phone")
	assert (await stub.health()).status == HealthStatus.UNKNOWN
	assert (await stub.read_state(device)).locked is None
	from kerb_core.models import Override

	from .conftest import START

	override = Override(child_id="c", kind=OverrideKind.LOCK, source="guardian", starts_at=START, expires_at=START)
	assert (await stub.apply(override, device)).status == ResultStatus.FAILED
	assert (await stub.revert(override, device)).status == ResultStatus.FAILED


def test_declared_capabilities_match_the_platform_matrix() -> None:
	assert FamilyLinkEnforcer().capabilities.lock_mode == Mode.PAUSE
	assert FamilyLinkEnforcer().capabilities.lossy_per_device
	assert FamilySafetyEnforcer().capabilities.lock_mode == Mode.ZERO_ALLOWANCE
	assert FamilySafetyEnforcer().capabilities.request_queue
	assert not FamilySafetyEnforcer().capabilities.grant_minutes
	assert NintendoEnforcer().capabilities.level == 3
	assert PlayStationEnforcer().capabilities.lock_mode is None
	assert PlayStationEnforcer().capabilities.level == 0


async def test_controller_shows_unknown_with_a_stub_bound(controller, alice) -> None:
	add_device(controller, "Phone", alice.id, FamilyLinkEnforcer())
	await controller.tick()
	state = controller.child_state(alice.id)
	assert str(state.status) == "unknown"
	override = await controller.lock(alice.id, minutes=10)
	assert override.status == OverrideStatus.FAILED
	assert override.results[0].status == ResultStatus.UNKNOWN
