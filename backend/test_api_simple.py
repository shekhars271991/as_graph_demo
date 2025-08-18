#!/usr/bin/env python3
"""
Simple API Test Script
Test the performance metrics API endpoints using only built-in Python modules
"""

import urllib.request
import urllib.parse
import json

def test_api_endpoint(url, description):
    """Test a single API endpoint"""
    print(f"\n🧪 Testing: {description}")
    print(f"URL: {url}")
    print("-" * 50)
    
    try:
        # Create request
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Performance-API-Test/1.0')
        
        # Make request
        with urllib.request.urlopen(req) as response:
            data = response.read()
            status_code = response.getcode()
            
            print(f"✅ Status: {status_code}")
            
            # Try to parse JSON response
            try:
                json_data = json.loads(data.decode('utf-8'))
                print("📊 Response:")
                print(json.dumps(json_data, indent=2))
            except json.JSONDecodeError:
                print("📄 Raw Response:")
                print(data.decode('utf-8'))
                
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        try:
            error_data = json.loads(e.read().decode('utf-8'))
            print("📊 Error Response:")
            print(json.dumps(error_data, indent=2))
        except:
            print("📄 Raw Error Response:")
            print(e.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Request Failed: {e}")

def main():
    """Test all performance metrics API endpoints"""
    base_url = "http://localhost:4000"
    
    print("🚀 Performance Metrics API Testing")
    print("=" * 60)
    
    # Test endpoints
    endpoints = [
        (f"{base_url}/performance/stats", "Performance Statistics"),
        (f"{base_url}/performance/overview", "Performance Overview"),
        (f"{base_url}/performance/logs", "Performance Logs (General)"),
        (f"{base_url}/performance/logs?transaction_id=test_tx_001", "Performance Logs (Specific Transaction)"),
        (f"{base_url}/performance/logs?transaction_id=ed5d6eca-38d8-45b1-8fb8-a8fc88c66a68", "Performance Logs (Real Transaction)"),
    ]
    
    for url, description in endpoints:
        test_api_endpoint(url, description)
    
    print("\n🎉 API Testing Completed!")
    print("\n💡 Available Endpoints:")
    print("  - GET /performance/stats - Get aggregate performance statistics")
    print("  - GET /performance/overview - Get comprehensive performance overview")
    print("  - GET /performance/logs - Get performance logs (requires transaction_id parameter)")
    print("  - GET /performance/logs?transaction_id={id} - Get specific transaction log")

if __name__ == "__main__":
    main()
