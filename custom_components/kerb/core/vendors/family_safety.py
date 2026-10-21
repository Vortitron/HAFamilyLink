"""Microsoft Family Safety, Windows and Xbox. Level 2 with parts of 3 through noiwid/HAFamilySafety.

Research notes (docs/PLATFORMS.md, October 2026):

- No official API. noiwid/HAFamilySafety and pantherale0/pyfamilysafety use
  the web API with cookies and a CSRF token. The session needs re-auth about
  daily and the stored session material is sensitive; HA backups contain it.
- Microsoft removed the instant lock endpoint and kept returning 201 on the
  old call. A lock is emulated by setting today's schedule to zero minutes,
  so this enforcer declares ``lock_emulated`` and must attach a ``restore``
  snapshot of the schedule it overwrote.
- Allowance and 30 minute windows are supported per device and per app.
  Child requests for more time appear in the API, so ``request_queue`` is
  true. Grants are only possible as an approval of a pending request.
- Usage is reported per device and per app, with ``msstore:`` and ``xbox:``
  app keys.

TODO, in order:

1. Discover noiwid's entities per device (schedule numbers, request sensors,
   usage sensors). Same discovery caveat as Family Link.
2. ``apply`` for a lock snapshots the current schedule into ``restore``, writes
   zero, returns ``applied`` with ``mode: zero_allowance``. ``revert`` writes
   the snapshot back. ``read_state`` reads the schedule: zero means locked.
3. ``pending_requests`` maps his request sensor attributes to Request
   objects; ``respond`` calls his approve or deny service.
4. Health: his coordinator ``unavailable`` or an auth error means ``unknown``
   within one poll and no unattended retry of the interactive login.
5. Tests first, including the removed-endpoint 201 case and the daily re-auth.
"""

from __future__ import annotations

from ..models import Capabilities
from ._stub import StubEnforcer


class FamilySafetyEnforcer(StubEnforcer):
	reason = "Family Safety enforcer not implemented; needs noiwid/HAFamilySafety entities (phase 2)"

	def __init__(self) -> None:
		super().__init__(
			"family_safety",
			Capabilities(
				enforcer="family_safety",
				level=2,
				lock_now=False,
				lock_emulated=True,
				unlock_now=True,
				grant_minutes=False,
				daily_allowance=True,
				allowed_windows=True,
				app_block=True,
				app_limit=True,
				usage_read=True,
				usage_per_app=True,
				request_queue=True,
				lossy_per_device=True,
				poll_interval_s=300,
				confirmation_window_s=600,
				notes="Web API with cookies through noiwid/HAFamilySafety. Lock is emulated by zeroing today's schedule. Daily re-auth.",
			),
		)
