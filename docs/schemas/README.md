# Kerb schemas 0.1

JSON Schema, draft 2020-12, one file per object in SPEC.md section 3 and for the enforcer interface in section 5. Published ids live under https://kerb.dev/schema/0.1/ (placeholder domain until the name is settled; see CHANGELOG.md for what that means for stability).

The schemas are normative. Where the prose in SPEC.md lists a vocabulary, the enum in the schema is the one that counts.

Rules shared by every schema:

- Unknown properties are allowed and preserved. Extensions use an `x_` prefix. The two community objects (tag vote, profile) are the exception: they refuse unknown properties and accept `x_` only, because they leave the house.
- Identifiers are UUIDs minted locally. Vendor identifiers never appear in these objects.
- Times are RFC 3339 with an explicit offset. Every date-time field carries a pattern that requires `Z` or `+hh:mm`, so a naive timestamp fails validation even without a format checker.
- Weekday arrays have seven entries, index 0 is Monday (ISO weekday 1).
- Minor versions only add optional fields.

Rules JSON Schema cannot express, which a conformance suite tests instead (SPEC.md 4.1):

- `expires_at` is later than `starts_at` on every override.
- A usage sample's `seconds` does not exceed `end` minus `start`, and `start` is not later than `end`.
- A policy window's `start` is not equal to its `end`. A window may cross midnight.

| File | Object |
|---|---|
| household.json | Household |
| child.json | Child |
| device.json | Device |
| policy.json | Policy |
| override.json | Override |
| enforcer_result.json | One enforcer's result for one device, as held on an override |
| ledger_entry.json | Ledger entry |
| usage_sample.json | Usage sample |
| request.json | Request |
| capabilities.json | Enforcer capabilities |
| device_ref.json | Device reference handed to an enforcer |
| enforced_state.json | State an enforcer reads back |
| health.json | Enforcer health |
| event.json | Event |
| rating_claim.json | Rating claim |
| tag.json | Tag (community) |
| tag_vote.json | Tag vote (community) |
| profile.json | Profile (community) |

Examples live in examples/ and are named `<schema>_<label>.json`. tests/test_schemas.py checks every schema, the examples, the output of every core model, and a set of documents that must fail.
