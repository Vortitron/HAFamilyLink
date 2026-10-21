# Kerb: an open household screen-time standard and Home Assistant integration

Version 0.1, draft, 21 October 2026.

Kerb is a small open standard for household screen time, a Home Assistant integration that implements it, and a later community layer for shared game and app tags. It is built backwards from two sentences a parent says out loud.

"No screens for an hour."

"Twenty minutes for emptying the dishwasher."

If a feature does not make one of those two sentences easier, faster or more trustworthy, it is not in the first release.

Companion documents:

- PLATFORMS.md: the honest platform matrix.
- schemas/: JSON Schema (draft 2020-12) for every object in section 3.

## 1. Name

Chosen name: **Kerb**. Home Assistant domain `kerb`. Short, UK spelling, and it is the thing that sets a boundary without being a wall. Easy to search for, unlikely to collide with an existing HA domain.

Alternatives, if Kerb does not stick:

- **Allowance**, domain `allowance`. The ledger is the heart of the design and the word is one parents already use. Downside: generic, hard to search.
- **Hourglass**, domain `hourglass`. Visual, easy icon, fits the ledger metaphor. Downside: several unrelated projects use it.

The repo Vortitron/HAFamilyLink is repurposed and should be renamed to match. See section 10.

## 2. Principles

The research behind this document (see PLATFORMS.md) leads to one hard rule and four principles.

The hard rule: the standard models what the parent wants, not what any vendor offers. Enforcement is pluggable, lossy and allowed to fail. When it fails, the parent is told.

1. Never trust a write. Google returns HTTP 200 for a no-op. Microsoft removed its lock endpoint and kept returning 201. Every write is followed by a read-back. Every operation carries three states: requested, applied, confirmed.
2. Degrade to unknown, never to unlocked. A lost session or a dead endpoint makes the state unknown, raises an alert, and never shows the child as locked or free by guess.
3. Capabilities are declared, not assumed. Every enforcer publishes what it can do. The controller composes the strongest available action per device and reports what was actually done.
4. Children's data stays in the house. The standard carries no credentials, no location and no date of birth. Nothing leaves the household unless the parent opts in, and then only app keys and votes.

## 3. Data model

Seven core objects plus three supporting ones. All identifiers are UUIDs minted locally. Vendor identifiers live in the adapter's own store, never in the core objects. Times are RFC 3339 with explicit offsets. Durations are whole minutes in the parent-facing surface and whole seconds in usage samples. Weekdays use ISO numbering, Monday is 1. Unknown properties are allowed and preserved. Extensions use an `x_` prefix.

### 3.1 Household

One per installation. Holds the time zone, the list of guardians (host user ids allowed to lock and grant), an optional parent PIN hash, and retention settings. The spec defines the shape. Which host user system fills `guardians` is up to the host.

### 3.2 Child

A pseudonymous id, a display name and an age band: `under_7`, `7_to_12`, `13_to_15`, `16_plus`. No date of birth is stored anywhere. The age band drives rating defaults and nothing else.

### 3.3 Device

Belongs to one child, or to the household with a `current_child` field for shared devices such as the family TV. Fields: platform (`android`, `windows`, `xbox`, `playstation`, `switch`, `ios`, `tv`, `pc`, `other`), optional network identity (MAC list, fixed IP, hostname), and a list of bound enforcer ids. A device can have no vendor account and still be governed through a network or power enforcer.

### 3.4 Policy

The standing rules for one child.

- `allowance_minutes`: seven values, one per weekday.
- `windows`: up to four allowed windows per weekday, 30 minute granularity, because that is the coarsest vendor UI.
- `bedtime`: a window per weekday during which the child is locked.
- `rating_ceiling`: an attributed claim (organisation, value, source, date), never a bare value.
- `app_rules`: list of app key plus effect. Effects: `allow_always` (works while locked), `allow` (counts against allowance), `count_half`, `count_double`, `require_approval`, `block`.
- `tag_rules`: same effects keyed on a community tag id. A per-app rule beats a tag rule.
- `grant_cap_minutes_per_day`: optional ceiling on ad hoc grants.

