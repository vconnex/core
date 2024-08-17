"""Base entity of Vconnex integration."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any, Generic, TypeVar

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, Entity, EntityDescription
from homeassistant.helpers.typing import UndefinedType

from .const import DOMAIN, DOMAIN_NAME, CommandName, DispatcherSignal

_LOGGER = logging.getLogger(__name__)

EntityDescT = TypeVar("EntityDescT", bound=EntityDescription)


ParamValueType = TypeVar("ParamValueType")
NativeParamValueType = TypeVar("NativeParamValueType")


class VconnexParamDescription(Generic[ParamValueType, NativeParamValueType]):
    """Vconnex param description."""

    def __init__(
        self,
        native_param: str,
        from_native_value: (
            Callable[[NativeParamValueType], ParamValueType] | None
        ) = None,
        to_native_value: Callable[[ParamValueType], NativeParamValueType] | None = None,
        extended_param: bool = False,
    ) -> None:
        """Create device param desctiption."""
        self.native_param = native_param
        self._from_native_value = from_native_value
        self._to_native_value = to_native_value
        self.extended_param = extended_param

    def from_native_value(self, native_value: NativeParamValueType) -> ParamValueType:
        """Convert value from native value."""
        return (
            self._from_native_value(native_value)
            if self._from_native_value is not None
            else native_value
        )

    def to_native_value(self, value: ParamValueType) -> NativeParamValueType:
        """Conver to native value."""
        return (
            self._to_native_value(value) if self._to_native_value is not None else value
        )

    def find_device_param(self, device: VconnexDevice) -> dict[str, Any] | None:
        """Find device param."""
        if device is not None and len(param_info_list := device.params) > 0:
            for param_info in param_info_list:
                if param_info["paramKey"] == self.native_param:
                    return param_info
        return None


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

        self._attr_unique_id = f"{DOMAIN}.{description.key}"
        self.entity_id = self._attr_unique_id

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vconnex_device.deviceId)},
            manufacturer=DOMAIN_NAME,
            name=vconnex_device.name,
            model=vconnex_device.deviceTypeName,
            sw_version=(
                vconnex_device.version if hasattr(vconnex_device, "version") else None
            ),
        )

        self._attr_name = (
            description.name
            if description.name not in (None, UndefinedType)
            else vconnex_device.name
        )
        self._attr_should_poll = False
        self._remove_dispatchers: list[Callable[[None], None]] = []

    @property
    def available(self) -> bool:
        """Get available status."""
        return len(self.vconnex_device.data) > 0

    async def async_added_to_hass(self) -> None:
        """Call when entity is added."""
        self._remove_dispatchers.append(
            async_dispatcher_connect(
                self.hass,
                f"{DispatcherSignal.DEVICE_UPDATED}.{self.vconnex_device.deviceId}",
                self.async_write_ha_state,
            )
        )
        self._remove_dispatchers.append(
            async_dispatcher_connect(
                self.hass,
                f"{DispatcherSignal.DEVICE_REMOVED}.{self.vconnex_device.deviceId}",
                self.async_write_ha_state,
            )
        )
        self._remove_dispatchers.append(
            async_dispatcher_connect(
                self.hass,
                f"{DispatcherSignal.DEVICE_DATA_UPDATED}.{self.vconnex_device.deviceId}",
                self.async_write_ha_state,
            )
        )

    async def async_will_remove_from_hass(self) -> None:
        """Run when entity will be removed from hass."""
        for remove_dispatcher in self._remove_dispatchers:
            remove_dispatcher()

    def _get_device_data(self, name: str) -> Any:
        """Get device data message."""
        try:
            device_data = self.vconnex_device.data
            if name in device_data:
                return self.vconnex_device.data.get(name)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Something went wrong!!!")

        return None

    def get_param_value(
        self, data_name: str, param_desc: VconnexParamDescription
    ) -> Any:
        """Get param value."""
        data_dict = self._get_device_data(data_name)
        if data_dict is not None and "devV" in data_dict:
            param_values = data_dict.get("devV")
            for param_value in param_values:
                if param_value.get("param") == param_desc.native_param:
                    return param_desc.from_native_value(param_value.get("value"))
        return None

    def get_data(
        self, param, converter: Callable[[Any, VconnexEntity], Any] | None = None
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
            _LOGGER.exception("Something went wrong!!!")

        return None

    def _send_command(self, command: str, values: dict[str, Any]) -> None:
        _LOGGER.debug(
            "Sending commands for device %s: %s", self.vconnex_device.deviceId, values
        )
        self.device_manager.send_commands(self.vconnex_device.deviceId, command, values)
