"""Test the Vigicrues config flow."""

from unittest.mock import AsyncMock, patch

from aiohttp import ClientError

from homeassistant.components.vigicrues.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.aiohttp_client import async_get_clientsession


async def test_user_step_show_form(hass: HomeAssistant) -> None:
    """Test that the user step shows the search method form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_get_client_creates_new_client(
    hass: HomeAssistant,
) -> None:
    """Test that _get_client creates a new client when none exists."""
    with patch(
        "homeassistant.components.vigicrues.config_flow.Vigicrues"
    ) as mock_vigicrues:
        mock_client = AsyncMock()
        mock_client.get_territories.side_effect = ClientError
        mock_vigicrues.return_value = mock_client

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        # Select hierarchical method - this triggers _get_client
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"search_method": "hierarchical"},
        )

        # Verify Vigicrues was called with client session
        client_session = async_get_clientsession(hass)
        mock_vigicrues.assert_called_once_with(client_session)
