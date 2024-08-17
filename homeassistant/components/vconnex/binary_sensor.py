"""Support for Vconnex Sensor."""

from __future__ import annotations

from typing import Any

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CommandName, DispatcherSignal
from .entity import VconnexEntity, VconnexParamDescription
from .vconnex_wrap import HomeAssistantVconnexData

_KEY__ENTITY_CONFIGS = "entity_configs"
_KEY__PARAM_DESC = "param_desc"
_KEY__ENTITY_DESC = "entity_desc"
_KEY__DEVICE_CLASS = "device_class"


_ENTITY_CONFIG_MAP = {
    3024: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.PROBLEM,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("waterLeak"),
            }
        ]
    },
    3027: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.GAS,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("gasLeak"),
            }
        ]
    },
    3028: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.SMOKE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("smokeAlarm"),
            }
        ]
    },
    3029: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.MOTION,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("motion"),
            }
        ]
    },
    3043: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.SAFETY,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("eleak"),
            }
        ]
    },
    3049: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.SMOKE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("smokeAlarm"),
            }
        ]
    },
    3052: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.SAFETY,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("eleak"),
            }
        ]
    },
    3056: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.SMOKE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("smokeAlarm"),
            }
        ]
    },
    3057: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.SMOKE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("smokeAlarm"),
            }
        ]
    },
    3066: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.DOOR,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("door"),
            }
        ]
    },
    3067: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: BinarySensorDeviceClass.MOTION,
                },
                _KEY__PARAM_DESC: VconnexParamDescription("motion"),
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
                        VconnexBinarySensorEntity(
                            vconnex_device=device,
                            device_manager=device_manager,
                            description=BinarySensorEntityDescription(
                                **entity_desc_dict
                            ),
                            param_desc=param_desc,
                        )
                    )
        if len(entities) > 0:
            async_add_entities(entities)

    entry.async_on_unload(
        async_dispatcher_connect(hass, DispatcherSignal.DEVICE_ADDED, on_device_added)
    )
    on_device_added(device_ids=device_manager.device_map.keys())


class VconnexBinarySensorEntity(VconnexEntity, BinarySensorEntity):
    """Vconnex Binary Sensor Device."""

    def __init__(
        self,
        vconnex_device: VconnexDevice,
        device_manager: VconnexDeviceManager,
        description: BinarySensorEntityDescription,
        param_desc: VconnexParamDescription,
    ) -> None:
        """Create Vconnex Binary Sensor Entity object."""
        super().__init__(
            vconnex_device=vconnex_device,
            device_manager=device_manager,
            description=description,
        )
        self.param_desc = param_desc

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        return self.get_param_value(CommandName.GET_DATA, self.param_desc) != 0
