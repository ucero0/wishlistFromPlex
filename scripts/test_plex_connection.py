#!/usr/bin/env python3
"""
Manual test script for Plex API connectivity.

Usage:
    python scripts/test_plex_connection.py YOUR_PLEX_TOKEN

This tests Plex API calls using direct HTTP requests.
"""
import sys
import httpx


PLEX_API_HEADERS = {
    "Accept": "application/json",
    "X-Plex-Client-Identifier": "plex-wishlist-service",
    "X-Plex-Product": "Plex Wishlist Service",
    "X-Plex-Version": "1.0.0",
}


def test_account_connection(token: str):
    """Test basic account connection."""
    print("\n" + "=" * 60)
    print("Testing Plex Account Connection")
    print("=" * 60)
    
    url = "https://plex.tv/api/v2/user"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Connected successfully!")
                print(f"   Username: {data.get('username')}")
                print(f"   Email: {data.get('email')}")
                print(f"   UUID: {data.get('uuid')}")
                print(f"   Title: {data.get('title')}")
                return data
            else:
                print(f"❌ Failed: {response.status_code} - {response.text[:200]}")
                return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_watchlist(token: str):
    """Test fetching watchlist using direct API."""
    print("\n" + "=" * 60)
    print("Testing Watchlist Fetch")
    print("=" * 60)
    
    url = "https://discover.provider.plex.tv/library/sections/watchlist/all"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                media_container = data.get("MediaContainer", {})
                items = media_container.get("Metadata", [])
                
                print(f"✅ Fetched {len(items)} items from watchlist")
                
                if items:
                    print("\nFirst 5 items:")
                    for i, item in enumerate(items[:5]):
                        print(f"\n   [{i+1}] {item.get('title', 'N/A')}")
                        print(f"       GUID: {item.get('guid', 'N/A')}")
                        print(f"       Rating Key: {item.get('ratingKey', 'N/A')}")
                        print(f"       Type: {item.get('type', 'N/A')}")
                        print(f"       Year: {item.get('year', 'N/A')}")
                
                return items
            else:
                print(f"❌ Error: {response.status_code} - {response.text[:200]}")
                return []
    except Exception as e:
        print(f"❌ Error fetching watchlist: {e}")
        return []


def test_search(token: str, query: str = "Breaking Bad"):
    """Test searching Plex using direct API."""
    print("\n" + "=" * 60)
    print(f"Testing Search: '{query}'")
    print("=" * 60)
    
    url = "https://discover.provider.plex.tv/library/search"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    params = {
        "query": query,
        "limit": 5,
        "searchTypes": "movies,tv",
        "includeMetadata": 1,
        "searchProviders": "discover",
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                media_container = data.get("MediaContainer", {})
                search_results = media_container.get("SearchResults", [])
                
                results = []
                for result_group in search_results:
                    for item in result_group.get("SearchResult", []):
                        metadata = item.get("Metadata")
                        if metadata:
                            results.append(metadata)
                
                print(f"✅ Found {len(results)} results")
                
                for i, item in enumerate(results[:5]):
                    print(f"\n   [{i+1}] {item.get('title', 'N/A')}")
                    print(f"       GUID: {item.get('guid', 'N/A')}")
                    print(f"       Type: {item.get('type', 'N/A')}")
                    print(f"       Year: {item.get('year', 'N/A')}")
                
                return results
            else:
                print(f"❌ Error: {response.status_code} - {response.text[:200]}")
                return []
    except Exception as e:
        print(f"❌ Error searching: {e}")
        return []


def test_servers(token: str):
    """Test listing connected servers."""
    print("\n" + "=" * 60)
    print("Testing Server Connection")
    print("=" * 60)
    
    url = "https://plex.tv/api/v2/resources"
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    params = {"includeHttps": 1, "includeRelay": 1}
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                resources = response.json()
                servers = [r for r in resources if r.get("provides") == "server"]
                
                print(f"✅ Found {len(servers)} server(s)")
                
                for server in servers:
                    print(f"\n   Server: {server.get('name')}")
                    print(f"   Client ID: {server.get('clientIdentifier')}")
                    print(f"   Owned: {server.get('owned')}")
                    
                    # Show connections
                    connections = server.get("connections", [])
                    if connections:
                        print(f"   Connections: {len(connections)}")
                        for conn in connections[:2]:
                            print(f"      - {conn.get('uri')}")
                
                return servers
            else:
                print(f"❌ Error: {response.status_code} - {response.text[:200]}")
                return []
    except Exception as e:
        print(f"❌ Error listing servers: {e}")
        return []


def test_add_remove_watchlist(token: str, guid: str):
    """Test adding/removing from watchlist."""
    print("\n" + "=" * 60)
    print(f"Testing Add/Remove Watchlist")
    print(f"GUID: {guid}")
    print("=" * 60)
    
    headers = {**PLEX_API_HEADERS, "X-Plex-Token": token}
    
    with httpx.Client(timeout=30.0) as client:
        # Test remove
        remove_url = "https://discover.provider.plex.tv/actions/removeFromWatchlist"
        try:
            response = client.put(remove_url, headers=headers, params={"ratingKey": guid})
            print(f"   Remove: {response.status_code} {'✅' if response.status_code == 200 else '⚠️'}")
        except Exception as e:
            print(f"   Remove: ❌ {e}")
        
        # Test add
        add_url = "https://discover.provider.plex.tv/actions/addToWatchlist"
        try:
            response = client.put(add_url, headers=headers, params={"ratingKey": guid})
            print(f"   Add: {response.status_code} {'✅' if response.status_code == 200 else '⚠️'}")
        except Exception as e:
            print(f"   Add: ❌ {e}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_plex_connection.py YOUR_PLEX_TOKEN")
        print("\nTo get your Plex token:")
        print("  1. Go to https://app.plex.tv")
        print("  2. Open browser DevTools (F12)")
        print("  3. Go to Application > Local Storage > https://app.plex.tv")
        print("  4. Find 'myPlexAccessToken'")
        sys.exit(1)
    
    token = sys.argv[1]
    
    # Test account
    account = test_account_connection(token)
    if not account:
        sys.exit(1)
    
    # Test watchlist
    watchlist = test_watchlist(token)
    
    # Test search
    test_search(token, "Breaking Bad")
    
    # Test servers
    test_servers(token)
    
    # Test add/remove if we have items
    if watchlist:
        guid = watchlist[0].get('guid')
        if guid:
            print("\n⚠️ Skipping add/remove test to avoid modifying your watchlist")
            print(f"   To test, run: test_add_remove_watchlist(token, '{guid}')")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
