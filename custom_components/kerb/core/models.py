"""Data model for Kerb 0.1 (SPEC.md section 3).

Every class here mirrors one JSON Schema in docs/schemas. Field names match
the schema property names so ``to_dict`` output validates directly. Vendor
identifiers never appear in these objects; they live in the enforcer's own
store.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
import uuid

WEEKDAYS = 7
MINUTES_PER_DAY = 1440


def new_id() -> str:
	"""Mint a local UUID."""
	return str(uuid.uuid4())


def _iso(value: datetime | None) -> str | None:
	return None if value is None else value.isoformat()


def _parse_dt(value: str | None) -> datetime | None:
	return None if value is None else datetime.fromisoformat(value)


def _strip_none(data: dict[str, Any]) -> dict[str, Any]:
	return {key: value for key, value in data.items() if value is not None}


class AgeBand(StrEnum):
	UNDER_7 = "under_7"
	SEVEN_TO_12 = "7_to_12"
	THIRTEEN_TO_15 = "13_to_15"
	SIXTEEN_PLUS = "16_plus"


class Platform(StrEnum):
	ANDROID = "android"
	WINDOWS = "windows"
	XBOX = "xbox"
	PLAYSTATION = "playstation"
	SWITCH = "switch"
	IOS = "ios"
	TV = "tv"
	PC = "pc"
	OTHER = "other"


class OverrideKind(StrEnum):
	LOCK = "lock"
	GRANT = "grant"
	UNLOCK = "unlock"
	ALLOWANCE_TODAY = "allowance_today"


class OverrideStatus(StrEnum):
	REQUESTED = "requested"
	APPLIED = "applied"
	PARTIAL = "partial"
	CONFIRMED = "confirmed"
	FAILED = "failed"
	EXPIRED = "expired"
	CANCELLED = "cancelled"


class ResultStatus(StrEnum):
	REQUESTED = "requested"
	APPLIED = "applied"
	CONFIRMED = "confirmed"
	FAILED = "failed"
	UNKNOWN = "unknown"


class Mode(StrEnum):
	"""How an enforcer actually did it."""

	PAUSE = "pause"
	ZERO_ALLOWANCE = "zero_allowance"
	NETWORK = "network"
	POWER = "power"
	MANUAL = "manual"
	BONUS = "bonus"
	ALLOWANCE = "allowance"


# Strongest first. Mode ``auto`` picks the first mode an enforcer offers.
MODE_STRENGTH: tuple[Mode, ...] = (
	Mode.PAUSE,
	Mode.ZERO_ALLOWANCE,
	Mode.NETWORK,
	Mode.POWER,
	Mode.MANUAL,
)


class Effect(StrEnum):
	"""Per-app or per-tag policy effect."""

	ALLOW_ALWAYS = "allow_always"
	ALLOW = "allow"
	COUNT_HALF = "count_half"
	COUNT_DOUBLE = "count_double"
	REQUIRE_APPROVAL = "require_approval"
	BLOCK = "block"


EFFECT_RATE: dict[Effect, float] = {
	Effect.ALLOW_ALWAYS: 0.0,
	Effect.ALLOW: 1.0,
	Effect.COUNT_HALF: 0.5,
	Effect.COUNT_DOUBLE: 2.0,
	Effect.REQUIRE_APPROVAL: 1.0,
	Effect.BLOCK: 1.0,
}


class HealthStatus(StrEnum):
	HEALTHY = "healthy"
	DEGRADED = "degraded"
	UNKNOWN = "unknown"
	REVOKED = "revoked"


class ChildStatus(StrEnum):
	"""The per-child status sensor."""

	FREE = "free"
	LOCKED = "locked"
	EXHAUSTED = "exhausted"
	BEDTIME = "bedtime"
	UNKNOWN = "unknown"


class EnforcementStatus(StrEnum):
	"""The per-child enforcement sensor."""

	CONFIRMED = "confirmed"
	PENDING = "pending"
	PARTIAL = "partial"
	DEGRADED = "degraded"
	UNKNOWN = "unknown"


class Confidence(StrEnum):
	CONFIRMED = "confirmed"
	ASSUMED = "assumed"
	STALE = "stale"


@dataclass(frozen=True)
class Health:
	status: HealthStatus
	reason: str = ""

	@property
	def trusted(self) -> bool:
		"""Whether read-backs from this enforcer can be believed."""
		return self.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)


@dataclass(frozen=True)
class Scope:
	type: str = "all"  # all | device | app | tag
	device_id: str | None = None
	app: str | None = None
	tag: str | None = None

	def covers_device(self, device_id: str) -> bool:
		if self.type == "all":
			return True
		if self.type == "device":
			return self.device_id == device_id
		# App and tag scopes are per-app rules; the device itself stays usable.
		return False

	def to_dict(self) -> dict[str, Any]:
		return _strip_none(asdict(self))

	@classmethod
	def from_dict(cls, data: dict[str, Any] | None) -> Scope:
		data = data or {}
		return cls(
			type=data.get("type", "all"),
			device_id=data.get("device_id"),
			app=data.get("app"),
			tag=data.get("tag"),
		)


@dataclass
class EnforcerResult:
	"""One enforcer's answer to one override."""

	enforcer: str
	status: ResultStatus
	device_id: str | None = None
	mode: Mode | None = None
	detail: str = ""
	confirmed_at: datetime | None = None
	restore: dict[str, Any] | None = None

	def to_dict(self) -> dict[str, Any]:
		return _strip_none(
			{
				"enforcer": self.enforcer,
				"device_id": self.device_id,
				"status": str(self.status),
				"mode": None if self.mode is None else str(self.mode),
				"detail": self.detail or None,
				"confirmed_at": _iso(self.confirmed_at),
				"restore": self.restore,
			}
		)

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> EnforcerResult:
		return cls(
			enforcer=data["enforcer"],
			status=ResultStatus(data["status"]),
			device_id=data.get("device_id"),
			mode=Mode(data["mode"]) if data.get("mode") else None,
			detail=data.get("detail", ""),
			confirmed_at=_parse_dt(data.get("confirmed_at")),
			restore=data.get("restore"),
		)


@dataclass
class Override:
	"""One parental decision with a lifetime (SPEC.md 3.5)."""

	child_id: str
	kind: OverrideKind
	source: str
	starts_at: datetime
	expires_at: datetime
	scope: Scope = field(default_factory=Scope)
	minutes: int | None = None
	reason: str = ""
	status: OverrideStatus = OverrideStatus.REQUESTED
	results: list[EnforcerResult] = field(default_factory=list)
	restore: dict[str, Any] = field(default_factory=dict)
	cancels: str | None = None
	id: str = field(default_factory=new_id)

	def active_at(self, now: datetime) -> bool:
		"""Whether the decision is in force at ``now``.

		A failed override still counts: the parent decided, enforcement did
		not happen, and the enforcement status says so. Only cancellation and
		expiry end a decision.
		"""
		if self.status in (OverrideStatus.CANCELLED, OverrideStatus.EXPIRED):
			return False
		return self.starts_at <= now < self.expires_at

	def to_dict(self) -> dict[str, Any]:
		data: dict[str, Any] = {
			"id": self.id,
			"child_id": self.child_id,
			"kind": str(self.kind),
			"scope": self.scope.to_dict(),
			"source": self.source,
			"starts_at": self.starts_at.isoformat(),
			"expires_at": self.expires_at.isoformat(),
			"status": str(self.status),
			"results": [result.to_dict() for result in self.results],
			"restore": self.restore,
		}
		if self.minutes is not None:
			data["minutes"] = self.minutes
		if self.reason:
			data["reason"] = self.reason
		if self.cancels is not None:
			data["cancels"] = self.cancels
		return data

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> Override:
		return cls(
			id=data["id"],
			child_id=data["child_id"],
			kind=OverrideKind(data["kind"]),
			scope=Scope.from_dict(data.get("scope")),
			source=data["source"],
			starts_at=datetime.fromisoformat(data["starts_at"]),
			expires_at=datetime.fromisoformat(data["expires_at"]),
			status=OverrideStatus(data.get("status", "requested")),
			minutes=data.get("minutes"),
			reason=data.get("reason", ""),
			results=[EnforcerResult.from_dict(item) for item in data.get("results", [])],
			restore=dict(data.get("restore") or {}),
			cancels=data.get("cancels"),
		)


@dataclass(frozen=True)
class TimeWindow:
	"""A local-time window at 30 minute granularity, ``HH:MM`` strings."""

	start: str
	end: str

	def contains(self, hhmm: str) -> bool:
		"""Whether the local time ``hhmm`` falls inside. Handles windows past midnight."""
		if self.start <= self.end:
			return self.start <= hhmm < self.end
		return hhmm >= self.start or hhmm < self.end

	def to_dict(self) -> dict[str, str]:
		return {"start": self.start, "end": self.end}


@dataclass(frozen=True)
class RatingClaim:
	"""An attributed age rating: a claim with provenance, never truth."""

	organisation: str
	value: str
	source: str
	retrieved_at: str
	region: str | None = None

	def to_dict(self) -> dict[str, Any]:
		return _strip_none(asdict(self))


@dataclass
class Policy:
	"""Standing rules for one child (SPEC.md 3.4)."""

	child_id: str
	allowance_minutes: list[int] = field(default_factory=lambda: [120] * WEEKDAYS)
	windows: list[list[TimeWindow]] = field(default_factory=lambda: [[] for _ in range(WEEKDAYS)])
	bedtime: list[TimeWindow | None] = field(default_factory=lambda: [None] * WEEKDAYS)
	rating_ceiling: RatingClaim | None = None
	app_rules: dict[str, Effect] = field(default_factory=dict)
	tag_rules: dict[str, Effect] = field(default_factory=dict)
	grant_cap_minutes_per_day: int | None = None
	id: str = field(default_factory=new_id)

	def __post_init__(self) -> None:
		if len(self.allowance_minutes) != WEEKDAYS:
			raise ValueError("allowance_minutes needs seven values, Monday first")
		if len(self.windows) != WEEKDAYS or len(self.bedtime) != WEEKDAYS:
			raise ValueError("windows and bedtime need seven entries, Monday first")
		for minutes in self.allowance_minutes:
			if not 0 <= minutes <= MINUTES_PER_DAY:
				raise ValueError("allowance must be between 0 and 1440 minutes")

	def to_dict(self) -> dict[str, Any]:
		data: dict[str, Any] = {
			"id": self.id,
			"child_id": self.child_id,
			"allowance_minutes": list(self.allowance_minutes),
			"windows": [[window.to_dict() for window in day] for day in self.windows],
			"bedtime": [None if window is None else window.to_dict() for window in self.bedtime],
			"app_rules": [{"app": app, "effect": str(effect)} for app, effect in self.app_rules.items()],
			"tag_rules": [{"tag": tag, "effect": str(effect)} for tag, effect in self.tag_rules.items()],
		}
		if self.rating_ceiling is not None:
			data["rating_ceiling"] = self.rating_ceiling.to_dict()
		if self.grant_cap_minutes_per_day is not None:
			data["grant_cap_minutes_per_day"] = self.grant_cap_minutes_per_day
		return data

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> Policy:
		rating = data.get("rating_ceiling")
		return cls(
			id=data.get("id") or new_id(),
			child_id=data["child_id"],
			allowance_minutes=list(data.get("allowance_minutes", [120] * WEEKDAYS)),
			windows=[
				[TimeWindow(item["start"], item["end"]) for item in day]
				for day in data.get("windows", [[] for _ in range(WEEKDAYS)])
			],
			bedtime=[
				None if item is None else TimeWindow(item["start"], item["end"])
				for item in data.get("bedtime", [None] * WEEKDAYS)
			],
			rating_ceiling=None if rating is None else RatingClaim(**rating),
			app_rules={item["app"]: Effect(item["effect"]) for item in data.get("app_rules", [])},
			tag_rules={item["tag"]: Effect(item["effect"]) for item in data.get("tag_rules", [])},
			grant_cap_minutes_per_day=data.get("grant_cap_minutes_per_day"),
		)


@dataclass
class LedgerEntry:
	"""Append-only line in a child's daily account (SPEC.md 3.6)."""

	child_id: str
	date: str  # ISO date, local
	kind: str  # allowance | grant | penalty | usage | lock
	minutes: float
	recorded_at: datetime
	rate: float = 1.0
	device_id: str | None = None
	app: str | None = None
	rule: str | None = None
	per_app_usage_available: bool | None = None
	override_id: str | None = None
	source: str | None = None
	reason: str | None = None
	id: str = field(default_factory=new_id)

	def to_dict(self) -> dict[str, Any]:
		data = asdict(self)
		data["recorded_at"] = self.recorded_at.isoformat()
		return _strip_none(data)

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> LedgerEntry:
		data = dict(data)
		data["recorded_at"] = datetime.fromisoformat(data["recorded_at"])
		return cls(**data)


@dataclass
class UsageSample:
	"""A fact about use, not a policy (SPEC.md 3.7)."""

	child_id: str
	device_id: str
	start: datetime
	end: datetime
	seconds: int
	enforcer: str
	observed_at: datetime
	app: str | None = None

	def to_dict(self) -> dict[str, Any]:
		return _strip_none(
			{
				"child_id": self.child_id,
				"device_id": self.device_id,
				"app": self.app,
				"start": self.start.isoformat(),
				"end": self.end.isoformat(),
				"seconds": self.seconds,
				"enforcer": self.enforcer,
				"observed_at": self.observed_at.isoformat(),
			}
		)


@dataclass
class Request:
	"""A child-initiated ask surfaced by a vendor (SPEC.md 3.8)."""

	child_id: str
	kind: str  # more_time | app_access
	created_at: datetime
	enforcer: str
	status: str = "pending"
	device_id: str | None = None
	minutes: int | None = None
	app: str | None = None
	decided_by: str | None = None
	id: str = field(default_factory=new_id)

	def to_dict(self) -> dict[str, Any]:
		data = asdict(self)
		data["created_at"] = self.created_at.isoformat()
		return _strip_none(data)


@dataclass(frozen=True)
class Capabilities:
	"""What an enforcer declares about itself (SPEC.md section 5)."""

	enforcer: str
	level: int
	poll_interval_s: int = 60
	confirmation_window_s: int = 120
	lock_now: bool = False
	lock_emulated: bool = False
	unlock_now: bool = False
	grant_minutes: bool = False
	daily_allowance: bool = False
	allowed_windows: bool = False
	app_block: bool = False
	app_limit: bool = False
	usage_read: bool = False
	usage_per_app: bool = False
	request_queue: bool = False
	network_block: bool = False
	power_off: bool = False
	lossy_per_device: bool = False
	manual: bool = False
	notes: str = ""

	@property
	def lock_mode(self) -> Mode | None:
		"""The mode this enforcer uses to stop a device, or None if it cannot."""
		if self.manual:
			return Mode.MANUAL
		if self.lock_now and not (self.network_block or self.power_off):
			return Mode.PAUSE
		if self.lock_emulated:
			return Mode.ZERO_ALLOWANCE
		if self.network_block:
			return Mode.NETWORK
		if self.power_off:
			return Mode.POWER
		if self.lock_now:
			return Mode.PAUSE
		return None

	def to_dict(self) -> dict[str, Any]:
		data = asdict(self)
		if not data["notes"]:
			del data["notes"]
		return data


@dataclass(frozen=True)
class DeviceRef:
	"""What an enforcer needs to know about a device."""

	device_id: str
	display_name: str = ""
	platform: Platform = Platform.OTHER
	power_off_allowed: bool = False


@dataclass(frozen=True)
class EnforcedState:
	"""What an enforcer read back for one device."""

	device_id: str
	locked: bool | None  # None means unknown
	in_use: bool | None = None
	detail: str = ""
	observed_at: datetime | None = None


@dataclass
class Event:
	type: str
	household_id: str
	at: datetime
	child_id: str | None = None
	payload: dict[str, Any] = field(default_factory=dict)

	def to_dict(self) -> dict[str, Any]:
		return _strip_none(
			{
				"type": self.type,
				"household_id": self.household_id,
				"child_id": self.child_id,
				"at": self.at.isoformat(),
				"payload": self.payload,
			}
		)


@dataclass
class Child:
	display_name: str
	age_band: AgeBand
	policy_id: str | None = None
	id: str = field(default_factory=new_id)

	def to_dict(self) -> dict[str, Any]:
		data = asdict(self)
		data["age_band"] = str(self.age_band)
		return _strip_none(data)


@dataclass
class Device:
	display_name: str
	platform: Platform
	child_id: str | None = None
	current_child_id: str | None = None
	enforcer_ids: list[str] = field(default_factory=list)
	network: dict[str, Any] = field(default_factory=dict)
	power_off_allowed: bool = False
	id: str = field(default_factory=new_id)

	def ref(self) -> DeviceRef:
		return DeviceRef(
			device_id=self.id,
			display_name=self.display_name,
			platform=self.platform,
			power_off_allowed=self.power_off_allowed,
		)

	def governs(self, child_id: str) -> bool:
		"""Whether this device currently belongs to ``child_id``."""
		return child_id in (self.child_id, self.current_child_id)

	def to_dict(self) -> dict[str, Any]:
		data = asdict(self)
		data["platform"] = str(self.platform)
		if not data["network"]:
			del data["network"]
		data["child_id"] = self.child_id
		if self.current_child_id is None:
			del data["current_child_id"]
		return data


@dataclass
class Household:
	time_zone: str
	guardians: list[str] = field(default_factory=list)
	pin_hash: str | None = None
	usage_retention_days: int = 31
	community_sharing: bool = False
	id: str = field(default_factory=new_id)

	def to_dict(self) -> dict[str, Any]:
		return asdict(self)