Policy is per child, not per device. Adapters that can only express per-device limits declare `lossy_per_device` and receive the same value for each device. A smarter split is an open decision (section 11).

### 3.5 Override

The ad hoc object and the heart of the design. One override is one parental decision with a lifetime.

```yaml
id: 8d0c0b8a-0f8e-4e4f-9d8f-6f8f6b3b2a11
child_id: c1d6b7b0-3b5f-4c7c-a2f6-0b3b5b1a1a22
kind: lock            # lock | grant | unlock | allowance_today
scope: {type: all}    # all | device | app | tag
minutes: 60           # grant and allowance_today only
reason: dinner
source: guardian:andy # guardian:<id> | automation:<id> | integration:<name>
starts_at: 2026-10-21T17:00:00+01:00
expires_at: 2026-10-21T18:00:00+01:00
status: requested     # requested | applied | partial | confirmed | failed | expired | cancelled
results:
  - enforcer: unifi
    device_id: ...
    status: confirmed
    mode: network
    detail: client blocked at controller
    confirmed_at: 2026-10-21T17:00:04+01:00
  - enforcer: family_safety
    device_id: ...
    status: confirmed
    mode: zero_allowance
    detail: schedule saved, all days set to 0
    restore: {...}
restore: {}
```

Rules.

- Every override has an expiry. The default is end of the local day. A lock switch turned on creates a lock that expires at end of day. Open-ended rules are policy changes, not overrides.
- The newest lock wins over any grant. A grant extends today's remaining time only, never the standing allowance.
- Overrides are idempotent on id and immutable once issued. Cancelling writes a compensating record, it does not delete.
- `results` carries one entry per enforcer that was asked. `mode` says how the enforcer actually did it: `pause`, `zero_allowance`, `network`, `power`, `manual`. If an enforcer emulated a pause by zeroing the allowance, it says so and attaches a `restore` snapshot so the schedule can be put back.
- `status` is `confirmed` only when every asked enforcer has read back the new state. `partial` means some did. `applied` means the writes were sent and the confirmation window has not expired. `failed` means nothing was confirmed within the window.
- A `failed` lock is still a decision in force. The child shows as locked and the enforcement sensor shows degraded, so a parent sees that the lock did not land rather than a child who looks free. Only cancellation and expiry end a decision.
- The controller never takes an enforcer's word for `confirmed`. It downgrades it to `applied` and does its own read-back.

### 3.6 Ledger

The running account for one child for one day. Entries are append-only:

- `allowance`: the day's base minutes from policy, or from an `allowance_today` override.
- `grant`: minutes added, with source, reason and actor.
- `penalty`: minutes removed, same fields.
- `usage`: minutes consumed, per device and per app when known, with a `rate` (1.0 by default, 0.5 for `count_half`, 2.0 for `count_double`).
- `lock`: a block in force, with scope and expiry.

Remaining today is allowance plus grants minus penalties minus weighted usage. Where no adapter can measure usage, the ledger charges elapsed minutes while a device is known to be on and not locked. The ledger entry records which rule it applied and whether per-app usage was available, so the dashboard can say "charged at full rate, this device cannot report per-app usage".

### 3.7 Usage sample

A fact, not a policy. Fields: child id, device id, optional app key, interval start and end, seconds, source enforcer, observed at. Samples are kept for a retention period (default 31 days) and then summarised to daily totals per child. Zero retention is a valid setting.

### 3.8 Request

A child-initiated ask surfaced by a vendor: more time, or access to an app. Fields: id, child id, device id, kind, minutes, app key, created at, status (`pending`, `approved`, `denied`, `expired`), decided by. Only some adapters surface these. Others leave the queue empty.

### 3.9 App key

A namespaced string so community tags attach without any vendor metadata API.

