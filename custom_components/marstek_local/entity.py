"""Base entity."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import MarstekCoordinator


class MarstekEntity(CoordinatorEntity[MarstekCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: MarstekCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device['ble_mac']}_{key}"

    @property
    def device_info(self) -> DeviceInfo:
        return self.coordinator.device_info
