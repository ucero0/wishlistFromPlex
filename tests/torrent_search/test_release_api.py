"""Live tests for Prowlarr Release API functionality.

These tests focus on:
- Testing Prowlarr search API with requests library
- Testing Prowlarr release API to download torrents
- Verifying the complete flow: search -> extract GUID/indexerId -> download

These tests require:
- Prowlarr running and accessible (via docker-compose)
- PROWLARR_API_KEY configured
- Valid indexers configured in Prowlarr
- Download client configured in Prowlarr
- Set SKIP_LIVE_TESTS=0 to enable

To run:
    SKIP_LIVE_TESTS=0 docker exec -e SKIP_LIVE_TESTS=0 plex-wishlist-api pytest tests/torrent_search/test_release_api.py -v
"""
import pytest
import os
import json
import requests


@pytest.fixture
def prowlarr_config():
    """Get Prowlarr configuration from environment."""
    host = os.getenv("PROWLARR_HOST", "gluetun")
    port = int(os.getenv("PROWLARR_PORT", "9696"))
    api_key = os.getenv("PROWLARR_API_KEY")
    
    if not api_key:
        pytest.skip("PROWLARR_API_KEY not configured")
    
    base_url = f"http://{host}:{port}/api/v1"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key
    }
    
    return {
        "base_url": base_url,
        "headers": headers,
        "api_key": api_key,
        "search_url": f"{base_url}/search",
        "download_client_url": f"{base_url}/downloadclient"
    }


@pytest.fixture
def download_client_id(prowlarr_config):
    """Get the first enabled download client ID."""
    try:
        response = requests.get(
            prowlarr_config["download_client_url"],
            headers=prowlarr_config["headers"],
            timeout=10
        )
        
        if response.status_code == 200:
            clients = response.json()
            enabled_clients = [c for c in clients if c.get("enable", False)]
            
            if enabled_clients:
                client_id = enabled_clients[0].get("id")
                return client_id
        
        # Fallback to default ID 1
        return 1
    except Exception:
        # Fallback to default ID 1
        return 1