```text
android:com.mojang.minecraftpe
msstore:9NBLGGH2JHXJ
xbox:1828326430
psn:CUSA00001
nintendo:0100D71004694000
steam:252950
igdb:1905
```

`igdb` is the canonical cross-platform key when known. Unknown apps are auto-created as stubs from the store id so usage is never dropped while waiting for a human to link them.

### 3.10 Rating claim

Organisation (`PEGI`, `ESRB`, `USK`, `IARC`, `other`), value, region, source URL, retrieved date. Ratings are claims with provenance, never truth, because no rating body offers a lawful bulk source.

### 3.11 Capabilities

What an enforcer declares about itself. See section 5.

## 4. Standard surface

### 4.1 Versioning

Versions are `major.minor`. Schemas carry `$id` with the version in the path. Minor versions only add optional fields. Major versions may remove or change meaning. The first published version is 0.1, marked experimental until two independent implementations conform.

### 4.2 Verbs

Any conforming controller offers these. Each returns an operation record with `requested_at`, `applied_at`, `confirmed_at` and the per-enforcer `results` list. Clients treat `applied` as provisional.

```text
lock(child, scope, minutes, reason)
unlock(child, scope, reason)
grant(child, minutes, reason, source)
set_allowance_today(child, minutes)
cancel_override(id)
set_policy(child, policy)
get_ledger(child, date)
list_requests(child)
respond_request(request_id, approve | deny, minutes)
reconcile(child | all)
get_capabilities(enforcer)
```

`reconcile` forces a read-back from every enforcer. It runs after a restart and after a session repair.

### 4.3 Events

A controller must emit these.

```text
override.applied          writes sent, awaiting confirmation
override.confirmed        every enforcer read back the new state
override.partial          some enforcers confirmed, others failed or unknown
override.failed           nothing confirmed within the window
override.expired
override.cancelled
enforcement.unconfirmed   one enforcer missed its confirmation window (the primary alert)
allowance.low             remaining under a threshold
allowance.exhausted
request.received
request.decided
enforcer.degraded         session lost, endpoint gone, device unreachable
enforcer.restored
usage.reported
```

The one semantic rule the standard insists on: an unknown enforcement state is reported as unknown, never as unlocked. Silent failure is a conformance violation.

### 4.4 Conformance levels

- Level 0, Observer. Reports usage or presence only.
- Level 1, Cut-off. Can stop a device now and release it later.
- Level 2, Budget. Can set daily allowance and windows and confirm them by read-back.
- Level 3, Interactive. Level 2 plus grants, child requests, per-app policy.
- Level 4, Native. The vendor accepts Policy and Override at one authenticated endpoint per household and emits the events above. Nobody today. The bar is deliberately low so that it could happen.

Field names mirror the Matter Content Control cluster where a match exists (`ScreenDailyTime`, `RemainingScreenTime`, `AddBonusTime`, `BlockContentTimeWindow`), so a Matter TV could become an enforcer later without renaming.

## 5. Enforcer interface

An enforcer is a Python class the integration loads, or any process speaking the same JSON over the host's event bus or MQTT. It declares what it can do, then does it, then proves it did it.

```python
class Enforcer(Protocol):
    capabilities: Capabilities

    async def discover(self) -> list[DeviceRef]: ...
    async def apply(self, override: Override, device: DeviceRef) -> EnforcerResult: ...
    async def revert(self, override: Override, device: DeviceRef) -> EnforcerResult: ...
    async def read_state(self, device: DeviceRef) -> EnforcedState: ...
    async def usage(self, device: DeviceRef, day: date) -> list[UsageSample]: ...
    async def set_policy(self, device: DeviceRef, policy: Policy) -> EnforcerResult: ...
    async def pending_requests(self) -> list[Request]: ...
    async def respond(self, request_id: str, approve: bool, minutes: int) -> EnforcerResult: ...
    async def health(self) -> Health: ...
```

`apply` and `revert` are called once per enforcer and device pair and answer for that device alone, so one enforcer can govern several devices and still return one result per device.

