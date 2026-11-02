"""Sensors: Battery (Bat.GetStatus), ES (ES.GetStatus) and CT power (ES.GetMode)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MarstekConfigEntry
from .coordinator import MarstekCoordinator
from .entity import MarstekEntity


@dataclass(frozen=True, kw_only=True)
class MarstekSensorDescription(SensorEntityDescription):
    source: str  # key in coordinator.data: "bat", "es" or "mode"
    field: str
    scale: float | None = None


def _power(key: str, source: str, field: str, **kw: Any) -> MarstekSensorDescription:
    return MarstekSensorDescription(
        key=key,
        source=source,
        field=field,
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        **kw,
    )


def _energy(key: str, field: str, scale: float | None = None) -> MarstekSensorDescription:
    return MarstekSensorDescription(
        key=key,
        translation_key=key,
        source="es",
        field=field,
        scale=scale,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
    )


SENSORS: tuple[MarstekSensorDescription, ...] = (
    # Battery
    MarstekSensorDescription(
        key="battery_soc",
        translation_key="battery_soc",
        source="bat",
        field="soc",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MarstekSensorDescription(
        key="battery_temperature",
        translation_key="battery_temperature",
        source="bat",
        field="bat_temp",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MarstekSensorDescription(
        key="battery_remaining_capacity",
        translation_key="battery_remaining_capacity",
        source="bat",
        field="bat_capacity",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MarstekSensorDescription(
        key="battery_rated_capacity",
        translation_key="battery_rated_capacity",
        source="bat",
        field="rated_capacity",
        device_class=SensorDeviceClass.ENERGY_STORAGE,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # ES
    _power("pv_power", "es", "pv_power", translation_key="pv_power"),
    _power("ongrid_power", "es", "ongrid_power", translation_key="ongrid_power"),
    _power("offgrid_power", "es", "offgrid_power", translation_key="offgrid_power"),
    _power("battery_power", "es", "bat_power", translation_key="battery_power"),
    # total_pv_energy is reported in 0.01 kWh = 10 Wh
    _energy("total_pv_energy", "total_pv_energy", scale=10),
    _energy("total_grid_output_energy", "total_grid_output_energy"),
    _energy("total_grid_input_energy", "total_grid_input_energy"),
    _energy("total_load_energy", "total_load_energy"),
    # CT (from ES.GetMode; only reported in Auto/AI mode)
    _power("ct_total_power", "mode", "total_power", translation_key="ct_total_power"),
    _power(
        "ct_phase_a_power",
        "mode",
        "a_power",
        translation_key="ct_phase_a_power",
        entity_registry_enabled_default=False,
    ),
    _power(
        "ct_phase_b_power",
        "mode",
        "b_power",
        translation_key="ct_phase_b_power",
        entity_registry_enabled_default=False,
    ),
    _power(
        "ct_phase_c_power",
        "mode",
        "c_power",
        translation_key="ct_phase_c_power",
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    es = coordinator.data.get("es") or {}
    async_add_entities(
        MarstekSensor(coordinator, d)
        for d in SENSORS
        # Not every model reports battery power in ES.GetStatus
        if d.key != "battery_power" or "bat_power" in es
    )


class MarstekSensor(MarstekEntity, SensorEntity):
    entity_description: MarstekSensorDescription

    def __init__(
        self, coordinator: MarstekCoordinator, description: MarstekSensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        d = self.entity_description
        value = (self.coordinator.data.get(d.source) or {}).get(d.field)
        if value is None:
            return None
        return value * d.scale if d.scale else value
