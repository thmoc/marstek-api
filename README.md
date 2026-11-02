# Marstek Local API for Home Assistant

Custom integration (HACS) for Marstek batteries (Venus A/C/D/E, E mini) using the
[Marstek Device Local API](https://www.marstek.com) over UDP. Fully local, no cloud.

Developed and tested on a **Venus E 3.0 (firmware 148)**.

## Installation (HACS)

1. HACS → ⋮ → *Custom repositories* → add `https://github.com/thmoc/marstek-api`, type **Integration**.
2. Install **Marstek Local API** and restart Home Assistant.
3. Enable the Local API in the Marstek app (note the UDP port, default `30000`).
4. Settings → Devices & services → *Add integration* → **Marstek Local API**, enter the IP and port.

> Give the battery a static IP / DHCP reservation. Enabling the Local API can disable some built-in device features.

## Entities

Polled every 30 s.

**Battery** (`Bat.GetStatus`): battery level, temperature, remaining capacity, rated capacity,
charging allowed, discharging allowed.

**ES** (`ES.GetStatus` / `ES.GetMode` / `ES.SetMode`):

| Entity | Description |
|---|---|
| Sensors | solar power, grid-tied power, off-grid power, battery power (if reported), total solar / grid in / grid out / load energy, CT total power (+ phases, disabled by default) |
| Operating mode (select) | Auto, AI, Passive, UPS (Manual is set via the action below) |
| Passive power (number) | W; **positive = discharge, negative = charge** (verified on a Venus E 3.0) |
| Passive duration (number) | countdown in seconds |
| Activate passive mode (button) | sends passive power + duration to the battery |

### Actions

- `marstek_local.set_passive_mode` — `power` (W, +discharge / −charge), `duration` (s).
- `marstek_local.set_manual_schedule` — one manual time slot (`time_num`, `start_time`, `end_time`, `days`, `power`, `enable`).

```yaml
action: marstek_local.set_passive_mode
data:
  device_id: <device>
  power: -100      # charge at 100 W
  duration: 60
```

## Notes

- When the passive `duration` ends, the device stays in *Passive* mode but at **0 W** (verified on a Venus E 3.0). Switch back to Auto/AI yourself, e.g. with an automation.
- Power is limited to ±2500 W in the integration.
- CT values (`CT total power`, phases) are only reported by the device in Auto/AI mode.
- UDP is lossy: requests are retried up to 3 times; a single missed answer keeps the previous value.
- Unofficial, use at your own risk (see the disclaimer in Marstek's API documentation).
