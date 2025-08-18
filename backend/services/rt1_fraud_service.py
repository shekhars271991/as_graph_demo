"""
RT1 Fraud Detection Service
Real-time detection of transactions involving flagged accounts

This service implements RT1 fraud detection which checks if a transaction
involves accounts that have been previously flagged as fraudulent.
"""

import asyncio
import logging
import time
import json
import aerospike
from datetime import datetime
from typing import Dict, Any, List
from services.graph_service import GraphService

# Setup logging
logger = logging.getLogger('fraud_detection.rt1')

class RT1FraudService:
    """RT1 Fraud Detection Service - Flagged Account Detection"""
    
    def __init__(self, graph_service: GraphService):
        self.graph_service = graph_service
        # Initialize performance tracking
        self.total_calls = 0
        self.total_time = 0.0
        self.graph_call_times = []
        
        # Initialize Aerospike client for logging
        try:
            config = {'hosts': [('127.0.0.1', 3000)]}
            self.aerospike_client = aerospike.client(config)
            self.aerospike_client.connect()
            logger.info("✅ Aerospike client initialized for performance logging")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Aerospike client: {e}")
            self.aerospike_client = None
    
    async def log_performance_metrics(self, transaction_id: str, overall_time: float, graph_call_details: List[Dict]):
        """Log performance metrics to the logs namespace using Aerospike key-value storage"""
        try:
            if not self.aerospike_client:
                logger.warning("⚠️ Aerospike client not available for performance logging")
                return
                
            loop = asyncio.get_event_loop()
            
            def store_performance_log():
                try:
                    # Store individual transaction performance log
                    log_key = ('logs', None, f'rt1_perf_log:{transaction_id}')
                    log_data = {
                        "service": "RT1_Fraud_Service",
                        "tx_id": transaction_id,
                        "overall_ms": round(overall_time * 1000, 2),
                        "graph_calls": len(graph_call_details),
                        "total_graph_ms": round(sum(call['time'] for call in graph_call_details) * 1000, 2),
                        "timestamp": datetime.now().isoformat(),
                        "call_type": "check_transaction",
                        "call_details": [
                            {
                                "operation": call['operation'],
                                "time_ms": round(call['time'] * 1000, 2)
                            } for call in graph_call_details
                        ]
                    }
                    
                    # Store in logs namespace
                    self.aerospike_client.put(log_key, log_data)
                    
                    # Update aggregate statistics
                    self.total_calls += 1
                    self.total_time += overall_time
                    self.graph_call_times.extend([call['time'] for call in graph_call_details])
                    
                    # Calculate averages
                    avg_overall_time = self.total_time / self.total_calls if self.total_calls > 0 else 0
                    avg_graph_call_time = sum(self.graph_call_times) / len(self.graph_call_times) if self.graph_call_times else 0
                    
                    # Store/update aggregate stats
                    stats_key = ('logs', None, 'rt1_aggregate_stats')
                    stats_data = {
                        "service": "RT1_Fraud_Service",
                        "total_calls": self.total_calls,
                        "total_ms": round(self.total_time * 1000, 2),
                        "avg_overall_ms": round(avg_overall_time * 1000, 2),
                        "avg_graph_ms": round(avg_graph_call_time * 1000, 2),
                        "created": datetime.now().isoformat(),
                        "updated": datetime.now().isoformat()
                    }
                    
                    self.aerospike_client.put(stats_key, stats_data)
                    
                    logger.info(f"📊 Performance metrics logged for transaction {transaction_id}: Overall: {overall_time*1000:.2f}ms, Graph calls: {len(graph_call_details)}")
                    
                except Exception as e:
                    logger.error(f"Error logging performance metrics: {e}")
            
            await loop.run_in_executor(None, store_performance_log)
            
        except Exception as e:
            logger.error(f"Error in performance logging: {e}")
    
    async def check_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if transaction involves flagged accounts (RT1)
        
        Args:
            transaction: Transaction data
            
        Returns:
            Dict with fraud detection results
        """
        start_time = time.time()
        graph_call_details = []
        
        try:
            if not self.graph_service.client:
                logger.warning("⚠️ Graph client not available for RT1 fraud detection")
                return {"is_fraud": False, "reason": "Graph client unavailable"}
            
            # Get sender and receiver account IDs from graph relationships
            # sender_account --TRANSFERS_TO--> transaction --TRANSFERS_FROM--> receiver_account
            
            loop = asyncio.get_event_loop()
            
            def get_account_ids():
                try:
                    call_start = time.time()
                    
                    # Find the transaction vertex
                    tx_vertex = self.graph_service.client.V().has_label("transaction").has("transaction_id", transaction['id']).next()
                    
                    # Get sender account (incoming TRANSFERS_TO edge)
                    sender_accounts = self.graph_service.client.V(tx_vertex).in_("TRANSFERS_TO").has_label("account").valueMap("account_id").to_list()
                    sender_account_id = sender_accounts[0].get("account_id", [""])[0] if sender_accounts else ""
                    
                    # Get receiver account (outgoing TRANSFERS_FROM edge)
                    receiver_accounts = self.graph_service.client.V(tx_vertex).out("TRANSFERS_FROM").has_label("account").valueMap("account_id").to_list()
                    receiver_account_id = receiver_accounts[0].get("account_id", [""])[0] if receiver_accounts else ""
                    
                    call_time = time.time() - call_start
                    graph_call_details.append({
                        'operation': 'get_account_ids',
                        'time': call_time
                    })
                    
                    return sender_account_id, receiver_account_id
                except Exception as e:
                    logger.error(f"Error getting account IDs: {e}")
                    return "", ""
            
            sender_account_id, receiver_account_id = await loop.run_in_executor(None, get_account_ids)
            
            logger.info(f"🔍 RT1 CHECK: Analyzing transaction {transaction['id']} for flagged account connections (Sender: {sender_account_id}, Receiver: {receiver_account_id})")
            
            def check_flagged_connections():
                try:
                    flagged_connections = []
                    
                    # Check if sender account is flagged
                    call_start = time.time()
                    sender_flagged = (self.graph_service.client.V()
                                    .has_label("account")
                                    .has("account_id", sender_account_id)
                                    .has("fraudFlag", True)
                                    .valueMap("account_id", "fraudFlag", "flagReason", "user_id")
                                    .to_list())
                    call_time = time.time() - call_start
                    graph_call_details.append({
                        'operation': 'check_sender_flagged',
                        'time': call_time
                    })
                    
                    if sender_flagged:
                        flagged_connections.extend([{
                            "account_id": conn.get("account_id", [""])[0],
                            "flag_reason": conn.get("flagReason", ["Unknown"])[0],
                            "user_id": conn.get("user_id", [""])[0],
                            "role": "sender"
                        } for conn in sender_flagged])
                    
                    # Check if receiver account is flagged
                    call_start = time.time()
                    receiver_flagged = (self.graph_service.client.V()
                                      .has_label("account")
                                      .has("account_id", receiver_account_id)
                                      .has("fraudFlag", True)
                                      .valueMap("account_id", "fraudFlag", "flagReason", "user_id")
                                      .to_list())
                    call_time = time.time() - call_start
                    graph_call_details.append({
                        'operation': 'check_receiver_flagged',
                        'time': call_time
                    })
                    
                    if receiver_flagged:
                        flagged_connections.extend([{
                            "account_id": conn.get("account_id", [""])[0],
                            "flag_reason": conn.get("flagReason", ["Unknown"])[0],
                            "user_id": conn.get("user_id", [""])[0],
                            "role": "receiver"
                        } for conn in receiver_flagged])
                    
                    return flagged_connections
                    
                except Exception as e:
                    logger.error(f"Error checking flagged connections: {e}")
                    return []
            
            flagged_connections = await loop.run_in_executor(None, check_flagged_connections)
            
            # If flagged connections found, calculate fraud score and status
            if flagged_connections:
                fraud_score = min(90 + len(flagged_connections) * 5, 100)  # Score 90-100 based on number of connections
                status = "blocked" if fraud_score >= 95 else "review"
                reason = f"Connected to {len(flagged_connections)} flagged account(s)"
                
                fraud_result = {
                    "is_fraud": True,
                    "fraud_score": fraud_score,
                    "status": status,
                    "reason": reason,
                    "rule_name": "RT1_FlaggedAccountRule",
                    "details": {
                        "flagged_connections": flagged_connections,
                        "detection_method": "RT1_Flagged_Account_Detection"
                    }
                }
                
                logger.warning(f"🚨 RT1 FRAUD DETECTED: Transaction {transaction['id']} - {reason} (Score: {fraud_score})")
                
                # Log performance metrics
                overall_time = time.time() - start_time
                await self.log_performance_metrics(transaction['id'], overall_time, graph_call_details)
                
                return fraud_result
            else:
                logger.info(f"✅ RT1 CHECK PASSED: Transaction {transaction['id']} - No flagged account connections")
                
                # Log performance metrics
                overall_time = time.time() - start_time
                await self.log_performance_metrics(transaction['id'], overall_time, graph_call_details)
                
                return {"is_fraud": False, "reason": "No flagged accounts involved"}
                
        except Exception as e:
            logger.error(f"❌ Error in RT1 fraud detection for transaction {transaction.get('id', 'unknown')}: {e}")
            
            # Log performance metrics even on error
            overall_time = time.time() - start_time
            await self.log_performance_metrics(transaction.get('id', 'unknown'), overall_time, graph_call_details)
            
            return {"is_fraud": False, "reason": f"Detection error: {str(e)}"}
    
    async def create_fraud_check_result(self, transaction: Dict[str, Any], fraud_result: Dict[str, Any]):
        """Create FraudCheckResult vertex and flagged_by edge"""
        try:
            if not self.graph_service.client or not fraud_result.get("is_fraud"):
                return
                
            loop = asyncio.get_event_loop()
            
            def create_fraud_result():
                try:
                    # Find the transaction vertex
                    transaction_vertex = self.graph_service.client.V().has_label("transaction").has("transaction_id", transaction['id']).next()
                    
                    # Create FraudCheckResult vertex
                    fraud_result_vertex = (self.graph_service.client.add_v("FraudCheckResult")
                                         .property("fraud_score", fraud_result["fraud_score"])
                                         .property("status", fraud_result["status"])
                                         .property("rule", fraud_result["rule_name"])
                                         .property("evaluation_timestamp", datetime.now().isoformat())
                                         .property("reason", fraud_result["reason"])
                                         .property("details", str(fraud_result["details"]))
                                         .next())
                    
                    # Create flagged_by edge from transaction to fraud result
                    self.graph_service.client.add_e("flagged_by").from_(transaction_vertex).to(fraud_result_vertex).iterate()
                    
                    logger.info(f"📊 Created RT1 FraudCheckResult for transaction {transaction['id']}: {fraud_result['status']} (Score: {fraud_result['fraud_score']})")
                    return True
                    
                except Exception as e:
                    logger.error(f"Error creating RT1 fraud check result: {e}")
                    return False
            
            await loop.run_in_executor(None, create_fraud_result)
            
        except Exception as e:
            logger.error(f"❌ Error creating RT1 fraud check result for transaction {transaction.get('id', 'unknown')}: {e}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics from logs namespace"""
        try:
            if not self.aerospike_client:
                return {"error": "Aerospike client unavailable"}
                
            loop = asyncio.get_event_loop()
            
            def fetch_stats():
                try:
                    # Get aggregate stats from logs namespace
                    stats_key = ('logs', None, 'rt1_aggregate_stats')
                    try:
                        (key, meta, stats_data) = self.aerospike_client.get(stats_key)
                        
                        if stats_data:
                            return {
                                "total_calls": stats_data.get("total_calls", 0),
                                "total_time_ms": stats_data.get("total_ms", 0),
                                "avg_overall_time_ms": stats_data.get("avg_overall_ms", 0),
                                "avg_graph_call_time_ms": stats_data.get("avg_graph_ms", 0),
                                "last_updated": stats_data.get("updated", "")
                            }
                        else:
                            return {"error": "No stats available"}
                    except Exception as e:
                        if "Record not found" in str(e):
                            return {"error": "No stats available"}
                        else:
                            raise e
                        
                except Exception as e:
                    logger.error(f"Error fetching performance stats: {e}")
                    return {"error": str(e)}
            
            return await loop.run_in_executor(None, fetch_stats)
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {"error": str(e)}
    
    async def get_recent_performance_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent performance logs from logs namespace"""
        try:
            if not self.aerospike_client:
                return []
                
            loop = asyncio.get_event_loop()
            
            def fetch_recent_logs():
                try:
                    # Get recent performance logs (this is a simplified approach since Aerospike doesn't have built-in ordering)
                    # In a production system, you might want to use a different approach for ordering
                    logs = []
                    
                    # For now, we'll get all logs and sort them (in production, consider using a timestamp-based key structure)
                    # This is a placeholder - you might want to implement a different strategy
                    return logs
                        
                except Exception as e:
                    logger.error(f"Error fetching recent logs: {e}")
                    return []
            
            return await loop.run_in_executor(None, fetch_recent_logs)
            
        except Exception as e:
            logger.error(f"Error getting recent performance logs: {e}")
            return []
    
    def __del__(self):
        """Cleanup Aerospike client on destruction"""
        if hasattr(self, 'aerospike_client') and self.aerospike_client:
            try:
                self.aerospike_client.close()
            except:
                pass 