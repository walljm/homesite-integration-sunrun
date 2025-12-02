#!/usr/bin/env python3
"""Test script to verify Sunrun API using the actual component code."""
import asyncio
import sys
import os
import re
from datetime import datetime, timedelta
from typing import Any

import aiohttp

# Import constants directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "custom_components", "sunrun"))
from const import (
    API_BASE_URL,
    AUTH_REQUEST_ENDPOINT,
    AUTH_RESPOND_ENDPOINT,
    CUMULATIVE_PRODUCTION_ENDPOINT,
    SITE_PRODUCTION_MINUTE_ENDPOINT,
)


class SunrunApiError(Exception):
    """Exception for Sunrun API errors."""


class SunrunAuthError(SunrunApiError):
    """Exception for authentication errors."""


class SunrunApi:
    """Sunrun API client - copied from api.py for standalone testing."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        access_token: str | None = None,
        prospect_id: str | None = None,
    ) -> None:
        self._session = session
        self._access_token = access_token
        self._prospect_id = prospect_id
        self._auth_token: str | None = None

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "HomeAssistant/Sunrun",
        }
        if self._access_token:
            headers["Authorization"] = self._access_token
        return headers

    async def request_otp(self, phone: str) -> bool:
        url = f"{API_BASE_URL}{AUTH_REQUEST_ENDPOINT}"
        payload = {"email": None, "phone": phone, "prospectId": None}

        async with self._session.post(url, json=payload, headers=self._get_headers()) as response:
            if response.status == 200:
                data = await response.json()
                self._auth_token = data.get("token")
                return bool(self._auth_token)
            return False

    async def verify_otp(self, phone: str, code: str) -> dict[str, Any]:
        if not self._auth_token:
            raise SunrunAuthError("No auth token")

        url = f"{API_BASE_URL}{AUTH_RESPOND_ENDPOINT}"
        payload = {"email": None, "phone": phone, "code": code, "token": self._auth_token}
        headers = self._get_headers()
        headers["Authorization"] = self._auth_token

        async with self._session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                self._access_token = data.get("data", {}).get("accessToken")
                opportunities = data.get("opportunitiesWithContracts", [])
                if opportunities:
                    self._prospect_id = opportunities[0].get("prospect_id")
                    pto_date = opportunities[0].get("contract", {}).get("ptoDate")
                else:
                    self._prospect_id = None
                    pto_date = None

                if not self._access_token or not self._prospect_id:
                    raise SunrunAuthError("Missing access token or prospect ID")

                return {
                    "access_token": self._access_token,
                    "prospect_id": self._prospect_id,
                    "pto_date": pto_date,
                }
            raise SunrunAuthError(f"Invalid OTP: {response.status}")

    async def get_cumulative_production(self, start_date=None, end_date=None):
        if not self._access_token or not self._prospect_id:
            raise SunrunAuthError("Not authenticated")

        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=30)

        tz_offset = datetime.now().astimezone().strftime("%z")
        tz_formatted = f"{tz_offset[:3]}:{tz_offset[3:]}"
        start_str = start_date.strftime(f"%Y-%m-%dT00:00:00.000{tz_formatted}")
        end_str = end_date.strftime(f"%Y-%m-%dT23:59:59.999{tz_formatted}")

        url = f"{API_BASE_URL}{CUMULATIVE_PRODUCTION_ENDPOINT}/{self._prospect_id}"
        params = {"startDate": start_str, "endDate": end_str}

        async with self._session.get(url, params=params, headers=self._get_headers()) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 401:
                raise SunrunAuthError("Authentication expired")
            raise SunrunApiError(f"Failed: {response.status}")

    async def get_site_production_minute(self, start_date=None, end_date=None):
        if not self._access_token or not self._prospect_id:
            raise SunrunAuthError("Not authenticated")

        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

        tz_offset = datetime.now().astimezone().strftime("%z")
        tz_formatted = f"{tz_offset[:3]}:{tz_offset[3:]}"
        start_str = start_date.strftime(f"%Y-%m-%dT%H:%M:%S{tz_formatted}")
        end_str = end_date.strftime(f"%Y-%m-%dT%H:%M:%S{tz_formatted}")

        url = f"{API_BASE_URL}{SITE_PRODUCTION_MINUTE_ENDPOINT}/{self._prospect_id}"
        params = {"startDate": start_str, "endDate": end_str}

        async with self._session.get(url, params=params, headers=self._get_headers()) as response:
            if response.status == 200:
                data = await response.json()
                return data if isinstance(data, list) else data.get("data", [])
            elif response.status == 401:
                raise SunrunAuthError("Authentication expired")
            raise SunrunApiError(f"Failed: {response.status}")

    async def get_latest_data(self) -> dict[str, Any]:
        """Get the latest production data - mirrors the actual component code."""
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
            if minute_data and isinstance(minute_data, list) and len(minute_data) > 0:
                latest = minute_data[-1]
                print(f"  [DEBUG] Latest minute data point: {latest}")
                
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
            print(f"  [WARN] Could not get minute data: {err}")

        # Get cumulative production data
        try:
            cumulative_data = await self.get_cumulative_production()
            if cumulative_data and isinstance(cumulative_data, list) and len(cumulative_data) > 0:
                today = datetime.now().strftime("%Y-%m-%d")
                print(f"  [DEBUG] Looking for data for date: {today}")
                
                today_record = None
                latest_record = cumulative_data[-1]
                
                for record in cumulative_data:
                    record_date = record.get("timestamp", "")[:10]
                    if record_date == today:
                        today_record = record
                        break
                
                use_record = today_record if today_record else latest_record
                print(f"  [DEBUG] Using cumulative record: {use_record}")
                
                result["daily_production"] = use_record.get("deliveredKwh")
                result["cumulative_production"] = use_record.get("cumulativeKwh")
                
        except SunrunApiError as err:
            print(f"  [WARN] Could not get cumulative data: {err}")

        return result


def format_phone(phone: str) -> str:
    """Format phone number to +1XXXXXXXXXX format."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 10:
        digits = "1" + digits
    return f"+{digits}"


