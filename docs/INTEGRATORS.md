# Kerb for integrators

This page is for people writing an enforcer, calling Kerb from another integration, or reusing the core outside Home Assistant. Read [SPEC.md](SPEC.md) for the standard itself.

## Layout

```text
custom_components/kerb/           the Home Assistant integration
custom_components/kerb/core/      the pure-Python domain, no HA imports
custom_components/kerb/core/vendors/  honest stubs for Family Link, Family Safety, Nintendo, PlayStation
custom_components/kerb/enforcers.py   network, power, manual and presence enforcers over HA entities
kerb_core/                        a shim so the core imports as kerb_core from a checkout
docs/schemas/                     JSON Schema 2020-12 for every object
blueprints/automation/kerb/       the shipped blueprints
tests/core, tests/ha, tests/test_schemas.py
```

The core lives inside the integration folder because a HACS install copies only that folder. The `kerb_core` shim points its package path there. When the core is published on PyPI the shim goes and the integration lists it in `manifest.json` requirements.

## The core in five objects

- `Controller` (core/controller.py) owns children, policies, devices, enforcers, overrides and ledgers. It offers the verbs `lock`, `unlock`, `grant`, `set_allowance_today`, `cancel_override`, `reconcile`, `forget_child`, and `tick`, which the host calls on a timer.
- `Policy` (core/models.py, core/policy.py) is per child: seven allowances, windows, bedtime, app rules, tag rules, grant cap.
- `Override` is one parental decision with a lifetime and per-enforcer `results`. The newest decision wins. A failed override is still a decision in force; the enforcement status says it did not land.
- `DayLedger` (core/ledger.py) is the append-only account for one child for one day. Remaining is allowance plus grants minus penalties minus weighted usage.
- `Enforcer` (core/enforcer.py) is the protocol an adapter implements.

Everything is tested without Home Assistant in `tests/core`. The `FakeEnforcer` in `tests/core/conftest.py` shows the contract, including a vendor that returns 200 and changes nothing.

## Writing an enforcer

Subclass `BaseEnforcer`, declare `Capabilities`, and implement at least `apply`, `revert`, `read_state` and `health`. `apply` and `revert` are called once per enforcer and device pair. Every object on the interface has a schema: `device_ref.json`, `enforcer_result.json`, `enforced_state.json`, `health.json` and `capabilities.json` in docs/schemas, and SPEC.md section 5 describes each field.

Rules the controller relies on:

1. Return `applied` (or `requested`, `failed`, `unknown`) from `apply`, never `confirmed`. The controller does its own read-back through `read_state` and downgrades any `confirmed` you return.
2. `read_state` returns `locked=None` when you do not know. Never guess.
3. If you emulate a lock (zeroing an allowance), declare `lock_emulated`, return `mode=zero_allowance` and attach a `restore` snapshot.
4. `health` returns `unknown` or `revoked` within one poll of losing a session, and you do not retry interactive logins unattended.
5. Credentials stay inside the enforcer. The core objects carry none.
6. `in_use` on `EnforcedState` is how the controller charges minutes for devices with no usage API. Return `True` only when you know.
7. `revert` may be called for a pair you locked under one override while another override still wants it locked. It is not: the controller skips pairs another lock in force still holds, and only releases what nothing else is holding. You never have to reason about other overrides.

`Capabilities.lock_mode` derives the mode the controller will use from your flags: `manual`, then `lock_now` without network or power (pause), `lock_emulated`, `network_block`, `power_off`. The controller asks every capable enforcer bound to a device in mode `auto`, skips power unless the device opted in, and reports one line per result.

Vendor adapters go in `core/vendors/`. The four stubs there carry the research notes and the TODO order. Write the fake of the vendor entity set first, then the adapter against it, including the degraded and no-op cases.

## Inside Home Assistant

`hub.py` holds one `KerbHub` per Home Assistant instance in `hass.data["kerb"]`. Each config entry is one child and gets a `KerbChildCoordinator`. The hub ticks the controller once a minute, pushes `ChildState` to every coordinator and saves to `.storage/kerb.state` with a five second debounce.

Enforcers in `enforcers.py` wrap HA entities. They call the entity's own domain service (`switch.turn_on`, `input_boolean.turn_off`, `remote.turn_off`) and read the entity state back. Add a new HA-side enforcer by subclassing `HAEnforcer` and wiring it in `KerbHub._add_device`.

Events from the controller are re-fired on the bus as `kerb_event` with the event's `type`, `child_id`, `at` and `payload`. `enforcer.degraded` also raises a repair issue; `enforcer.restored` clears it.

### Calling Kerb from your integration

Use the services. They return a response.

```python
response = await hass.services.async_call(
	"kerb",
	"grant",
	{"child": "Alice", "minutes": 20, "reason": "emptied the dishwasher", "source": "taskmate"},
	blocking=True,
	return_response=True,
)
response["status"]   # confirmed | applied | partial | failed
response["summary"]  # one line per enforcer result
```

Calls with no user in the context (automations, integrations) are trusted. Calls from a Home Assistant user must come from a guardian, and must carry `pin` when one is set, unless that guardian entered it on the PIN entity within the last five minutes. A null or blank `pin` means none was given. `kerb.confirm_manual` never needs the PIN. Pass `source` so the ledger says who granted the minutes.

Scope can be `all` or a device name. Mode can be `auto`, `network`, `power`, `manual`, `pause` or `zero_allowance`; the last two only matter once vendor adapters exist.

## Standard surface

`docs/schemas` has one JSON Schema per object and a CHANGELOG.md. `tests/test_schemas.py` checks every schema parses, the examples validate, `to_dict()` on every core model produces a valid document, and a set of documents that must fail do fail. Keep that test green when you change a model, and add a line to the changelog when you change a schema.

Every stored model keeps properties it does not know in `extras` and writes them back out, so an `x_` extension from another client survives this controller. Extensions use an `x_` prefix. While the version is 0.x the schemas may change freely; from 1.0 minor versions add optional fields only.
