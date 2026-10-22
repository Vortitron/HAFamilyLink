# Kerb for parents

This page is for the person who sets Kerb up and uses it day to day. Short version: add a child, point Kerb at the switches that can stop their devices, then use the lock switch and the grant buttons.

## Before you start

Kerb does not log in to Google, Microsoft, Sony or Nintendo. In this release it stops a device in one of three ways.

- Network. A switch in Home Assistant that blocks the device at your router, firewall or DNS filter. UniFi, FRITZ!Box, OPNsense, AdGuard Home and Pi-hole all offer one. This is the recommended way. It is instant and works for every platform. Offline games keep running.
- Power. A smart plug. Kerb can ask the device to shut down first (an Xbox remote entity, a media player) and then cut the plug after a delay. Cutting power during an update can corrupt a console, so you opt in per device.
- Manual. Kerb sends you a notification telling you what to do in the vendor's own app, and you press a done button when you have. This is the honest answer for a PlayStation today.

You can combine them. A PS5 with a network switch and manual, an Xbox with a plug, a phone with manual.

You will also want, per device, an entity that is on while the device is in use. A smart plug's power sensor turned into a binary sensor, a media player, or a device tracker all work. Without one, Kerb cannot count minutes for that device.

## Adding a child

Settings, Devices and services, Add integration, Kerb.

1. Name and age band. No date of birth is stored.
2. Devices. For each one: a name, the platform, the network switch or switches, the plug, the entity to turn off gracefully, whether Kerb may cut power, an in-use entity, and whether this device is manual. Tick "add another" to keep going.
3. Guardians and PIN. Pick the Home Assistant users who may lock, unlock and grant. Everyone else is refused. The PIN is optional and applies to everyone, including guardians, so a child who finds the dashboard still cannot unlock themselves. With a PIN set, a guardian types it into the PIN entity first. That arms the dashboard for five minutes.

Then open the integration's Configure page for the weekly allowance, bedtime, a cap on daily grants, and how long Kerb waits for an enforcer to confirm.

Repeat for each child. Each child is their own entry.

## What you get

Every child becomes a device in Home Assistant with these entities.

| Entity | What it means |
|---|---|
| Lock (switch) | On locks every device until the end of the day. Off releases them. The attributes show the reason, when it expires, and one line per device saying what was actually done. |
| PS5 lock, Xbox lock (switch) | The same, for one device. |
| Remaining today (minutes) | Allowance plus grants minus what was used. The confidence attribute says confirmed, assumed or stale. |
| Used today (minutes) | Weighted usage. The attribute lists devices that cannot report which app was used. |
| Status | free, locked, exhausted, bedtime or unknown. |
| Enforcement | confirmed, pending, partial, degraded or unknown. Pending means the writes went out and Kerb is waiting for a read-back or for you to press done. This is the one to watch. |
| Allowance today (number) | Replace today's allowance without changing the weekly rule. |
| Grant 15, 30, 60 minutes (buttons) | One tap. |
| PS5 manual done (button) | Press after you have done the manual step in the vendor app. Never needs the PIN. |
| PIN (text) | Only matters when a PIN is set. Type the PIN here and the switches, buttons and number work for you for five minutes. The field clears itself and the PIN is never stored. |
| Any enforcer degraded (binary sensor) | On when a lock failed, only partly landed, or a switch has gone missing. Not on while a manual step is simply waiting for you. Use it for alerts. |

Unknown means unknown. If the router switch disappears, Kerb will not guess that the child is free or locked. It shows unknown, raises a repair issue, and keeps the lock request on record.

## Day to day

"No screens for an hour": call `kerb.lock` with a duration, or use the lock switch for the rest of the day.

```yaml
action: kerb.lock
data:
  child: Alice
  duration: "01:00:00"
  reason: dinner
```

"Twenty minutes for emptying the dishwasher": press a grant button or call `kerb.grant`.

```yaml
action: kerb.grant
data:
  child: Alice
  minutes: 20
  reason: emptied the dishwasher
```

When the allowance runs out, Kerb locks the devices on its own and the status shows exhausted. A grant lifts that lock. Bedtime locks on its own and lifts in the morning.

Lock, unlock and grant answer with a summary you can show on a dashboard or read out:

```text
PS5 network blocked (network:switch.unifi_block_ps5). PS5 may still run offline games.
PS5 manual action requested (manual:...). PS5 waiting for a parent to press done. Awaiting confirmation.
Xbox powered off (power:switch.plug_xbox).
```

## Blueprints

Import from `blueprints/automation/kerb`.

- Lock a child for a duration from any trigger. Bind a button to an hour of no screens.
- Grant minutes when something happens. Listen for a chore integration's event and add minutes with a reason.

A good third automation: notify yourself when `binary_sensor.<child>_any_enforcer_degraded` has been on for five minutes.

## Children and the dashboard

Home Assistant cannot hide entities from one user and show them to another. Three things help.

1. Children should not have Home Assistant logins. Give them a view-only kiosk dashboard fed by the sensors if they want to see their remaining time.
2. Lock, unlock and grant refuse writes from users who are not guardians.
3. Set a PIN. Then even a guardian's open dashboard refuses the lock switch, the grant buttons and the allowance number until the guardian types the PIN into the PIN entity. The dashboard stays armed for that guardian for five minutes, then asks again. Service calls can carry the PIN in the `pin` field instead. The manual done button never needs it. Automations never need it.

## What Kerb stores

An age band, device names, which entities belong to which device, the daily ledgers (allowance, grants, usage, locks) and the lock and grant records for 31 days, and the hash of the PIN. After 31 days a day's ledger is deleted outright; nothing is summarised or kept. No location, no date of birth, no vendor credentials. Nothing is sent anywhere.

Deleting a child's entry removes everything Kerb holds about them at once. Reloading or restarting keeps it.

Backups. All of this lives in `.storage/kerb.state`, which is inside every Home Assistant backup. A backup is therefore a record of your child's days. Encrypt your backups and keep them where only you can read them. Deleting a child does not reach into backups you already made.

Your child can see it. The ledger is written to be shown: every line says what was granted or used, by whom and why. A kiosk dashboard fed by the sensors gives them their remaining time, and you can read them the ledger on request. For teenagers it is worth agreeing the rules together; Kerb records the decision, it does not make it.
