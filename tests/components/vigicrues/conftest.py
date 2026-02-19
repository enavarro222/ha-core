"""Common fixtures for the Vigicrues tests."""

from collections.abc import Generator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from vigicrues import (
    Observation,
    ObservationType,
    Station,
    StationDetails,
    Territory,
    Troncon,
)

from homeassistant.components.vigicrues.const import DOMAIN

from tests.common import MockConfigEntry

STATION_PARIS = Station(
    id="A123456789",
    name="Paris - Seine",
)


STATION_PARIS_DETAILS = StationDetails(
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

WATER_LEVEL_OBSERVATION = Observation(
    timestamp=datetime(2024, 4, 27, 10, 0, tzinfo=UTC),
    value=2.45,
    type=ObservationType.HEIGHT,
    unit="m",
)

WATER_FLOW_OBSERVATION = Observation(
    timestamp=datetime(2024, 4, 27, 10, 0, tzinfo=UTC),
    value=125.5,
    type=ObservationType.FLOW,
    unit="m3/s",
)

TERRITORIES = [
    Territory(id="1", name="Seine-Normandie"),
    Territory(id="2", name="Loire-Bretagne"),
]

TRONCONS = [
    Troncon(id="S1", name="Seine amont"),  # codespell:ignore amont
    Troncon(id="S2", name="Seine aval"),
]


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.vigicrues.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


def _get_observation_mock(station_id: str, obs_type: str) -> Observation | None:
    """Return appropriate observation based on type."""
    if obs_type == "H":
        return WATER_LEVEL_OBSERVATION
    if obs_type == "Q":
        return WATER_FLOW_OBSERVATION
    return None


@pytest.fixture
def mock_vigicrues_client() -> Generator[AsyncMock]:
    """Mock a Vigicrues client."""
    with patch(
        "homeassistant.components.vigicrues.Vigicrues", autospec=True
    ) as mock_client:
        client = mock_client.return_value
        client.get_station_details.return_value = STATION_PARIS_DETAILS
        client.get_latest_observations.side_effect = _get_observation_mock
        client.search_stations.return_value = [STATION_PARIS_DETAILS]
        client.get_territories.return_value = TERRITORIES
        client.get_troncons.return_value = TRONCONS
        client.get_troncon_stations.return_value = [STATION_PARIS]

        yield client


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Paris - Seine (Seine)",
        unique_id="A123456789",
        data={
            "station_id": "A123456789",
        },
    )


@pytest.fixture
def mock_configflow_vigicrues_client(
    mock_vigicrues_client: AsyncMock,
) -> Generator[AsyncMock]:
    """Mock vigicrues client for config flow."""
    with patch(
        "homeassistant.components.vigicrues.config_flow.VigicruesFlowHandler._get_client",
        return_value=mock_vigicrues_client,
    ):
        yield mock_vigicrues_client
