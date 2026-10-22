"""Vendor enforcer stubs for phase 2.

None of these talks to a vendor yet. Each declares the capabilities the
research in docs/PLATFORMS.md supports, reports health ``unknown`` so the
controller never trusts it, and fails every write honestly. The docstrings
carry the research notes and TODOs so the next person starts from facts.
"""

from .family_link import FamilyLinkEnforcer
from .family_safety import FamilySafetyEnforcer
from .nintendo import NintendoEnforcer
from .playstation import PlayStationEnforcer

__all__ = ["FamilyLinkEnforcer", "FamilySafetyEnforcer", "NintendoEnforcer", "PlayStationEnforcer"]
