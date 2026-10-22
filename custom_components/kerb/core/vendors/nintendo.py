"""Nintendo Switch. Level 3 through the Home Assistant core nintendo_parental_controls integration.

Research notes (docs/PLATFORMS.md, October 2026):

- Nintendo has no official API but the mobile app's API is stable and the
  pynintendoparental library covers it. Home Assistant core ships the
  nintendo_parental_controls integration on top of it, with the parent's
  session held by core, not by us. This is the cleanest Level 3 proof.
- The core integration exposes, per Switch, today's play time, a daily limit
  that can be set, a bedtime alarm and a software allow list. Check the
  entity list in your install rather than trusting ids written here.
- A lock is a daily limit of zero or the "suspend software" switch where
  present. Grants raise today's limit. Usage per title gives
  ``nintendo:<title id>`` app keys.

TODO, in order:

1. Bind to the core integration's entities by device registry and
   translation key: play time sensor, daily limit number, bedtime time,
   suspend switch if present.
2. ``apply`` for a lock turns suspend on or sets today's limit to zero with a
   ``restore`` snapshot, and reads it back. ``apply`` for a grant adds minutes
   to today's limit. ``set_policy`` writes the weekly limits.
3. Health follows the core integration's availability.
4. Tests against a fake of the core entity set. This enforcer is the
   conformance Level 3 reference, so write the conformance suite against it.
"""

from __future__ import annotations

from ..models import Capabilities
from ._stub import StubEnforcer


class NintendoEnforcer(StubEnforcer):
	reason = "Nintendo enforcer not implemented; binds to HA core nintendo_parental_controls entities (phase 2)"

	def __init__(self) -> None:
		super().__init__(
			"nintendo",
			Capabilities(
				enforcer="nintendo",
				level=3,
				lock_now=True,
				unlock_now=True,
				grant_minutes=True,
				daily_allowance=True,
				allowed_windows=False,
				app_block=True,
				usage_read=True,
				usage_per_app=True,
				poll_interval_s=300,
				confirmation_window_s=300,
				notes="Over the HA core nintendo_parental_controls integration. Bedtime is an alarm, not a window.",
			),
		)
