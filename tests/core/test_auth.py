"""Guardian check and PIN."""

import pytest

from kerb_core.auth import BadPin, NotAGuardian, authorise, hash_pin, verify_pin
from kerb_core.models import Household


def test_pin_hash_round_trip() -> None:
	stored = hash_pin("1234")
	assert stored.startswith("sha256$")
	assert verify_pin(stored, "1234")
	assert not verify_pin(stored, "0000")
	assert not verify_pin(stored, None)
	assert verify_pin(None, None)
	assert not verify_pin("garbage", "1234")


def test_authorise_refuses_strangers_and_no_user() -> None:
	household = Household(time_zone="Europe/London", guardians=["andy"])
	authorise(household, "andy", None)
	with pytest.raises(NotAGuardian):
		authorise(household, "alice", None)
	with pytest.raises(NotAGuardian):
		authorise(household, None, None)
	authorise(household, None, None, trusted=True)


def test_authorise_checks_pin_even_for_guardians() -> None:
	household = Household(time_zone="Europe/London", guardians=["andy"], pin_hash=hash_pin("4321"))
	with pytest.raises(BadPin):
		authorise(household, "andy", None)
	with pytest.raises(BadPin):
		authorise(household, "andy", "1111")
	authorise(household, "andy", "4321")
	with pytest.raises(BadPin):
		authorise(household, None, None, trusted=True)
