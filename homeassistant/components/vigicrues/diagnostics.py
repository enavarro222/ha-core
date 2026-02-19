"""Diagnostics support for Vigicrues."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import VigicruesConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: VigicruesConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data

    return {
        "config_entry_data": entry.as_dict(),
        "station_data": asdict(coordinator.data),
    }
