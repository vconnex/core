"""Config flow for Vconnex integration."""
from __future__ import annotations

import logging
from typing import Any

from vconnex.api import VconnexAPI
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PROJECT_NAME,
    CONF_USER_ID,
    DEFAULT_ENDPOINT,
    DOMAIN,
    DOMAIN_NAME,
    PROJECT_CODE,
)

LOGGER = logging.getLogger(__name__)

TOKEN_USER_ID = "userId"
TOKEN_PROJECT_NAME = "projectName"


def validate_input(hass: HomeAssistant, user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    client_id = user_input.get(CONF_CLIENT_ID, "").strip()
    client_secret = user_input.get(CONF_CLIENT_SECRET, "").strip()

    if "" in (client_id, client_secret):
        raise InvalidCredentials

    if (
        DOMAIN in hass.data
        and (datas := hass.data[DOMAIN].values())
        and (client_id in [data.config_data.get(CONF_CLIENT_ID) for data in datas])
    ):
        raise CredentialsUsed

    is_valid_credentials = False
    try:
        api = VconnexAPI(
            DEFAULT_ENDPOINT, client_id, client_secret, project_code=PROJECT_CODE
        )
        is_valid_credentials = api.is_valid()
    except Exception:  # pylint: disable=broad-except
        LOGGER.error("Could not connect to endpoint: %s", DEFAULT_ENDPOINT)
        raise CannotConnect from Exception

    if not is_valid_credentials:
        LOGGER.error("Could not validate user credentials: %s", client_id)
        raise InvalidCredentials

    token_data = api.get_token_data()
    user_id = token_data.get(TOKEN_USER_ID)
    project_name = token_data.get(TOKEN_PROJECT_NAME)
    if (
        DOMAIN in hass.data
        and len(datas := hass.data[DOMAIN].values())
        and (user_id in map(lambda data: data.config_data.get(CONF_USER_ID), datas))
    ):
        raise CredentialsUsed

    return {
        "title": f"[{DOMAIN_NAME}] {project_name}",
        "data": {
            CONF_CLIENT_ID: client_id,
            CONF_CLIENT_SECRET: client_secret,
            CONF_PROJECT_NAME: project_name,
            CONF_USER_ID: user_id,
        },
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vconnex."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Async step user."""
        errors = {}
        if user_input is not None:
            try:
                info = await self.hass.async_add_executor_job(
                    validate_input, self.hass, user_input
                )

                return self.async_create_entry(title=info["title"], data=info["data"])

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidCredentials:
                errors["base"] = "invalid_credentials"
            except CredentialsUsed:
                LOGGER.error("User credentials has been used, please use an other!")
                errors["base"] = "credentials_used"
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        else:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_CLIENT_ID, default=user_input.get(CONF_CLIENT_ID)
                    ): str,
                    vol.Required(
                        CONF_CLIENT_SECRET,
                        default=user_input.get(CONF_CLIENT_SECRET),
                    ): str,
                }
            ),
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class CredentialsUsed(HomeAssistantError):
    """Error to indicate there is credential is used."""


class InvalidCredentials(HomeAssistantError):
    """Error to indicate there is invalid credential."""
