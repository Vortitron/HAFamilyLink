"""The running account for one child for one day (SPEC.md 3.6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import LedgerEntry, Override


class GrantCapExceeded(Exception):
	"""The day's ad hoc grants would pass the policy cap."""


@dataclass
class DayLedger:
	child_id: str
	date: str
	entries: list[LedgerEntry] = field(default_factory=list)

	def _add(self, kind: str, minutes: float, recorded_at: datetime, **fields: Any) -> LedgerEntry:
		entry = LedgerEntry(child_id=self.child_id, date=self.date, kind=kind, minutes=minutes, recorded_at=recorded_at, **fields)
		self.entries.append(entry)
		return entry

	def add_allowance(self, minutes: int, recorded_at: datetime, source: str, override_id: str | None = None) -> LedgerEntry:
		"""Set the day's base minutes. The newest allowance entry wins."""
		return self._add("allowance", minutes, recorded_at, source=source, override_id=override_id, rule="allowance")

	def add_grant(
		self,
		minutes: int,
		recorded_at: datetime,
		source: str,
		reason: str = "",
		override_id: str | None = None,
		cap: int | None = None,
	) -> LedgerEntry:
		if minutes <= 0:
			raise ValueError("a grant must add at least one minute")
		if cap is not None and self.granted + minutes > cap:
			raise GrantCapExceeded(f"{self.granted + minutes} minutes would pass the daily grant cap of {cap}")
		return self._add("grant", minutes, recorded_at, source=source, reason=reason or None, override_id=override_id)

	def add_penalty(
		self, minutes: int, recorded_at: datetime, source: str, reason: str = "", override_id: str | None = None
	) -> LedgerEntry:
		if minutes <= 0:
			raise ValueError("a penalty must remove at least one minute")
		return self._add("penalty", minutes, recorded_at, source=source, reason=reason or None, override_id=override_id)

	def charge_usage(
		self,
		minutes: float,
		recorded_at: datetime,
		rate: float = 1.0,
		device_id: str | None = None,
		app: str | None = None,
		rule: str = "default",
		per_app_usage_available: bool = False,
		source: str | None = None,
	) -> LedgerEntry | None:
		"""Record raw minutes at a rate. The weighted cost is minutes times rate."""
		if minutes <= 0:
			return None
		return self._add(
			"usage",
			minutes,
			recorded_at,
			rate=rate,
			device_id=device_id,
			app=app,
			rule=rule,
			per_app_usage_available=per_app_usage_available,
			source=source,
		)

	def add_lock(self, override: Override, recorded_at: datetime) -> LedgerEntry:
		return self._add(
			"lock",
			0,
			recorded_at,
			override_id=override.id,
			source=override.source,
			reason=override.reason or None,
			rule=f"scope:{override.scope.type}",
		)

	def _of(self, kind: str) -> list[LedgerEntry]:
		return [entry for entry in self.entries if entry.kind == kind]

	@property
	def allowance(self) -> int:
		entries = self._of("allowance")
		return int(entries[-1].minutes) if entries else 0

	@property
	def granted(self) -> int:
		return int(sum(entry.minutes for entry in self._of("grant")))

	@property
	def penalised(self) -> int:
		return int(sum(entry.minutes for entry in self._of("penalty")))

	@property
	def used_raw(self) -> float:
		return sum(entry.minutes for entry in self._of("usage"))

	@property
	def used_weighted(self) -> float:
		return sum(entry.minutes * entry.rate for entry in self._of("usage"))

	@property
	def budget(self) -> int:
		return self.allowance + self.granted - self.penalised

	@property
	def remaining(self) -> int:
		"""Whole minutes left today, never negative."""
		return max(0, int(self.budget - self.used_weighted))

	@property
	def devices_without_per_app_usage(self) -> list[str]:
		found = {entry.device_id for entry in self._of("usage") if entry.device_id and entry.per_app_usage_available is False}
		return sorted(found)

	def to_dict(self) -> dict[str, Any]:
		return {"child_id": self.child_id, "date": self.date, "entries": [entry.to_dict() for entry in self.entries]}

	@classmethod
	def from_dict(cls, data: dict[str, Any]) -> DayLedger:
		return cls(
			child_id=data["child_id"],
			date=data["date"],
			entries=[LedgerEntry.from_dict(item) for item in data.get("entries", [])],
		)
