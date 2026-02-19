"""Vigicrues sensor platform."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from vigicrues import StationDetails

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfLength, UnitOfVolumeFlowRate
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import (
    VigicruesConfigEntry,
    VigicruesDataUpdateCoordinator,
    VigicruesStationData,
)
from .entity import VigicruesEntity

# Coordinator is used to centralize the data updates
PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class VigicruesSensorEntityDescription(SensorEntityDescription):
    """Vigicrues sensor entity description."""

    value: Callable[[VigicruesStationData], StateType]
    timestamp: Callable[[VigicruesStationData], datetime | None]
    exists: Callable[[StationDetails], bool]


SENSOR_TYPES: tuple[VigicruesSensorEntityDescription, ...] = (
    VigicruesSensorEntityDescription(
        key="water_level",
        translation_key="water_level",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value=lambda data: data.water_level.value if data.water_level else None,
        timestamp=lambda data: data.water_level.timestamp if data.water_level else None,
        exists=lambda station: station.has_height_data,
    ),
    VigicruesSensorEntityDescription(
        key="water_flow",
        translation_key="water_flow",
        native_unit_of_measurement=UnitOfVolumeFlowRate.CUBIC_METERS_PER_SECOND,
        device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
        value=lambda data: data.water_flow.value if data.water_flow else None,
        timestamp=lambda data: data.water_flow.timestamp if data.water_flow else None,
        exists=lambda station: station.has_flow_data,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VigicruesConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add a Vigicrues sensor entity from a config_entry."""
    coordinator = entry.runtime_data

    async_add_entities(
        VigicruesSensorEntity(coordinator, description)
        for description in SENSOR_TYPES
        if description.exists(coordinator.station_details)
    )


class VigicruesSensorEntity(VigicruesEntity, SensorEntity):
    """Define Vigicrues sensor entity."""

    entity_description: VigicruesSensorEntityDescription

    def __init__(
        self,
        coordinator: VigicruesDataUpdateCoordinator,
        description: VigicruesSensorEntityDescription,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self._attr_unique_id = f"{coordinator.station_id}_{description.key}"
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return self.entity_description.value(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "measurement_time": self.entity_description.timestamp(
                self.coordinator.data
            ),
        }
