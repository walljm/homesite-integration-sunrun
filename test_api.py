#!/usr/bin/env python3
"""Test script to verify Sunrun API responses."""
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

API_BASE_URL = "https://gateway.sunrun.com"
AUTH_REQUEST_ENDPOINT = "/portal-auth/request-passwordless"
AUTH_RESPOND_ENDPOINT = "/portal-auth/respond-passwordless"
CUMULATIVE_PRODUCTION_ENDPOINT = "/performance-api/v1/cumulative-production/daily"
SITE_PRODUCTION_MINUTE_ENDPOINT = "/performance-api/v1/site-production-minute"


def get_headers(access_token: str | None = None) -> dict:
    """Get headers for API requests."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "HomeAssistant/Sunrun",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    }
    if access_token:
        headers["Authorization"] = access_token
    return headers


async def request_otp(session: aiohttp.ClientSession, phone: str) -> str | None:
    """Request OTP and return the auth token."""
    url = f"{API_BASE_URL}{AUTH_REQUEST_ENDPOINT}"
    payload = {"email": None, "phone": phone, "prospectId": None}
    
    async with session.post(url, json=payload, headers=get_headers()) as response:
        print(f"\n=== OTP Request ===")
        print(f"Status: {response.status}")
        data = await response.json()
        print(f"Response keys: {list(data.keys())}")
        
        if response.status == 200:
            return data.get("token")
    return None


async def verify_otp(session: aiohttp.ClientSession, phone: str, code: str, auth_token: str) -> dict | None:
    """Verify OTP and return access token and prospect ID."""
    url = f"{API_BASE_URL}{AUTH_RESPOND_ENDPOINT}"
    payload = {"email": None, "phone": phone, "code": code, "token": auth_token}
    headers = get_headers()
    headers["Authorization"] = auth_token
    
    async with session.post(url, json=payload, headers=headers) as response:
        print(f"\n=== OTP Verify ===")
        print(f"Status: {response.status}")
        
        if response.status == 200:
            data = await response.json()
            print(f"Response keys: {list(data.keys())}")
            
            access_token = data.get("data", {}).get("accessToken")
            opportunities = data.get("opportunitiesWithContracts", [])
            
            if opportunities:
                prospect_id = opportunities[0].get("prospect_id")
                print(f"Access token: {access_token[:50]}..." if access_token else "No access token")
                print(f"Prospect ID: {prospect_id}")
                return {"access_token": access_token, "prospect_id": prospect_id}
        else:
            print(f"Error: {await response.text()}")
    return None


async def get_cumulative_production(session: aiohttp.ClientSession, access_token: str, prospect_id: str):
    """Get cumulative production data."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    tz_offset = datetime.now().astimezone().strftime("%z")
    tz_formatted = f"{tz_offset[:3]}:{tz_offset[3:]}"
    start_str = start_date.strftime(f"%Y-%m-%dT00:00:00.000{tz_formatted}")
    end_str = end_date.strftime(f"%Y-%m-%dT23:59:59.999{tz_formatted}")
    
    url = f"{API_BASE_URL}{CUMULATIVE_PRODUCTION_ENDPOINT}/{prospect_id}"
    params = {"startDate": start_str, "endDate": end_str}
    
    async with session.get(url, params=params, headers=get_headers(access_token)) as response:
        print(f"\n=== Cumulative Production ===")
        print(f"URL: {url}")
        print(f"Status: {response.status}")
        
        if response.status == 200:
            data = await response.json()
            print(f"Response type: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())[:10]}")
                # Print first few items
                for i, (k, v) in enumerate(data.items()):
                    if i < 3:
                        print(f"  {k}: {v}")
            elif isinstance(data, list):
                print(f"List length: {len(data)}")
                if data:
                    print(f"First item: {json.dumps(data[0], indent=2)}")
                    print(f"Last item: {json.dumps(data[-1], indent=2)}")
            return data
        else:
            print(f"Error: {await response.text()}")
    return None


async def get_site_production_minute(session: aiohttp.ClientSession, access_token: str, prospect_id: str):
    """Get minute-level production data."""
    end_date = datetime.now()
    start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    tz_offset = datetime.now().astimezone().strftime("%z")
    tz_formatted = f"{tz_offset[:3]}:{tz_offset[3:]}"
    start_str = start_date.strftime(f"%Y-%m-%dT%H:%M:%S{tz_formatted}")
    end_str = end_date.strftime(f"%Y-%m-%dT%H:%M:%S{tz_formatted}")
    
    url = f"{API_BASE_URL}{SITE_PRODUCTION_MINUTE_ENDPOINT}/{prospect_id}"
    params = {"startDate": start_str, "endDate": end_str}
    
    async with session.get(url, params=params, headers=get_headers(access_token)) as response:
        print(f"\n=== Site Production Minute ===")
        print(f"URL: {url}")
        print(f"Status: {response.status}")
        
        if response.status == 200:
            data = await response.json()
            print(f"Response type: {type(data).__name__}")
            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                if "data" in data:
                    inner = data["data"]
                    print(f"data type: {type(inner).__name__}")
                    if isinstance(inner, list) and inner:
                        print(f"data length: {len(inner)}")
                        print(f"First item: {json.dumps(inner[0], indent=2)}")
                        print(f"Last item: {json.dumps(inner[-1], indent=2)}")
            elif isinstance(data, list):
                print(f"List length: {len(data)}")
                if data:
                    print(f"First item: {json.dumps(data[0], indent=2)}")
                    print(f"Last item: {json.dumps(data[-1], indent=2)}")
            return data
        else:
            print(f"Error: {await response.text()}")
    return None


async def main():
    """Main test function."""
    print("Sunrun API Test Script")
    print("=" * 50)
    
    phone = input("Enter phone number (e.g., +13145551234): ").strip()
    if not phone.startswith("+"):
        phone = "+1" + phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Request OTP
        auth_token = await request_otp(session, phone)
        if not auth_token:
            print("Failed to get auth token")
            return
        
        print("\nOTP sent! Check your phone.")
        code = input("Enter the 6-digit code: ").strip()
        
        # Step 2: Verify OTP
        auth_data = await verify_otp(session, phone, code, auth_token)
        if not auth_data:
            print("Failed to verify OTP")
            return
        
        access_token = auth_data["access_token"]
        prospect_id = auth_data["prospect_id"]
        
        # Step 3: Get production data
        await get_cumulative_production(session, access_token, prospect_id)
        await get_site_production_minute(session, access_token, prospect_id)
        
        print("\n" + "=" * 50)
        print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())