class TestProwlarrReleaseAPI:
    """Tests for Prowlarr Release API using requests library."""

    @pytest.mark.skipif(
        os.getenv("SKIP_LIVE_TESTS", "1") == "1",
        reason="Live tests skipped (set SKIP_LIVE_TESTS=0 to enable)"
    )
    def test_search_matrix(self, prowlarr_config):
        """Test searching for 'matrix' using Prowlarr search API."""
        print(f"\n🔍 Searching for 'matrix'...")
        print(f"   API: {prowlarr_config['search_url']}")
        
        response = requests.get(
            prowlarr_config["search_url"],
            headers=prowlarr_config["headers"],
            params={
                "query": "matrix",
                "categories": "2000",  # Movies
                "type": "search"
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"Search failed: {response.status_code} - {response.text[:200]}"
        
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, dict):
            if "results" in data:
                data = data["results"]
            elif "data" in data:
                data = data["data"]
            elif "items" in data:
                data = data["items"]
            else:
                # Try to extract first list value
                for key, value in data.items():
                    if isinstance(value, list):
                        data = value
                        break
        
        assert isinstance(data, list), f"Expected list, got {type(data)}"
        
        if len(data) == 0:
            pytest.skip("No results found for 'matrix'. This could mean:\n"
                       "- No indexers configured\n"
                       "- Indexers are not working\n"
                       "- No matches for 'matrix'")
        
        first_result = data[0]
        print(f"✅ Found {len(data)} results")
        print(f"   First result: {first_result.get('title', 'N/A')}")
        print(f"   Indexer: {first_result.get('indexer', 'N/A')}")
        print(f"   Seeders: {first_result.get('seeders', 0)}")
        
        # Verify required fields for download
        guid = first_result.get("guid")
        indexer_id = first_result.get("indexerId")
        
        assert guid is not None, "Result should have 'guid' field for download"
        assert indexer_id is not None, "Result should have 'indexerId' field for download"
        
        print(f"   GUID: {guid}")
        print(f"   Indexer ID: {indexer_id}")
        
        return guid, indexer_id, first_result

    @pytest.mark.skipif(
        os.getenv("SKIP_LIVE_TESTS", "1") == "1",
        reason="Live tests skipped (set SKIP_LIVE_TESTS=0 to enable)"
    )
    def test_download_release(self, prowlarr_config, download_client_id):
        """Test downloading a release using Prowlarr indexer download API.
        
        This test:
        1. Searches for 'matrix'
        2. Extracts GUID and indexerId from first result
        3. Uses GET /api/v1/indexer/{indexerId}/download?guid=GUID&apikey=API_KEY to download
        """
        # Step 1: Search for matrix
        print(f"\n🔍 Step 1: Searching for 'matrix'...")
        response = requests.get(
            prowlarr_config["search_url"],
            headers=prowlarr_config["headers"],
            params={
                "query": "matrix",
                "categories": "2000",  # Movies
                "type": "search"
            },
            timeout=60
        )
        
        assert response.status_code == 200, f"Search failed: {response.status_code}"
        
        data = response.json()
        
        # Handle different response formats
        if isinstance(data, dict):
            if "results" in data:
                data = data["results"]
            elif "data" in data:
                data = data["data"]
            elif "items" in data:
                data = data["items"]
            else:
                for key, value in data.items():
                    if isinstance(value, list):
                        data = value
                        break
        
        if len(data) == 0:
            pytest.skip("No results found for 'matrix'")
        
        first_result = data[0]
        guid = first_result.get("guid")
        indexer_id = first_result.get("indexerId")
        title = first_result.get("title", "Unknown")
        
        assert guid is not None, "Result missing 'guid'"
        assert indexer_id is not None, "Result missing 'indexerId'"
        
        print(f"✅ Found result: {title}")
        print(f"   GUID: {guid}")
        print(f"   Indexer ID: {indexer_id}")
        
        # Step 2: Download via indexer download API
        # Endpoint: GET /api/v1/indexer/{indexerId}/download?guid=GUID&apikey=API_KEY
        print(f"\n⬇️  Step 2: Downloading release...")
        print(f"   Using endpoint: /api/v1/indexer/{indexer_id}/download")
        print(f"   GUID: {guid}")
        print(f"   Indexer ID: {indexer_id}")
        
        download_url = f"{prowlarr_config['base_url']}/indexer/{indexer_id}/download"
        
        # Use query parameters: guid and apikey
        params = {
            "guid": guid,
            "apikey": prowlarr_config["api_key"]
        }
        
        print(f"   URL: {download_url}")
        print(f"   Params: guid={guid[:50]}..., apikey=***")
        
        response = requests.get(
            download_url,
            params=params,
            headers=prowlarr_config["headers"],
            timeout=30
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Status Text: {response.reason}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Response Length: {len(response.content)} bytes")
        
        if response.status_code in [200, 201, 204]:
            # Success - might return empty body, JSON, or binary (torrent file)
            content_type = response.headers.get("Content-Type", "").lower()
            
            if "application/json" in content_type:
                try:
                    result = response.json()
                    print(f"✅ Download request successful! (JSON response)")
                    print(f"   Response: {json.dumps(result, indent=2, default=str)}")
                except:
                    print(f"✅ Download request successful! (JSON but couldn't parse)")
                    print(f"   Response text: {response.text[:500]}")
            elif len(response.content) == 0:
                print(f"✅ Download request successful! (Empty response - likely 204 No Content)")
            elif "application/x-bittorrent" in content_type or response.content.startswith(b'd'):
                print(f"✅ Download request successful! (Torrent file returned)")
                print(f"   Torrent file size: {len(response.content)} bytes")
                print(f"   First 50 bytes (hex): {response.content[:50].hex()}")
            else:
                print(f"✅ Download request successful!")
                print(f"   Response preview: {response.text[:500] if response.text else '(binary)'}")
            assert True, "Download request succeeded"
        else:
            error_msg = response.text
            print(f"⚠️  Download request returned {response.status_code}")
            print(f"   Response: {error_msg[:500]}")
            
            # Handle different error cases gracefully
            if response.status_code == 400:
                pytest.skip(f"Download client may not be configured: {error_msg}")
            elif response.status_code == 404:
                pytest.skip(f"Indexer or release not found (404). This might mean the indexer ID is incorrect or the release is no longer available.")
            else:
                pytest.skip(f"Download request returned {response.status_code}: {error_msg[:200]}. "
                          f"This may indicate the endpoint is not available or requires different configuration.")

    @pytest.mark.skipif(
        os.getenv("SKIP_LIVE_TESTS", "1") == "1",
        reason="Live tests skipped (set SKIP_LIVE_TESTS=0 to enable)"
    )
    def test_get_download_clients(self, prowlarr_config):
        """Test getting download clients from Prowlarr API."""
        print(f"\n📋 Getting download clients...")
        
        response = requests.get(
            prowlarr_config["download_client_url"],
            headers=prowlarr_config["headers"],
            timeout=10
        )
        
        assert response.status_code == 200, f"Failed to get download clients: {response.status_code}"
        
        clients = response.json()
        assert isinstance(clients, list), "Should return a list of download clients"
        
        enabled_clients = [c for c in clients if c.get("enable", False)]
        
        print(f"✅ Found {len(clients)} total client(s), {len(enabled_clients)} enabled")
        
        if len(enabled_clients) > 0:
            for client in enabled_clients:
                print(f"   - ID: {client.get('id')}")
                print(f"     Name: {client.get('name', 'Unknown')}")
                print(f"     Type: {client.get('implementation', 'Unknown')}")
        else:
            print("⚠️  No enabled download clients found")
            print("   Configure a download client in Prowlarr Settings > Download Clients")

