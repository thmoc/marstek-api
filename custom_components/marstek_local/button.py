"""Button that activates passive mode with the configured power and duration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MarstekConfigEntry
from .api import MarstekError
from .coordinator import MarstekCoordinator
from .entity import MarstekEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MarstekActivatePassive(entry.runtime_data)])


class MarstekActivatePassive(MarstekEntity, ButtonEntity):
    _attr_translation_key = "activate_passive"

    def __init__(self, coordinator: MarstekCoordinator) -> None:
        super().__init__(coordinator, "activate_passive")

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.set_passive(
                self.coordinator.passive_power, self.coordinator.passive_duration
            )
        except MarstekError as err:
            raise ServiceValidationError(str(err)) from err
        await self.coordinator.async_request_refresh()
