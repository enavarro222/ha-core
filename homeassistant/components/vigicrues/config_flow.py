"""Config flow for Vigicrues integration."""

from __future__ import annotations

import logging
from typing import Any

from aiohttp import ClientError
from vigicrues import Vigicrues
from vigicrues.models import Station, StationDetails
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import CONF_STATION_ID, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("search_method"): SelectSelector(
            SelectSelectorConfig(
                options=[
                    SelectOptionDict(value="search", label=""),
                    SelectOptionDict(value="hierarchical", label=""),
                ],
                multiple=False,
                mode=SelectSelectorMode.LIST,
                translation_key="search_method",
            )
        )
    }
)


class VigicruesFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Vigicrues."""

    VERSION = 1
    MINOR_VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._selected_territory: str | None = None
        self._selected_troncon: str | None = None
        # Stations pre-selected either from search or from territory/troncon browsing
        self._stations: list[Station] | list[StationDetails] = []
        self._client: Vigicrues | None = None

    def _get_client(self) -> Vigicrues:
        """Get or create the Vigicrues client."""
        if self._client is None:
            client_session = async_get_clientsession(self.hass)
            self._client = Vigicrues(client_session)
        return self._client

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            if user_input["search_method"] == "search":
                return await self.async_step_search()
            return await self.async_step_hierarchical_territory()

        return self.async_show_form(step_id="user", data_schema=STEP_USER_DATA_SCHEMA)

    async def async_step_search(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the search step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            search_term = user_input.get("search_term", "").strip()
            if search_term:
                client = self._get_client()
                try:
                    stations: list[StationDetails] = await client.search_stations(
                        search_term, check=True
                    )
                except ClientError, TimeoutError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected exception during search")
                    errors["base"] = "unknown"
                else:
                    if not stations:
                        errors["base"] = "no_stations_found"
                    elif len(stations) == 1:
                        # Single station found, create entry directly
                        station_details = stations[0]
                        return await self._create_entry(station_details)
                    else:
                        # Multiple stations found, show selection
                        self._stations = stations
                        return await self.async_step_select_station()
            else:
                errors["base"] = "search_term_required"

        return self.async_show_form(
            step_id="search",
            data_schema=vol.Schema({vol.Required("search_term"): str}),
            errors=errors,
        )

    async def async_step_hierarchical_territory(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the territory selection step."""
        if user_input is not None:
            self._selected_territory = user_input["territory"]
            return await self.async_step_hierarchical_troncon()

        client = self._get_client()
        try:
            territories = await client.get_territories()
        except ClientError, TimeoutError:
            return self.async_abort(reason="cannot_connect")

        options: list[SelectOptionDict] = [
            SelectOptionDict(value=t.id, label=t.name) for t in territories
        ]

        return self.async_show_form(
            step_id="hierarchical_territory",
            data_schema=vol.Schema(
                {
                    vol.Required("territory"): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            multiple=False,
                            sort=True,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_hierarchical_troncon(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the troncon selection step."""
        client = self._get_client()
        if user_input is not None:
            # User has selected a troncon — get its stations and move to selection step
            self._selected_troncon = user_input["troncon"]
            try:
                stations = await client.get_troncon_stations(self._selected_troncon)
            except ClientError, TimeoutError:
                return self.async_abort(reason="cannot_connect")
            else:
                self._stations = stations
                return await self.async_step_select_station()

        try:
            assert (
                self._selected_territory is not None
            )  # this should has been set in previous step
            troncons = await client.get_troncons(self._selected_territory)
        except ClientError, TimeoutError:
            return self.async_abort(reason="cannot_connect")

        options: list[SelectOptionDict] = [
            SelectOptionDict(value=t.id, label=t.name) for t in troncons
        ]

        return self.async_show_form(
            step_id="hierarchical_troncon",
            data_schema=vol.Schema(
                {
                    vol.Required("troncon"): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            multiple=False,
                            sort=True,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_select_station(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the station selection step after search or after troncon selection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            station_id = user_input["station"]

            client = self._get_client()
            try:
                station_details = await client.get_station_details(station_id)
            except ClientError, TimeoutError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return await self._create_entry(station_details)

        options: list[SelectOptionDict] = [
            SelectOptionDict(value=s.id, label=s.name) for s in self._stations
        ]

        return self.async_show_form(
            step_id="select_station",
            data_schema=vol.Schema(
                {
                    vol.Required("station"): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            multiple=False,
                            sort=True,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors,
        )

    async def _create_entry(self, station_details: StationDetails) -> ConfigFlowResult:
        """Create the config entry."""
        await self.async_set_unique_id(station_details.id)
        self._abort_if_unique_id_configured()

        title = f"{station_details.name} ({station_details.river})"
        return self.async_create_entry(
            title=title,
            data={CONF_STATION_ID: station_details.id},
        )
