#!/usr/bin/env python3
"""
Performance Logs Query Utility
Query and display performance metrics from the logs namespace using Aerospike key-value storage
"""

import asyncio
import aerospike

async def query_performance_logs():
    """Query and display performance logs from logs namespace"""
    try:
        # Initialize Aerospike client directly
        config = {
            'hosts': [('127.0.0.1', 3000)]
        }
        
        client = aerospike.client(config)
        client.connect()
        
        print("🔍 Querying Performance Logs from 'logs' namespace...")
        print("=" * 60)
        
        # Get aggregate statistics
        print("\n📊 AGGREGATE PERFORMANCE STATISTICS:")
        print("-" * 40)
        
        try:
            stats_key = ('logs', None, 'rt1_aggregate_stats')
            (key, meta, stats_data) = client.get(stats_key)
            
            if stats_data:
                print(f"Total Calls: {stats_data.get('total_calls', 0)}")
                print(f"Total Time: {stats_data.get('total_ms', 0):.2f} ms")
                print(f"Average Overall Time: {stats_data.get('avg_overall_ms', 0):.2f} ms")
                print(f"Average Graph Call Time: {stats_data.get('avg_graph_ms', 0):.2f} ms")
                print(f"Last Updated: {stats_data.get('updated', 'N/A')}")
            else:
                print("No aggregate statistics found.")
                
        except aerospike.exception.RecordNotFound:
            print("No aggregate statistics found.")
        except Exception as e:
            print(f"❌ Error fetching stats: {e}")
        
        # Query recent performance logs
        print("\n📝 RECENT PERFORMANCE LOGS:")
        print("-" * 40)
        
        logs = []
        
        # Try to discover existing performance logs by looking for common patterns
        # Since Aerospike doesn't have built-in scanning, we'll try to get logs
        # that we know exist from the AQL query
        known_transaction_ids = [
            'ed5d6eca-38d8-45b1-8fb8-a8fc88c66a68',  # From AQL query
            'test_tx_001',  # From test script
            'test_tx_002'   # From test script
        ]
        
        for tx_id in known_transaction_ids:
            try:
                log_key = ('logs', None, f'rt1_perf_log:{tx_id}')
                (key, meta, log_data) = client.get(log_key)
                if log_data:
                    logs.append(log_data)
            except aerospike.exception.RecordNotFound:
                continue
            except Exception as e:
                print(f"Error fetching log {tx_id}: {e}")
                continue
        
        # Also try to get some logs with common patterns
        # This is a workaround since Aerospike doesn't support wildcard queries
        for i in range(1, 6):
            try:
                # Try some common transaction ID patterns
                patterns = [
                    f'tx_{i}',
                    f'transaction_{i}',
                    f'id_{i}'
                ]
                
                for pattern in patterns:
                    try:
                        log_key = ('logs', None, f'rt1_perf_log:{pattern}')
                        (key, meta, log_data) = client.get(log_key)
                        if log_data:
                            logs.append(log_data)
                            break  # Found one, no need to try other patterns
                    except aerospike.exception.RecordNotFound:
                        continue
                    except Exception:
                        continue
                        
            except Exception:
                continue
        
        if not logs:
            print("No performance logs found.")
            print("Note: Logs are stored with keys like 'rt1_perf_log:{transaction_id}' in the 'logs' namespace")
        else:
            for i, log in enumerate(logs, 1):
                print(f"\n{i}. Transaction: {log.get('tx_id', 'N/A')}")
                print(f"   Overall Time: {log.get('overall_ms', 0)} ms")
                print(f"   Graph Calls: {log.get('graph_calls', 0)}")
                print(f"   Total Graph Time: {log.get('total_graph_ms', 0)} ms")
                print(f"   Timestamp: {log.get('timestamp', 'N/A')}")
                
                # Show graph call details
                call_details = log.get('call_details', [])
                if call_details:
                    print(f"   Graph Call Breakdown:")
                    for call in call_details:
                        print(f"     - {call.get('operation', 'N/A')}: {call.get('time_ms', 0)} ms")
        
        # Show how to query specific logs
        print("\n💡 QUERYING SPECIFIC LOGS:")
        print("-" * 30)
        print("To query specific performance logs, use these keys in the 'logs' namespace:")
        print("- 'rt1_aggregate_stats' - Overall statistics")
        print("- 'rt1_perf_log:{transaction_id}' - Individual transaction logs")
        print("\nExample AQL queries:")
        print("- SELECT * FROM logs WHERE PK = 'rt1_aggregate_stats'")
        print("- SELECT * FROM logs WHERE PK LIKE 'rt1_perf_log:%'")
        
        # Show how to query using Python client
        print("\n🐍 PYTHON CLIENT EXAMPLES:")
        print("-" * 30)
        print("Get aggregate stats:")
        print("  stats_key = ('logs', None, 'rt1_aggregate_stats')")
        print("  (key, meta, data) = client.get(stats_key)")
        print("\nGet specific transaction log:")
        print("  log_key = ('logs', None, 'rt1_perf_log:tx_123')")
        print("  (key, meta, data) = client.get(log_key)")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(query_performance_logs())
