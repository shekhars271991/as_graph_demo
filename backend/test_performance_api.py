#!/usr/bin/env python3
"""
Test Performance Metrics API
Test script to verify that the performance metrics API endpoints work correctly
"""

import requests
import json
from datetime import datetime

def test_performance_api():
    """Test the performance metrics API endpoints"""
    base_url = "http://localhost:4000"
    
    print("🧪 Testing Performance Metrics API Endpoints...")
    print("=" * 60)
    
    # Test 1: Get performance stats
    print("\n📊 Test 1: GET /performance/stats")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/performance/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Service: {data.get('service')}")
            stats = data.get('stats', {})
            if "error" not in stats:
                print(f"Total Calls: {stats.get('total_calls', 0)}")
                print(f"Total Time: {stats.get('total_time_ms', 0):.2f} ms")
                print(f"Average Overall Time: {stats.get('avg_overall_time_ms', 0):.2f} ms")
                print(f"Average Graph Call Time: {stats.get('avg_graph_call_time_ms', 0):.2f} ms")
                print(f"Last Updated: {stats.get('last_updated', 'N/A')}")
            else:
                print(f"❌ Error: {stats.get('error')}")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 2: Get performance overview
    print("\n📊 Test 2: GET /performance/overview")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/performance/overview")
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Service: {data.get('service')}")
            overview = data.get('overview', {})
            stats = overview.get('stats', {})
            if "error" not in stats:
                print(f"Total Calls: {stats.get('total_calls', 0)}")
                print(f"Recent Logs Count: {overview.get('recent_logs_count', 0)}")
                print(f"Sample Logs: {len(overview.get('sample_logs', []))}")
            else:
                print(f"❌ Error: {stats.get('error')}")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 3: Get performance logs (without transaction ID)
    print("\n📊 Test 3: GET /performance/logs")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/performance/logs")
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Message: {data.get('message')}")
            print(f"Note: {data.get('note')}")
            print("Available endpoints:")
            for endpoint in data.get('available_endpoints', []):
                print(f"  - {endpoint}")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 4: Get specific transaction log (using a known transaction ID)
    print("\n📊 Test 4: GET /performance/logs?transaction_id=test_tx_001")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/performance/logs?transaction_id=test_tx_001")
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Transaction ID: {data.get('transaction_id')}")
            log = data.get('log', {})
            print(f"Overall Time: {log.get('overall_ms', 0)} ms")
            print(f"Graph Calls: {log.get('graph_calls', 0)}")
            print(f"Total Graph Time: {log.get('total_graph_ms', 0)} ms")
        elif response.status_code == 404:
            print("ℹ️  Transaction log not found (this is expected if no test data exists)")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test 5: Get specific transaction log (using the real transaction ID from AQL)
    print("\n📊 Test 5: GET /performance/logs?transaction_id=ed5d6eca-38d8-45b1-8fb8-a8fc88c66a68")
    print("-" * 30)
    try:
        response = requests.get(f"{base_url}/performance/logs?transaction_id=ed5d6eca-38d8-45b1-8fb8-a8fc88c66a68")
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Transaction ID: {data.get('transaction_id')}")
            log = data.get('log', {})
            print(f"Overall Time: {log.get('overall_ms', 0)} ms")
            print(f"Graph Calls: {log.get('graph_calls', 0)}")
            print(f"Total Graph Time: {log.get('total_graph_ms', 0)} ms")
            print(f"Timestamp: {log.get('timestamp')}")
        elif response.status_code == 404:
            print("ℹ️  Transaction log not found")
        else:
            print(f"❌ Failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n🎉 Performance Metrics API Testing Completed!")
    print("\n💡 API Endpoints Available:")
    print("  - GET /performance/stats - Get aggregate performance statistics")
    print("  - GET /performance/overview - Get comprehensive performance overview")
    print("  - GET /performance/logs - Get performance logs (requires transaction_id parameter)")
    print("  - GET /performance/logs?transaction_id={id} - Get specific transaction log")

if __name__ == "__main__":
    test_performance_api()
