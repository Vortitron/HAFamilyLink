# Kerb: an open household screen-time standard, with a Home Assistant reference controller

Version 0.1, draft, 21 October 2026.

Kerb is a small open standard for household screen time. It is not an app. A controller is any certified software that holds a child's plan and ledger: a vendor's own parent app once it is certified, an independent app or website, or a home hub. The Home Assistant integration in section 6 is the open-source reference controller, one of many, and a later community layer adds shared game and app tags. It is built backwards from two sentences a parent says out loud.

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
4. Children's data stays in the house. The standard carries no vendor logins, passwords or session tokens, no location and no date of birth. Nothing leaves the household unless the parent opts in, and then only app keys and votes.

## 3. Data model

Seven core objects plus three supporting ones. All identifiers are UUIDs minted locally. Vendor identifiers live in the adapter's own store, never in the core objects. Times are RFC 3339 with explicit offsets. Durations are whole minutes in the parent-facing surface and whole seconds in usage samples. Weekday lists are seven-entry arrays, index 0 is Monday (ISO weekday 1). Unknown properties are allowed and preserved: a conforming implementation reads them, keeps them and writes them out unchanged, and the reference controller does exactly that on every object it stores. Extensions use an `x_` prefix. The schemas in schemas/ are normative; where this prose and a schema disagree, the schema wins. See Appendix A.

### 3.1 Household

One per installation. Holds the time zone, the list of guardians (host user ids allowed to lock and grant), an optional parent PIN hash, and retention settings. The spec defines the shape. Which host user system fills `guardians` is up to the host.

Portability. A household exports as one bundle in the standard format: its children, their policies, overrides still in force, ledgers within retention, the milestone summary and app keys. Host-specific fields (guardian ids, the PIN hash, enforcer config entries) are left out and made again on import. Every conforming controller must produce this bundle for any household it holds, whenever a guardian asks, and must accept a bundle produced by any other conforming controller. The bundle belongs to the household. A controller run by a vendor holds it only under the family's own account and uses it only to run the plan.

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
- `app_rules`: list of app key plus effect. Effects: `allow_always` (works while locked, recorded at rate 0), `allow` (counts against allowance), `count_half`, `count_double`, `require_approval`, `block`.
- `tag_rules`: same effects keyed on a community tag id. A per-app rule beats a tag rule. Among several matching tags the strictest wins.
- `grant_cap_minutes_per_day`: optional ceiling on ad hoc grants.
- `profile_ref`: optional, the community profile this policy started from.

Per-app daily limits and time-of-day tag windows ("block chat after 19:00") are phase 3. They are not in the 0.1 schema, so a rule a parent writes cannot silently vanish on save.

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
- `scope.type` of `device`, `app` or `tag` requires the matching `device_id`, `app` or `tag`. `minutes` is required for `grant` and `allowance_today`. `expires_at` is later than `starts_at`.
- `results` carries one entry per enforcer that was asked (schema enforcer_result.json). `mode` says how the enforcer actually did it: `pause`, `zero_allowance`, `network`, `power`, `manual` for locks and unlocks, `bonus` for a grant, `allowance` for `allowance_today`. A result's `status` is `requested`, `applied`, `confirmed`, `failed` or `unknown`; `unknown` means the enforcer could not be trusted or could not read the device. If an enforcer emulated a pause by zeroing the allowance, it says so and attaches a `restore` snapshot so the schedule can be put back.
- `status` is `confirmed` only when every asked enforcer has read back the new state. `partial` means some did. `applied` means the writes were sent and the confirmation window has not expired. `failed` means nothing was confirmed within the window.
- An unlock ends the locks it covers: they are marked `cancelled` with the unlock as the compensating record. A lock whose time runs out is marked `expired`. When a lock ends, the controller releases only the enforcer and device pairs no other lock in force still holds, so an hour's lock expiring inside bedtime, or under a later rest-of-day lock, frees nothing.
- A `failed` lock is still a decision in force. The child shows as locked and the enforcement sensor shows degraded, so a parent sees that the lock did not land rather than a child who looks free. Only cancellation and expiry end a decision.
- The controller never takes an enforcer's word for `confirmed`. It downgrades it to `applied` and does its own read-back.

### 3.6 Ledger

The running account for one child for one day. Entries are append-only:

