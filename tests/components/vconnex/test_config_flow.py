"""Test the Vconnex config flow."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.vconnex.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_PROJECT_NAME,
    CONF_USER_ID,
    DOMAIN,
    DOMAIN_NAME,
)
from homeassistant.components.vconnex.vconnex_wrap import HomeAssistantVconnexData
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import RESULT_TYPE_CREATE_ENTRY, RESULT_TYPE_FORM

TEST_CLIENT_ID = "1234"
TEST_CLIENT_SECRET = "1234abc"
INPUT_DATA = {
    CONF_CLIENT_ID: TEST_CLIENT_ID,
    CONF_CLIENT_SECRET: TEST_CLIENT_SECRET,
}

TEST_PROJECT_NAME = "test"
TEST_USER_ID = 1
RESP_TOKEN_DATA = {
    "userId": TEST_USER_ID,
    "projectName": TEST_PROJECT_NAME,
}

CONFIG_RETURN_DATA = {
    CONF_CLIENT_ID: TEST_CLIENT_ID,
    CONF_CLIENT_SECRET: TEST_CLIENT_SECRET,
    CONF_USER_ID: TEST_USER_ID,
    CONF_PROJECT_NAME: TEST_PROJECT_NAME,
}


async def test_flow_success(
    hass: HomeAssistant,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.vconnex.config_flow.VconnexAPI.is_valid",
        return_value=True,
    ), patch(
        "homeassistant.components.vconnex.config_flow.VconnexAPI.get_token_data",
        return_value=RESP_TOKEN_DATA,
    ), patch(
        "homeassistant.components.vconnex.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            INPUT_DATA,
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == f"[{DOMAIN_NAME}] {TEST_PROJECT_NAME}"
    assert result2["data"] == CONFIG_RETURN_DATA


async def test_form_invalid_input(
    hass: HomeAssistant,
) -> None:
    """Test we handle invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.vconnex.config_flow.VconnexAPI.is_valid",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLIENT_ID: " ",
                CONF_CLIENT_SECRET: "  ",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "invalid_credentials"}


async def test_form_invalid_credential(
    hass: HomeAssistant,
) -> None:
    """Test we handle invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.vconnex.config_flow.VconnexAPI.is_valid",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            INPUT_DATA,
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "invalid_credentials"}


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.vconnex.config_flow.VconnexAPI.is_valid",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            INPUT_DATA,
        )

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_runtime_exception(hass: HomeAssistant) -> None:
    """Test we handle credentials in used."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.vconnex.config_flow.validate_input",
        side_effect=Exception,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            INPUT_DATA,
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_credential_used__client_id(hass: HomeAssistant) -> None:
    """Test we handle credentials in used."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    hass.data[DOMAIN] = {
        "12345": HomeAssistantVconnexData(
            config_data=CONFIG_RETURN_DATA, device_manager=None
        )
    }
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        INPUT_DATA,
    )
    await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "credentials_used"}


async def test_form_credential_used__user_id(hass: HomeAssistant) -> None:
    """Test we handle credentials in used."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] == {}

    config_data = dict(CONFIG_RETURN_DATA)
    config_data[CONF_CLIENT_ID] = CONFIG_RETURN_DATA[CONF_CLIENT_ID] + "1"
    hass.data[DOMAIN] = {
        "12345": HomeAssistantVconnexData(config_data=config_data, device_manager=None)
    }

    with patch(
        "homeassistant.components.vconnex.config_flow.VconnexAPI.is_valid",
        return_value=True,
    ), patch(
        "homeassistant.components.vconnex.config_flow.VconnexAPI.get_token_data",
        return_value=RESP_TOKEN_DATA,
    ), patch(
        "homeassistant.components.vconnex.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            INPUT_DATA,
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "credentials_used"}
