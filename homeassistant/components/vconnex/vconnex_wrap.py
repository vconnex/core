"""The Vconnex wrap."""
from __future__ import annotations

import logging
from typing import Any, NamedTuple

from vconnex.api import VconnexAPI
from vconnex.device import VconnexDevice, VconnexDeviceListener, VconnexDeviceManager

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry
from homeassistant.helpers.dispatcher import dispatcher_send

from .const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DEFAULT_ENDPOINT,
    DOMAIN,
    PROJECT_CODE,
    CommandName,
    DispatcherSignal,
)

LOGGER = logging.getLogger(__name__)


class HomeAssistantVconnexData(NamedTuple):
    """Home Assistant data for Vconnex domain."""

    config_data: dict[str, Any]
    device_manager: VconnexDeviceManager


async def init_sdk(
    hass: HomeAssistant, entry: ConfigEntry
) -> HomeAssistantVconnexData | None:
    """Init vconnex sdk."""
    api = VconnexAPI(
        endpoint=DEFAULT_ENDPOINT,
        client_id=entry.data[CONF_CLIENT_ID],
        client_secret=entry.data[CONF_CLIENT_SECRET],
        project_code=PROJECT_CODE,
    )

    if not await hass.async_add_executor_job(api.is_valid):
        LOGGER.error("Cannot connect!")
        return None

    device_manager = VconnexDeviceManager(api)
    await hass.async_add_executor_job(device_manager.initialize)

    if not device_manager.is_initialized():
        LOGGER.error(
            "Could not initialize! Please reload integration or restart the server"
        )
        return None

    hass.async_add_executor_job(
        retrieve_device_data,
        device_manager.device_map.values(),
        device_manager,
    )

    device_manager.add_device_listener(DeviceListener(hass, device_manager))

    config_data = dict(entry.data)
    config_data.pop(CONF_CLIENT_SECRET, None)

    return HomeAssistantVconnexData(
        config_data=config_data, device_manager=device_manager
    )


def release_sdk(data: HomeAssistantVconnexData):
    """Release Vconnex sdk."""
    try:
        data.device_manager.release()
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Oops, something went wrong!")


def retrieve_device_data(
    device_list: list[VconnexDevice], device_manager: VconnexDeviceManager
):
    """Retrieve all device data."""
    if list is not None:
        for device in device_list:
            try:
                device_manager.send_commands(
                    device.deviceId, CommandName.GET_DATA, {"all": 1}
                )
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Request command failure")


class DeviceListener(VconnexDeviceListener):
    """DeviceListener for HomeAssistan."""

    def __init__(
        self, hass: HomeAssistant, device_manager: VconnexDeviceManager
    ) -> None:
        """Init new Device Listener object."""
        self.hass = hass
        self.device_manager = device_manager

    def on_device_added(self, device: VconnexDevice):
        """On device added callback."""
        dispatcher_send(
            self.hass, f"{DispatcherSignal.DEVICE_ADDED}", [device.deviceId]
        )
        retrieve_device_data([device], self.device_manager)

    def on_device_removed(self, device: VconnexDevice):
        """On device removed callback."""
        dispatcher_send(
            self.hass, f"{DispatcherSignal.DEVICE_REMOVED}.{device.deviceId}"
        )
        self.hass.add_job(self.remove_device_entry, device)

    def on_device_update(
        self, new_device: VconnexDevice, old_device: VconnexDevice = None
    ):
        """On device update callback."""
        dispatcher_send(
            self.hass, f"{DispatcherSignal.DEVICE_UPDATED}.{new_device.deviceId}"
        )

    @callback
    async def remove_device_entry(self, device: VconnexDevice):
        """Remove device entry."""
        device_reg = device_registry.async_get(self.hass)
        device_entry = device_reg.async_get_device(
            identifiers={(DOMAIN, device.deviceId)}
        )
        if device_entry is not None:
            device_reg.async_remove_device(device_entry.id)