Capability flags: `lock_now`, `lock_emulated`, `unlock_now`, `grant_minutes`, `daily_allowance`, `allowed_windows`, `app_block`, `app_limit`, `usage_read`, `usage_per_app`, `request_queue`, `network_block`, `power_off`, `lossy_per_device`, `manual`. Plus two numbers: `poll_interval_s` and `confirmation_window_s`.

Rules every enforcer follows.

1. Never report confirmed without a read-back. If the vendor returned 200 and the state did not change, that is failed.
2. Translate honestly. If lock is emulated by zeroing today's allowance, declare `lock_emulated`, set `mode: zero_allowance` in the result and attach a restore snapshot.
3. Poll at the declared interval and no faster. Rate limits are the enforcer's job.
4. On authentication loss, go to unknown within one poll and stay there. Do not retry interactive logins unattended.
5. Credentials stay inside the enforcer. The core objects carry none. Browser-based sign-in stays out of the controller process, as both noiwid projects already do.
6. Be idempotent on override id.

Health values: `healthy`, `degraded`, `unknown`, `revoked`, with a human-readable reason.

### 5.1 Enforcers that ship, in order of reliability

1. **Network.** Wraps any HA switch entity the parent marks as "blocks this device": UniFi block-client, FRITZ!Box device switch, OPNsense alias or rule, AdGuard Home client, Pi-hole group via rest_command. Instant, vendor-free, works on every platform. Level 1.
2. **Power.** Any HA switch marked as power for a device, with an optional graceful-off entity (Xbox remote off, ps5-mqtt standby) and a delay before cutting. Level 1. Opt-in per device because of the corruption risk.
3. **Manual.** The null enforcer. The parent gets a notification with the action to perform in the vendor app and a done button. Status becomes confirmed only when the parent presses it. This gives PlayStation a row in the ledger without pretending.
4. **Family Link.** Binds to noiwid/HAFamilyLink entities and services if that integration is installed. Lock switch, bonus buttons, usage sensors. Declares `lossy_per_device`. Level 3.
5. **Family Safety.** Binds to noiwid/HAFamilySafety. Declares `lock_now: false`, `lock_emulated: true`, `request_queue: true`. Level 2 with parts of 3.
6. **Nintendo.** Binds to the HA core nintendo_parental_controls entities. Level 3. The first clean Level 3 proof because it is in core.
7. **Observer.** Charges minutes from Xbox, Steam and PSN now-playing sensors and ps5-mqtt activity. Level 0.

Later, if someone writes them: TimeLimit self-hosted server, OpenWrt ubus, Steam IParentalService (research spike first), iOS companion.

## 6. Home Assistant integration

Domain `kerb`. A custom component first, written to core quality standards. It plays the controller role and hosts enforcers as sub-entries. No vendor logins inside this integration. Vendor sessions stay inside noiwid's integrations and the Nintendo core integration.

### 6.1 Config flow

1. Add a child: name, age band.
2. Add devices by picking existing HA entities. The flow lists candidates: UniFi and FRITZ block switches, plug switches, Xbox and PS remotes, Family Link, Family Safety and Nintendo device entities if present. The parent ticks what belongs to this child and marks each as network, power, or vendor.
3. Pick which HA users are guardians.
4. Optional PIN for lock, unlock and grant.

Options flow: weekly allowance and windows per child, bedtime, confirmation window, grant cap per day, usage retention, whether a lock also covers shared devices, community tag source on or off.

A repair issue is raised whenever an enforcer's health goes to unknown or revoked, and cleared when it recovers.

### 6.2 Entities per child

