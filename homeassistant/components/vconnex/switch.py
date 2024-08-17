"""Support for Vconnex Switch."""

from __future__ import annotations

import logging
from typing import Any

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CommandName, DispatcherSignal
from .entity import VconnexEntity, VconnexParamDescription
from .vconnex_wrap import HomeAssistantVconnexData

_LOGGER = logging.getLogger(__name__)

_KEY__ENTITY_CONFIGS = "entity_configs"
_KEY__PARAM_DESC = "param_desc"
_KEY__ENTITY_DESC = "entity_desc"
_KEY__DEVICE_CLASS = "device_class"

_ENTITY_CONFIG_MAP = {
    3010: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("vconnex_switch_3_1"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("vconnex_switch_3_2"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("vconnex_switch_3_3"),
            },
        ]
    },
    3012: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("vconnex_switch_1_1"),
            },
        ]
    },
    3013: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("vconnex_switch_2_1"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("vconnex_switch_2_2"),
            },
        ]
    },
    3015: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_1"),
            },
        ]
    },
    3016: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_1"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_2"),
            },
        ]
    },
    3017: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_1"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_2"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_3"),
            },
        ]
    },
    3018: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_1"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_2"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_3"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_4"),
            },
        ]
    },
    3043: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_1"),
            },
        ]
    },
    3052: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_1"),
            },
        ]
    },
    3071: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_1"),
            },
        ]
    },
    3072: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_1"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_2"),
            },
        ]
    },
    3076: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SwitchDeviceClass.SWITCH,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("switch_1"),
            },
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
    def on_device_added(
        device_ids: list[str],
    ) -> None:
        """Device added callback."""
        entities: list[VconnexEntity] = []
        for device_id in device_ids:
            if (device := device_manager.get_device(device_id)) is not None:
                if device.deviceTypeCode not in _ENTITY_CONFIG_MAP:
                    continue

                entity_configs = list[dict[str, Any]](
                    _ENTITY_CONFIG_MAP[device.deviceTypeCode].get(_KEY__ENTITY_CONFIGS)
                )
                for entity_config in entity_configs:
                    param_desc: VconnexParamDescription = entity_config.get(
                        _KEY__PARAM_DESC
                    )
                    if (param_info := param_desc.find_device_param(device)) is None:
                        continue

                    entity_desc_dict = {
                        **entity_config.get(_KEY__ENTITY_DESC),
                        "key": f"{device.deviceId}.{param_desc.native_param}",
                        "name": param_info.get("name"),
                    }

                    entities.append(
                        VconnexSwitchEntity(
                            vconnex_device=device,
                            device_manager=device_manager,
                            description=SwitchEntityDescription(**entity_desc_dict),
                            param_desc=param_desc,
                        )
                    )
        if len(entities) > 0:
            async_add_entities(entities)

    entry.async_on_unload(
        async_dispatcher_connect(hass, DispatcherSignal.DEVICE_ADDED, on_device_added)
    )
    on_device_added(device_ids=device_manager.device_map.keys())


class VconnexSwitchEntity(VconnexEntity, SwitchEntity):
    """Vconnex Switch Device."""

    def __init__(
        self,
        vconnex_device: VconnexDevice,
        device_manager: VconnexDeviceManager,
        description: SwitchEntityDescription,
        param_desc: VconnexParamDescription,
    ) -> None:
        """Create Vconnex Switch Entity object."""
        super().__init__(
            vconnex_device=vconnex_device,
            device_manager=device_manager,
            description=description,
        )
        self.param_desc = param_desc

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.get_param_value(CommandName.GET_DATA, self.param_desc) != 0

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        self._send_command(CommandName.SET_DATA, {self.param_desc.native_param: 1})

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        self._send_command(CommandName.SET_DATA, {self.param_desc.native_param: 0})
