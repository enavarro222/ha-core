"""Test the Vigicrues config flow hierarchical search methods."""

from unittest.mock import AsyncMock

from aiohttp import ClientError

from homeassistant.components.vigicrues.const import CONF_STATION_ID, DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType


async def test_hierarchical_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test hierarchical search flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select hierarchical method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "hierarchical"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hierarchical_territory"

    # Select territory
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"territory": "1"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hierarchical_troncon"

    # Select troncon
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"troncon": "S1"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_station"

    # Select station
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"station": "A123456789"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Paris - Seine (Seine)"
    assert result["data"] == {CONF_STATION_ID: "A123456789"}


async def test_hierarchical_flow_abort_on_territory_error(
    hass: HomeAssistant,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test hierarchical flow aborts when territory fetch fails."""
    mock_configflow_vigicrues_client.get_territories.side_effect = ClientError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select hierarchical method - should abort
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "hierarchical"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_hierarchical_flow_abort_on_troncons_error(
    hass: HomeAssistant,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test hierarchical flow aborts when troncons fetch fails."""
    mock_configflow_vigicrues_client.get_troncons.side_effect = ClientError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select hierarchical method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "hierarchical"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hierarchical_territory"

    # Select territory - should abort due to error fetching troncons
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"territory": "1"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_hierarchical_flow_abort_on_troncon_stations_error(
    hass: HomeAssistant,
    mock_configflow_vigicrues_client: AsyncMock,
) -> None:
    """Test hierarchical flow aborts when troncon stations fetch fails."""
    mock_configflow_vigicrues_client.get_troncon_stations.side_effect = ClientError

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    # Select hierarchical method
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"search_method": "hierarchical"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hierarchical_territory"

    # Select territory
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"territory": "1"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hierarchical_troncon"

    # Select troncon - should abort due to error fetching stations
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"troncon": "S1"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"