- `allowance`: the day's base minutes from policy, or from an `allowance_today` override.
- `grant`: minutes added, with source, reason and actor.
- `penalty`: minutes removed, same fields.
- `usage`: minutes consumed, per device and per app when known, with a `rate` (1.0 by default, 0.5 for `count_half`, 2.0 for `count_double`, 0.0 for `allow_always`: the minutes are recorded so the child's day is complete, but cost nothing).
- `lock`: a block in force, with scope and expiry.

Remaining today is allowance plus grants minus penalties minus weighted usage. Where no adapter can measure usage, the ledger charges elapsed minutes while a device is known to be on and not locked. The ledger entry records which rule it applied and whether per-app usage was available, so the dashboard can say "charged at full rate, this device cannot report per-app usage".

### 3.7 Usage sample

A fact, not a policy. Fields: child id, device id, optional app key, interval start and end, seconds (never more than end minus start), source enforcer, observed at.

Retention in 0.1 is simple and honest: the reference controller does not persist usage samples at all. It charges minutes into the day ledger as they happen, and keeps whole day ledgers and overrides for the retention period (`usage_retention_days`, default 31), then deletes them. Nothing is summarised first. A controller that does summarise before deleting conforms too, as long as the summary carries no app keys. Zero retention is a valid setting.

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
apple:1234567890
other:anything-without-whitespace
```

`igdb` is the canonical cross-platform key when known. `apple` is reserved for an iOS companion. `other` is for an app no store knows, such as a sideloaded or self-built one. Unknown apps are auto-created as stubs from the store id so usage is never dropped while waiting for a human to link them.

### 3.10 Rating claim

Organisation (`PEGI`, `ESRB`, `USK`, `IARC`, `ACB`, `CERO`, `other`), value, region, source URL, retrieved date. Ratings are claims with provenance, never truth, because no rating body offers a lawful bulk source.

### 3.11 Capabilities

What an enforcer declares about itself. See section 5.

## 4. Standard surface

### 4.1 Versioning

Versions are `major.minor`. Schemas carry `$id` with the version in the path. From 1.0 on, minor versions only add optional fields, major versions may remove or change meaning, and `$id` values are fixed. While the major version is 0 anything may change between commits, including `$id`, whose kerb.dev domain is a placeholder. Every schema change is recorded in schemas/CHANGELOG.md. The first published version is 0.1, marked experimental until two independent implementations conform.

Conformance is judged against the schemas plus a short list of rules JSON Schema cannot express: `expires_at` later than `starts_at`, a usage sample's `seconds` no more than its interval, a window's `start` not equal to its `end`, and every timestamp carrying an explicit offset (the schemas enforce the last one with a pattern). The phase 3 conformance suite tests all four.

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
delete_child(child)
export_household() -> bundle
import_household(bundle)
transfer_control(child, platform, to_controller)
```

`reconcile` forces a read-back from every enforcer. It runs after a restart and after a session repair. `delete_child` removes every record the controller holds about a child: the child, their devices, overrides and ledgers. Nothing about a child outlives the parent's decision to remove them.

`export_household` and `import_household` move a whole household between controllers; an import followed by `reconcile` must leave every child with the same policy, the same overrides and the same ledger history. `transfer_control` hands one child on one platform to another controller: the platform starts taking the plan from the new controller and stops taking it from the old one, which keeps read access to the ledger but can no longer change anything. Each transfer is written to the ledger as an override with the guardian as actor, so the child sees it. After every platform has confirmed the transfer, the old controller deletes its copy of the household unless a guardian asked it to keep one.

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

An enforcer is a Python class the integration loads. It declares what it can do, then does it, then proves it did it. A transport for out-of-process enforcers (MQTT or the host's event bus) is on the roadmap (section 9, phase 3) and is not specified in 0.1; until it is, an adapter in another language wraps itself in a small Python class.

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

The objects on this interface each have a schema in schemas/.

- `DeviceRef` (device_ref.json): what the controller hands over about a device. `device_id`, `display_name`, `platform` and `power_off_allowed`. Nothing about the child.
- `Override` (override.json): the decision being applied or reverted. The enforcer reads `kind`, `scope`, `minutes` and `id`, and is idempotent on `id`.
- `EnforcerResult` (enforcer_result.json): the answer. `status` is `requested` (queued, nothing sent yet), `applied` (sent), `failed` (the vendor refused or the call raised) or `unknown` (cannot say). An enforcer never returns `confirmed`; only the controller writes that, after its own read-back, and downgrades any `confirmed` it receives to `applied`. `mode` says how it was done. `restore` carries whatever is needed to undo an emulation.
- `EnforcedState` (enforced_state.json): what `read_state` saw. `locked` is `true`, `false` or `null`, and `null` means unknown: the controller treats it as unknown and never as free. `in_use` is `true` only when the enforcer knows the device is being used now; it is how minutes are charged for devices with no usage API. `detail` is shown to the parent.
- `Health` (health.json): `status` and a `reason`. The controller trusts `healthy` and `degraded` read-backs, and treats `unknown` and `revoked` as unknown state. An unhealthy enforcer is never asked to write.
- `Capabilities` (capabilities.json): below.

Capabilities carry the enforcer's `enforcer` name and conformance `level`, the flags `lock_now`, `lock_emulated`, `unlock_now`, `grant_minutes`, `daily_allowance`, `allowed_windows`, `app_block`, `app_limit`, `usage_read`, `usage_per_app`, `request_queue`, `network_block`, `power_off`, `lossy_per_device`, `manual`, two numbers `poll_interval_s` and `confirmation_window_s`, and free-text `notes`. The controller derives the lock mode from the flags: `manual`, then `lock_now` without network or power (pause), `lock_emulated` (zero_allowance), `network_block`, `power_off`.

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

Items 4 and 5 reach Google and Microsoft through noiwid's integrations, which sign in as the parent and use endpoints the vendors have not published. The proposal (docs/proposal/PROPOSAL.md, section 4.3) says a controller that does this is not covered by the certification mark, so these two enforcers sit outside the mark. They are off by default, appear only when the parent has installed noiwid's integration and ticks those entities in the config flow, and the child dashboard shows that the route exists. A build of the reference controller submitted for certification excludes them. They exist to show what the standard would let a parent do, and to retire the day the vendor offers a Level 4 endpoint.

### 5.2 Where a certified platform plugs in (Level 4)

The enforcer class above is the controller's side of the standard. It wraps a device or vendor service that has no Kerb interface of its own, and it runs inside the controller. A platform that reaches Level 4 writes no enforcer. It exposes one authenticated endpoint per household that accepts the verbs in 4.2 and emits the events in 4.3, using the objects in section 3 and nothing else. Any certified controller, this one or a vendor's own app, talks to that endpoint the same way. That is what lets a parent set the plan from the app they already use, and what stops a vendor giving another company's controller fewer controls than its own.

## 6. Home Assistant integration

Domain `kerb`. A custom component first, written to core quality standards. It is the reference controller, one implementation of the controller role, and hosts enforcers as sub-entries. No vendor logins inside this integration. Vendor sessions stay inside noiwid's integrations and the Nintendo core integration.

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
| Status | sensor | free, locked, exhausted, bedtime, unknown. Exhausted while the allowance lock is in force. |
| Enforcement | sensor | confirmed, pending, partial, degraded, unknown. Pending while writes await read-back or a parent's done; degraded for a failed lock or an unhealthy enforcer. |
| PIN | text | Takes the PIN once and arms the dashboard for that guardian for five minutes. Always reads empty. |
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
3. An optional PIN, mirroring Matter AddBonusTime. Missing or wrong PIN is refused and logged. Service calls carry it in `pin`. Dashboard entities cannot, so a guardian enters it on the PIN text entity, which arms the other entities for that guardian for five minutes. Confirming a manual step (the done button, `kerb.confirm_manual`) needs the guardian check but never the PIN: it decides nothing.

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

Every write carries a contributor id, client name and version, so a misbehaving client or household can be rate limited or blocked without touching past votes. The contributor id is a random UUID the client mints locally when the parent turns sharing on. It is separate from `Household.id`, never derived from it, and the parent may rotate it at any time; past votes stay but are no longer linked to the new id. Votes and profiles are the only two objects that leave the house and both refuse any property the schema does not name (`x_` excepted), so no client can attach a child's name or usage by accident. `evidence` is a store or IGDB page, never an image, and the server does not accept uploads in 0.1. `note` and profile text must not contain names; the server may strip or reject them. Edits are logged and revertable. A right-to-forget call deletes a contributor's votes and profile submissions in one request.

### 7.3 Profiles

Parents differ but cluster. Rather than invent clustering, a household can publish its tag overlay and allowance defaults as a named profile (strict under 10, educational first, weekend only) and others subscribe. A subscribed profile overrides crowd tags locally. Local per-app overrides beat everything, so "Minecraft counts as educational in this house" is one record. Clustering can come later from the subscription graph, offline and explainable.

### 7.4 Openness

Data under ODbL. Schemas and code under MIT. Vocabulary under CC BY-SA. Reads are anonymous and cacheable. A nightly JSON Lines dump is published and the HA integration embeds the last dump, so a fresh install works offline and the server is not a single point of failure. A resolution endpoint maps any store id to a canonical app and auto-creates stubs.

### 7.5 How it reaches the parent

With a tag source enabled, each app in a child's app list gains tags and policy can say "always allow anything tagged educational" or "block anything tagged chat_with_strangers". Time-of-day tag rules ("after 19:00") are phase 3. Tag effects such as `count_half` apply in the local ledger only and are gated on `usage_per_app`. Where an enforcer cannot report per-app usage the child sensor says so in attributes.

## 8. Privacy and security

Children's data is the sensitive asset, so the defaults are the conservative ones.

- Nothing leaves the house except app keys and votes to the community service, and only if the parent opts in. No child names, no usage, no device ids, no age beyond a band.
- Age band, never date of birth. No location. Family Link exposes location and this project does not read it.
- Day ledgers and overrides are kept 31 days by default, then deleted. Usage samples are not persisted by the reference controller. Zero retention is valid. See 3.7.
- Logs redact app and game titles unless debug logging is on, because a per-title log is a behaviour record of a child.
- The standard carries no vendor logins, passwords or session tokens. Enforcers hold them in their own config entries.
- Controller credential. Where a platform accepts a plan directly (Level 4), the controller presents a credential issued by the steward and bound to the household through the guardian's existing platform family account, once per platform. The platform verifies a signature and never asks the parent to log in to anything else. The steward can revoke it; a revoked controller is treated as `revoked` health and the platform falls back to what the law requires of it. The README and the parent guide state that HA backups contain Kerb's own storage file (ledgers with app keys per child, the PIN hash, guardian ids) and, once vendor paths exist, their session material, so backups are children's data and must be protected as such.
- Moving is a right. A household can leave any controller at any time and take everything with it (3.1, 4.2). The conformance suite tests export from one controller and import into another; a controller that fails it is not conforming.
- Fail closed for state, fail honest for control. Unknown is shown as unknown and raises a repair.
- Every override logs who or what created it. The ledger is the audit trail a parent can show a child.
- Vendor terms. The README states that the Family Link and Family Safety paths rely on third-party integrations that may breach vendor terms and could stop working. Network and power are the recommended default.

### 8.1 The child

The child is the person the data is about, and the standard owes them a position too.

- What is recorded: an age band, device names, which minutes were used on which device (and app, where known), what was granted and why, and every lock with its reason. Nothing else.
- Visible on request. The ledger is written so it can be shown to the child in full: every line says who did what and why. The HA integration exposes it through the sensors a kiosk dashboard can read. A controller that hides the ledger from the child does not conform in spirit.
- For `13_to_15` and `16_plus`, UK guidance expects the young person's own view to count. The standard cannot enforce a conversation, but a profile for those bands should default to fewer blocks and more counting, and a parent-facing guide should say so.
- Leaving the household: `delete_child` (4.2) removes every record about the child. There is no partial retention. Community sharing never includes anything per child, so there is nothing to delete there.

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
3. Per-app rules and tag rules in the local ledger, with honest attributes: an options field or service to set them per child, a now-playing observer so the controller knows which app is running, then per-app daily limits and time-of-day tag windows added back to the schema.
4. A PLATFORMS.md refresh and a conformance test suite any enforcer can run, covering the rules JSON Schema cannot express (4.1).
5. An out-of-process enforcer transport: topic names, message envelope, correlation id, capability announcement, heartbeat and timeouts over MQTT and the HA event bus.

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
12. **The protected list.** The standard fixes a short list no plan may block: emergency numbers, children’s helplines, public health advice, how to report abuse, children’s rights. Decide whether sexual and reproductive health information for older children joins it, and who maintains the list (proposal section 4.2a).

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

## Appendix A. Vocabularies

The schemas are normative. This list is a reading aid kept in step with them by hand; tests/test_schemas.py checks the schemas, not this table.

| Where | Values |
|---|---|
| age_band | under_7, 7_to_12, 13_to_15, 16_plus |
| platform | android, windows, xbox, playstation, switch, ios, tv, pc, other |
| override.kind | lock, grant, unlock, allowance_today |
| scope.type | all, device, app, tag |
| override.status | requested, applied, partial, confirmed, failed, expired, cancelled |
| result.status | requested, applied, confirmed, failed, unknown |
| result.mode | pause, zero_allowance, network, power, manual, bonus, allowance |
| effect | allow_always, allow, count_half, count_double, require_approval, block |
| ledger.kind | allowance, grant, penalty, usage, lock |
| ledger.rate | 0.0, 0.5, 1.0, 2.0 |
| app key namespace | android, msstore, xbox, psn, nintendo, steam, igdb, apple, other |
| rating organisation | PEGI, ESRB, USK, IARC, ACB, CERO, other |
| health.status | healthy, degraded, unknown, revoked |
| request.kind | more_time, app_access |
| request.status | pending, approved, denied, expired |
| tag polarity | value, neutral, caution |
| source prefix | guardian:, automation:, integration: |
