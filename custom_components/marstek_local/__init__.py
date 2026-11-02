"""Marstek Local API integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr

from .api import MarstekClient, MarstekError
from .const import DOMAIN, MAX_POWER, SERVICE_SET_MANUAL, SERVICE_SET_PASSIVE
from .coordinator import MarstekCoordinator

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.BUTTON,
]

type MarstekConfigEntry = ConfigEntry[MarstekCoordinator]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

PASSIVE_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("power"): vol.All(
            vol.Coerce(int), vol.Range(min=-MAX_POWER, max=MAX_POWER)
        ),
        vol.Optional("duration", default=300): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=86400)
        ),
    }
)

MANUAL_SCHEMA = vol.Schema(
    {
        vol.Required("device_id"): cv.string,
        vol.Required("time_num"): vol.All(vol.Coerce(int), vol.Range(min=0, max=9)),
        vol.Required("start_time"): cv.string,
        vol.Required("end_time"): cv.string,
        vol.Optional("days", default=DAYS): vol.All(cv.ensure_list, [vol.In(DAYS)]),
        vol.Required("power"): vol.All(
            vol.Coerce(int), vol.Range(min=-MAX_POWER, max=MAX_POWER)
        ),
        vol.Optional("enable", default=True): cv.boolean,
        vol.Optional("manual_set"): vol.All(vol.Coerce(int), vol.Range(min=0, max=3)),
    }
)


def _coordinator_for(hass: HomeAssistant, device_id: str) -> MarstekCoordinator:
    device = dr.async_get(hass).async_get(device_id)
    if device:
        for entry_id in device.config_entries:
            entry = hass.config_entries.async_get_entry(entry_id)
            if entry and entry.domain == DOMAIN and hasattr(entry, "runtime_data"):
                return entry.runtime_data
    raise ServiceValidationError("Device is not a loaded Marstek Local API device")


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    async def passive(call: ServiceCall) -> None:
        coord = _coordinator_for(hass, call.data["device_id"])
        try:
            await coord.client.set_passive(call.data["power"], call.data["duration"])
        except MarstekError as err:
            raise ServiceValidationError(str(err)) from err
        await coord.async_request_refresh()

    async def manual(call: ServiceCall) -> None:
        coord = _coordinator_for(hass, call.data["device_id"])
        d = call.data
        cfg = {
            "time_num": d["time_num"],
            "start_time": d["start_time"],
            "end_time": d["end_time"],
            "week_set": sum(1 << DAYS.index(day) for day in set(d["days"])),
            "power": d["power"],
            "enable": 1 if d["enable"] else 0,
        }
        if "manual_set" in d:
            cfg["manual_set"] = d["manual_set"]
        try:
            await coord.client.set_manual(cfg)
        except MarstekError as err:
            raise ServiceValidationError(str(err)) from err
        await coord.async_request_refresh()

    hass.services.async_register(DOMAIN, SERVICE_SET_PASSIVE, passive, PASSIVE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_SET_MANUAL, manual, MANUAL_SCHEMA)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MarstekConfigEntry) -> bool:
    client = MarstekClient(entry.data[CONF_HOST], entry.data[CONF_PORT])
    try:
        device = await client.get_device()
    except MarstekError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = MarstekCoordinator(hass, entry, client, device)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MarstekConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
