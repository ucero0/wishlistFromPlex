#!/usr/bin/env python3
"""
Test script to remove and re-add an item from Plex watchlist.

Usage:
    python scripts/test_watchlist_modify.py YOUR_PLEX_TOKEN

This will:
1. Fetch your watchlist
2. Remove the first item
3. Add it back

Your watchlist will remain unchanged after the test.
"""
import sys
import asyncio
import httpx

PLEX_API_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "plex-wishlist-service",
    "X-Plex-Product": "Plex Wishlist Service",
    "X-Plex-Version": "1.0.0",
}


async def get_watchlist(token: str) -> list:
    """Fetch watchlist items."""
    url = "https://discover.provider.plex.tv/library/sections/watchlist/all"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("MediaContainer", {}).get("Metadata", [])
        return []


async def remove_from_watchlist(token: str, rating_key: str) -> tuple[bool, str]:
    """Remove item from watchlist using ratingKey."""
    url = "https://discover.provider.plex.tv/actions/removeFromWatchlist"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.put(url, headers=headers, params={"ratingKey": rating_key})
        return response.status_code == 200, f"{response.status_code}: {response.text[:200]}"


async def add_to_watchlist(token: str, rating_key: str) -> tuple[bool, str]:
    """Add item to watchlist using ratingKey."""
    url = "https://discover.provider.plex.tv/actions/addToWatchlist"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.put(url, headers=headers, params={"ratingKey": rating_key})
        return response.status_code == 200, f"{response.status_code}: {response.text[:200]}"


async def main(token: str):
    print("=" * 60)
    print("Plex Watchlist Remove/Add Test")
    print("=" * 60)
    
    # Step 1: Get watchlist
    print("\n[1] Fetching watchlist...")
    watchlist = await get_watchlist(token)
    print(f"    Found {len(watchlist)} items")
    
    if not watchlist:
        print("\n❌ Watchlist is empty. Add some items first!")
        return
    
    # Step 2: Pick first item
    item = watchlist[0]
    guid = item.get("guid")
    rating_key = item.get("ratingKey")
    title = item.get("title")
    year = item.get("year", "N/A")
    
    print(f"\n[2] Selected item to test:")
    print(f"    Title: {title} ({year})")
    print(f"    GUID: {guid}")
    print(f"    Rating Key: {rating_key}")
    
    # Step 3: Try removing with ratingKey
    print(f"\n[3] Removing '{title}' using ratingKey...")
    success, response = await remove_from_watchlist(token, rating_key)
    print(f"    Response: {response}")
    
    if success:
        print(f"    ✅ Successfully removed with ratingKey!")
        
        # Add back
        print(f"\n[4] Adding '{title}' back...")
        add_success, add_response = await add_to_watchlist(token, rating_key)
        print(f"    Response: {add_response}")
        
        if add_success:
            print(f"    ✅ Successfully added back!")
        else:
            print(f"    ❌ Failed to add back")
    else:
        # Try with full GUID
        print(f"\n[3b] Trying with full GUID...")
        success, response = await remove_from_watchlist(token, guid)
        print(f"    Response: {response}")
        
        if success:
            print(f"    ✅ Successfully removed with GUID!")
            
            # Add back
            print(f"\n[4] Adding '{title}' back...")
            add_success, add_response = await add_to_watchlist(token, guid)
            print(f"    Response: {add_response}")
        else:
            print(f"    ❌ Both methods failed")
            
            # Debug: show all item keys
            print(f"\n[DEBUG] Item data:")
            for key in sorted(item.keys()):
                print(f"    {key}: {item.get(key)}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_watchlist_modify.py YOUR_PLEX_TOKEN")
        sys.exit(1)
    
    token = sys.argv[1]
    asyncio.run(main(token))
