"""Test the Vigicrues sensor platform."""

from unittest.mock import AsyncMock

import pytest
from syrupy.assertion import SnapshotAssertion
from vigicrues import StationDetails

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import init_integration

from tests.common import MockConfigEntry, snapshot_platform


async def test_entities(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
    entity_registry: er.EntityRegistry,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
) -> None:
    """Test sensor entity states and attributes."""
    await init_integration(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


async def test_sensor_no_height_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
) -> None:
    """Test that water level sensor is not created when station has no height data."""
    mock_vigicrues_client.get_station_details.return_value = StationDetails(
        id="A123456789",
        name="Paris - Seine",
        river="Seine",
        city="Paris",
        latitude=48.8566,
        longitude=2.3522,
        picture_url=None,
        commune_code="75056",
        is_prediction_station=True,
        has_height_data=False,
        has_flow_data=True,
        has_predictions=True,
        historical_floods=[],
        related_stations=[],
    )

    await init_integration(hass, mock_config_entry)

    assert hass.states.get("sensor.paris_seine_water_level") is None
    assert hass.states.get("sensor.paris_seine_water_flow") is not None


async def test_sensor_no_flow_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
) -> None:
    """Test that water flow sensor is not created when station has no flow data."""
    mock_vigicrues_client.get_station_details.return_value = StationDetails(
        id="A123456789",
        name="Paris - Seine",
        river="Seine",
        city="Paris",
        latitude=48.8566,
        longitude=2.3522,
        picture_url=None,
        commune_code="75056",
        is_prediction_station=True,
        has_height_data=True,
        has_flow_data=False,
        has_predictions=True,
        historical_floods=[],
        related_stations=[],
    )

    await init_integration(hass, mock_config_entry)

    assert hass.states.get("sensor.paris_seine_water_level") is not None
    assert hass.states.get("sensor.paris_seine_water_flow") is None


async def test_sensor_update_with_none_value(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
) -> None:
    """Test sensor state when observation returns None."""
    mock_vigicrues_client.get_latest_observations.side_effect = lambda *args: None

    await init_integration(hass, mock_config_entry)

    state = hass.states.get("sensor.paris_seine_water_level")
    assert state is not None
    assert state.state == "unknown"
    assert mock_vigicrues_client.get_latest_observations.call_count == 2


@pytest.mark.parametrize(
    ("obs_type", "entity_id"),
    [
        ("H", "sensor.paris_seine_water_level"),
        ("Q", "sensor.paris_seine_water_flow"),
    ],
)
async def test_sensor_unavailable_on_water_level_update_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
    obs_type: str,
    entity_id: str,
) -> None:
    """Test that sensors become unavailable when coordinator update fails on water level."""
    await init_integration(hass, mock_config_entry)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != "unavailable"

    # only first call will fail, it's water level loading
    mock_vigicrues_client.get_latest_observations.reset_mock()
    mock_vigicrues_client.get_latest_observations.side_effect = [TimeoutError, None]

    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "unavailable"

    # only one call has been done, as water flow should not be called after water level fails
    assert mock_vigicrues_client.get_latest_observations.call_count == 1


@pytest.mark.parametrize(
    ("obs_type", "entity_id"),
    [
        ("H", "sensor.paris_seine_water_level"),
        ("Q", "sensor.paris_seine_water_flow"),
    ],
)
async def test_sensor_unavailable_on_update_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
    obs_type: str,
    entity_id: str,
) -> None:
    """Test that sensors become unavailable when coordinator update fails."""
    await init_integration(hass, mock_config_entry)

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != "unavailable"

    mock_vigicrues_client.get_latest_observations.reset_mock()
    mock_vigicrues_client.get_latest_observations.side_effect = [None, TimeoutError]

    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "unavailable"

    # Two call have been done, as water flow (that fail) is called after water level
    assert mock_vigicrues_client.get_latest_observations.call_count == 2


async def test_sensor_coordinator_refresh(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_vigicrues_client: AsyncMock,
) -> None:
    """Test sensor state is consistent after coordinator refresh with same data."""
    await init_integration(hass, mock_config_entry)

    # Reset call history before the refresh
    mock_vigicrues_client.get_latest_observations.reset_mock()

    state = hass.states.get("sensor.paris_seine_water_level")
    assert state is not None
    assert state.state == "2.45"

    coordinator = mock_config_entry.runtime_data
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    state = hass.states.get("sensor.paris_seine_water_level")
    assert state is not None
    assert state.state == "2.45"

    # Two API calls per refresh: one for water level, one for water flow
    assert mock_vigicrues_client.get_latest_observations.call_count == 2
