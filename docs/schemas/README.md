# Kerb schemas 0.1

JSON Schema, draft 2020-12, one file per object in SPEC.md section 3. Published ids live under https://kerb.dev/schema/0.1/ (placeholder domain until the name is settled).

Rules shared by every schema:

- Unknown properties are allowed and preserved. Extensions use an `x_` prefix.
- Identifiers are UUIDs minted locally. Vendor identifiers never appear in these objects.
- Times are RFC 3339 with explicit offsets. Weekday arrays have seven entries, index 0 is Monday.
- Minor versions only add optional fields.

| File | Object |
|---|---|
| household.json | Household |
| child.json | Child |
| device.json | Device |
| policy.json | Policy |
| override.json | Override |
| ledger_entry.json | Ledger entry |
| usage_sample.json | Usage sample |
| request.json | Request |
| capabilities.json | Enforcer capabilities |
| event.json | Event |
| rating_claim.json | Rating claim |
| tag.json | Tag (community) |
| tag_vote.json | Tag vote (community) |
| profile.json | Profile (community) |

The example in examples/override_lock.json validates against override.json.
