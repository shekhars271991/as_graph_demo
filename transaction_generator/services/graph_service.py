import asyncio
from typing import List, Dict, Any, Optional
import random
from datetime import datetime, timedelta
import uuid
import logging
import json
import os
import sys

# Add the parent directory to the path so we can import from models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from gremlin_python.process.anonymous_traversal import traversal
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.traversal import P

from models.schemas import (
    User, Account, Transaction, UserSummary, TransactionDetail,
    DashboardStats, SearchResult, FraudRiskLevel, TransactionStatus
)

# Get logger for graph service
logger = logging.getLogger('fraud_detection.graph')

class GraphService:
    def __init__(self, host: str = "localhost", port: int = 8182):
        self.host = host
        self.port = port
        self.client = None
        self.connection = None
        self.users_data = []
        
    def connect_sync(self):
        """Synchronous connection to Aerospike Graph (to be called outside async context)"""
        try:
            url = f'ws://{self.host}:{self.port}/gremlin'
            logger.info(f"🔄 Connecting to Aerospike Graph: {url}")
            
            # Use the same approach as the working sample
            self.connection = DriverRemoteConnection(url, "g")
            self.client = traversal().with_remote(self.connection)
            
            # Test connection using the same method as the sample
            test_result = self.client.inject(0).next()
            if test_result != 0:
                raise Exception("Failed to connect to graph instance")
            
            logger.info("✅ Connected to Aerospike Graph Service")
            return True
                
        except Exception as e:
            logger.warning(f"⚠️  Could not connect to Aerospike Graph: {e}")
            logger.warning("   Running in mock mode - graph features will be simulated")
            self.client = None
            self.connection = None
            return False

    async def connect(self):
        """Async wrapper for synchronous connection"""
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Run the synchronous connection in a thread pool
        success = await loop.run_in_executor(None, self.connect_sync)
        return success

    def close_sync(self):
        """Synchronous close of graph connection"""
        if self.connection:
            try:
                self.connection.close()
                logger.info("✅ Disconnected from Aerospike Graph")
            except Exception as e:
                logger.warning(f"⚠️  Error closing connection: {e}")

    async def close(self):
        """Async wrapper for synchronous close"""
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.close_sync)

    async def _execute_query(self, query: str) -> List[Any]:
        """Execute a Gremlin query using the traversal API"""
        if not self.client:
            logger.debug("Graph client not available, returning empty results")
            return []
        
        try:
            logger.debug(f"Executing Gremlin query: {query}")
            # For now, we'll use the traversal API directly in the specific methods
            # This method is kept for compatibility but the real queries will be in the specific methods
            return []
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []

    async def seed_sample_data(self, num_users: int = None, num_transactions: int = None) -> Dict[str, int]:
        """Load data from users.json file into the graph"""
        try:
            # Load users data from JSON file - try multiple possible paths
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'users.json'),
                os.path.join(os.getcwd(), 'data', 'users.json'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'users.json')
            ]
            
            users_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    users_file_path = path
                    break
            
            if not users_file_path:
                logger.error(f"Users data file not found. Tried paths: {possible_paths}")
                return {"users": 0, "accounts": 0, "transactions": 0, "error": "Users data file not found"}
            
            logger.info(f"Loading users from: {users_file_path}")
            
            with open(users_file_path, 'r') as f:
                data = json.load(f)
                self.users_data = data.get('users', [])
            
            logger.info(f"Loaded {len(self.users_data)} users from users.json")
            
            if self.client:
                # Use real graph database - load data asynchronously
                return await self._load_users_to_graph_async()
            else:
                # Store data in memory for mock mode
                return {"users": len(self.users_data), "accounts": 0, "transactions": 0, "message": "Data loaded in mock mode"}
                
        except Exception as e:
            logger.error(f"Error loading users data: {e}")
            return {"users": 0, "accounts": 0, "transactions": 0, "error": str(e)}

    async def _load_users_to_graph_async(self) -> Dict[str, int]:
        """Load users data from JSON into the real graph database asynchronously"""
        users_created = 0
        accounts_created = 0
        transactions_created = 0
        
        try:
            logger.info("Loading data into graph asynchronously...")
            
            # Run all Gremlin operations in a thread pool since they're blocking
            loop = asyncio.get_event_loop()
            
            # Clear existing data first
            logger.info("Clearing existing data...")
            await loop.run_in_executor(None, lambda: self.client.V().drop().iterate())
            
            # Load users and their accounts
            for user_data in self.users_data:
                try:
                    # Create user vertex
                    def create_user():
                        return self.client.add_v("user").property("user_id", user_data['id']).property("name", user_data['name']).property("email", user_data['email']).property("phone", user_data.get('phone', '')).property("age", user_data['age']).property("location", user_data['location']).property("occupation", user_data.get('occupation', 'Unknown')).property("risk_score", user_data.get('risk_score', 0.0)).property("signup_date", user_data['signup_date']).next()
                    
                    user_vertex = await loop.run_in_executor(None, create_user)
                    users_created += 1
                    
                    # Create accounts for this user
                    for account_data in user_data.get('accounts', []):
                        try:
                            def create_account():
                                return self.client.add_v("account").property("account_id", account_data['id']).property("type", account_data['type']).property("balance", account_data['balance']).property("status", "active").property("bank_name", "Demo Bank").property("created_date", account_data['created_date']).next()
                            
                            account_vertex = await loop.run_in_executor(None, create_account)
                            accounts_created += 1
                            
                            # Link user to account
                            def create_ownership():
                                return self.client.add_e("OWNS").from_(user_vertex).to(account_vertex).property("since", account_data['created_date']).iterate()
                            
                            await loop.run_in_executor(None, create_ownership)
                        except Exception as e:
                            logger.error(f"Error creating account {account_data['id']}: {e}")
                            continue
                    
                    # Create some sample transactions between accounts
                    try:
                        def get_user_accounts():
                            return self.client.V().has_label("account").has("account_id", P.within([acc['id'] for acc in user_data.get('accounts', [])])).to_list()
                        
                        user_accounts = await loop.run_in_executor(None, get_user_accounts)
                        
                        if len(user_accounts) > 0:
                            # Create 2-5 transactions per user
                            num_transactions = random.randint(2, 5)
                            for i in range(num_transactions):
                                try:
                                    # Get random source and destination accounts
                                    source_account = random.choice(user_accounts)
                                    destination_account = random.choice(user_accounts)
                                    
                                    if source_account != destination_account:
                                        # Create transaction
                                        amount = random.uniform(10, 1000)
                                        transaction_id = f"T{user_data['id']}_{i+1}"
                                        
                                        def create_transaction():
                                            # Create transaction vertex
                                            transaction_vertex = self.client.add_v("transaction").property("transaction_id", transaction_id).property("amount", amount).property("timestamp", datetime.now().isoformat()).property("status", "completed").property("method", "transfer").property("ip_address", f"192.168.{random.randint(1,255)}.{random.randint(1,255)}").property("location_city", user_data['location']).property("location_country", "India").property("latitude", random.uniform(8.0, 37.0)).property("longitude", random.uniform(68.0, 97.0)).next()
                                            
                                            # Create INITIATED edge from source account to transaction
                                            self.client.add_e("INITIATED").from_(source_account).to(transaction_vertex).iterate()
                                            
                                            # Create TRANSFERS_TO edge from source account to destination account
                                            self.client.add_e("TRANSFERS_TO").from_(source_account).to(destination_account).property("transaction_id", transaction_id).property("amount", amount).property("timestamp", datetime.now().isoformat()).property("status", "completed").property("method", "transfer").iterate()
                                            
                                            return transaction_vertex
                                        
                                        await loop.run_in_executor(None, create_transaction)
                                        transactions_created += 1
                                except Exception as e:
                                    logger.error(f"Error creating transaction {i+1} for user {user_data['id']}: {e}")
                                    continue
                    except Exception as e:
                        logger.error(f"Error creating transactions for user {user_data['id']}: {e}")
                        continue
                        
                except Exception as e:
                    logger.error(f"Error creating user {user_data['id']}: {e}")
                    continue
            
            logger.info(f"Graph data loaded: {users_created} users, {accounts_created} accounts, {transactions_created} transactions")
            return {
                "users": users_created,
                "accounts": accounts_created,
                "transactions": transactions_created
            }
            
        except Exception as e:
            logger.error(f"Error loading data to graph: {e}")
            return {
                "users": users_created,
                "accounts": accounts_created,
                "transactions": transactions_created,
                "error": str(e)
            }

    async def get_user_summary(self, user_id: str) -> Optional[UserSummary]:
        """Get user's profile, connected accounts, and transaction summary"""
        try:
            if self.client:
                # Query real graph - run in thread pool
                loop = asyncio.get_event_loop()
                
                def get_user_vertices():
                    return self.client.V().has_label("User").has("userId", user_id).to_list()
                
                user_vertices = await loop.run_in_executor(None, get_user_vertices)
                if not user_vertices:
                    return None
                
                user_vertex = user_vertices[0]
                
                def get_user_props():
                    return user_vertex.value_map().next()
                
                user_props = await loop.run_in_executor(None, get_user_props)
                
                # Get user's accounts
                def get_account_vertices():
                    return self.client.V(user_vertex).out("owns").to_list()
                
                account_vertices = await loop.run_in_executor(None, get_account_vertices)
                accounts = []
                for acc_vertex in account_vertices:
                    def get_acc_props():
                        return acc_vertex.value_map().next()
                    
                    acc_props = await loop.run_in_executor(None, get_acc_props)
                    accounts.append(Account(
                        id=acc_props.get('accountId', [''])[0],
                        user_id=user_id,
                        account_type=acc_props.get('account_type', ['checking'])[0],
                        balance=acc_props.get('balance', [0.0])[0],
                        created_date=acc_props.get('created_date', [''])[0]
                    ))
                
                # Get transaction summary
                def get_transaction_edges():
                    return self.client.V(user_vertex).out("owns").outE("Transaction").to_list()
                
                transaction_edges = await loop.run_in_executor(None, get_transaction_edges)
                total_transactions = len(transaction_edges)
                
                total_amount = 0.0
                for edge in transaction_edges:
                    def get_edge_props():
                        return edge.value_map().next()
                    
                    edge_props = await loop.run_in_executor(None, get_edge_props)
                    total_amount += edge_props.get('amount', [0.0])[0]
                
                return UserSummary(
                    user=User(
                        id=user_props.get('userId', [''])[0],
                        name=user_props.get('name', [''])[0],
                        email=user_props.get('email', [''])[0],
                        age=user_props.get('age', [0])[0],
                        location=user_props.get('location', [''])[0],
                        risk_score=user_props.get('risk_score', [0.0])[0],
                        signup_date=user_props.get('signup_date', [''])[0]
                    ),
                    accounts=accounts,
                    total_transactions=total_transactions,
                    total_amount=total_amount
                )
            else:
                # Mock mode - return data from loaded users
                user_data = next((u for u in self.users_data if u['id'] == user_id), None)
                if not user_data:
                    return None
                
                accounts = []
                for acc_data in user_data.get('accounts', []):
                    accounts.append(Account(
                        id=acc_data['id'],
                        user_id=user_id,
                        account_type=acc_data['type'],
                        balance=acc_data['balance'],
                        created_date=acc_data['created_date']
                    ))
                
                return UserSummary(
                    user=User(
                        id=user_data['id'],
                        name=user_data['name'],
                        email=user_data['email'],
                        age=user_data['age'],
                        location=user_data['location'],
                        risk_score=user_data.get('risk_score', 0.0),
                        signup_date=user_data['signup_date']
                    ),
                    accounts=accounts,
                    total_transactions=0,  # No transactions in mock mode
                    total_amount=0.0
                )
                
        except Exception as e:
            logger.error(f"Error getting user summary: {e}")
            return None

    async def get_transaction_detail(self, transaction_id: str) -> Optional[TransactionDetail]:
        """Get detailed transaction information"""
        try:
            if self.client:
                # Query real graph
                transaction_edges = self.client.E().has("transactionId", transaction_id).to_list()
                if not transaction_edges:
                    return None
                
                edge = transaction_edges[0]
                edge_props = edge.value_map().next()
                
                # Get source and destination accounts
                source_vertex = edge.in_vertex().next()
                dest_vertex = edge.out_vertex().next()
                
                source_props = source_vertex.value_map().next()
                dest_props = dest_vertex.value_map().next()
                
                return TransactionDetail(
                    id=edge_props.get('transactionId', [''])[0],
                    sender_id=source_props.get('accountId', [''])[0],
                    receiver_id=dest_props.get('accountId', [''])[0],
                    amount=edge_props.get('amount', [0.0])[0],
                    currency="USD",
                    timestamp=edge_props.get('timestamp', [''])[0],
                    location=edge_props.get('location', [''])[0],
                    status="completed",
                    fraud_score=edge_props.get('fraud_score', [0.0])[0],
                    device_id=None
                )
            else:
                # Mock mode - no transactions available
                return None
                
        except Exception as e:
            logger.error(f"Error getting transaction detail: {e}")
            return None

    def get_dashboard_stats_sync(self) -> DashboardStats:
        """Get dashboard statistics synchronously"""
        try:
            if self.client:
                # Query real graph
                total_users = len(self.client.V().has_label("User").to_list())
                total_transactions = len(self.client.E().has_label("Transaction").to_list())
                
                # Get flagged transactions (high fraud score)
                flagged_transactions = len(self.client.E().has_label("Transaction").has("fraud_score", P.gte(70)).to_list())
                
                # Calculate total amount
                transaction_edges = self.client.E().has_label("Transaction").to_list()
                total_amount = sum(edge.value_map().next().get('amount', [0.0])[0] for edge in transaction_edges)
                
                fraud_rate = (flagged_transactions / total_transactions * 100) if total_transactions > 0 else 0
                
                return DashboardStats(
                    total_users=total_users,
                    total_transactions=total_transactions,
                    flagged_transactions=flagged_transactions,
                    total_amount=total_amount,
                    fraud_detection_rate=fraud_rate,
                    graph_health="connected"
                )
            else:
                # Mock mode
                return DashboardStats(
                    total_users=len(self.users_data),
                    total_transactions=0,
                    flagged_transactions=0,
                    total_amount=0.0,
                    fraud_detection_rate=0.0,
                    graph_health="error"
                )
                
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return DashboardStats(
                total_users=0,
                total_transactions=0,
                flagged_transactions=0,
                total_amount=0.0,
                fraud_detection_rate=0.0,
                graph_health="error"
            )

    async def get_dashboard_stats(self) -> DashboardStats:
        """Get dashboard statistics asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_dashboard_stats_sync)

    async def get_users_paginated(self, page: int, page_size: int) -> Dict[str, Any]:
        """Get paginated list of all users"""
        try:
            if self.client:
                # Query real graph
                all_users = self.client.V().has_label("User").to_list()
                
                # Paginate
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_users = all_users[start_idx:end_idx]
                
                users_data = []
                for user_vertex in paginated_users:
                    user_props = user_vertex.value_map().next()
                    users_data.append({
                        'id': user_props.get('userId', [''])[0],
                        'name': user_props.get('name', [''])[0],
                        'email': user_props.get('email', [''])[0],
                        'age': user_props.get('age', [0])[0],
                        'location': user_props.get('location', [''])[0],
                        'risk_score': user_props.get('risk_score', [0.0])[0],
                        'signup_date': user_props.get('signup_date', [''])[0]
                    })
                
                return {
                    'users': users_data,
                    'total': len(all_users),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(all_users) + page_size - 1) // page_size
                }
            else:
                # Mock mode
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_users = self.users_data[start_idx:end_idx]
                
                return {
                    'users': paginated_users,
                    'total': len(self.users_data),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(self.users_data) + page_size - 1) // page_size
                }
                
        except Exception as e:
            logger.error(f"Error getting users paginated: {e}")
            return {
                'users': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }

    async def search_users_paginated(self, query: str, page: int, page_size: int) -> Dict[str, Any]:
        """Search users with pagination"""
        try:
            if self.client:
                # Query real graph with search
                all_users = self.client.V().has_label("User").or_(
                    __.has("name", P.text_contains(query)),
                    __.has("userId", P.text_contains(query)),
                    __.has("email", P.text_contains(query))
                ).to_list()
                
                # Paginate
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_users = all_users[start_idx:end_idx]
                
                users_data = []
                for user_vertex in paginated_users:
                    user_props = user_vertex.value_map().next()
                    users_data.append({
                        'id': user_props.get('userId', [''])[0],
                        'name': user_props.get('name', [''])[0],
                        'email': user_props.get('email', [''])[0],
                        'age': user_props.get('age', [0])[0],
                        'location': user_props.get('location', [''])[0],
                        'risk_score': user_props.get('risk_score', [0.0])[0],
                        'signup_date': user_props.get('signup_date', [''])[0]
                    })
                
                return {
                    'users': users_data,
                    'total': len(all_users),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(all_users) + page_size - 1) // page_size
                }
            else:
                # Mock mode - search in loaded users
                filtered_users = [
                    user for user in self.users_data
                    if query.lower() in user['name'].lower() or 
                       query.lower() in user['id'].lower() or 
                       query.lower() in user['email'].lower()
                ]
                
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_users = filtered_users[start_idx:end_idx]
                
                return {
                    'users': paginated_users,
                    'total': len(filtered_users),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(filtered_users) + page_size - 1) // page_size
                }
                
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return {
                'users': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }

    async def search_users(self, query: str) -> List[SearchResult]:
        """Search users and return simplified results"""
        try:
            if self.client:
                # Query real graph
                users = self.client.V().has_label("User").or_(
                    __.has("name", P.text_contains(query)),
                    __.has("userId", P.text_contains(query)),
                    __.has("email", P.text_contains(query))
                ).to_list()
                
                results = []
                for user_vertex in users:
                    user_props = user_vertex.value_map().next()
                    results.append(SearchResult(
                        id=user_props.get('userId', [''])[0],
                        name=user_props.get('name', [''])[0],
                        type="user",
                        score=user_props.get('risk_score', [0.0])[0]
                    ))
                
                return results
            else:
                # Mock mode
                filtered_users = [
                    user for user in self.users_data
                    if query.lower() in user['name'].lower() or 
                       query.lower() in user['id'].lower() or 
                       query.lower() in user['email'].lower()
                ]
                
                return [
                    SearchResult(
                        id=user['id'],
                        name=user['name'],
                        type="user",
                        score=user.get('risk_score', 0.0)
                    )
                    for user in filtered_users
                ]
                
        except Exception as e:
            logger.error(f"Error searching users: {e}")
            return []

    async def search_transactions(self, query: str) -> List[SearchResult]:
        """Search transactions and return simplified results"""
        try:
            if self.client:
                # Query real graph
                transactions = self.client.E().has_label("Transaction").has("transactionId", P.text_contains(query)).to_list()
                
                results = []
                for edge in transactions:
                    edge_props = edge.value_map().next()
                    results.append(SearchResult(
                        id=edge_props.get('transactionId', [''])[0],
                        name=f"Transaction {edge_props.get('transactionId', [''])[0]}",
                        type="transaction",
                        score=edge_props.get('fraud_score', [0.0])[0]
                    ))
                
                return results
            else:
                # Mock mode - no transactions available
                return []
                
        except Exception as e:
            logger.error(f"Error searching transactions: {e}")
            return []

    async def update_transaction_status(self, transaction_id: str, status: str) -> bool:
        """Update transaction status"""
        try:
            if self.client:
                # Update in real graph
                edges = self.client.E().has("transactionId", transaction_id).to_list()
                if edges:
                    edge = edges[0]
                    edge.property("status", status).iterate()
                    return True
                return False
            else:
                # Mock mode - no transactions to update
                return False
                
        except Exception as e:
            logger.error(f"Error updating transaction status: {e}")
            return False

    def _calculate_risk_level(self, score: float) -> FraudRiskLevel:
        """Calculate fraud risk level based on score"""
        if score >= 80:
            return FraudRiskLevel.HIGH
        elif score >= 50:
            return FraudRiskLevel.MEDIUM
        else:
            return FraudRiskLevel.LOW

    def _convert_timestamp_to_long(self, date_str: str) -> int:
        """Convert timestamp string to long integer"""
        import datetime
        timestamp = datetime.datetime.now().timestamp()
        long_timestamp = int(timestamp)
        return long_timestamp

    async def get_transactions_paginated(self, page: int, page_size: int) -> Dict[str, Any]:
        """Get paginated list of all transactions"""
        try:
            if self.client:
                # Query real graph
                all_transactions = self.client.E().has_label("Transaction").to_list()
                
                # Paginate
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_transactions = all_transactions[start_idx:end_idx]
                
                transactions_data = []
                for edge in paginated_transactions:
                    edge_props = edge.value_map().next()
                    
                    # Get source and destination accounts
                    source_vertex = edge.in_vertex().next()
                    dest_vertex = edge.out_vertex().next()
                    
                    source_props = source_vertex.value_map().next()
                    dest_props = dest_vertex.value_map().next()
                    
                    transactions_data.append({
                        'id': edge_props.get('transactionId', [''])[0],
                        'sender_id': source_props.get('accountId', [''])[0],
                        'receiver_id': dest_props.get('accountId', [''])[0],
                        'amount': edge_props.get('amount', [0.0])[0],
                        'currency': 'USD',
                        'timestamp': edge_props.get('timestamp', [''])[0],
                        'location': edge_props.get('location', [''])[0],
                        'status': edge_props.get('status', ['completed'])[0],
                        'fraud_score': edge_props.get('fraud_score', [0.0])[0],
                        'device_id': None
                    })
                
                return {
                    'transactions': transactions_data,
                    'total': len(all_transactions),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(all_transactions) + page_size - 1) // page_size
                }
            else:
                # Mock mode - no transactions available
                return {
                    'transactions': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting transactions paginated: {e}")
            return {
                'transactions': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }

    async def search_transactions_paginated(self, query: str, page: int, page_size: int) -> Dict[str, Any]:
        """Search transactions with pagination"""
        try:
            if self.client:
                # Query real graph with search
                all_transactions = self.client.E().has_label("Transaction").or_(
                    __.has("transactionId", P.text_contains(query)),
                    __.has("location", P.text_contains(query))
                ).to_list()
                
                # Paginate
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_transactions = all_transactions[start_idx:end_idx]
                
                transactions_data = []
                for edge in paginated_transactions:
                    edge_props = edge.value_map().next()
                    
                    # Get source and destination accounts
                    source_vertex = edge.in_vertex().next()
                    dest_vertex = edge.out_vertex().next()
                    
                    source_props = source_vertex.value_map().next()
                    dest_props = dest_vertex.value_map().next()
                    
                    transactions_data.append({
                        'id': edge_props.get('transactionId', [''])[0],
                        'sender_id': source_props.get('accountId', [''])[0],
                        'receiver_id': dest_props.get('accountId', [''])[0],
                        'amount': edge_props.get('amount', [0.0])[0],
                        'currency': 'USD',
                        'timestamp': edge_props.get('timestamp', [''])[0],
                        'location': edge_props.get('location', [''])[0],
                        'status': edge_props.get('status', ['completed'])[0],
                        'fraud_score': edge_props.get('fraud_score', [0.0])[0],
                        'device_id': None
                    })
                
                return {
                    'transactions': transactions_data,
                    'total': len(all_transactions),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(all_transactions) + page_size - 1) // page_size
                }
            else:
                # Mock mode - no transactions available
                return {
                    'transactions': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0
                }
                
        except Exception as e:
            logger.error(f"Error searching transactions: {e}")
            return {
                'transactions': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            } 