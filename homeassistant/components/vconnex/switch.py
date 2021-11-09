"""Support for Vconnex Switch."""

from __future__ import annotations

import logging
from typing import Any

from vconnex.device import VconnexDevice, VconnexDeviceManager

from homeassistant.components.switch import (
    DEVICE_CLASS_SWITCH,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CommandName, DispatcherSignal, ParamType
from .entity import EntityDescListResolver, EntityDescResolver, VconnexEntity
from .vconnex_wrap import HomeAssistantVconnexData

logger = logging.getLogger(__name__)


DEVICE_TYPE_SET = {3010, 3011, 3012, 3015, 3016, 3017, 3018, 3043}
DEVICE_PARAM_TYPE_SET = {ParamType.ON_OFF}
ENTITY_DESC_RESOLVER = EntityDescResolver.of(
    SwitchEntityDescription
).with_additional_param_value({"device_class": DEVICE_CLASS_SWITCH})

ENTITY_DESC_LIST_RESOLVER_LIST = [
    EntityDescListResolver(DEVICE_TYPE_SET, DEVICE_PARAM_TYPE_SET, ENTITY_DESC_RESOLVER)
]


class VconnexSwitchEntity(VconnexEntity, SwitchEntity):
    """Vconnex Switch Device."""

    def __init__(
        self,
        vconnex_device: VconnexDevice,
        device_manager: VconnexDeviceManager,
        description: SwitchEntityDescription,
    ) -> None:
        """Create Vconnex Switch Entity object."""
        super().__init__(
            vconnex_device=vconnex_device,
            device_manager=device_manager,
            description=description,
        )
        self._attr_unique_id = f"{super().unique_id}.{description.key}"
        self.entity_id = self._attr_unique_id

    @property
    def is_on(self) -> bool:
        """Return true if switch is on."""
        return self.get_data(
            param=self.entity_description.key, converter=lambda val, entity: val != 0
        )

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        self._send_command("CmdSetData", {self.entity_description.key: 1})

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        self._send_command(CommandName.SET_DATA, {self.entity_description.key: 0})


TargetEntity = VconnexSwitchEntity


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
            device = device_manager.device_map.get(device_id)
            if device is not None:
                for description_list_resolver in ENTITY_DESC_LIST_RESOLVER_LIST:
                    description_list = description_list_resolver.from_device(device)
                    if len(description_list) > 0:
                        for description in description_list:
                            entities.append(
                                TargetEntity(
                                    vconnex_device=device,
                                    device_manager=device_manager,
                                    description=description,
                                )
                            )
        async_add_entities(entities)

    async_dispatcher_connect(hass, DispatcherSignal.DEVICE_ADDED, on_device_added)
    on_device_added(device_ids=device_manager.device_map.keys())
