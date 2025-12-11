#!/usr/bin/env python
"""
Test script to verify Fever API functionality
"""
import hashlib
import requests
import json


def test_fever_api():
    """Test basic Fever API endpoints"""
    base_url = "http://localhost:8000/api/"
    
    # Test data
    email = "test@example.com"
    password = "testpassword"
    
    # Calculate API key (md5 of email:password)
    api_key = hashlib.md5(f"{email}:{password}".encode()).hexdigest()
    
    print("=" * 60)
    print("Fever API Test Script")
    print("=" * 60)
    print(f"\nBase URL: {base_url}")
    print(f"Email: {email}")
    print(f"API Key: {api_key}")
    
    # Test 1: Check authentication failure
    print("\n" + "-" * 60)
    print("Test 1: Authentication (should fail without valid credentials)")
    print("-" * 60)
    try:
        response = requests.post(base_url, data={'api_key': 'invalid_key'})
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        assert data['auth'] == 0, "Should not be authenticated with invalid key"
        assert data['api_version'] == 3, "API version should be 3"
        print("✓ Test passed")
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    # Test 2: Groups endpoint (unauthenticated)
    print("\n" + "-" * 60)
    print("Test 2: Groups endpoint (unauthenticated)")
    print("-" * 60)
    try:
        response = requests.get(base_url, params={'groups': ''})
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(data, indent=2)}")
        assert data['auth'] == 0, "Should not be authenticated"
        assert 'groups' not in data, "Should not return groups without auth"
        print("✓ Test passed")
    except Exception as e:
        print(f"✗ Test failed: {e}")
    
    print("\n" + "=" * 60)
    print("Setup Instructions:")
    print("=" * 60)
    print("\nTo fully test the API, create a user first:")
    print("\n1. Start the Django shell:")
    print("   uv run python manage.py shell")
    print("\n2. Create a test user:")
    print("   from api.models import FeverUser")
    print(f"   user = FeverUser.objects.create_user(email='{email}', password='{password}')")
    print("   user.save()")
    print("\n3. Add some test data (optional):")
    print("   from api.models import Group, Feed")
    print("   group = Group.objects.create(user=user, title='Test Group')")
    print("   import hashlib")
    print("   url = 'https://news.ycombinator.com/rss'")
    print("   checksum = int(hashlib.md5(url.encode()).hexdigest()[:8], 16)")
    print("   feed = Feed.objects.create(user=user, title='Hacker News', url=url, url_checksum=checksum)")
    print("   feed.groups.add(group)")
    print("\n4. Run this script again")
    print("\n5. Refresh feeds:")
    print("   uv run python manage.py refresh_feeds --user test@example.com")


if __name__ == '__main__':
    test_fever_api()
