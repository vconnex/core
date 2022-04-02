"""Base entity of Vconnex integration."""
from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any, Generic, TypeVar

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, Entity, EntityDescription

from .const import DOMAIN, DOMAIN_NAME, CommandName, DispatcherSignal

LOGGER = logging.getLogger(__name__)

EntityDescT = TypeVar("EntityDescT", bound=EntityDescription)


class EntityDescResolver(Generic[EntityDescT]):
    """Entity Description Resolver."""

    def __init__(self, class_type: type[EntityDescT]) -> None:
        """Create Entity Description Resolver object."""
        self.__cls = class_type
        self._additional_param_value: dict = {}
        self._additional_param_func: Callable[
            [dict, VconnexDevice], dict | None
        ] | None = None

    def set_additional_param_value(self, param_values: dict) -> None:
        """Set additional param value."""
        self._additional_param_value.clear()
        if param_values is not None:
            self._additional_param_value.update(param_values)

    def _process_param(
        self, param_dict: dict[str, Any], device: VconnexDevice | None = None
    ) -> dict[str, Any] | None:
        """Delete or change attribute of param."""
        if any(key not in param_dict for key in ("paramKey", "name")):
            return None

        new_param_dict = {}

        new_param_dict["key"] = param_dict["paramKey"]
        new_param_dict["name"] = param_dict["name"]

        new_param_dict.update(self._additional_param_value)

        return (
            new_param_dict
            if self._additional_param_func is None
            else self._additional_param_func(new_param_dict, device)
        )

    def with_additional_param_value(self, param_values: dict) -> EntityDescResolver:
        """Set additional param value dict."""
        self.set_additional_param_value(param_values)
        return self

    def with_additional_param_func(
        self, func: Callable[[dict, VconnexDevice], dict]
    ) -> EntityDescResolver:
        """Set additional param function."""
        self._additional_param_func = func
        return self

    def from_param(
        self, param_dict: dict, device: VconnexDevice = None
    ) -> EntityDescT | None:
        """Get Entity Description from param dict."""
        new_param_dict = self._process_param(param_dict, device)
        if new_param_dict is not None:
            return self.__cls(**new_param_dict)
        return None

    @staticmethod
    def of(  # pylint: disable=invalid-name
        cls_type: type[EntityDescT],
    ) -> EntityDescResolver:
        """Create Entity Description Resolver instance."""
        return EntityDescResolver(cls_type)


class EntityDescListResolver:
    """Entity Description List Resolver."""

    def __init__(
        self,
        device_types: set[int],
        param_types: set[int],
        resolver: EntityDescResolver,
    ) -> None:
        """Create Entity Description List Resolver object."""
        self._accept_device_types = device_types
        self._accept_param_types = param_types
        self._entity_desc_resolver: EntityDescResolver = resolver

    def from_device(self, device: VconnexDevice) -> list:
        """Get Description Entity List from device."""
        if int(device.deviceTypeCode) in self._accept_device_types:
            if device is not None and len(param_list := device.params) > 0:
                description_list = []
                for param in param_list:
                    if (
                        len(self._accept_param_types) == 0
                        or int(param.get("type", 0)) in self._accept_param_types
                    ):
                        description = self._entity_desc_resolver.from_param(
                            param, device
                        )
                        if description is not None:
                            description_list.append(description)
                return description_list
        return []


class VconnexEntity(Entity):
    """Vconnex Entity."""

    def __init__(
        self,
        vconnex_device: VconnexDevice,
        device_manager: VconnexDeviceManager,
        description: EntityDescription,
    ) -> None:
        """Create base entity object."""
        self.vconnex_device = vconnex_device
        self.device_manager = device_manager
        self.entity_description = description

        self._attr_unique_id = f"{DOMAIN}.{vconnex_device.deviceId}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vconnex_device.deviceId)},
            manufacturer=DOMAIN_NAME,
            name=vconnex_device.name,
            model=f"[{vconnex_device.deviceTypeCode}] {vconnex_device.deviceTypeName}",
            sw_version=(
                vconnex_device.version if hasattr(vconnex_device, "version") else None
            ),
        )

        if description is not None and description.name is not None:
            self._attr_name = f"[{vconnex_device.name}] {description.name}"
        else:
            self._attr_name = vconnex_device.name

    @property
    def available(self) -> bool:
        """Get available status."""
        return len(self.vconnex_device.data) > 0

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""
        async_dispatcher_connect(
            self.hass,
            f"{DispatcherSignal.DEVICE_UPDATED}.{self.vconnex_device.deviceId}",
            self.async_write_ha_state,
        )

        async_dispatcher_connect(
            self.hass,
            f"{DispatcherSignal.DEVICE_REMOVED}.{self.vconnex_device.deviceId}",
            self.async_write_ha_state,
        )

    def _get_device_data(self, name: str) -> Any:
        """Get device data message."""
        try:
            device_data = self.vconnex_device.data
            if name in device_data:
                return self.vconnex_device.data.get(name)
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Something went wrong!!!")

        return None

    def get_data(
        self, param, converter: Callable[[Any, VconnexEntity], Any] = None
    ) -> Any:
        """Get data of CmdGetData message."""
        try:
            data_dict = self._get_device_data(CommandName.GET_DATA)
            if data_dict is not None and "devV" in data_dict:
                d_values = data_dict.get("devV")
                for d_value in d_values:
                    if d_value.get("param") == param:
                        param_value = d_value.get("value")
                        return (
                            param_value
                            if converter is None
                            else converter(param_value, self)
                        )
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Something went wrong!!!")

        return None

    def _send_command(self, command: str, values: dict[str, Any]) -> None:
        LOGGER.debug(
            "Sending commands for device %s: %s", self.vconnex_device.deviceId, values
        )
        self.device_manager.send_commands(self.vconnex_device.deviceId, command, values)
