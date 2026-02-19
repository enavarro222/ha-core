"""Define the Vigicrues entity."""

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import VigicruesDataUpdateCoordinator


class VigicruesEntity(CoordinatorEntity[VigicruesDataUpdateCoordinator]):
    """Define Vigicrues entity."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VigicruesDataUpdateCoordinator,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)

        self._attr_device_info = coordinator.device_info
