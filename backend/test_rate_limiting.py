#!/usr/bin/env python3
"""
Rate Limiting Test Script for VaultMind
Tests that rate limits are working correctly
"""
import time
import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000"
ENDPOINTS = {
    "health": {"path": "/health", "method": "GET", "limit": 100, "window": 60},
    "chat": {"path": "/agent/chat", "method": "POST", "limit": 10, "window": 60},
}

def test_rate_limit(endpoint_name: str, config: dict):
    """Test rate limiting for a specific endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing {endpoint_name.upper()} endpoint")
    print(f"Limit: {config['limit']} requests per {config['window']}s")
    print(f"{'='*60}\n")
    
    url = f"{BASE_URL}{config['path']}"
    success_count = 0
    rate_limited_count = 0
    
    # Send requests rapidly
    for i in range(config['limit'] + 5):  # Try 5 extra to trigger rate limit
        try:
            if config['method'] == "GET":
                response = requests.get(url, timeout=5)
            else:
                # For POST endpoints, we'd need a valid JWT
                # This test will fail auth but we can still see rate limit headers
                response = requests.post(
                    url,
                    json={"message": f"Test {i+1}"},
                    timeout=5
                )
            
            # Check response
            if response.status_code == 429:
                rate_limited_count += 1
                retry_after = response.headers.get('Retry-After', 'unknown')
                print(f"❌ Request {i+1}: RATE LIMITED (429) - Retry after {retry_after}s")
            elif response.status_code == 401:
                # Expected for protected endpoints without JWT
                success_count += 1
                print(f"✅ Request {i+1}: AUTH REQUIRED (401) - Rate limit not hit")
            elif response.status_code == 200:
                success_count += 1
                print(f"✅ Request {i+1}: SUCCESS (200)")
            else:
                print(f"⚠️  Request {i+1}: UNEXPECTED ({response.status_code})")
            
            # Show rate limit headers
            limit_header = response.headers.get('X-RateLimit-Limit')
            remaining = response.headers.get('X-RateLimit-Remaining')
            if limit_header:
                print(f"   Rate limit: {remaining}/{limit_header} remaining")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request {i+1}: ERROR - {str(e)}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY for {endpoint_name.upper()}")
    print(f"{'='*60}")
    print(f"Total requests: {config['limit'] + 5}")
    print(f"Successful (within limit): {success_count}")
    print(f"Rate limited (429): {rate_limited_count}")
    
    if rate_limited_count > 0:
        print(f"\n✅ Rate limiting is WORKING correctly!")
    else:
        print(f"\n⚠️  No rate limits hit - either limit is too high or server is not running")
    
    return rate_limited_count > 0


def main():
    """Main test runner"""
    print(f"\n{'#'*60}")
    print(f"VaultMind Rate Limiting Test Suite")
    print(f"{'#'*60}\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Server is running at {BASE_URL}")
        print(f"   Status: {response.json()}")
    except requests.exceptions.RequestException:
        print(f"❌ Error: Server is not running at {BASE_URL}")
        print(f"\nPlease start the server first:")
        print(f"   cd backend && uvicorn main:app --reload")
        sys.exit(1)
    
    # Test health endpoint (public, high limit)
    test_rate_limit("health", ENDPOINTS["health"])
    
    # Note about protected endpoints
    print(f"\n{'='*60}")
    print(f"NOTE: Chat endpoint requires JWT authentication")
    print(f"To fully test /agent/chat rate limiting:")
    print(f"1. Get a JWT token from Auth0")
    print(f"2. Add it to the request headers:")
    print(f"   headers = {{'Authorization': 'Bearer YOUR_JWT_TOKEN'}}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
