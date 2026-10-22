# Kerb

Household screen time for Home Assistant, built on a small open standard.

Kerb is built backwards from two sentences a parent says out loud.

"No screens for an hour."

"Twenty minutes for emptying the dishwasher."

Android, PlayStation, Xbox and Windows each come with their own parental-controls app. None of them can be driven by anything else. Kerb puts one model of what you want on top of all of them, enforces it through whatever you already have in Home Assistant, and tells you honestly when something did not land.

## What works today (phase 1)

- One lock switch per child. On means no screens until the end of the day, or for a duration you give. Off releases every device.
- Grant buttons and a `kerb.grant` service. Chores, good behaviour or a chore integration add minutes to today's remaining time, with a reason the child can read.
- A daily allowance per weekday, a bedtime, and an allowance-today override. When the allowance runs out the devices lock on their own. A grant unlocks them again.
- Enforcement through entities you already have: a router or DNS block switch (UniFi, FRITZ!Box, OPNsense, AdGuard, Pi-hole), a smart plug (opt-in, with a graceful off first), or a manual step where you act in the vendor's app and press done. The PlayStation gets a row in the ledger without anyone pretending it was enforced.
- Honest status. Every write is followed by a read-back. The enforcement sensor says confirmed, pending, partial, degraded or unknown. A lost switch makes the child show as unknown, never as free.
- Guardians and an optional PIN. Dashboard writes from other Home Assistant users are refused. Automations are trusted. With a PIN set, a guardian types it into the PIN entity once and the dashboard works for five minutes.
- Two blueprints: lock for a duration from any button, grant on any event.

What does not work yet:

- Family Link, Family Safety and Nintendo. The vendor adapters are honest stubs with research notes.
- "Educational games do not count." The core can weight minutes by app and by community tag, but nothing in Home Assistant sets those rules or tells Kerb which game is running yet. Every minute is charged at full rate for now. Phase 3 adds the options and a now-playing observer.
- Per-app daily limits and time-of-day tag rules. Phase 3.
- The community tag service. Phase 4. The schemas for it are here so nothing has to be redesigned.

See the roadmap in [docs/SPEC.md](docs/SPEC.md) and the platform matrix in [docs/PLATFORMS.md](docs/PLATFORMS.md).

## Install

1. Add this repository to HACS as a custom integration repository, or copy `custom_components/kerb` into your `config/custom_components` folder.
2. Restart Home Assistant.
3. Settings, Devices and services, Add integration, Kerb. Add one child at a time. See [docs/PARENTS.md](docs/PARENTS.md) for the walk-through.

Home Assistant 2025.10 or newer.

## Documents

- [docs/PARENTS.md](docs/PARENTS.md): setting up a child, what the entities mean, example automations.
- [docs/INTEGRATORS.md](docs/INTEGRATORS.md): the core package, writing an enforcer, calling the services from another integration.
- [docs/SPEC.md](docs/SPEC.md): the Kerb 0.1 standard. Data model, verbs, events, conformance levels, community layer, roadmap and open decisions.
- [docs/PLATFORMS.md](docs/PLATFORMS.md): what each platform can and cannot do, and the risk of each route.
- [docs/schemas](docs/schemas): JSON Schema for every object in the standard.

## Privacy and terms

Children's data stays in the house. Kerb stores an age band, never a date of birth, no location, and keeps daily ledgers and overrides for 31 days by default, then deletes them. Nothing leaves your Home Assistant.

Backups. Kerb's storage file (`.storage/kerb.state`) holds each child's daily ledgers, with the app key where known, the hash of the PIN and the guardian user ids. It is part of every Home Assistant backup, and so will be the vendor session material once the Family Link and Family Safety paths exist. Treat your backups as children's data: encrypt them and keep them where only you can read them. Deleting a child's entry removes their records from the live store, not from backups you already made.

The Family Link and Family Safety routes, when they arrive, will bind to third-party integrations by noiwid that use private vendor APIs. Those may breach the vendors' terms and may stop working without notice. Network and power enforcement are the recommended default and need no vendor account at all.

## Development

```sh
pip install -r requirements_test.txt
pytest
ruff check custom_components tests kerb_core
```

The core domain has no Home Assistant imports and is importable as `kerb_core` from a checkout. Tests live under `tests/core` for the domain, `tests/ha` for the integration and `tests/test_schemas.py` for the standard.

## Credits

noiwid/HAFamilyLink and noiwid/HAFamilySafety for the vendor paths this project will bind to. pynintendoparental and the Home Assistant core Nintendo integration. The Matter Content Control cluster for field names. MusicBrainz and Open Food Facts for the community model.

MIT licence for code and schemas.
