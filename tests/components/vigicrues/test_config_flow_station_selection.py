"""Test the Vigicrues config flow station selection."""

from unittest.mock import AsyncMock

from aiohttp import ClientError
import pytest
from vigicrues import StationDetails

from homeassistant.components.vigicrues.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry


async def test_already_configured(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test that already configured station aborts."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select search method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "search"},
    )

    # Enter search term - should abort because already configured
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_term": "Paris"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    ("exc", "base_error"),
    [
        (ClientError, "cannot_connect"),
        (TimeoutError, "cannot_connect"),
        (Exception, "unknown"),
    ],
)
async def test_select_station_connection_error(
    hass: HomeAssistant,
    exc: Exception,
    base_error: str,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test station selection with connection error."""
    # Mock search_stations to return multiple stations (to reach select_station)
    station1 = StationDetails(
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
        has_flow_data=True,
        has_predictions=True,
        historical_floods=[],
        related_stations=[],
    )
    station2 = StationDetails(
        id="B987654321",
        name="Paris - Marne",
        river="Marne",
        city="Paris",
        latitude=48.8566,
        longitude=2.3522,
        picture_url=None,
        commune_code="75056",
        is_prediction_station=True,
        has_height_data=True,
        has_flow_data=True,
        has_predictions=True,
        historical_floods=[],
        related_stations=[],
    )
    mock_configflow_vigicrues_client.search_stations.return_value = [station1, station2]
    # Mock get_station_details to raise the exception
    mock_configflow_vigicrues_client.get_station_details.side_effect = exc

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select search method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "search"},
    )

    # Enter search term - multiple results
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_term": "Paris"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_station"

    # Select station - should show error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"station": "A123456789"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_station"
    assert result["errors"] == {"base": base_error}