| Entity | Type | Purpose |
|---|---|---|
| Lock | switch | On creates a lock override expiring at end of day. Off cancels it. |
| Remaining today | sensor, minutes | Ledger balance. Attribute `confidence`: confirmed, assumed, stale. |
| Used today | sensor, minutes | Weighted usage. Attribute lists devices that could not report per-app usage. |
| Allowance today | number, 0 to 1440 | Writes an `allowance_today` override. Mirrors Matter SetScreenDailyTime. |
| Status | sensor | free, locked, exhausted, bedtime, unknown. |
| Enforcement | sensor | confirmed, partial, degraded, unknown. |
| Pending requests | sensor | Count, with the queue as attributes. |
| Grant 15, 30, 60 | button | One-tap bonus. |
| Approve oldest, Deny oldest | button | For vendor request queues. |
| Allowance Monday to Sunday | number | Seven baseline values, disabled by default. |
| Bedtime start, Bedtime end | time | Disabled by default. |
| Any enforcer degraded | binary_sensor | Alert hook. |

### 6.3 Entities per device

Lock switch, status sensor, now playing sensor (from Xbox, Steam, ps5-mqtt or Family Link top app), enforcement sensor, network blocked switch where a network enforcer is bound, in use binary sensor.

### 6.4 Services

```yaml
kerb.lock:
  child: Alice
  duration: "01:00:00"     # optional, end of day if omitted
  scope: all               # or a device id, app key or tag id
  mode: auto               # auto | pause | network | power
  reason: dinner
  pin: "1234"              # required if a PIN is set

kerb.grant:
  child: Alice
  minutes: 20
  reason: emptied the dishwasher
  source: taskmate
  pin: "1234"

kerb.unlock:
  child: Alice
  pin: "1234"

kerb.set_allowance_today:
  child: Alice
  minutes: 90

kerb.respond_request:
  request_id: ...
  approve: true
  minutes: 15

kerb.reconcile: {}

kerb.tag:                   # forwards a community vote, only if the tag source is enabled
  app: android:com.mojang.minecraftpe
  tag: educational
  vote: up
  note: redstone is logic gates
```

Mode `auto` picks the strongest confirmed capability for each of the child's devices: vendor pause where it exists, zero allowance where only that works, network block for devices with no account, power only where the parent opted in. The service response lists what was done per device, verbatim for the dashboard:

```text
Phone locked (Family Link).
Xbox allowance zeroed (Family Safety).
PS5 network blocked (UniFi). PS5 may still run offline games.
```

Grant is the hook for chores. TaskMate, ChoreOps and MedienStop call one service with a reason and a source rather than inventing a fourth ledger.

### 6.5 Blueprints shipped

- Lock all children for a duration from any button.
- Grant on a chore event.
- Bedtime lock on a schedule.
- Notify when enforcement is partial or unconfirmed for more than five minutes.
- Warn the child's device two minutes before a lock where a notify target exists.

### 6.6 Child access

HA has no per-user entity ACL. Three mitigations, all documented plainly:

1. Children should not have HA logins. A child dashboard is a view-only kiosk fed by the sensors.
2. Lock, unlock and grant refuse calls from HA users not listed as guardians and from contexts with no user. Automations run as the owner and are trusted.
3. An optional PIN, mirroring Matter AddBonusTime. Missing or wrong PIN is refused and logged.

## 7. Community layer

A separate service and repo, not part of the HA integration, because parents will not want their home server talking to the internet about their children. The HA side only ever sends app keys and votes, and only if the parent turns it on. The tag and vote schemas ship in 0.1 so nothing has to be redesigned. The server is phase 4.

### 7.1 Taxonomy

A curated allow-list in the Open Food Facts style with canonical ids, definitions, synonyms and a polarity hint (`value`, `neutral`, `caution`). Proposed v1:

- Value: `educational`, `creative`, `reading`, `maths`, `physical_activity`, `music`.
- Social: `chat_with_strangers`, `voice_chat`, `friends_only_multiplayer`, `local_coop`, `solo`.
- Commerce: `in_app_purchases`, `loot_boxes`, `pay_to_win`, `subscription`, `ads_heavy`.
- Content: `violence_mild`, `violence_graphic`, `horror`, `gambling_mechanics`, `user_generated_content`.
- Attention: `short_sessions`, `no_stopping_point`, `autoplay`, `endless_feed`, `offline_ok`.

