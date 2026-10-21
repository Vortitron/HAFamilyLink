"""Google Family Link, Android. Level 3 through noiwid/HAFamilyLink, when built.

Research notes (docs/PLATFORMS.md, October 2026):

- Google offers no official API. noiwid/HAFamilyLink drives the private web
  API with cookies captured by a browser session kept in a companion add-on.
  Google returns HTTP 200 for a no-op, so every write needs a read-back.
- Family Link can lock a device now, add bonus minutes, set a daily limit
  per device, set downtime windows and per-app limits, and reports usage
  per app. It cannot surface child requests to us. Limits are per device,
  not per child, so this enforcer declares ``lossy_per_device``.
- Google's terms forbid automated access. The README must say so and the
  parent must opt in knowingly. Account suspension is the realistic risk.
- Family Link exposes location. Kerb never reads it (SPEC.md section 8).

TODO, in order:

1. Bind to noiwid's entities when his integration is present: a lock switch
   per device, bonus-time buttons, usage sensors. Entity ids changed between
   his v1 and v2, so discover by device registry and entity translation key,
   not by hard-coded id. Spec decision 6 proposes entities first, not a
   client import.
2. ``apply`` for a lock turns his lock switch on and returns ``applied``.
   ``read_state`` reads the same switch back. Health follows his coordinator:
   ``unavailable`` means our ``unknown``.
3. ``apply`` for a grant presses his bonus button for the nearest supported
   step, records the remainder in our ledger only, and says so in ``detail``.
4. ``usage`` maps his per-app sensors to usage samples with ``android:<package>``
   app keys.
5. Tests first against a fake of his entity set, including the no-op 200 case.
"""

from __future__ import annotations

from ..models import Capabilities
from ._stub import StubEnforcer


class FamilyLinkEnforcer(StubEnforcer):
	reason = "Family Link enforcer not implemented; needs noiwid/HAFamilyLink entities (phase 2)"

	def __init__(self) -> None:
		super().__init__(
			"family_link",
			Capabilities(
				enforcer="family_link",
				level=3,
				lock_now=True,
				unlock_now=True,
				grant_minutes=True,
				daily_allowance=True,
				allowed_windows=True,
				app_block=True,
				app_limit=True,
				usage_read=True,
				usage_per_app=True,
				request_queue=False,
				lossy_per_device=True,
				poll_interval_s=300,
				confirmation_window_s=300,
				notes="Private Google API through noiwid/HAFamilyLink. Against Google's terms. Returns 200 on no-op, so read back everything.",
			),
		)
