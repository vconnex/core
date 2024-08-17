"""Support for Vconnex Corver."""

from __future__ import annotations

from typing import Any

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityDescription,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CommandName, DispatcherSignal
from .entity import VconnexEntity, VconnexParamDescription
from .vconnex_wrap import HomeAssistantVconnexData

_KEY__ENTITY_CONFIGS = "entity_configs"
_KEY__ENTITY_DESC = "entity_desc"
_KEY__DEVICE_CLASS = "device_class"
_KEY__ENTITY_KEY = "key"
_KEY__OPEN_PARAM_DESC = "open_param_desc"
_KEY__STOP_PARAM_DESC = "stop_param_desc"
_KEY__CLOSE_PARAM_DESC = "close_param_desc"
_KEY__OPEN_LEVEL_PARAM_DESC = "open_level_param_desc"

_ENTITY_CONFIG_MAP = {
    3040: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__ENTITY_KEY: "cover_1",
                    _KEY__DEVICE_CLASS: CoverDeviceClass.CURTAIN,
                },
                _KEY__OPEN_PARAM_DESC: VconnexParamDescription("curtain_open"),
                _KEY__STOP_PARAM_DESC: VconnexParamDescription("curtain_stop"),
                _KEY__CLOSE_PARAM_DESC: VconnexParamDescription("curtain_close"),
                _KEY__OPEN_LEVEL_PARAM_DESC: VconnexParamDescription("open_level"),
            },
        ]
    },
    3041: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__ENTITY_KEY: "cover_1",
                    _KEY__DEVICE_CLASS: CoverDeviceClass.CURTAIN,
                },
                _KEY__OPEN_PARAM_DESC: VconnexParamDescription("curtain_open"),
                _KEY__CLOSE_PARAM_DESC: VconnexParamDescription("curtain_close"),
                _KEY__OPEN_LEVEL_PARAM_DESC: VconnexParamDescription("open_level"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__ENTITY_KEY: "cover_2",
                    _KEY__DEVICE_CLASS: CoverDeviceClass.CURTAIN,
                },
                _KEY__OPEN_PARAM_DESC: VconnexParamDescription("curtain_2_open"),
                _KEY__CLOSE_PARAM_DESC: VconnexParamDescription("curtain_2_close"),
                _KEY__OPEN_LEVEL_PARAM_DESC: VconnexParamDescription("open_2_level"),
            },
        ]
    },
    3042: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__ENTITY_KEY: "cover_motor",
                    _KEY__DEVICE_CLASS: CoverDeviceClass.CURTAIN,
                },
                _KEY__OPEN_PARAM_DESC: VconnexParamDescription("curtain_open"),
                _KEY__STOP_PARAM_DESC: VconnexParamDescription("curtain_stop"),
                _KEY__CLOSE_PARAM_DESC: VconnexParamDescription("curtain_close"),
                _KEY__OPEN_LEVEL_PARAM_DESC: VconnexParamDescription("open_level"),
            }
        ]
    },
    3048: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__ENTITY_KEY: "cover_motor",
                    _KEY__DEVICE_CLASS: CoverDeviceClass.CURTAIN,
                },
                _KEY__OPEN_PARAM_DESC: VconnexParamDescription("curtain_open"),
                _KEY__STOP_PARAM_DESC: VconnexParamDescription("curtain_stop"),
                _KEY__CLOSE_PARAM_DESC: VconnexParamDescription("curtain_close"),
                _KEY__OPEN_LEVEL_PARAM_DESC: VconnexParamDescription("open_level"),
            }
        ]
    },
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Async setup Home Assistant entry."""
    vconnex_data: HomeAssistantVconnexData = hass.data[DOMAIN][entry.entry_id]
    device_manager = vconnex_data.device_manager

    @callback
    def on_device_added(device_ids: list[str]) -> None:
        """Device added callback."""
        entities: list[VconnexEntity] = []
        for device_id in device_ids:
            if (device := device_manager.get_device(device_id)) is not None:
                if device.deviceTypeCode not in _ENTITY_CONFIG_MAP:
                    continue

                entity_configs = list[dict[str, Any]](
                    _ENTITY_CONFIG_MAP[device.deviceTypeCode].get(_KEY__ENTITY_CONFIGS)
                )
                for idx, entity_config in enumerate(entity_configs):
                    open_param_desc: VconnexParamDescription = entity_config.get(
                        _KEY__OPEN_PARAM_DESC, None
                    )
                    close_param_desc: VconnexParamDescription = entity_config.get(
                        _KEY__CLOSE_PARAM_DESC, None
                    )
                    stop_param_desc: VconnexParamDescription = entity_config.get(
                        _KEY__STOP_PARAM_DESC, None
                    )
                    open_level_param_desc: VconnexParamDescription = entity_config.get(
                        _KEY__OPEN_LEVEL_PARAM_DESC, None
                    )

                    entity_desc_dict = entity_config.get(_KEY__ENTITY_DESC)
                    entity_desc_dict["key"] = (
                        f"{device.deviceId}.{entity_desc_dict[_KEY__ENTITY_KEY]}"
                        if _KEY__ENTITY_KEY in entity_desc_dict
                        else device.deviceId
                    )
                    entity_desc_dict["name"] = (
                        f"{device.name} {idx + 1}"
                        if len(entity_configs) > 1
                        else device.name
                    )

                    entities.append(
                        VconnexCoverEntity(
                            vconnex_device=device,
                            device_manager=device_manager,
                            description=CoverEntityDescription(**entity_desc_dict),
                            open_param_desc=open_param_desc,
                            close_param_desc=close_param_desc,
                            open_level_param_desc=open_level_param_desc,
                            stop_param_desc=stop_param_desc,
                        )
                    )
        if len(entities) > 0:
            async_add_entities(entities)

    entry.async_on_unload(
        async_dispatcher_connect(hass, DispatcherSignal.DEVICE_ADDED, on_device_added)
    )
    on_device_added(device_ids=device_manager.device_map.keys())


class VconnexCoverEntity(VconnexEntity, CoverEntity):
    """Vconnex Cover Device."""

    def __init__(
        self,
        vconnex_device: VconnexDevice,
        device_manager: VconnexDeviceManager,
        description: CoverEntityDescription,
        open_param_desc: VconnexParamDescription,
        close_param_desc: VconnexParamDescription,
        open_level_param_desc: VconnexParamDescription,
        stop_param_desc: VconnexParamDescription | None = None,
    ) -> None:
        """Create Vconnex Cover Entity object."""
        super().__init__(
            vconnex_device=vconnex_device,
            device_manager=device_manager,
            description=description,
        )

        self.open_param_desc = open_param_desc
        self.stop_param_desc = stop_param_desc
        self.close_param_desc = close_param_desc
        self.open_level_param_desc = open_level_param_desc
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.SET_POSITION
        )
        if stop_param_desc is not None:
            self._attr_supported_features |= CoverEntityFeature.STOP

    @property
    def current_cover_position(self) -> int | None:
        """Return current position of cover."""
        return self.get_param_value(CommandName.GET_DATA, self.open_level_param_desc)

    @property
    def is_opening(self) -> bool | None:
        """Return if the cover is opening or not."""
        return self.get_param_value(CommandName.GET_DATA, self.open_param_desc) != 0

    @property
    def is_closing(self) -> bool | None:
        """Return if the cover is closing or not."""
        return self.get_param_value(CommandName.GET_DATA, self.close_param_desc) != 0

    @property
    def is_closed(self) -> bool | None:
        """Return if the cover is closed or not."""
        return (
            position == 0
            if (position := self.current_cover_position) is not None
            else None
        )

    def open_cover(self, **kwargs: Any) -> None:
        """Open the cover."""
        self._send_command(CommandName.SET_DATA, {self.open_param_desc.native_param: 1})

    def close_cover(self, **kwargs: Any) -> None:
        """Close cover."""
        self._send_command(
            CommandName.SET_DATA, {self.close_param_desc.native_param: 1}
        )

    def set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        param_dict = dict(kwargs)
        if "position" in param_dict:
            self._send_command(
                CommandName.SET_DATA,
                {self.open_level_param_desc.native_param: param_dict["position"]},
            )

    def stop_cover(self, **kwargs: Any) -> None:
        """Stop the cover."""
        if self.stop_param_desc is not None:
            self._send_command(
                CommandName.SET_DATA, {self.stop_param_desc.native_param: 1}
            )
