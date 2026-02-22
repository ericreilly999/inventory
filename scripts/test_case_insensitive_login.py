#!/usr/bin/env python3
"""Test case-insensitive username login."""

import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

DEV_URL = "http://dev-inventory-alb-62171694.us-west-2.elb.amazonaws.com"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

def test_login(username: str, password: str) -> bool:
    """Test login with given username."""
    print(f"\n🔐 Testing login with username: '{username}'")
    
    try:
        response = requests.post(
            f"{DEV_URL}/api/v1/auth/login",
            data={"username": username, "password": password},
            timeout=10,
        )
        
        if response.status_code == 200:
            print(f"   ✅ Success! Logged in as '{username}'")
            data = response.json()
            print(f"   User in response: {data.get('user', {}).get('username')}")
            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Test case-insensitive login."""
    print("=" * 60)
    print("Testing Case-Insensitive Username Login")
    print("=" * 60)
    
    if not ADMIN_PASSWORD:
        print("❌ ADMIN_PASSWORD environment variable not set")
        sys.exit(1)
    
    # Test different case variations
    test_cases = [
        "admin",      # lowercase
        "Admin",      # title case
        "ADMIN",      # uppercase
        "aDmIn",      # mixed case
    ]
    
    results = []
    for username in test_cases:
        success = test_login(username, ADMIN_PASSWORD)
        results.append((username, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    print("=" * 60)
    
    for username, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - Login with '{username}'")
    
    # Check if all passed
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n✅ All tests passed! Case-insensitive login is working.")
    else:
        print("\n❌ Some tests failed. Case-insensitive login is NOT working.")
        print("\nDebugging steps:")
        print("1. Check if the user service deployed correctly")
        print("2. Check CloudWatch logs for the user service")
        print("3. Verify the database has the updated code")
        sys.exit(1)


if __name__ == "__main__":
    main()
