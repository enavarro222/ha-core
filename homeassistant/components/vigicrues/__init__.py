"""The Vigicrues integration."""

from __future__ import annotations

import logging

from aiohttp import ClientError
from vigicrues import Vigicrues

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_STATION_ID, DOMAIN
from .coordinator import VigicruesConfigEntry, VigicruesDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: VigicruesConfigEntry) -> bool:
    """Set up Vigicrues from a config entry."""
    station_id: str = entry.data[CONF_STATION_ID]

    _LOGGER.debug("Using hydrological station ID: %s", station_id)

    client_session = async_get_clientsession(hass)

    try:
        client = Vigicrues(client_session)
        station_details = await client.get_station_details(station_id)
    except (ClientError, TimeoutError, ValueError) as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={
                "entry": entry.title,
                "error": repr(err),
            },
        ) from err

    coordinator = VigicruesDataUpdateCoordinator(
        hass, entry, client, station_id, station_details
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: VigicruesConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
