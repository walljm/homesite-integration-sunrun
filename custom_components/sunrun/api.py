"""Sunrun API client."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from .const import (
    API_BASE_URL,
    AUTH_REQUEST_ENDPOINT,
    AUTH_RESPOND_ENDPOINT,
    CUMULATIVE_PRODUCTION_ENDPOINT,
    SITE_PRODUCTION_MINUTE_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)


class SunrunApiError(Exception):
    """Exception for Sunrun API errors."""


class SunrunAuthError(SunrunApiError):
    """Exception for authentication errors."""


class SunrunApi:
    """Sunrun API client."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        access_token: str | None = None,
        prospect_id: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self._session = session
        self._access_token = access_token
        self._prospect_id = prospect_id
        self._auth_token: str | None = None  # Temporary token for OTP flow

    @property
    def access_token(self) -> str | None:
        """Return the access token."""
        return self._access_token

    @property
    def prospect_id(self) -> str | None:
        """Return the prospect ID."""
        return self._prospect_id

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "HomeAssistant/Sunrun",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
        if self._access_token:
            headers["Authorization"] = self._access_token
        return headers

    async def request_otp(self, phone: str) -> bool:
        """Request OTP code via SMS.

        Args:
            phone: Phone number in format +1XXXXXXXXXX

        Returns:
            True if OTP was sent successfully
        """
        url = f"{API_BASE_URL}{AUTH_REQUEST_ENDPOINT}"
        payload = {
            "email": None,
            "phone": phone,
            "prospectId": None,
        }

        try:
            _LOGGER.warning("Requesting OTP for phone: %s", phone)
            _LOGGER.warning("Request URL: %s", url)
            async with self._session.post(
                url, json=payload, headers=self._get_headers()
            ) as response:
                response_text = await response.text()
                _LOGGER.warning("OTP request response status: %s", response.status)
                _LOGGER.warning("OTP request response: %s", response_text)
                if response.status == 200:
                    import json
                    data = json.loads(response_text)
                    _LOGGER.warning("Parsed response keys: %s", list(data.keys()))
                    if "data" in data:
                        _LOGGER.warning("data keys: %s", list(data["data"].keys()) if isinstance(data.get("data"), dict) else type(data.get("data")))
                    
                    # Try multiple possible token locations
                    self._auth_token = (
                        data.get("data", {}).get("token") or
                        data.get("token") or
                        data.get("data", {}).get("authToken") or
                        data.get("authToken")
                    )
                    
                    if self._auth_token:
                        _LOGGER.debug("OTP requested successfully, token received")
                        return True
                    _LOGGER.error("No token received in OTP request response. Full response: %s", response_text)
                    return False
                else:
                    _LOGGER.error(
                        "Failed to request OTP: %s - %s", response.status, response_text
                    raise SunrunAuthError(f"Failed to request OTP: {response.status}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error requesting OTP: %s", err)
            raise SunrunApiError(f"Network error: {err}") from err

    async def verify_otp(self, phone: str, code: str) -> dict[str, Any]:
        """Verify OTP code and get access token.

        Args:
            phone: Phone number used for OTP request
            code: 6-digit OTP code from SMS

        Returns:
            Dict containing access_token, prospect_id, and pto_date
        """
        if not self._auth_token:
            raise SunrunAuthError("No auth token - request OTP first")

        url = f"{API_BASE_URL}{AUTH_RESPOND_ENDPOINT}"
        payload = {
            "email": None,
            "phone": phone,
            "code": code,
            "token": self._auth_token,
        }
        headers = self._get_headers()
        headers["Authorization"] = self._auth_token

        try:
            _LOGGER.debug("Verifying OTP for phone: %s with code: %s", phone, code)
            _LOGGER.debug("Verify URL: %s", url)
            _LOGGER.debug("Verify payload: %s", {**payload, "token": "[REDACTED]"})
            _LOGGER.debug("Auth token present: %s", bool(self._auth_token))
            async with self._session.post(
                url, json=payload, headers=headers
            ) as response:
                response_text = await response.text()
                _LOGGER.debug("OTP verify response status: %s", response.status)
                _LOGGER.debug("OTP verify response: %s", response_text[:500] if len(response_text) > 500 else response_text)
                if response.status == 200:
                    import json
                    data = json.loads(response_text)
                    
                    # Extract access token
                    self._access_token = data.get("data", {}).get("accessToken")
                    
                    # Extract prospect ID and PTO date from opportunities
                    opportunities = data.get("opportunitiesWithContracts", [])
                    if opportunities:
                        self._prospect_id = opportunities[0].get("prospect_id")
                        pto_date = opportunities[0].get("contract", {}).get("ptoDate")
                    else:
                        self._prospect_id = None
                        pto_date = None

                    if not self._access_token or not self._prospect_id:
                        raise SunrunAuthError(
                            "Missing access token or prospect ID in response"
                        )

                    _LOGGER.debug("OTP verified successfully")
                    return {
                        "access_token": self._access_token,
                        "prospect_id": self._prospect_id,
                        "pto_date": pto_date,
                    }
                else:
                    error_text = await response.text()
                    _LOGGER.error(
                        "Failed to verify OTP: %s - %s", response.status, error_text
                    )
                    raise SunrunAuthError(f"Invalid OTP code: {response.status}")
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error verifying OTP: %s", err)
            raise SunrunApiError(f"Network error: {err}") from err

    async def get_cumulative_production(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> dict[str, Any]:
        """Get cumulative daily production data.

        Args:
            start_date: Start date for data range (defaults to 30 days ago)
            end_date: End date for data range (defaults to now)

        Returns:
            Dict with daily production data
        """
        if not self._access_token or not self._prospect_id:
            raise SunrunAuthError("Not authenticated")

        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        # Format dates for API
        start_str = start_date.strftime("%Y-%m-%dT00:00:00.000%z")
        end_str = end_date.strftime("%Y-%m-%dT23:59:59.999%z")

        # Handle timezone - add timezone offset if not present
        if not start_str.endswith("+00:00") and "+" not in start_str and "-" not in start_str[-6:]:
            tz_offset = datetime.now().astimezone().strftime("%z")
            tz_formatted = f"{tz_offset[:3]}:{tz_offset[3:]}"
            start_str = start_date.strftime(f"%Y-%m-%dT00:00:00.000{tz_formatted}")
            end_str = end_date.strftime(f"%Y-%m-%dT23:59:59.999{tz_formatted}")

        url = f"{API_BASE_URL}{CUMULATIVE_PRODUCTION_ENDPOINT}/{self._prospect_id}"
        params = {
            "startDate": start_str,
            "endDate": end_str,
        }

        try:
            async with self._session.get(
                url, params=params, headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug("Got cumulative production data")
                    return data
                elif response.status == 401:
                    raise SunrunAuthError("Authentication expired")
                else:
                    error_text = await response.text()
                    _LOGGER.error(
                        "Failed to get cumulative production: %s - %s",
                        response.status,
                        error_text,
                    )
                    raise SunrunApiError(
                        f"Failed to get production data: {response.status}"
                    )
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error getting cumulative production: %s", err)
            raise SunrunApiError(f"Network error: {err}") from err

    async def get_site_production_minute(
        self, start_date: datetime | None = None, end_date: datetime | None = None
    ) -> list[dict[str, Any]]:
        """Get minute-level site production data.

        Args:
            start_date: Start date for data range (defaults to start of today)
            end_date: End date for data range (defaults to now)

        Returns:
            List of production data points
        """
        if not self._access_token or not self._prospect_id:
            raise SunrunAuthError("Not authenticated")

        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Format as RFC3339
        tz_offset = datetime.now().astimezone().strftime("%z")
        tz_formatted = f"{tz_offset[:3]}:{tz_offset[3:]}"
        start_str = start_date.strftime(f"%Y-%m-%dT%H:%M:%S{tz_formatted}")
        end_str = end_date.strftime(f"%Y-%m-%dT%H:%M:%S{tz_formatted}")

        url = f"{API_BASE_URL}{SITE_PRODUCTION_MINUTE_ENDPOINT}/{self._prospect_id}"
        params = {
            "startDate": start_str,
            "endDate": end_str,
        }

        try:
            async with self._session.get(
                url, params=params, headers=self._get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.debug("Got site production minute data")
                    return data if isinstance(data, list) else data.get("data", [])
                elif response.status == 401:
                    raise SunrunAuthError("Authentication expired")
                else:
                    error_text = await response.text()
                    _LOGGER.error(
                        "Failed to get site production: %s - %s",
                        response.status,
                        error_text,
                    )
                    raise SunrunApiError(
                        f"Failed to get production data: {response.status}"
                    )
        except aiohttp.ClientError as err:
            _LOGGER.error("Network error getting site production: %s", err)
            raise SunrunApiError(f"Network error: {err}") from err

    async def get_latest_data(self) -> dict[str, Any]:
        """Get the latest production data.

        Returns:
            Dict with current power, daily production, cumulative production, etc.
        """
        result: dict[str, Any] = {
            "current_power": None,
            "daily_production": None,
            "cumulative_production": None,
            "consumption": None,
            "grid_export": None,
            "grid_import": None,
            "battery_solar": None,
            "last_update": None,
        }

        # Get minute-level data for current power
        try:
            minute_data = await self.get_site_production_minute()
            if minute_data:
                # Get the most recent data point
                latest = minute_data[-1] if isinstance(minute_data, list) else minute_data
                
                # Convert kW to W if necessary (API returns kW)
                solar = latest.get("solar") or latest.get("pvSolar") or 0
                result["current_power"] = solar * 1000 if solar < 100 else solar
                
                consumption = latest.get("consumption")
                if consumption is not None:
                    result["consumption"] = consumption * 1000 if consumption < 100 else consumption
                
                export_reading = latest.get("exportReading")
                if export_reading is not None:
                    result["grid_export"] = export_reading * 1000 if export_reading < 100 else export_reading
                
                import_reading = latest.get("importReading")
                if import_reading is not None:
                    result["grid_import"] = import_reading * 1000 if import_reading < 100 else import_reading
                
                battery_solar = latest.get("batterySolar")
                if battery_solar is not None:
                    result["battery_solar"] = battery_solar * 1000 if battery_solar < 100 else battery_solar
                
                result["last_update"] = latest.get("timestamp")
        except SunrunApiError as err:
            _LOGGER.warning("Could not get minute data: %s", err)

        # Get cumulative production data
        try:
            cumulative_data = await self.get_cumulative_production()
            if cumulative_data:
                # Find today's data and the most recent cumulative value
                today = datetime.now().strftime("%Y-%m-%d")
                
                if isinstance(cumulative_data, dict):
                    # Data is keyed by date
                    if today in cumulative_data:
                        today_data = cumulative_data[today]
                        result["daily_production"] = today_data.get("deliveredKwh", 0)
                        result["cumulative_production"] = today_data.get("cumulativeKwh", 0)
                    else:
                        # Get the most recent date's data
                        dates = sorted(cumulative_data.keys(), reverse=True)
                        if dates:
                            latest_data = cumulative_data[dates[0]]
                            result["cumulative_production"] = latest_data.get("cumulativeKwh", 0)
                            # If it's yesterday, still show the daily production
                            result["daily_production"] = latest_data.get("deliveredKwh", 0)
        except SunrunApiError as err:
            _LOGGER.warning("Could not get cumulative data: %s", err)

        return result

    async def test_connection(self) -> bool:
        """Test if the current credentials are valid.

        Returns:
            True if credentials are valid
        """
        try:
            await self.get_cumulative_production()
            return True
        except SunrunAuthError:
            return False
        except SunrunApiError:
            # API error doesn't necessarily mean auth is invalid
            return True