async def main():
    """Main test function."""
    print("Sunrun API Test Script (using component code)")
    print("=" * 50)
    
    phone = input("Enter phone number (e.g., 3145551234): ").strip()
    phone = format_phone(phone)
    print(f"Formatted phone: {phone}")
    
    async with aiohttp.ClientSession() as session:
        api = SunrunApi(session)
        
        # Step 1: Request OTP
        print("\n=== Requesting OTP ===")
        try:
            success = await api.request_otp(phone)
            if not success:
                print("Failed to request OTP")
                return
            print("OTP sent successfully!")
        except SunrunApiError as e:
            print(f"Error requesting OTP: {e}")
            return
        
        code = input("Enter the 6-digit code: ").strip()
        
        # Step 2: Verify OTP
        print("\n=== Verifying OTP ===")
        try:
            auth_data = await api.verify_otp(phone, code)
            print(f"Authentication successful!")
            print(f"  Prospect ID: {auth_data['prospect_id']}")
            print(f"  PTO Date: {auth_data.get('pto_date')}")
            print(f"  Access Token: {auth_data['access_token'][:50]}...")
        except SunrunAuthError as e:
            print(f"Auth error: {e}")
            return
        except SunrunApiError as e:
            print(f"API error: {e}")
            return
        
        # Step 3: Get cumulative production
        print("\n=== Cumulative Production (raw) ===")
        try:
            data = await api.get_cumulative_production()
            print(f"Response type: {type(data).__name__}")
            if isinstance(data, list):
                print(f"Records: {len(data)}")
                if data:
                    print(f"First: {data[0]}")
                    print(f"Last:  {data[-1]}")
            elif isinstance(data, dict):
                print(f"Keys: {list(data.keys())[:5]}")
        except SunrunApiError as e:
            print(f"Error: {e}")
        
        # Step 4: Get minute-level production
        print("\n=== Site Production Minute (raw) ===")
        try:
            data = await api.get_site_production_minute()
            print(f"Response type: {type(data).__name__}")
            if isinstance(data, list):
                print(f"Records: {len(data)}")
                if data:
                    print(f"First: {data[0]}")
                    print(f"Last:  {data[-1]}")
            elif isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
        except SunrunApiError as e:
            print(f"Error: {e}")
        
        # Step 5: Get latest data (the main function used by Home Assistant)
        print("\n=== Get Latest Data (HA function) ===")
        try:
            data = await api.get_latest_data()
            print("Result:")
            for key, value in data.items():
                print(f"  {key}: {value}")
        except SunrunApiError as e:
            print(f"Error: {e}")
        
        print("\n" + "=" * 50)
        print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
