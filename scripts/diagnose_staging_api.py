"""Diagnose staging API routing issues."""

import requests
import sys

STAGING_URL = "http://staging-inventory-alb-349623539.us-east-1.elb.amazonaws.com"

def login():
    """Login and get token."""
    try:
        response = requests.post(
            f"{STAGING_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin"},
            timeout=10
        )
        if response.status_code != 200:
            print(f"Login failed: {response.status_code}")
            print(response.text)
            return None
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login error: {e}")
        return None

def test_endpoints(token):
    """Test various endpoint paths."""
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/api/v1/locations",
        "/api/v1/locations/",
        "/api/location/locations",
        "/api/location/v1/locations",
        "/locations",
        "/api/v1/items/parent-items",
        "/api/v1/users",
        "/api/v1/roles",
    ]
    
    print("\nTesting endpoints:")
    print("=" * 70)
    
    for endpoint in endpoints:
        try:
            response = requests.get(
                f"{STAGING_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {endpoint:40} -> {response.status_code}")
            
            if response.status_code not in [200, 401, 403]:
                print(f"   Response: {response.text[:100]}")
        except Exception as e:
            print(f"✗ {endpoint:40} -> ERROR: {e}")
    
    print("=" * 70)

def check_health():
    """Check health endpoints."""
    print("\nChecking health endpoints:")
    print("=" * 70)
    
    health_endpoints = [
        "/health",
        "/api/v1/health",
    ]
    
    for endpoint in health_endpoints:
        try:
            response = requests.get(
                f"{STAGING_URL}{endpoint}",
                timeout=10
            )
            print(f"✓ {endpoint:40} -> {response.status_code}")
            if response.status_code == 200:
                print(f"   {response.json()}")
        except Exception as e:
            print(f"✗ {endpoint:40} -> ERROR: {e}")
    
    print("=" * 70)

def main():
    """Main diagnostic function."""
    print("=" * 70)
    print("Staging API Routing Diagnostic")
    print("=" * 70)
    
    # Check health first
    check_health()
    
    # Login
    print("\nLogging in...")
    token = login()
    if not token:
        print("\n✗ Cannot login to staging")
        sys.exit(1)
    print("✓ Login successful")
    
    # Test endpoints
    test_endpoints(token)

if __name__ == "__main__":
    main()
