"""Kerb core, importable as ``kerb_core`` without Home Assistant.

The code lives in custom_components/kerb/core so that a HACS install, which
copies only that folder, carries it. This shim points the package path there
so ``import kerb_core.controller`` works from a checkout, and so the core can
later be published on PyPI under this name without changing any import.
"""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent.parent / "custom_components" / "kerb" / "core")]

from .models import (  # noqa: E402
	AgeBand,
	Capabilities,
	Child,
	Device,
	Effect,
	EnforcedState,
	EnforcerResult,
	Event,
	Health,
	HealthStatus,
	Household,
	LedgerEntry,
	Mode,
	Override,
	OverrideKind,
	OverrideStatus,
	Platform,
	Policy,
	Request,
	ResultStatus,
	Scope,
	UsageSample,
)

__all__ = [
	"AgeBand",
	"Capabilities",
	"Child",
	"Device",
	"Effect",
	"EnforcedState",
	"EnforcerResult",
	"Event",
	"Health",
	"HealthStatus",
	"Household",
	"LedgerEntry",
	"Mode",
	"Override",
	"OverrideKind",
	"OverrideStatus",
	"Platform",
	"Policy",
	"Request",
	"ResultStatus",
	"Scope",
	"UsageSample",
]

__version__ = "0.1.0"
