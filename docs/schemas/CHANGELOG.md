# Schema changelog

Kerb is at 0.1 and marked experimental. While the major version is 0 the schemas may change in any way between commits, and `$id` values are not yet stable: the kerb.dev domain is a placeholder and will change when the name is settled. From 1.0 on, `$id` values are fixed, minor versions only add optional fields, and every change is recorded here first.

## 0.1, unreleased

Changes since the first publication of the 0.1 schemas (commit 9e3d68a), newest first.

- override.json: `results[]` is now a `$ref` to enforcer_result.json. `scope.type` of `device`, `app` or `tag` requires the matching `device_id`, `app` or `tag`. `kind` of `grant` or `allowance_today` requires `minutes`.
- enforcer_result.json, device_ref.json, enforced_state.json, health.json added, so the enforcer interface in SPEC.md section 5 can be implemented from the documents alone.
- Every `date-time` field carries a pattern requiring an explicit offset.
- ledger_entry.json: `rate` accepts 0.0, the rate the controller records for `allow_always` use.
- policy.json: `app_rules[].daily_limit_minutes` and `tag_rules[].windows` removed until phase 3 implements them. They validated but the reference controller dropped them on save.
- tag_vote.json: `household_id` renamed `contributor_id` and defined as a rotating id separate from Household.id. `additionalProperties` is now false (`x_` still allowed). `evidence` is restricted to store and IGDB pages. `note` must not carry names.
- profile.json: `author_household_id` renamed `author_contributor_id`. `additionalProperties` is now false.
- usage_sample.json, policy.json: prose constraints on `seconds` and on windows recorded in descriptions.
- capabilities.json: `manual` flag added after the first publication, for the manual enforcer. `enforcer` and `level` described.
