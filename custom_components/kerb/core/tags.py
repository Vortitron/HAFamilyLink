"""Community tag consumption (SPEC.md section 7).

The HA side never talks to the community server directly in phase 1. It
reads a local dump in JSON Lines form, applies the visibility rules, then
lets a subscribed profile and local per-app overrides win over the crowd.
The dump format is the one the phase 4 server will publish nightly.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any

MAX_VISIBLE_TAGS = 10
CAUTION_MIN_CONTRIBUTORS = 3

# SPEC.md 7.1, the proposed v1 vocabulary with a polarity hint.
TAXONOMY: dict[str, str] = {
	"educational": "value",
	"creative": "value",
	"reading": "value",
	"maths": "value",
	"physical_activity": "value",
	"music": "value",
	"chat_with_strangers": "caution",
	"voice_chat": "neutral",
	"friends_only_multiplayer": "neutral",
	"local_coop": "neutral",
	"solo": "neutral",
	"in_app_purchases": "caution",
	"loot_boxes": "caution",
	"pay_to_win": "caution",
	"subscription": "neutral",
	"ads_heavy": "caution",
	"violence_mild": "caution",
	"violence_graphic": "caution",
	"horror": "caution",
	"gambling_mechanics": "caution",
	"user_generated_content": "caution",
	"short_sessions": "neutral",
	"no_stopping_point": "caution",
	"autoplay": "caution",
	"endless_feed": "caution",
	"offline_ok": "neutral",
}


@dataclass(frozen=True)
class TagScore:
	"""One line of the nightly dump: the crowd's view of one tag on one app."""

	app: str
	tag: str
	score: int
	contributors: int = 0
	evidence: bool = False

	@property
	def visible(self) -> bool:
		if self.tag not in TAXONOMY or self.score <= 0:
			return False
		if TAXONOMY[self.tag] == "caution":
			return self.evidence and self.contributors >= CAUTION_MIN_CONTRIBUTORS
		return True


@dataclass
class Profile:
	"""A named overlay another household published (SPEC.md 7.3)."""

	name: str
	tags: dict[str, set[str]] = field(default_factory=dict)  # app key -> tags
	allowance_minutes: list[int] | None = None

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> Profile:
		return cls(
			name=data["name"],
			tags={item["app"]: set(item["tags"]) for item in data.get("tags", [])},
			allowance_minutes=data.get("allowance_minutes"),
		)


class TagSource:
	"""Resolve the tags for an app key: local overrides, then profile, then crowd."""

	def __init__(self, scores: Iterable[TagScore] = ()) -> None:
		self._crowd: dict[str, list[TagScore]] = {}
		for score in scores:
			self._crowd.setdefault(score.app, []).append(score)
		self._profile: Profile | None = None
		self._local: dict[str, dict[str, bool]] = {}

	@classmethod
	def from_jsonl(cls, path: Path | str) -> TagSource:
		scores = []
		for line in Path(path).read_text(encoding="utf-8").splitlines():
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			data = json.loads(line)
			scores.append(
				TagScore(
					app=data["app"],
					tag=data["tag"],
					score=int(data.get("score", 0)),
					contributors=int(data.get("contributors", 0)),
					evidence=bool(data.get("evidence", False)),
				)
			)
		return cls(scores)

	def subscribe(self, profile: Profile | None) -> None:
		self._profile = profile

	def set_local(self, app: str, tag: str, present: bool) -> None:
		"""A household decision: 'Minecraft counts as educational in this house'."""
		if tag not in TAXONOMY:
			raise ValueError(f"unknown tag {tag}")
		self._local.setdefault(app, {})[tag] = present

	def crowd_tags(self, app: str) -> list[str]:
		visible = [score for score in self._crowd.get(app, []) if score.visible]
		visible.sort(key=lambda score: (-score.score, score.tag))
		return [score.tag for score in visible[:MAX_VISIBLE_TAGS]]

	def tags_for(self, app: str | None) -> set[str]:
		if app is None:
			return set()
		if self._profile is not None and app in self._profile.tags:
			tags = set(self._profile.tags[app])
		else:
			tags = set(self.crowd_tags(app))
		for tag, present in self._local.get(app, {}).items():
			if present:
				tags.add(tag)
			else:
				tags.discard(tag)
		return tags
