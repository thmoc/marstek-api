"""Operating mode select (ES.GetMode / ES.SetMode)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import MarstekConfigEntry
from .api import MarstekError
from .const import MODE_AI, MODE_AUTO, MODE_MANUAL, MODE_PASSIVE, MODE_UPS, MODES
from .coordinator import MarstekCoordinator
from .entity import MarstekEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MarstekConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([MarstekModeSelect(entry.runtime_data)])


class MarstekModeSelect(MarstekEntity, SelectEntity):
    _attr_translation_key = "operating_mode"
    _attr_options = MODES

    def __init__(self, coordinator: MarstekCoordinator) -> None:
        super().__init__(coordinator, "operating_mode")

    @property
    def current_option(self) -> str | None:
        mode = (self.coordinator.data.get("mode") or {}).get("mode")
        if not mode:
            return None
        for option in MODES:
            if option.lower() == str(mode).lower():
                return option
        return None

    async def async_select_option(self, option: str) -> None:
        client = self.coordinator.client
        if option == MODE_MANUAL:
            raise ServiceValidationError(
                "Manual mode needs a schedule: use the marstek_local.set_manual_schedule action"
            )
        try:
            if option == MODE_AUTO:
                await client.set_auto()
            elif option == MODE_AI:
                await client.set_ai()
            elif option == MODE_UPS:
                await client.set_ups()
            elif option == MODE_PASSIVE:
                await client.set_passive(
                    self.coordinator.passive_power, self.coordinator.passive_duration
                )
        except MarstekError as err:
            raise ServiceValidationError(str(err)) from err
        await self.coordinator.async_request_refresh()
