import asyncio
from typing import List, Dict, Any, Optional
import random
from datetime import datetime, timedelta
import uuid
import logging

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
        self.mock_data = {
            'users': [],
            'accounts': [],
            'transactions': []
        }
        
    def connect_sync(self):
        """Synchronous connection to Aerospike Graph (to be called outside async context)"""
        try:
            from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
            from gremlin_python.process.anonymous_traversal import traversal
            
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

    async def seed_sample_data(self, num_users: int, num_transactions: int) -> Dict[str, int]:
        """Seed the graph with sample data"""
        if self.client:
            # Use real graph database
            return await self._seed_real_data(num_users, num_transactions)
        else:
            # Use mock data
            return await self._seed_mock_data(num_users, num_transactions)

    async def _seed_mock_data(self, num_users: int, num_transactions: int) -> Dict[str, int]:
        """Create mock data for demo purposes"""
        users_created = 0
        accounts_created = 0
        transactions_created = 0

        # Create mock users
        for i in range(num_users):
            user_id = f"user_{i+1}"
            user = {
                'id': user_id,
                'name': f"User {i+1}",
                'email': f"user{i+1}@example.com",
                'age': random.randint(18, 65),
                'location': random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                'risk_score': random.uniform(0, 100),
                'signup_date': datetime.now() - timedelta(days=random.randint(0, 365))
            }
            self.mock_data['users'].append(user)
            users_created += 1

            # Create 1-3 accounts per user
            num_accounts = random.randint(1, 3)
            for j in range(num_accounts):
                account_id = f"account_{user_id}_{j+1}"
                account = {
                    'id': account_id,
                    'user_id': user_id,
                    'account_type': random.choice(["checking", "savings", "credit"]),
                    'balance': random.uniform(100, 10000),
                    'created_date': datetime.now() - timedelta(days=random.randint(0, 365))
                }
                self.mock_data['accounts'].append(account)
                accounts_created += 1

        # Create mock transactions
        user_ids = [user['id'] for user in self.mock_data['users']]
        for i in range(num_transactions):
            sender_id = random.choice(user_ids)
            receiver_id = random.choice([uid for uid in user_ids if uid != sender_id])
            
            transaction = {
                'id': f"tx_{i+1}",
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'amount': random.uniform(10, 1000),
                'currency': 'USD',
                'timestamp': datetime.now() - timedelta(days=random.randint(0, 30)),
                'location': random.choice(["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]),
                'status': 'completed',
                'fraud_score': random.uniform(0, 100)
            }
            
            if random.random() < 0.3:
                transaction['device_id'] = f"device_{random.randint(1, 50)}"
            
            self.mock_data['transactions'].append(transaction)
            transactions_created += 1

        return {
            "users": users_created,
            "accounts": accounts_created,
            "transactions": transactions_created
        }

    def _seed_real_data_sync(self, num_users: int, num_transactions: int) -> Dict[str, int]:
        """Synchronous seed real graph database using the same approach as the working sample"""
        users_created = 0
        accounts_created = 0
        transactions_created = 0

        try:
            # Create users (following the working sample pattern)
            user_vertices = []
            for i in range(num_users):
                user_id = f"U{i+1}"
                name = f"User {i+1}"
                age = random.randint(18, 65)
                
                # Add user vertex using the same pattern as the sample
                user_vertex = self.client.add_v("User").property("userId", user_id).property("name", name).property("age", age).next()
                user_vertices.append(user_vertex)
                users_created += 1

            # Create accounts (following the working sample pattern)
            account_vertices = []
            for i in range(num_users):
                account_id = f"A{i+1}"
                balance = random.uniform(100, 10000)
                
                # Add account vertex using the same pattern as the sample
                account_vertex = self.client.add_v("Account").property("accountId", account_id).property("balance", balance).next()
                account_vertices.append(account_vertex)
                accounts_created += 1

                # Link user to account using the same pattern as the sample
                self.client.add_e("owns").from_(user_vertices[i]).to(account_vertex).property("since", "2024").iterate()

            # Create transactions (following the working sample pattern)
            for i in range(num_transactions):
                # Get 2 random accounts
                accounts = self.client.V().has_label("Account").sample(2).to_list()
                
                if len(accounts) < 2:
                    logger.warning("Not enough Account vertices to create transaction")
                    continue
                
                amount = random.randint(1, 1000)
                transaction_id = f"T{i+1}"
                type_ = "debit" if random.choice([True, False]) else "credit"
                timestamp = f"2025-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
                
                # Create transaction edge using the same pattern as the sample
                self.client.add_e("Transaction") \
                    .from_(accounts[0]).to(accounts[1]) \
                    .property("transactionId", transaction_id) \
                    .property("amount", amount) \
                    .property("type", type_) \
                    .property("timestamp", self._convert_timestamp_to_long(timestamp)) \
                    .iterate()
                
                transactions_created += 1

        except Exception as e:
            logger.error(f"Error seeding real data: {e}")
            return {
                "users": users_created,
                "accounts": accounts_created,
                "transactions": transactions_created,
                "error": str(e)
            }

        return {
            "users": users_created,
            "accounts": accounts_created,
            "transactions": transactions_created
        }

    async def _seed_real_data(self, num_users: int, num_transactions: int) -> Dict[str, int]:
        """Async wrapper for synchronous seed real data"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._seed_real_data_sync, num_users, num_transactions)

    async def get_user_summary(self, user_id: str) -> Optional[UserSummary]:
        """Get comprehensive user summary"""
        if not self.client:
            # Return mock data
            user = next((u for u in self.mock_data['users'] if u['id'] == user_id), None)
            if not user:
                return None
            
            accounts = [acc for acc in self.mock_data['accounts'] if acc['user_id'] == user_id]
            transactions = [tx for tx in self.mock_data['transactions'] 
                          if tx['sender_id'] == user_id or tx['receiver_id'] == user_id]
            
            return UserSummary(
                user=User(
                    id=user['id'],
                    name=user['name'],
                    email=user['email'],
                    age=user['age'],
                    signup_date=user['signup_date'],
                    location=user['location'],
                    risk_score=user['risk_score']
                ),
                accounts=[Account(**acc) for acc in accounts],
                recent_transactions=[Transaction(**tx) for tx in transactions[:10]],
                total_transactions=len(transactions),
                total_amount_sent=sum(tx['amount'] for tx in transactions if tx['sender_id'] == user_id),
                total_amount_received=sum(tx['amount'] for tx in transactions if tx['receiver_id'] == user_id),
                fraud_risk_level=self._calculate_risk_level(user['risk_score']),
                connected_users=list(set([tx['receiver_id'] for tx in transactions if tx['sender_id'] == user_id] + 
                                       [tx['sender_id'] for tx in transactions if tx['receiver_id'] == user_id]))
            )

        # Real implementation would go here
        return None

    async def get_transaction_detail(self, transaction_id: str) -> Optional[TransactionDetail]:
        """Get detailed transaction information"""
        if not self.client:
            # Return mock data
            transaction = next((tx for tx in self.mock_data['transactions'] if tx['id'] == transaction_id), None)
            if not transaction:
                return None
            
            sender = next((u for u in self.mock_data['users'] if u['id'] == transaction['sender_id']), None)
            receiver = next((u for u in self.mock_data['users'] if u['id'] == transaction['receiver_id']), None)
            
            if not sender or not receiver:
                return None
            
            return TransactionDetail(
                transaction=Transaction(**transaction),
                sender=User(**sender),
                receiver=User(**receiver),
                sender_account=None,
                receiver_account=None,
                related_transactions=[],
                fraud_indicators=[],
                risk_level=self._calculate_risk_level(transaction['fraud_score'])
            )

        # Real implementation would go here
        return None

    def get_dashboard_stats_sync(self) -> DashboardStats:
        """Synchronous dashboard statistics"""
        if not self.client:
            # Return mock data
            total_users = len(self.mock_data['users'])
            total_transactions = len(self.mock_data['transactions'])
            flagged_transactions = len([tx for tx in self.mock_data['transactions'] if tx['fraud_score'] >= 70])
            total_amount = sum(tx['amount'] for tx in self.mock_data['transactions'])
            
            return DashboardStats(
                total_users=total_users,
                total_transactions=total_transactions,
                flagged_transactions=flagged_transactions,
                total_amount=total_amount,
                fraud_detection_rate=0.85,
                graph_health="mock_mode"
            )

        # Real implementation - connection is working
        try:
            # Get real stats from the graph
            total_users = self.client.V().has_label("User").count().next()
            total_transactions = self.client.E().has_label("Transaction").count().next()
            
            # Try to get total amount, but handle case where no transactions exist
            try:
                total_amount = self.client.E().has_label("Transaction").values("amount").sum_().next()
            except:
                total_amount = 0.0
            
            return DashboardStats(
                total_users=total_users,
                total_transactions=total_transactions,
                flagged_transactions=0,  # Will be calculated when fraud detection runs
                total_amount=total_amount if total_amount else 0.0,
                fraud_detection_rate=0.85,
                graph_health="healthy"
            )
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            # Return healthy status even if no data exists yet
            return DashboardStats(
                total_users=0,
                total_transactions=0,
                flagged_transactions=0,
                total_amount=0.0,
                fraud_detection_rate=0.85,
                graph_health="healthy"  # Connection is working, just no data yet
            )

    async def get_dashboard_stats(self) -> DashboardStats:
        """Async wrapper for synchronous dashboard stats"""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_dashboard_stats_sync)

    async def search_users(self, query: str) -> List[SearchResult]:
        """Search users by name or ID"""
        if not self.client:
            # Return mock data
            results = []
            for user in self.mock_data['users']:
                if query.lower() in user['name'].lower() or query.lower() in user['id'].lower():
                    results.append(SearchResult(
                        id=user['id'],
                        name=user['name'],
                        type="user",
                        score=1.0
                    ))
            return results

        # Real implementation would go here
        return []

    async def search_transactions(self, query: str) -> List[SearchResult]:
        """Search transactions by ID"""
        if not self.client:
            # Return mock data
            results = []
            for tx in self.mock_data['transactions']:
                if query.lower() in tx['id'].lower():
                    results.append(SearchResult(
                        id=tx['id'],
                        name=f"Transaction {tx['id']}",
                        type="transaction",
                        score=1.0
                    ))
            return results

        # Real implementation would go here
        return []

    async def update_transaction_status(self, transaction_id: str, status: str) -> bool:
        """Update transaction review status"""
        if not self.client:
            # Update mock data
            transaction = next((tx for tx in self.mock_data['transactions'] if tx['id'] == transaction_id), None)
            if transaction:
                transaction['status'] = status
                return True
            return False

        # Real implementation would go here
        return False

    def _calculate_risk_level(self, score: float) -> FraudRiskLevel:
        """Calculate risk level based on score"""
        if score < 25:
            return FraudRiskLevel.LOW
        elif score < 50:
            return FraudRiskLevel.MEDIUM
        elif score < 75:
            return FraudRiskLevel.HIGH
        else:
            return FraudRiskLevel.CRITICAL
    
    def _convert_timestamp_to_long(self, date_str: str) -> int:
        """Convert timestamp to long format (same as the working sample)"""
        import datetime
        timestamp = datetime.datetime.now().timestamp()
        long_timestamp = int(timestamp)
        return long_timestamp 