import asyncio
from typing import List, Dict, Any, Optional
import random
from datetime import datetime, timedelta
import uuid
import logging
import json
import os

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
            logger.error(f"❌ Could not connect to Aerospike Graph: {e}")
            logger.error("   Graph database connection is required. Please ensure Aerospike Graph is running on port 8182")
            self.client = None
            self.connection = None
            raise Exception(f"Failed to connect to Aerospike Graph: {e}")

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
                # No graph client available
                raise Exception("Graph client not available. Cannot load data without graph database connection.")
                
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
                # Query real graph - use synchronous calls like get_users_paginated
                user_vertices = self.client.V().has_label("user").has("user_id", user_id).to_list()
                if not user_vertices:
                    return None
                
                user_vertex = user_vertices[0]
                user_props = {}
                
                # Get user properties using the same approach as get_users_paginated
                props = self.client.V(user_vertex).value_map().next()
                for key, value in props.items():
                    if isinstance(value, list) and len(value) > 0:
                        user_props[key] = value[0]
                    else:
                        user_props[key] = value
                
                # Get user's accounts
                account_vertices = self.client.V(user_vertex).out("OWNS").to_list()
                accounts = []
                for acc_vertex in account_vertices:
                    acc_props = {}
                    acc_prop_map = self.client.V(acc_vertex).value_map().next()
                    for key, value in acc_prop_map.items():
                        if isinstance(value, list) and len(value) > 0:
                            acc_props[key] = value[0]
                        else:
                            acc_props[key] = value
                    
                    accounts.append(Account(
                        id=acc_props.get('account_id', ''),
                        user_id=user_id,
                        account_type=acc_props.get('type', 'checking'),
                        balance=acc_props.get('balance', 0.0),
                        created_date=acc_props.get('created_date', '')
                    ))
                
                # Get transaction summary
                transaction_edges = self.client.V(user_vertex).out("OWNS").out("INITIATED").to_list()
                total_transactions = len(transaction_edges)
                
                total_amount = 0.0
                for edge in transaction_edges:
                    edge_props = {}
                    edge_prop_map = edge.value_map().next()
                    for key, value in edge_prop_map.items():
                        if isinstance(value, list) and len(value) > 0:
                            edge_props[key] = value[0]
                        else:
                            edge_props[key] = value
                    total_amount += edge_props.get('amount', 0.0)
                
                # Calculate fraud risk level based on risk score
                risk_score = user_props.get('risk_score', 0.0)
                if risk_score < 25:
                    fraud_risk_level = FraudRiskLevel.LOW
                elif risk_score < 50:
                    fraud_risk_level = FraudRiskLevel.MEDIUM
                elif risk_score < 75:
                    fraud_risk_level = FraudRiskLevel.HIGH
                else:
                    fraud_risk_level = FraudRiskLevel.CRITICAL
                
                # For now, we'll set sent/received amounts to the same value
                # In a real implementation, you'd calculate these separately
                total_amount_sent = total_amount / 2
                total_amount_received = total_amount / 2
                
                # Create empty recent transactions list (we'll populate this later)
                recent_transactions = []
                
                # For now, we'll set connected users to empty list
                # In a real implementation, you'd find users connected via transactions
                connected_users = []
                
                return UserSummary(
                    user=User(
                        id=user_props.get('user_id', ''),
                        name=user_props.get('name', ''),
                        email=user_props.get('email', ''),
                        age=user_props.get('age', 0),
                        location=user_props.get('location', ''),
                        risk_score=user_props.get('risk_score', 0.0),
                        signup_date=user_props.get('signup_date', '')
                    ),
                    accounts=accounts,
                    recent_transactions=recent_transactions,
                    total_transactions=total_transactions,
                    total_amount_sent=total_amount_sent,
                    total_amount_received=total_amount_received,
                    fraud_risk_level=fraud_risk_level,
                    connected_users=connected_users
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
                
                # Calculate fraud risk level based on risk score
                risk_score = user_data.get('risk_score', 0.0)
                if risk_score < 25:
                    fraud_risk_level = FraudRiskLevel.LOW
                elif risk_score < 50:
                    fraud_risk_level = FraudRiskLevel.MEDIUM
                elif risk_score < 75:
                    fraud_risk_level = FraudRiskLevel.HIGH
                else:
                    fraud_risk_level = FraudRiskLevel.CRITICAL
                
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
                    recent_transactions=[],  # No transactions in mock mode
                    total_transactions=0,
                    total_amount_sent=0.0,
                    total_amount_received=0.0,
                    fraud_risk_level=fraud_risk_level,
                    connected_users=[]
                )
                
        except Exception as e:
            logger.error(f"Error getting user summary: {e}")
            return None

    async def get_transaction_detail(self, transaction_id: str) -> Optional[TransactionDetail]:
        """Get detailed transaction information"""
        try:
            if self.client:
                # Query real graph - look for transaction vertex
                loop = asyncio.get_event_loop()
                
                def get_transaction_vertex():
                    return self.client.V().has_label("transaction").has("transaction_id", transaction_id).to_list()
                
                transaction_vertices = await loop.run_in_executor(None, get_transaction_vertex)
                if not transaction_vertices:
                    return None
                
                transaction_vertex = transaction_vertices[0]
                
                def get_transaction_props():
                    return transaction_vertex.value_map().next()
                
                transaction_props = await loop.run_in_executor(None, get_transaction_props)
                
                # Get source account (account that initiated the transaction)
                def get_source_account():
                    return self.client.V(transaction_vertex).in_("INITIATED").to_list()
                
                source_accounts = await loop.run_in_executor(None, get_source_account)
                source_account = source_accounts[0] if source_accounts else None
                
                # Get destination account from TRANSFERS_TO edge
                def get_dest_account():
                    return self.client.V(source_account).out("TRANSFERS_TO").to_list()
                
                dest_accounts = await loop.run_in_executor(None, get_dest_account)
                dest_account = dest_accounts[0] if dest_accounts else None
                
                if source_account and dest_account:
                    def get_source_props():
                        return source_account.value_map().next()
                    
                    def get_dest_props():
                        return dest_account.value_map().next()
                    
                    source_props = await loop.run_in_executor(None, get_source_props)
                    dest_props = await loop.run_in_executor(None, get_dest_props)
                    
                    return TransactionDetail(
                        id=transaction_props.get('transaction_id', [''])[0],
                        sender_id=source_props.get('account_id', [''])[0],
                        receiver_id=dest_props.get('account_id', [''])[0],
                        amount=transaction_props.get('amount', [0.0])[0],
                        currency="USD",
                        timestamp=transaction_props.get('timestamp', [''])[0],
                        location=transaction_props.get('location_city', [''])[0],
                        status=transaction_props.get('status', ['completed'])[0],
                        fraud_score=0.0,  # Not stored in new model
                        device_id=None
                    )
                else:
                    return None
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
                total_users = len(self.client.V().has_label("user").to_list())
                total_transactions = len(self.client.V().has_label("transaction").to_list())
                
                # Get flagged transactions (high risk transactions)
                flagged_transactions = len(self.client.V().has_label("transaction").has("amount", P.gte(10000)).to_list())
                
                # Calculate total amount
                transaction_vertices = self.client.V().has_label("transaction").to_list()
                total_amount = sum(vertex.value_map().next().get('amount', [0.0])[0] for vertex in transaction_vertices)
                
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
                # No graph client available
                raise Exception("Graph client not available. Cannot get dashboard stats without graph database connection.")
                
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
                all_users = self.client.V().has_label("user").to_list()
                
                # Paginate
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_users = all_users[start_idx:end_idx]
                
                users_data = []
                for user_vertex in paginated_users:
                    # Get user properties using the correct Gremlin syntax
                    user_props = {}
                    try:
                        # Get all properties of the vertex
                        props = self.client.V(user_vertex).value_map().next()
                        for key, value in props.items():
                            if isinstance(value, list) and len(value) > 0:
                                user_props[key] = value[0]
                            else:
                                user_props[key] = value
                    except Exception as e:
                        logger.error(f"Error getting user properties: {e}")
                        continue
                    
                    # Get user's accounts
                    accounts = []
                    try:
                        account_vertices = self.client.V(user_vertex).out("OWNS").to_list()
                        for acc_vertex in account_vertices:
                            acc_props = {}
                            try:
                                acc_prop_map = self.client.V(acc_vertex).value_map().next()
                                for key, value in acc_prop_map.items():
                                    if isinstance(value, list) and len(value) > 0:
                                        acc_props[key] = value[0]
                                    else:
                                        acc_props[key] = value
                                accounts.append(acc_props)
                            except Exception as e:
                                logger.error(f"Error getting account properties: {e}")
                    except Exception as e:
                        logger.error(f"Error getting user accounts: {e}")
                    
                    users_data.append({
                        'id': user_props.get('user_id', ''),
                        'name': user_props.get('name', ''),
                        'email': user_props.get('email', ''),
                        'age': user_props.get('age', 0),
                        'location': user_props.get('location', ''),
                        'risk_score': user_props.get('risk_score', 0.0),
                        'signup_date': user_props.get('signup_date', ''),
                        'accounts': accounts
                    })
                
                return {
                    'users': users_data,
                    'total': len(all_users),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(all_users) + page_size - 1) // page_size
                }
            else:
                # No graph client available
                raise Exception("Graph client not available. Cannot get users without graph database connection.")
                
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
                all_users = self.client.V().has_label("user").or_(
                    __.has("name", P.text_contains(query)),
                    __.has("user_id", P.text_contains(query)),
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
                users = self.client.V().has_label("user").or_(
                    __.has("name", P.text_contains(query)),
                    __.has("user_id", P.text_contains(query)),
                    __.has("email", P.text_contains(query))
                ).to_list()
                
                results = []
                for user_vertex in users:
                    user_props = user_vertex.value_map().next()
                    results.append(SearchResult(
                        id=user_props.get('user_id', [''])[0],
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
                transactions = self.client.V().has_label("transaction").has("transaction_id", P.text_contains(query)).to_list()
                
                results = []
                for transaction_vertex in transactions:
                    transaction_props = transaction_vertex.value_map().next()
                    results.append(SearchResult(
                        id=transaction_props.get('transaction_id', [''])[0],
                        name=f"Transaction {transaction_props.get('transaction_id', [''])[0]}",
                        type="transaction",
                        score=0.0
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
                loop = asyncio.get_event_loop()
                
                def update_transaction():
                    vertices = self.client.V().has_label("transaction").has("transaction_id", transaction_id).to_list()
                    if vertices:
                        vertex = vertices[0]
                        vertex.property("status", status).iterate()
                        return True
                    return False
                
                return await loop.run_in_executor(None, update_transaction)
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
                # Query real graph - use synchronous calls like get_users_paginated
                all_transactions = self.client.V().has_label("transaction").to_list()
                
                # Paginate
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_transactions = all_transactions[start_idx:end_idx]
                
                transactions_data = []
                for transaction_vertex in paginated_transactions:
                    try:
                        # Get transaction properties using the same approach as get_users_paginated
                        transaction_props = {}
                        props = self.client.V(transaction_vertex).value_map().next()
                        for key, value in props.items():
                            if isinstance(value, list) and len(value) > 0:
                                transaction_props[key] = value[0]
                            else:
                                transaction_props[key] = value
                        
                        # Get the sender account that initiated this transaction
                        try:
                            logger.info(f"Looking for sender account that initiated transaction {transaction_props.get('transaction_id', 'unknown')}")
                            
                            # Try to find the sender account using the INITIATED edge
                            sender_account_vertices = self.client.V(transaction_vertex).in_("INITIATED").to_list()
                            logger.info(f"Found {len(sender_account_vertices)} sender account vertices")
                            
                            if sender_account_vertices:
                                sender_account_vertex = sender_account_vertices[0]
                                logger.info(f"Found sender account vertex: {sender_account_vertex}")
                                
                                sender_account_props = {}
                                sender_acc_prop_map = self.client.V(sender_account_vertex).value_map().next()
                                for key, value in sender_acc_prop_map.items():
                                    if isinstance(value, list) and len(value) > 0:
                                        sender_account_props[key] = value[0]
                                    else:
                                        sender_account_props[key] = value
                                logger.info(f"Sender account properties: {sender_account_props}")
                                sender_id = sender_account_props.get('account_id', 'Unknown')
                                logger.info(f"Sender ID: {sender_id}")
                            else:
                                logger.warning("No sender account vertices found")
                                sender_id = 'Unknown'
                        except Exception as e:
                            # If no sender account found, use a default
                            logger.error(f"Error getting sender account for transaction: {e}")
                            sender_id = 'Unknown'
                        
                        # Get the receiver account that received this transaction
                        try:
                            logger.info(f"Looking for receiver account for transaction {transaction_props.get('transaction_id', 'unknown')}")
                            
                            # Try to find the receiver account using the RECEIVED edge
                            receiver_account_vertices = self.client.V(transaction_vertex).out("RECEIVED").to_list()
                            logger.info(f"Found {len(receiver_account_vertices)} receiver account vertices")
                            
                            if receiver_account_vertices:
                                receiver_account_vertex = receiver_account_vertices[0]
                                logger.info(f"Found receiver account vertex: {receiver_account_vertex}")
                                
                                receiver_account_props = {}
                                receiver_acc_prop_map = self.client.V(receiver_account_vertex).value_map().next()
                                for key, value in receiver_acc_prop_map.items():
                                    if isinstance(value, list) and len(value) > 0:
                                        receiver_account_props[key] = value[0]
                                    else:
                                        receiver_account_props[key] = value
                                logger.info(f"Receiver account properties: {receiver_account_props}")
                                receiver_id = receiver_account_props.get('account_id', 'Unknown')
                                logger.info(f"Receiver ID: {receiver_id}")
                            else:
                                logger.warning("No receiver account vertices found")
                                receiver_id = 'Unknown'
                        except Exception as e:
                            # If no receiver account found, use a default
                            logger.error(f"Error getting receiver account for transaction: {e}")
                            receiver_id = 'Unknown'
                        
                        transactions_data.append({
                            'id': transaction_props.get('transaction_id', ''),
                            'sender_id': sender_id,
                            'receiver_id': receiver_id,
                            'amount': transaction_props.get('amount', 0.0),
                            'currency': 'USD',
                            'timestamp': transaction_props.get('timestamp', ''),
                            'location': transaction_props.get('location', 'Unknown'),
                            'status': transaction_props.get('status', 'completed'),
                            'fraud_score': transaction_props.get('fraud_score', 0.0),
                            'transaction_type': transaction_props.get('type', 'transfer'),
                            'merchant': transaction_props.get('merchant', 'Unknown'),
                            'is_fraud': transaction_props.get('is_fraud', False),
                            'device_id': None
                        })
                    except Exception as e:
                        logger.error(f"Error processing transaction vertex: {e}")
                        continue
                
                return {
                    'transactions': transactions_data,
                    'total': len(all_transactions),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(all_transactions) + page_size - 1) // page_size
                }
            else:
                # No graph client available
                raise Exception("Graph client not available. Cannot get transactions without graph database connection.")
                
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
                # Query real graph with search using thread pool
                import asyncio
                loop = asyncio.get_event_loop()
                
                def search_transactions():
                    return self.client.V().has_label("transaction").or_(
                        __.has("transaction_id", P.text_contains(query)),
                        __.has("location_city", P.text_contains(query))
                    ).to_list()
                
                all_transactions = await loop.run_in_executor(None, search_transactions)
                
                # Paginate
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                paginated_transactions = all_transactions[start_idx:end_idx]
                
                transactions_data = []
                for transaction_vertex in paginated_transactions:
                    try:
                        def get_transaction_props():
                            return transaction_vertex.value_map().next()
                        
                        transaction_props = await loop.run_in_executor(None, get_transaction_props)
                        
                        # Get the account that initiated this transaction
                        def get_account_vertex():
                            return transaction_vertex.in_("INITIATED").next()
                        
                        try:
                            account_vertex = await loop.run_in_executor(None, get_account_vertex)
                            
                            def get_account_props():
                                return account_vertex.value_map().next()
                            
                            account_props = await loop.run_in_executor(None, get_account_props)
                            sender_id = account_props.get('account_id', [''])[0]
                        except:
                            # If no account found, use a default
                            sender_id = 'Unknown'
                        
                        # For now, use the same account as receiver (self-transaction)
                        receiver_id = sender_id
                        
                        transactions_data.append({
                            'id': transaction_props.get('transaction_id', [''])[0],
                            'sender_id': sender_id,
                            'receiver_id': receiver_id,
                            'amount': transaction_props.get('amount', [0.0])[0],
                            'currency': 'USD',
                            'timestamp': transaction_props.get('timestamp', [''])[0],
                            'location': transaction_props.get('location_city', ['Unknown'])[0],
                            'status': transaction_props.get('status', ['completed'])[0],
                            'fraud_score': 0.0,
                            'transaction_type': transaction_props.get('method', ['transfer'])[0],
                            'merchant': 'Unknown',
                            'is_fraud': False,
                            'device_id': None
                        })
                    except Exception as e:
                        logger.error(f"Error processing search transaction vertex: {e}")
                        continue
                
                return {
                    'transactions': transactions_data,
                    'total': len(all_transactions),
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (len(all_transactions) + page_size - 1) // page_size
                }
            else:
                # No graph client available
                raise Exception("Graph client not available. Cannot search transactions without graph database connection.")
                
        except Exception as e:
            logger.error(f"Error searching transactions: {e}")
            return {
                'transactions': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0
            }

    async def get_user_transactions_paginated(self, user_id: str, page: int, page_size: int) -> Dict[str, Any]:
        """Get paginated transactions for a specific user"""
        try:
            if self.client:
                # Query real graph for user's transactions
                # This would need to be implemented to query the graph database
                # For now, return empty result
                return {
                    "transactions": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 0,
                    "user_id": user_id
                }
            else:
                # No graph client available
                raise Exception("Graph client not available. Cannot get user transactions without graph database connection.")
        except Exception as e:
            logger.error(f"Error in get_user_transactions_paginated: {e}")
            raise Exception(f"Failed to get user transactions: {e}")

    async def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all accounts for a specific user"""
        try:
            if self.client:
                # Query real graph for user's accounts
                # This would need to be implemented to query the graph database
                # For now, return empty result
                return []
            else:
                # No graph client available
                raise Exception("Graph client not available. Cannot get user accounts without graph database connection.")
        except Exception as e:
            logger.error(f"Error in get_user_accounts: {e}")
            raise Exception(f"Failed to get user accounts: {e}")

    async def delete_all_data(self) -> Dict[str, Any]:
        """Delete all data from the graph database"""
        try:
            if self.client:
                # Delete all vertices and edges using thread pool
                logger.info("Deleting all vertices and edges from graph database...")
                
                import asyncio
                loop = asyncio.get_event_loop()
                
                # Delete all edges first
                def delete_edges():
                    return self.client.E().drop().to_list()
                
                edges_deleted = await loop.run_in_executor(None, delete_edges)
                logger.info(f"Deleted {len(edges_deleted)} edges")
                
                # Delete all vertices
                def delete_vertices():
                    return self.client.V().drop().to_list()
                
                vertices_deleted = await loop.run_in_executor(None, delete_vertices)
                logger.info(f"Deleted {len(vertices_deleted)} vertices")
                
                return {
                    "message": "All data deleted successfully",
                    "edges_deleted": len(edges_deleted),
                    "vertices_deleted": len(vertices_deleted)
                }
            else:
                # Mock mode - clear in-memory data
                logger.info("Mock mode: Clearing in-memory data")
                self.users_data = []
                return {
                    "message": "Mock data cleared successfully",
                    "edges_deleted": 0,
                    "vertices_deleted": 0
                }
        except Exception as e:
            logger.error(f"Error deleting all data: {e}")
            return {"error": str(e)}

    async def load_users_only(self) -> Dict[str, Any]:
        """Load only user and account data (no transactions) from users.json"""
        try:
            # Load users data from JSON file
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'users.json'),
                os.path.join(os.path.dirname(__file__), '..', 'data', 'users.json'),
                'data/users.json',
                '../data/users.json',
                '../../data/users.json'
            ]
            
            users_file_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    users_file_path = path
                    break
            
            if not users_file_path:
                return {"error": "users.json file not found"}
            
            logger.info(f"Loading users from: {users_file_path}")
            
            with open(users_file_path, 'r') as f:
                data = json.load(f)
            
            users = data.get('users', [])
            total_users = len(users)
            total_accounts = 0
            
            if self.client:
                # Real graph mode - use thread pool to avoid event loop conflicts
                logger.info("Loading users and accounts into graph database...")
                
                import asyncio
                loop = asyncio.get_event_loop()
                
                # Run all Gremlin operations in a thread pool
                for user_data in users:
                    try:
                        # Create user vertex
                        def create_user():
                            return self.client.addV("user").property(
                                "user_id", user_data['id']
                            ).property(
                                "name", user_data['name']
                            ).property(
                                "email", user_data['email']
                            ).property(
                                "phone", user_data.get('phone', '')
                            ).property(
                                "age", user_data['age']
                            ).property(
                                "location", user_data['location']
                            ).property(
                                "occupation", user_data.get('occupation', 'Unknown')
                            ).property(
                                "risk_score", user_data.get('risk_score', 0.0)
                            ).property(
                                "signup_date", user_data['signup_date']
                            ).next()
                        
                        user_vertex = await loop.run_in_executor(None, create_user)
                        
                        # Create accounts for this user
                        for account_data in user_data.get('accounts', []):
                            def create_account():
                                return self.client.addV("account").property(
                                    "account_id", account_data['id']
                                ).property(
                                    "type", account_data['type']
                                ).property(
                                    "balance", account_data['balance']
                                ).property(
                                    "status", "active"
                                ).property(
                                    "bank_name", "Demo Bank"
                                ).property(
                                    "created_date", account_data['created_date']
                                ).next()
                            
                            account_vertex = await loop.run_in_executor(None, create_account)
                            
                            # Create ownership edge
                            def create_edge():
                                return self.client.addE("OWNS").from_(user_vertex).to(account_vertex).next()
                            
                            await loop.run_in_executor(None, create_edge)
                            total_accounts += 1
                            
                    except Exception as e:
                        logger.error(f"Error creating user {user_data.get('id', 'unknown')}: {e}")
                        continue
                
                logger.info(f"✅ Loaded {total_users} users and {total_accounts} accounts into graph database")
                
                return {
                    "users": total_users,
                    "accounts": total_accounts,
                    "transactions": 0
                }
            else:
                # Mock mode
                logger.info("Mock mode: Loading users and accounts into memory")
                self.users_data = users
                total_accounts = sum(len(user.get('accounts', [])) for user in users)
                
                logger.info(f"✅ Loaded {total_users} users and {total_accounts} accounts into memory")
                
                return {
                    "users": total_users,
                    "accounts": total_accounts,
                    "transactions": 0
                }
                
        except Exception as e:
            logger.error(f"Error loading users only: {e}")
            return {"error": str(e)} 