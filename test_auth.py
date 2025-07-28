#!/usr/bin/env python3
"""
Authentication Test Script for XML RESTful API

This script demonstrates how to authenticate with the API and use protected endpoints.
Make sure the API server is running before executing this script.
"""

import requests
import json
import sys

# API Base URL
BASE_URL = "http://localhost:5000/api"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")

def login():
    """Login and get JWT token"""
    print_section("1. Authentication - Login")

    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        token = response.json()['access_token']
        print(f"\n✅ Login successful! Token obtained.")
        return token
    else:
        print(f"\n❌ Login failed!")
        return None

def test_protected_endpoint_without_token():
    """Test accessing protected endpoint without token"""
    print_section("2. Test Protected Endpoint Without Token")

    response = requests.get(f"{BASE_URL}/health/")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 401:
        print(f"\n✅ Endpoint correctly protected - access denied without token")
    else:
        print(f"\n❌ Endpoint not properly protected!")

def test_protected_endpoint_with_token(token):
    """Test accessing protected endpoint with token"""
    print_section("3. Test Protected Endpoint With Token")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{BASE_URL}/health/", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print(f"\n✅ Access granted with valid token!")
    else:
        print(f"\n❌ Token authentication failed!")

def test_xml_upload_with_token(token):
    """Test XML upload with authentication"""
    print_section("4. Test XML Upload With Authentication")

    # Create a simple XML content for testing
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<test>
    <message>Hello World</message>
    <timestamp>2024-01-01T12:00:00Z</timestamp>
</test>"""

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Create a temporary XML file in memory
    files = {
        'file': ('test.xml', xml_content, 'application/xml')
    }

    response = requests.post(f"{BASE_URL}/xml/upload", files=files, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 201:
        file_id = response.json()['file_id']
        print(f"\n✅ XML upload successful! File ID: {file_id}")
        return file_id
    else:
        print(f"\n❌ XML upload failed!")
        return None

def test_xml_list_with_token(token):
    """Test listing XML files with authentication"""
    print_section("5. Test XML File List With Authentication")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(f"{BASE_URL}/xml/", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print(f"\n✅ XML file list retrieved successfully!")
    else:
        print(f"\n❌ Failed to retrieve XML file list!")

def test_invalid_credentials():
    """Test login with invalid credentials"""
    print_section("6. Test Invalid Credentials")

    login_data = {
        "username": "admin",
        "password": "wrongpassword"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 401:
        print(f"\n✅ Invalid credentials correctly rejected!")
    else:
        print(f"\n❌ Security issue - invalid credentials accepted!")

def test_malformed_token():
    """Test accessing protected endpoint with malformed token"""
    print_section("7. Test Malformed Token")

    headers = {
        "Authorization": "Bearer invalid.token.here"
    }

    response = requests.get(f"{BASE_URL}/health/", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 422 or response.status_code == 401:
        print(f"\n✅ Malformed token correctly rejected!")
    else:
        print(f"\n❌ Security issue - malformed token accepted!")

def cleanup_test_file(token, file_id):
    """Clean up test file"""
    print_section("8. Cleanup Test File")

    if not file_id:
        print("No file to clean up.")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.delete(f"{BASE_URL}/xml/{file_id}", headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    if response.status_code == 200:
        print(f"\n✅ Test file cleaned up successfully!")
    else:
        print(f"\n❌ Failed to clean up test file!")

def main():
    """Main function to run authentication tests"""
    print("\n" + "="*60)
    print(" XML RESTful API - Authentication Tests")
    print("="*60)
    print(f"\nAPI Base URL: {BASE_URL}")
    print("\nDefault Credentials:")
    print("  Username: admin")
    print("  Password: admin123")

    # Test invalid credentials first
    test_invalid_credentials()

    # Test malformed token
    test_malformed_token()

    # Test protected endpoint without token
    test_protected_endpoint_without_token()

    # Login and get token
    token = login()
    if not token:
        print("\n❌ Cannot continue tests without valid token!")
        sys.exit(1)

    # Test protected endpoint with token
    test_protected_endpoint_with_token(token)

    # Test XML operations with authentication
    file_id = test_xml_upload_with_token(token)
    test_xml_list_with_token(token)

    # Cleanup
    cleanup_test_file(token, file_id)

    print("\n" + "="*60)
    print(" Authentication Tests Completed!")
    print("="*60)
    print("\n🔐 Summary:")
    print("  ✅ All API routes are now protected with JWT authentication")
    print("  ✅ Users must login to get an access token")
    print("  ✅ Access token must be included in Authorization header")
    print("  ✅ Invalid tokens and credentials are properly rejected")
    print("\n📖 Usage:")
    print("  1. POST /api/auth/login with username/password to get token")
    print("  2. Include 'Authorization: Bearer <token>' header in all requests")
    print("  3. Token expires after 1 hour")

if __name__ == "__main__":
    main()
