"""Sony PlayStation. Level 0 through PSN, Level 1 only through network or power.

Research notes (docs/PLATFORMS.md, October 2026):

- No parental-control API of any kind. The PlayStation Family app is the only
  surface, and reverse engineering it (mitmproxy against the app) carries a
  real account-ban risk. SPEC.md decision 11 asks Andy whether to fund that
  spike; the default answer is no.
- PSNAWP can read what a child is playing (now playing, trophies) with a
  parent's npsso token. That is a Level 0 observer, nothing more. ps5-mqtt
  can put a PS5 into rest mode and reports activity, which is also Level 0
  plus a soft power-off that the child can undo with the controller.
- The honest Phase 1 answer is the manual enforcer: the parent gets a
  notification telling them to lock the console in the Family app and
  presses done. The network enforcer stops online play immediately. A smart
  plug stops everything, opt-in, with the corruption caveat.

TODO, only if the research changes:

1. An observer over PSNAWP or ps5-mqtt now-playing, charging minutes with
   ``psn:`` app keys. This is the only safe piece and belongs in phase 2.
2. Nothing else until Sony publishes an API or the spike is funded.
"""

from __future__ import annotations

from ..models import Capabilities
from ._stub import StubEnforcer


class PlayStationEnforcer(StubEnforcer):
	reason = "PlayStation has no parental-control API; use the manual, network or power enforcer"

	def __init__(self) -> None:
		super().__init__(
			"playstation",
			Capabilities(
				enforcer="playstation",
				level=0,
				usage_read=True,
				usage_per_app=True,
				poll_interval_s=300,
				confirmation_window_s=0,
				notes="Observer only, via PSNAWP or ps5-mqtt now-playing. No lock, no allowance, no grants.",
			),
		)
