"""Test the Vigicrues init."""

from unittest.mock import AsyncMock

from aiohttp import ClientError

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_integration

from tests.common import MockConfigEntry


async def test_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
) -> None:
    """Test successful setup of entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED


async def test_setup_entry_connection_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
) -> None:
    """Test setup failure due to connection error."""
    mock_vigicrues_client.get_station_details.side_effect = ClientError

    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unload_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
) -> None:
    """Test successful unload of entry."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


async def test_coordinator_timeout_error_during_update(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
) -> None:
    """Test that TimeoutError during coordinator update marks entities unavailable."""
    await init_integration(hass, mock_config_entry)
    assert mock_config_entry.state is ConfigEntryState.LOADED

    mock_vigicrues_client.get_latest_observations.side_effect = TimeoutError

    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.paris_seine_water_level")
    assert state is not None
    assert state.state == "unavailable"
