"""Number entities holding the passive mode settings."""

from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.const import UnitOfPower, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MarstekConfigEntry
from .const import MAX_POWER
from .coordinator import MarstekCoordinator
from .entity import MarstekEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [MarstekPassivePower(coordinator), MarstekPassiveDuration(coordinator)]
    )


class MarstekPassivePower(MarstekEntity, NumberEntity):
    """Target power for passive mode. Positive = discharge, negative = charge.

    Only stored locally; applied by the "Activate passive mode" button.
    """

    _attr_translation_key = "passive_power"
    _attr_device_class = NumberDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_native_min_value = -MAX_POWER
    _attr_native_max_value = MAX_POWER
    _attr_native_step = 10
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: MarstekCoordinator) -> None:
        super().__init__(coordinator, "passive_power")

    @property
    def native_value(self) -> float:
        return self.coordinator.passive_power

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.passive_power = int(value)
        self.async_write_ha_state()


class MarstekPassiveDuration(MarstekEntity, NumberEntity):
    """Countdown (seconds) after which passive mode ends."""

    _attr_translation_key = "passive_duration"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_native_min_value = 1
    _attr_native_max_value = 86400
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: MarstekCoordinator) -> None:
        super().__init__(coordinator, "passive_duration")

    @property
    def native_value(self) -> float:
        return self.coordinator.passive_duration

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.passive_duration = int(value)
        self.async_write_ha_state()
