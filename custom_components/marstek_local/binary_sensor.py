"""Binary sensors: charge/discharge permission and CT connection."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MarstekConfigEntry
from .coordinator import MarstekCoordinator
from .entity import MarstekEntity


@dataclass(frozen=True, kw_only=True)
class MarstekBinaryDescription(BinarySensorEntityDescription):
    source: str
    field: str


BINARY_SENSORS: tuple[MarstekBinaryDescription, ...] = (
    MarstekBinaryDescription(
        key="charge_allowed",
        translation_key="charge_allowed",
        source="bat",
        field="charg_flag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MarstekBinaryDescription(
        key="discharge_allowed",
        translation_key="discharge_allowed",
        source="bat",
        field="dischrg_flag",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    MarstekBinaryDescription(
        key="ct_connected",
        translation_key="ct_connected",
        source="mode",
        field="ct_state",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(MarstekBinarySensor(coordinator, d) for d in BINARY_SENSORS)


class MarstekBinarySensor(MarstekEntity, BinarySensorEntity):
    entity_description: MarstekBinaryDescription

    def __init__(
        self, coordinator: MarstekCoordinator, description: MarstekBinaryDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        d = self.entity_description
        value = (self.coordinator.data.get(d.source) or {}).get(d.field)
        return None if value is None else bool(value)
