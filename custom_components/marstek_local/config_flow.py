"""Config flow for Marstek Local API."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .api import MarstekClient, MarstekError
from .const import DEFAULT_PORT, DOMAIN


class MarstekConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = MarstekClient(user_input[CONF_HOST], user_input[CONF_PORT])
            try:
                device = await client.get_device()
            except MarstekError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(device["ble_mac"])
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    }
                )
                name = device.get("device", "Marstek")
                return self.async_create_entry(
                    title=f"{name} ({user_input[CONF_HOST]})", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )
