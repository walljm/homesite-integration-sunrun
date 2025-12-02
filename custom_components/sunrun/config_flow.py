"""Config flow for Sunrun integration."""
from __future__ import annotations

import logging
import re
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SunrunApi, SunrunApiError, SunrunAuthError
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_PHONE,
    CONF_PROSPECT_ID,
    CONF_PTO_DATE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def format_phone_number(phone: str) -> str:
    """Format phone number to +1XXXXXXXXXX format."""
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)
    
    # Add country code if missing
    if len(digits) == 10:
        digits = "1" + digits
    
    # Ensure it starts with +
    return f"+{digits}"


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    formatted = format_phone_number(phone)
    return len(formatted) == 12 and formatted.startswith("+1")


class SunrunConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Sunrun."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api: SunrunApi | None = None
        self._phone: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - phone number entry."""
        errors: dict[str, str] = {}

        if user_input is not None:
            phone = user_input.get(CONF_PHONE, "")
            
            if not validate_phone_number(phone):
                errors["base"] = "invalid_phone"
            else:
                self._phone = format_phone_number(phone)
                
                # Create API client and request OTP
                session = async_get_clientsession(self.hass)
                self._api = SunrunApi(session)
                
                try:
                    await self._api.request_otp(self._phone)
                    return await self.async_step_otp()
                except SunrunApiError as err:
                    _LOGGER.error("Failed to request OTP: %s", err)
                    errors["base"] = "cannot_connect"
                except Exception as err:
                    _LOGGER.exception("Unexpected error: %s", err)
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PHONE): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "phone_format": "(XXX) XXX-XXXX or +1XXXXXXXXXX"
            },
        )

    async def async_step_otp(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle OTP verification step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            code = user_input.get("code", "").strip()
            
            if not code or len(code) != 6 or not code.isdigit():
                errors["base"] = "invalid_code"
            else:
                try:
                    auth_data = await self._api.verify_otp(self._phone, code)
                    
                    # Check if this account is already configured
                    await self.async_set_unique_id(auth_data["prospect_id"])
                    self._abort_if_unique_id_configured()
                    
                    # Create the config entry
                    return self.async_create_entry(
                        title=f"Sunrun ({self._phone})",
                        data={
                            CONF_PHONE: self._phone,
                            CONF_ACCESS_TOKEN: auth_data["access_token"],
                            CONF_PROSPECT_ID: auth_data["prospect_id"],
                            CONF_PTO_DATE: auth_data.get("pto_date"),
                        },
                    )
                except SunrunAuthError as err:
                    _LOGGER.error("OTP verification failed: %s", err)
                    errors["base"] = "invalid_auth"
                except SunrunApiError as err:
                    _LOGGER.error("API error during OTP verification: %s", err)
                    errors["base"] = "cannot_connect"
                except Exception as err:
                    _LOGGER.exception("Unexpected error during OTP verification: %s", err)
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="otp",
            data_schema=vol.Schema(
                {
                    vol.Required("code"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "phone": self._phone,
            },
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Handle reauthentication."""
        self._phone = entry_data.get(CONF_PHONE)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauthentication confirmation."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Request new OTP
            session = async_get_clientsession(self.hass)
            self._api = SunrunApi(session)
            
            try:
                await self._api.request_otp(self._phone)
                return await self.async_step_reauth_otp()
            except SunrunApiError as err:
                _LOGGER.error("Failed to request OTP for reauth: %s", err)
                errors["base"] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected error during reauth: %s", err)
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({}),
            errors=errors,
            description_placeholders={
                "phone": self._phone,
            },
        )

    async def async_step_reauth_otp(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle OTP verification for reauthentication."""
        errors: dict[str, str] = {}

        if user_input is not None:
            code = user_input.get("code", "").strip()
            
            if not code or len(code) != 6 or not code.isdigit():
                errors["base"] = "invalid_code"
            else:
                try:
                    auth_data = await self._api.verify_otp(self._phone, code)
                    
                    # Find the existing entry and update it
                    existing_entry = await self.async_set_unique_id(
                        auth_data["prospect_id"]
                    )
                    if existing_entry:
                        self.hass.config_entries.async_update_entry(
                            existing_entry,
                            data={
                                CONF_PHONE: self._phone,
                                CONF_ACCESS_TOKEN: auth_data["access_token"],
                                CONF_PROSPECT_ID: auth_data["prospect_id"],
                                CONF_PTO_DATE: auth_data.get("pto_date"),
                            },
                        )
                        await self.hass.config_entries.async_reload(
                            existing_entry.entry_id
                        )
                        return self.async_abort(reason="reauth_successful")
                    
                    return self.async_abort(reason="reauth_failed")
                except SunrunAuthError as err:
                    _LOGGER.error("OTP verification failed during reauth: %s", err)
                    errors["base"] = "invalid_auth"
                except SunrunApiError as err:
                    _LOGGER.error("API error during reauth OTP verification: %s", err)
                    errors["base"] = "cannot_connect"
                except Exception as err:
                    _LOGGER.exception("Unexpected error during reauth: %s", err)
                    errors["base"] = "unknown"

        return self.async_show_form(
            step_id="reauth_otp",
            data_schema=vol.Schema(
                {
                    vol.Required("code"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "phone": self._phone,
            },
        )
