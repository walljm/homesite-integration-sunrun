"""Data update coordinator for Sunrun integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SunrunApi, SunrunApiError, SunrunAuthError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_PROSPECT_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class SunrunDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Sunrun data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        
        self._entry = entry
        session = async_get_clientsession(hass)
        self._api = SunrunApi(
            session,
            access_token=entry.data[CONF_ACCESS_TOKEN],
            prospect_id=entry.data[CONF_PROSPECT_ID],
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Sunrun API."""
        try:
            return await self._api.get_latest_data()
        except SunrunAuthError as err:
            # Token expired, trigger reauthentication
            raise ConfigEntryAuthFailed(
                "Authentication expired. Please reauthenticate."
            ) from err
        except SunrunApiError as err:
            raise UpdateFailed(f"Error fetching Sunrun data: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching Sunrun data")
            raise UpdateFailed(f"Unexpected error: {err}") from err
