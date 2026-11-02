"""Data update coordinator for Marstek Local API."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MarstekClient, MarstekError
from .const import DEFAULT_PASSIVE_DURATION, DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class MarstekCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls battery, ES status and ES mode."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: MarstekClient,
        device: dict[str, Any],
    ) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, config_entry=entry, update_interval=SCAN_INTERVAL
        )
        self.client = client
        self.device = device
        # Values used by the "activate passive mode" button.
        self.passive_power = 0
        self.passive_duration = DEFAULT_PASSIVE_DURATION

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.device["ble_mac"])},
            manufacturer="Marstek",
            model=self.device.get("device"),
            name=self.device.get("device", "Marstek"),
            sw_version=str(self.device.get("ver")),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        data = dict(self.data) if self.data else {}
        errors = 0
        for key, call in (
            ("bat", self.client.get_battery_status),
            ("es", self.client.get_es_status),
            ("mode", self.client.get_es_mode),
        ):
            try:
                data[key] = await call()
            except MarstekError as err:
                errors += 1
                _LOGGER.debug("Update of %s failed: %s", key, err)
        if errors == 3:
            raise UpdateFailed("Device did not answer")
        return data
