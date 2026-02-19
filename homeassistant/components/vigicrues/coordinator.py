"""Data Update Coordinator for Vigicrues integration."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from aiohttp import ClientError
from vigicrues import Observation, StationDetails, Vigicrues

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class VigicruesStationData:
    """Data for a Vigicrues station."""

    station: StationDetails
    water_level: Observation | None
    water_flow: Observation | None


type VigicruesConfigEntry = ConfigEntry[VigicruesDataUpdateCoordinator]


class VigicruesDataUpdateCoordinator(DataUpdateCoordinator[VigicruesStationData]):
    """Class to manage fetching Vigicrues data."""

    config_entry: VigicruesConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: VigicruesConfigEntry,
        client: Vigicrues,
        station_id: str,
        station_details: StationDetails,
    ) -> None:
        """Initialize."""
        self.client = client
        self.station_id = station_id
        self.station_details = station_details
        self.device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, station_id)},
            manufacturer="Vigicrues",
            name=station_details.name,
            model=station_details.river,
            configuration_url=f"https://www.vigicrues.gouv.fr/station/{station_id}",
        )

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> VigicruesStationData:
        """Update data via library."""
        water_level: Observation | None = None
        water_flow: Observation | None = None

        if self.station_details.has_height_data:
            try:
                water_level = await self.client.get_latest_observations(
                    self.station_id, "H"
                )
            except (ClientError, TimeoutError, ValueError) as err:
                raise UpdateFailed(
                    f"Failed to fetch water level for station {self.station_id}: {err}"
                ) from err

        if self.station_details.has_flow_data:
            try:
                water_flow = await self.client.get_latest_observations(
                    self.station_id, "Q"
                )
            except (ClientError, TimeoutError, ValueError) as err:
                raise UpdateFailed(
                    f"Failed to fetch water flow for station {self.station_id}: {err}"
                ) from err

        return VigicruesStationData(
            station=self.station_details,
            water_level=water_level,
            water_flow=water_flow,
        )
