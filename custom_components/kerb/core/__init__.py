"""Kerb core: the household screen-time domain, with no Home Assistant imports.

Importable as ``custom_components.kerb.core`` inside Home Assistant and as
``kerb_core`` from a checkout (see kerb_core/__init__.py).

The package implements SPEC.md sections 3 to 5: the data model, policy
evaluation, override stacking, the ledger, the enforcer interface and the
controller that composes them. Everything here is pure Python so it can be
tested without a running host and reused by a controller other than Home
Assistant.
"""

from .models import (
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
