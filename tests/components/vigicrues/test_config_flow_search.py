"""Test the Vigicrues config flow search methods."""

from unittest.mock import AsyncMock

from aiohttp import ClientError
import pytest
from vigicrues import StationDetails

from homeassistant.components.vigicrues.const import CONF_STATION_ID, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_search_flow_single_result(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test search flow with a single result creates entry directly."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select search method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "search"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "search"

    # Enter search term - single result should create entry directly
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_term": "Paris"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Paris - Seine (Seine)"
    assert result["data"] == {CONF_STATION_ID: "A123456789"}
    assert result["context"]["unique_id"] == "A123456789"
    assert len(mock_setup_entry.mock_calls) == 1


async def test_search_flow_no_results(
    hass: HomeAssistant,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test search flow with no results shows error."""
    mock_configflow_vigicrues_client.search_stations.return_value = []

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select search method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "search"},
    )

    # Enter search term - no results
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_term": "Nonexistent"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_stations_found"}


async def test_search_flow_empty_search_term(
    hass: HomeAssistant,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test search flow with empty search term shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select search method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "search"},
    )

    # Enter empty search term
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_term": ""},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "search_term_required"}


@pytest.mark.parametrize(
    ("exc", "base_error"),
    [
        (Exception, "unknown"),
        (ClientError, "cannot_connect"),
        (TimeoutError, "cannot_connect"),
    ],
)
async def test_search_flow_connection_error(
    hass: HomeAssistant,
    exc: Exception,
    base_error: str,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test search flow with connection error."""
    mock_configflow_vigicrues_client.search_stations.side_effect = exc

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select search method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "search"},
    )

    # Enter search term - error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_term": "Paris"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": base_error}


async def test_search_flow_multiple_results(
    hass: HomeAssistant,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test search flow with multiple results shows station selection."""

    # Mock search_stations to return multiple stations
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

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select search method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "search"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "search"

    # Enter search term - multiple results should show station selection
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_term": "Paris"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_station"
