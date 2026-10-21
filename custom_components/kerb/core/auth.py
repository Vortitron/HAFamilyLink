"""Guardian check and PIN (SPEC.md 6.6).

The PIN is stored as ``sha256$<salt>$<hex>``. It is a speed bump against a
child who found the dashboard, not a cryptographic boundary, so a plain
salted hash is enough. Never log the PIN.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

from .models import Household


class NotAGuardian(PermissionError):
	"""The caller is not in the household's guardian list."""


class BadPin(PermissionError):
	"""The PIN is missing or wrong."""


def hash_pin(pin: str, salt: str | None = None) -> str:
	salt = salt or secrets.token_hex(8)
	digest = hashlib.sha256(f"{salt}:{pin}".encode()).hexdigest()
	return f"sha256${salt}${digest}"


def verify_pin(pin_hash: str | None, pin: str | None) -> bool:
	"""True when no PIN is set, or when ``pin`` matches."""
	if not pin_hash:
		return True
	if pin is None:
		return False
	try:
		_algo, salt, _digest = pin_hash.split("$", 2)
	except ValueError:
		return False
	return hmac.compare_digest(hash_pin(pin, salt), pin_hash)


def authorise(household: Household, user_id: str | None, pin: str | None, trusted: bool = False, check_pin: bool = True) -> None:
	"""Raise unless the caller may lock, unlock or grant.

	``trusted`` is for automations and the host's own owner context. A call
	with no user and not trusted is refused. The PIN is checked whenever one is
	set, even for guardians, unless ``check_pin`` is False: the host turns it
	off for a caller who has just entered the PIN, and for confirmations that
	decide nothing (a parent saying the manual step is done).
	"""
	if not trusted:
		if user_id is None or user_id not in household.guardians:
			raise NotAGuardian("only a guardian may do that")
	if check_pin and not verify_pin(household.pin_hash, pin):
		raise BadPin("PIN missing or wrong")
