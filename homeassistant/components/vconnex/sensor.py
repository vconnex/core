"""Support for Vconnex Sensor."""

from __future__ import annotations

from collections.abc import Callable
import datetime
import logging
from typing import Any

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    LIGHT_LUX,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN, DispatcherSignal
from .entity import VconnexEntity, VconnexParamDescription
from .vconnex_wrap import HomeAssistantVconnexData

_LOGGER = logging.getLogger(__name__)


_KEY__ENTITY_CONFIGS = "entity_configs"
_KEY__PARAM_DESC = "param_desc"
_KEY__ENTITY_DESC = "entity_desc"
_KEY__DEVICE_CLASS = "device_class"
_KEY__STATE_CLASS = "state_class"
_KEY__NATIVE_UNIT_OF_MEASUREMENT = "native_unit_of_measurement"

_ENTITY_CONFIG_MAP = {
    3009: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.CURRENT,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfElectricCurrent.AMPERE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="Current"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.VOLTAGE,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfElectricPotential.VOLT,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="Voltage"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.POWER,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfPower.WATT,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="Power"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.ENERGY,
                    _KEY__STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="EnergyCount"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.ENERGY,
                    _KEY__STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(
                    native_param="ExportEnergyCount"
                ),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.ENERGY,
                    _KEY__STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(
                    native_param="ConsumptionCountToday", extended_param=True
                ),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.ENERGY,
                    _KEY__STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(
                    native_param="ConsumptionCountThisMonth", extended_param=True
                ),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(
                    native_param="ConsumptionCostThisMonth", extended_param=True
                ),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.ENERGY,
                    _KEY__STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(
                    native_param="ExportCountToday", extended_param=True
                ),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.ENERGY,
                    _KEY__STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(
                    native_param="ExportCountThisMonth", extended_param=True
                ),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(
                    native_param="ExportCostThisMonth", extended_param=True
                ),
            },
        ]
    },
    3020: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="temp"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: PERCENTAGE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="humi"),
            },
        ]
    },
    3029: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.ILLUMINANCE,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: LIGHT_LUX,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="lux"),
            },
        ]
    },
    3049: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.BATTERY,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: PERCENTAGE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="battery"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.SIGNAL_STRENGTH,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="RSSI"),
            },
        ]
    },
    3056: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.BATTERY,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: PERCENTAGE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="battery"),
            },
        ]
    },
    3057: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.BATTERY,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: PERCENTAGE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="battery"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.SIGNAL_STRENGTH,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="RSSI"),
            },
        ]
    },
    3066: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.BATTERY,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: PERCENTAGE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="battery"),
            },
        ]
    },
    3067: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.ILLUMINANCE,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: LIGHT_LUX,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="lux"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.BATTERY,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: PERCENTAGE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="battery"),
            },
        ]
    },
    3076: {
        _KEY__ENTITY_CONFIGS: [
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.CURRENT,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfElectricCurrent.AMPERE,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="current"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.VOLTAGE,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfElectricPotential.VOLT,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="voltage"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.POWER,
                    _KEY__STATE_CLASS: SensorStateClass.MEASUREMENT,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfPower.WATT,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="activepower"),
            },
            {
                _KEY__ENTITY_DESC: {
                    _KEY__DEVICE_CLASS: SensorDeviceClass.ENERGY,
                    _KEY__STATE_CLASS: SensorStateClass.TOTAL_INCREASING,
                    _KEY__NATIVE_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR,
                },
                _KEY__PARAM_DESC: VconnexParamDescription(native_param="energy"),
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
                        VconnexSensorEntity(
                            vconnex_device=device,
                            device_manager=device_manager,
                            description=SensorEntityDescription(**entity_desc_dict),
                            param_desc=param_desc,
                        )
                    )
        if len(entities) > 0:
            async_add_entities(entities)

    entry.async_on_unload(
        async_dispatcher_connect(hass, DispatcherSignal.DEVICE_ADDED, on_device_added)
    )
    on_device_added(device_ids=device_manager.device_map.keys())


class VconnexSensorEntity(VconnexEntity, SensorEntity):
    """Vconnex Sensor Device."""

    def __init__(
        self,
        vconnex_device: VconnexDevice,
        device_manager: VconnexDeviceManager,
        description: SensorEntityDescription,
        param_desc: VconnexParamDescription,
    ) -> None:
        """Create Vconnex Sensor Entity object."""
        super().__init__(
            vconnex_device=vconnex_device,
            device_manager=device_manager,
            description=description,
        )
        # self._attr_unit_of_measurement = description.native_unit_of_measurement
        self.param_desc = param_desc

    @property
    def native_value(self) -> StateType:
        """Get native value of sensor."""
        return self.get_param_value(
            "ExtendedDeviceData" if self.param_desc.extended_param else "CmdGetData",
            self.param_desc,
        )

    @property
    def last_reset(self) -> datetime.datetime | None:
        """The time when an accumulating sensor was initialized."""
        return None

    def _get_extended_data(
        self, param, converter: Callable[[Any, VconnexEntity], Any] | None = None
    ) -> Any:
        """Get data of ExtendedDeviceData message."""
        try:
            data_dict = self._get_device_data("ExtendedDeviceData")
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