New tags are proposed through an issue. Free text is accepted into a separate tag table but never drives policy.

### 7.2 Voting

MusicBrainz rules. One vote per household per tag per app key, up or down. A tag shows when its net score is positive. Caution tags additionally need evidence (a store URL or screenshot reference) and at least three distinct contributors before they show. Value tags accept a note. Visible tags are capped at ten per app, Steam's lesson. Early data is seeded from IGDB genres and age ratings, stored as attributed claims.

Every write carries a pseudonymous household id, client name and version, so a misbehaving client or household can be rate limited or blocked without touching past votes. Edits are logged and revertable. A right-to-forget call deletes a household's votes and profile submissions in one request.

### 7.3 Profiles

Parents differ but cluster. Rather than invent clustering, a household can publish its tag overlay and allowance defaults as a named profile (strict under 10, educational first, weekend only) and others subscribe. A subscribed profile overrides crowd tags locally. Local per-app overrides beat everything, so "Minecraft counts as educational in this house" is one record. Clustering can come later from the subscription graph, offline and explainable.

### 7.4 Openness

Data under ODbL. Schemas and code under MIT. Vocabulary under CC BY-SA. Reads are anonymous and cacheable. A nightly JSON Lines dump is published and the HA integration embeds the last dump, so a fresh install works offline and the server is not a single point of failure. A resolution endpoint maps any store id to a canonical app and auto-creates stubs.

### 7.5 How it reaches the parent

With a tag source enabled, each app in a child's app list gains tags and policy can say "always allow anything tagged educational" or "block anything tagged chat_with_strangers after 19:00". Tag effects such as `count_half` apply in the local ledger only and are gated on `usage_per_app`. Where an enforcer cannot report per-app usage the child sensor says so in attributes.

## 8. Privacy and security

Children's data is the sensitive asset, so the defaults are the conservative ones.

- Nothing leaves the house except app keys and votes to the community service, and only if the parent opts in. No child names, no usage, no device ids, no age beyond a band.
- Age band, never date of birth. No location. Family Link exposes location and this project does not read it.
- Usage samples are kept 31 days by default, then summarised to daily totals. Zero retention is valid.
- Logs redact app and game titles unless debug logging is on, because a per-title log is a behaviour record of a child.
- The standard carries no credentials. Enforcers hold them in their own config entries. The README states that HA backups contain session material for the vendor paths.
- Fail closed for state, fail honest for control. Unknown is shown as unknown and raises a repair.
- Every override logs who or what created it. The ledger is the audit trail a parent can show a child.
- Vendor terms. The README states that the Family Link and Family Safety paths rely on third-party integrations that may breach vendor terms and could stop working. Network and power are the recommended default.

## 9. Roadmap

Each phase is a set of small commits. Phase 1 is buildable now with what Andy owns.

### Phase 1: lock and grant on every device, no vendor APIs

1. Schemas and this spec.
2. Core domain in pure Python with tests: policy, override stacking, ledger, confirmation windows, the unknown-not-unlocked rule.
3. HA integration with per-child entities, lock, grant, unlock and set_allowance_today services, guardian check and PIN.
4. Network, power and manual enforcers.
5. Config flow picking existing HA entities.
6. Two blueprints: lock for a duration, grant on event.

Success: Andy presses one button and every child device drops off the network and the Xbox turns off within one poll. TaskMate approves a chore and remaining today rises by twenty minutes. The PS5 shows a manual action with a done button.

### Phase 2: vendor wrappers and observers

1. Family Link and Family Safety enforcers, gated on noiwid's integrations being present, with degraded-state handling tested first.
2. Observer enforcer charging minutes from Xbox, Steam and ps5-mqtt now-playing.
3. Repair issues for unknown enforcers. Remaining three blueprints.
4. Nintendo enforcer over the core integration, as the Level 3 proof.

### Phase 3: policy depth

