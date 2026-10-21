# Platform matrix

What can be controlled today, by which route, and at what risk. Dated 21 October 2026. Vendor behaviour changes without notice, so treat every row as a snapshot.

Levels are the conformance levels defined in SPEC.md.

- Level 0, Observer: can see usage or presence, cannot change anything.
- Level 1, Cut-off: can stop a device now and release it later. No budget awareness.
- Level 2, Budget: can set daily allowance and windows and confirm them by read-back.
- Level 3, Interactive: Level 2 plus grants, child requests, per-app policy.
- Level 4, Native: the vendor implements the schemas directly. Nobody today.

## Summary table

| Platform | Official API | Best route today | Level reachable | Lock now | Grant minutes | Daily allowance | Windows | Per-app | Child requests | Usage read | Risk |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Android (Family Link) | None | noiwid/HAFamilyLink, private kidsmanagement API, browser cookies via Playwright add-on | 3 | Yes | Yes (bonus) | Yes, per device | Yes (bedtime, school) | Yes | No queue | Yes, per app | High: undocumented, 200 on no-op, Google ToS forbids |
| Windows and Xbox (Family Safety) | None | noiwid/HAFamilySafety, private web API plus mobile aggregator, cookies and CSRF token | 2, parts of 3 | Emulated only (allowance to zero) | Approve child request only | Yes | Yes, 30 min slots | Yes | Yes | Yes, per device and app | Highest: Microsoft already removed the lock endpoint, daily re-auth on some accounts, plaintext session in HA storage, ToS forbids |
| Xbox (Xbox Live) | Partial, SmartGlass | HA core xbox integration, remote.turn_off | 1 and 0 | Power off only | No | No | No | No | No | Now playing, presence | Medium: needs HA Cloud linking, child can turn it back on |
| PlayStation (PS Family) | None | None. PlayStation Family app and console only | 0 via PSN, 1 via power or network | No (rest mode via ps5-mqtt, not a lock) | No | No | No | No | No | Title and play time via PSNAWP, read only | PSN ban risk if polled hard. Reverse engineering the Family app is new work and out of scope |
| Nintendo Switch | None, but stable unofficial | HA core nintendo_parental_controls (pynintendoparental) | 3 | Yes (limit 0 plus suspend) | Yes (bonus) | Yes | Bedtime only | Allow list | No | Yes, per title | Low to medium: shipped in HA core, Nintendo can change it |
| Steam (Steam Families) | Undocumented IParentalService | Nothing built. Protobufs public, auth path unproven | 0 today | Unproven (LockClient exists) | Unproven | Unproven | Unproven | n/a | Unproven | Now playing via steam_online | Medium: research spike needed, Steam Guard in the loop |
| Apple (Screen Time) | Device-local only | None from HA. Network block only | 1 via network | Via network only | No | No | No | No | No | No | An iOS companion app with the FamilyControls entitlement is a separate project |
| Any device, network layer | n/a | UniFi block-client switch (core), FRITZ!Box device switch (core), OPNsense alias or rule (HACS), AdGuard Home client, Pi-hole group | 1 | Yes, immediate | No | Windows only via schedules on some routers | Partial | No | No | Partial (presence) | Low: vendor-free. DNS-only layers do not stop a game already running or hard-coded IPs. MAC randomisation and offline games are the gaps |
| Any device, power layer | n/a | Smart plug switch, Xbox remote off, ps5-mqtt standby | 1 | Yes, blunt | No | No | No | No | No | Power draw as presence | Low to medium: data corruption if cut mid-update. Send graceful off first. Child can replug |
| Windows local account | n/a | net user /times plus HASS.Agent lock or shutdown | 1, crude 2 | Yes | No | Logon hours only | Whole hours | No | No | Active window via HASS.Agent | Low: needs agent running as a service the child cannot stop |
| Android alternative (TimeLimit) | Open source, self-hosted server | Replace Family Link with TimeLimit device-owner build and self-hosted server | 3 potential | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Low legal risk. Loses Family Link purchase approvals. Server API undocumented beyond code |

## Notes per vendor

### Google Family Link

Limits are per device. Two hours means two hours on each device. The project models budgets per child and declares this as a lossy mapping. Google returns HTTP 200 even when a write does nothing, so every write is followed by a read. Bonus time can be granted while locked. There is no child request queue. Sessions are browser cookies and have lasted months in practice. The live Google session sits inside the auth add-on, so that add-on must not be exposed beyond the LAN.

### Microsoft Family Safety

Instant lock is broken because Microsoft removed or disabled the endpoint. Lock is emulated by saving the schedule and setting every day's allowance to zero, then restoring. This hits Windows and Xbox at once. Some accounts are forced to sign in interactively every 24 hours by a server-side policy, which the maintainer will not bypass. Credentials sit unencrypted in the HA config entry and in backups. This is the most fragile route in the matrix and the adapter must declare that.

### Xbox

Microsoft routes all parental control through Family Safety. Xbox Live itself only offers power off, reboot and presence. Xbox counts time while signed in, even when idle.

### PlayStation

Nothing exists. The honest answer is the manual enforcer: the parent gets a notification telling them what to do in the PlayStation Family app and a done button, and the ledger still counts the minutes. Rest mode via ps5-mqtt plus a network or plug cut-off gives a crude stop. Nobody has published the endpoints behind the PlayStation Family app.

### Nintendo

The only platform already in Home Assistant core. Its entity shape (number for today's limit, switch for suspend, time for bedtime, action for bonus) is the template this project copies. Andy does not own one, so it is a second-phase adapter.

### Network and power layers

These are the only routes that work on every device in the house and depend on no vendor goodwill. They are the recommended default and the first thing shipped. They cannot grant minutes or set allowances. The project pairs them with the local ledger: the ledger counts the minutes, the network or plug enforces the stop.

## Legal position

Google and Microsoft terms forbid reverse engineering and circumventing access restrictions. The project does not reimplement those techniques. It binds to noiwid's integrations when they are installed and credits them. The README must say that those two paths may breach vendor terms and may stop working at any time. The core, the network and power enforcers, the Nintendo adapter and the community layer carry no such risk.