1. Weekly allowance and windows written through to vendors that accept them, with read-back.
2. Request queue entities and approve or deny.
3. Per-app rules and tag rules in the local ledger, with honest attributes.
4. A PLATFORMS.md refresh and a conformance test suite any enforcer can run.

### Phase 4: community

1. Community server: FastAPI plus SQLite, taxonomy, votes, profiles, resolution endpoint, nightly dump, right-to-forget.
2. HA tag source and the `kerb.tag` service.
3. Named profiles and subscriptions. Clustering later, from the subscription graph.

### Phase 5: research spikes, only if someone wants them

Steam IParentalService auth path. TimeLimit server adapter. OpenWrt ubus enforcer. iOS companion with the FamilyControls entitlement.

## 10. Repo plan

The Vortitron/HAFamilyLink placeholder is repurposed. The Family Link README is replaced, the stub Python under custom_components/familylink is removed, and the layout becomes:

```text
docs/                         spec, platform matrix, schemas
custom_components/kerb/       the HA integration
custom_components/kerb/core/  pure Python domain, no HA imports (lives here so a HACS install carries it)
kerb_core/                    shim so the core imports as kerb_core from a checkout, until it is on PyPI
blueprints/
tests/
```

The repo should be renamed to kerb (or the chosen alternative). hacs.json is rewritten for the new domain.

## 11. Open decisions for Andy

1. Name. Kerb, Allowance or Hourglass. Check the HA domain and the GitHub name before committing.
2. Per-child allowance on per-device vendors. Send the same value to each device (simple, over-generous) or split it by recent usage share (fairer, more writes against fragile APIs). Proposed default: same value, flagged `lossy_per_device`.
3. Lock switch expiry. End of local day, or end of the current bedtime window if one is active. Proposed: end of day.
4. Power enforcer default. Off unless the parent opts in per device, because of the corruption risk. Agree?
5. Guardian check. Refuse service calls from non-guardian HA users even when no PIN is set, or only when a PIN is set. Proposed: always refuse.
6. Dependency on noiwid. Bind to his integrations' entities (loose, breaks when his entity ids change, as they did in v2.0) or import his client modules (tighter, pulls his auth add-on into our dependency tree). Proposed: entities first.
7. Usage retention default. 31 days, or shorter.
8. Community server hosting. Who runs it, which domain, and whether to start as a GitHub-hosted nightly dump only with no live server.
9. Licence for the data. ODbL as proposed, or CC BY-SA to match the vocabulary.
10. Whether to publish the spec to the HA community forum and the X-PPC and PARCEP authors once 0.1 has a working Phase 1, so it can feed those drafts rather than compete with them.
11. PlayStation. Accept the manual enforcer as the long-term answer, or fund a mitmproxy spike on the PlayStation Family app knowing the account ban risk.

## 12. Deliberately out of scope

- Reimplementing the private Google or Microsoft APIs. noiwid maintains those. This project binds to them and credits them.
- Reverse engineering PlayStation Family.
- An iOS companion app.
- A chore or points system. Grant is the hook.
- Age verification, jurisdiction and operator policy. That is PARCEP territory. This spec defines the household clause set those drafts leave blank.
- Content and web filtering, location, messaging, purchase approval.
- Algorithmic clustering of parents before there is a subscription graph to learn from.
- Per-user access control inside HA. Documented as a platform gap, mitigated by the guardian check and PIN.

## 13. Prior art and credits

noiwid/HAFamilyLink and noiwid/HAFamilySafety (MIT) for the vendor adapters this project binds to. pantherale0/pyfamilysafety, pynintendoparental and the HA core nintendo_parental_controls integration for the entity template. Matter Content Control cluster 0x050F for field names. IETF draft-oprea-x-ppc-00 for the shared-quota idea and draft-campling-parcep-sync-00 for the policy vocabulary. MusicBrainz and Open Food Facts for the voting and governance model. TimeLimit and Timekpr-nExT for the policy shapes. TaskMate, ChoreOps and MedienStop for showing the demand for a grant hook.
