import asyncio
import random
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum
import json
import uuid
import os

# Import local modules
from models.schemas import Transaction
from services.graph_service import GraphService

# Configure logging
def setup_logging():
    """Setup comprehensive logging for transaction generator"""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Main logger
    logger = logging.getLogger('fraud_detection.transaction_generator')
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler for all transactions
    file_handler = logging.FileHandler('logs/transactions.log')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Separate file handler for fraud transactions
    fraud_handler = logging.FileHandler('logs/fraud_transactions.log')
    fraud_handler.setLevel(logging.INFO)
    fraud_formatter = logging.Formatter(
        '%(asctime)s - FRAUD - %(message)s'
    )
    fraud_handler.setFormatter(fraud_formatter)
    logger.addHandler(fraud_handler)
    
    # Separate file handler for normal transactions
    normal_handler = logging.FileHandler('logs/normal_transactions.log')
    normal_handler.setLevel(logging.INFO)
    normal_formatter = logging.Formatter(
        '%(asctime)s - NORMAL - %(message)s'
    )
    normal_handler.setFormatter(normal_formatter)
    logger.addHandler(normal_handler)
    
    # Statistics logger
    stats_logger = logging.getLogger('fraud_detection.stats')
    stats_logger.setLevel(logging.INFO)
    stats_logger.handlers.clear()
    
    stats_handler = logging.FileHandler('logs/statistics.log')
    stats_handler.setLevel(logging.INFO)
    stats_formatter = logging.Formatter(
        '%(asctime)s - STATS - %(message)s'
    )
    stats_handler.setFormatter(stats_formatter)
    stats_logger.addHandler(stats_handler)
    
    return logger, stats_logger

# Setup logging
logger, stats_logger = setup_logging()

class FraudScenario(Enum):
    SCENARIO_A = "Multiple Small Credits Followed by Large Debit"
    SCENARIO_B = "Large Credit Followed by Structured Equal Debits"
    SCENARIO_C = "Multiple Large ATM Withdrawals"
    SCENARIO_D = "High-Frequency Transfers Between Mule Accounts"
    SCENARIO_E = "Salary-Like Deposits Followed by Suspicious Transfers"
    SCENARIO_F = "Dormant Account Sudden Activity"
    SCENARIO_G = "International Transfers to High-Risk Jurisdictions"
    SCENARIO_H = "Region-Specific Fraud (Indian Context)"

class TransactionGeneratorService:
    def __init__(self, graph_service: GraphService):
        self.graph_service = graph_service
        self.is_running = False
        self.generation_rate = 1  # transactions per second
        self.generated_transactions = []
        self.fraud_counter = 0
        self.normal_counter = 0
        self.task = None
        
        # Fraud scenario tracking
        self.fraud_scenarios_generated = {scenario: 0 for scenario in FraudScenario}
        
        # High-risk jurisdictions for international transfers
        self.high_risk_jurisdictions = ['Dubai', 'Bahrain', 'Thailand', 'Cayman Islands', 'Panama']
        
        # Indian fraud locations
        self.indian_fraud_locations = ['Jamtara', 'Bharatpur', 'Alwar', 'Mewat', 'Nuh']
        
        # Normal locations
        self.normal_locations = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia',
            'San Antonio', 'San Diego', 'Dallas', 'San Jose', 'Austin', 'Jacksonville',
            'Fort Worth', 'Columbus', 'Charlotte', 'San Francisco', 'Indianapolis',
            'Seattle', 'Denver', 'Washington', 'Boston', 'El Paso', 'Nashville'
        ]
        
        # Merchant categories
        self.merchant_categories = [
            'Retail', 'Restaurant', 'Gas Station', 'Online Shopping', 'Grocery Store',
            'Entertainment', 'Transportation', 'Healthcare', 'Education', 'Travel',
            'Technology', 'Fashion', 'Home & Garden', 'Sports', 'Books'
        ]
        
        # Transaction types
        self.transaction_types = ['purchase', 'transfer', 'withdrawal', 'deposit', 'payment']

    def _log_transaction(self, transaction: Dict[str, Any], transaction_type: str = "TRANSACTION"):
        """Log transaction details to appropriate log files"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create detailed log message
        log_data = {
            "timestamp": timestamp,
            "transaction_id": transaction['id'],
            "user_id": transaction['user_id'],
            "account_id": transaction['account_id'],
            "amount": transaction['amount'],
            "currency": transaction['currency'],
            "transaction_type": transaction['transaction_type'],
            "merchant": transaction['merchant'],
            "location": transaction['location'],
            "fraud_score": transaction['fraud_score'],
            "is_fraud": transaction.get('is_fraud', False),
            "fraud_type": transaction.get('fraud_type'),
            "fraud_scenario": transaction.get('fraud_scenario'),
            "status": transaction['status']
        }
        
        # Log to main transaction log
        logger.info(f"{transaction_type}: {json.dumps(log_data, indent=2)}")
        
        # Log to specific log files based on transaction type
        if transaction.get('is_fraud'):
            fraud_log_msg = f"ID: {transaction['id']} | Amount: ₹{transaction['amount']} | Type: {transaction['transaction_type']} | Scenario: {transaction.get('fraud_type', 'Unknown')} | Score: {transaction['fraud_score']:.1f}"
            logger.info(f"FRAUD: {fraud_log_msg}")
        else:
            normal_log_msg = f"ID: {transaction['id']} | Amount: ₹{transaction['amount']} | Type: {transaction['transaction_type']} | Merchant: {transaction['merchant']} | Score: {transaction['fraud_score']:.1f}"
            logger.info(f"NORMAL: {normal_log_msg}")

    def _log_statistics(self):
        """Log current statistics"""
        total = self.normal_counter + self.fraud_counter
        fraud_percentage = (self.fraud_counter / total * 100) if total > 0 else 0
        
        stats_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_transactions": total,
            "normal_transactions": self.normal_counter,
            "fraud_transactions": self.fraud_counter,
            "fraud_percentage": round(fraud_percentage, 2),
            "generation_rate": self.generation_rate,
            "is_running": self.is_running,
            "fraud_scenarios": {
                scenario.value: count for scenario, count in self.fraud_scenarios_generated.items() if count > 0
            }
        }
        
        stats_logger.info(f"STATISTICS: {json.dumps(stats_data, indent=2)}")

    async def start_generation(self, rate: int = 1):
        """Start transaction generation at specified rate"""
        if self.is_running:
            logger.warning("Transaction generation is already running")
            return False
            
        self.generation_rate = max(1, min(5, rate))  # Clamp between 1-5
        self.is_running = True
        self.fraud_counter = 0
        self.normal_counter = 0
        
        logger.info(f"🚀 Starting transaction generation at {self.generation_rate} transactions/second")
        stats_logger.info(f"START: Generation started at {self.generation_rate} txn/sec")
        
        # Start the generation task
        self.task = asyncio.create_task(self._generation_loop())
        return True

    async def stop_generation(self):
        """Stop transaction generation"""
        if not self.is_running:
            logger.warning("Transaction generation is not running")
            return False
            
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        
        logger.info("🛑 Transaction generation stopped")
        logger.info(f"📊 Generated {self.normal_counter} normal and {self.fraud_counter} fraudulent transactions")
        logger.info("🎯 Fraud scenario distribution:")
        for scenario, count in self.fraud_scenarios_generated.items():
            if count > 0:
                logger.info(f"  📈 {scenario.value}: {count}")
        
        stats_logger.info(f"STOP: Generation stopped. Total: {self.normal_counter + self.fraud_counter} transactions")
        self._log_statistics()
        
        return True

    async def _generation_loop(self):
        """Main generation loop"""
        while self.is_running:
            try:
                # Generate transaction
                transaction = await self._generate_transaction()
                
                # Store transaction in memory
                self.generated_transactions.append(transaction)
                
                # Store transaction in graph database
                await self._store_transaction_in_graph(transaction)
                
                # Keep only last 1000 transactions
                if len(self.generated_transactions) > 1000:
                    self.generated_transactions = self.generated_transactions[-1000:]
                
                # Log transaction
                self._log_transaction(transaction)
                
                # Log statistics every 10 transactions
                if (self.normal_counter + self.fraud_counter) % 10 == 0:
                    self._log_statistics()
                
                # Wait for next generation
                await asyncio.sleep(1.0 / self.generation_rate)
                
            except Exception as e:
                logger.error(f"❌ Error in generation loop: {e}")
                await asyncio.sleep(1)

    async def _generate_transaction(self) -> Dict[str, Any]:
        """Generate a single transaction (normal or fraudulent)"""
        # Decide if this should be a fraud transaction
        should_generate_fraud = self._should_generate_fraud()
        
        if should_generate_fraud:
            return await self._generate_fraud_transaction()
        else:
            return await self._generate_normal_transaction()

    def _should_generate_fraud(self) -> bool:
        """Determine if we should generate a fraud transaction"""
        # Generate fraud every 10-15 transactions
        fraud_interval = random.randint(10, 15)
        total_transactions = self.normal_counter + self.fraud_counter
        
        if total_transactions > 0 and total_transactions % fraud_interval == 0:
            return True
        return False

    async def _generate_normal_transaction(self) -> Dict[str, Any]:
        """Generate a normal transaction between real users and accounts"""
        try:
            # Get random sender and receiver users from the graph database
            sender_user = await self._get_random_user()
            receiver_user = await self._get_random_user()
            
            if not sender_user or not receiver_user:
                logger.warning("Could not get users from graph database, using fallback")
                return self._generate_fallback_transaction()
            
            # Get account IDs from the users
            sender_account_id = None
            receiver_account_id = None
            
            logger.info(f"Sender user: {sender_user.get('id')}, accounts: {sender_user.get('accounts')}")
            logger.info(f"Receiver user: {receiver_user.get('id')}, accounts: {receiver_user.get('accounts')}")
            
            if sender_user.get('accounts') and len(sender_user['accounts']) > 0:
                sender_account = random.choice(sender_user['accounts'])
                sender_account_id = sender_account.get('account_id', sender_account.get('id', 'unknown'))
                logger.info(f"Selected sender account: {sender_account_id}")
            
            if receiver_user.get('accounts') and len(receiver_user['accounts']) > 0:
                receiver_account = random.choice(receiver_user['accounts'])
                receiver_account_id = receiver_account.get('account_id', receiver_account.get('id', 'unknown'))
                logger.info(f"Selected receiver account: {receiver_account_id}")
            
            # Generate transaction data
            transaction_id = str(uuid.uuid4())
            amount = random.uniform(100.0, 1000000.0)
            transaction_type = random.choice(["transfer", "payment", "deposit", "withdrawal"])
            
            # Get merchant and location data
            merchants = ["Amazon", "Walmart", "Target", "Starbucks", "McDonald's", "Uber", "Netflix", "Spotify"]
            locations = ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ"]
            
            transaction = {
                "id": transaction_id,
                "user_id": sender_user.get("id", "unknown"),
                "account_id": sender_account_id or "unknown",
                "amount": round(amount, 2),
                "currency": "USD",
                "transaction_type": transaction_type,
                "merchant": random.choice(merchants),
                "location": random.choice(locations),
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "fraud_score": random.uniform(0.0, 0.3),  # Low fraud score for normal transactions
                "is_fraud": False,
                "fraud_type": None,
                "fraud_scenario": None,
                "receiver_user_id": receiver_user.get("id", "unknown"),
                "receiver_account_id": receiver_account_id or "unknown"
            }
            
            # Store transaction in graph database
            await self._store_transaction_in_graph(transaction)
            
            # Log and update counters
            self._log_transaction(transaction, "NORMAL")
            self.normal_counter += 1
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error generating normal transaction: {e}")
            return self._generate_fallback_transaction()

    async def _generate_fraud_transaction(self) -> Dict[str, Any]:
        """Generate a fraudulent transaction"""
        self.fraud_counter += 1
        
        # Randomly select a fraud scenario
        fraud_scenarios = [
            self._generate_scenario_a_fraud,
            self._generate_scenario_b_fraud,
            self._generate_scenario_c_fraud,
            self._generate_scenario_d_fraud,
            self._generate_scenario_e_fraud,
            self._generate_scenario_f_fraud,
            self._generate_scenario_g_fraud,
            self._generate_scenario_h_fraud
        ]
        
        try:
            # Get random users for fraud transaction
            sender_user = await self._get_random_user()
            receiver_user = await self._get_random_user()
            
            if not sender_user or not receiver_user:
                logger.warning("Could not get users from graph database for fraud transaction")
                return self._generate_fallback_transaction()
            
            # Select random fraud scenario
            fraud_generator = random.choice(fraud_scenarios)
            transaction = await fraud_generator()
            
            # Update transaction with real user data
            transaction.update({
                "user_id": sender_user.get("id", "unknown"),
                "account_id": sender_user.get("account_id", "unknown"),
                "receiver_user_id": receiver_user.get("id", "unknown"),
                "receiver_account_id": receiver_user.get("account_id", "unknown"),
                "is_fraud": True
            })
            
            # Store in graph database
            await self._store_transaction_in_graph(transaction)
            
            # Log fraud transaction
            self._log_transaction(transaction, "FRAUD")
            
            return transaction
            
        except Exception as e:
            logger.error(f"Error generating fraud transaction: {e}")
            return self._generate_fallback_transaction()

    async def _generate_scenario_a_fraud(self) -> Dict[str, Any]:
        """Generate fraud for Scenario A: Multiple Small Credits → Large Debit"""
        user_data = await self._get_random_user()
        account = random.choice(user_data.get('accounts', []))
        
        # Generate multiple small credits first (simulate previous transactions)
        small_credits = []
        total_credits = 0
        num_credits = random.randint(2, 5)
        
        for i in range(num_credits):
            credit_amount = random.uniform(100, 500)
            small_credits.append(credit_amount)
            total_credits += credit_amount
        
        # Generate large debit that matches total credits
        debit_amount = total_credits * random.uniform(0.9, 1.0)
        
        return {
            'id': f"T{uuid.uuid4().hex[:8].upper()}",
            'user_id': user_data['id'],
            'account_id': account['id'],
            'amount': round(debit_amount, 2),
            'currency': 'USD',
            'transaction_type': 'transfer',
            'merchant': 'Online Transfer Service',
            'location': random.choice(self.normal_locations),
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'fraud_score': random.uniform(80, 95),
            'fraud_details': {
                'scenario': 'A',
                'small_credits': [round(amt, 2) for amt in small_credits],
                'total_credits': round(total_credits, 2),
                'pattern': 'Multiple small credits followed by large debit'
            }
        }

    async def _generate_scenario_b_fraud(self) -> Dict[str, Any]:
        """Generate fraud for Scenario B: Large Credit → Structured Equal Debits"""
        user_data = await self._get_random_user()
        account = random.choice(user_data.get('accounts', []))
        
        # Large credit amount
        credit_amount = random.uniform(10000, 50000)
        debit_amount = credit_amount / 4  # Each debit is 1/4 of credit
        
        return {
            'id': f"T{uuid.uuid4().hex[:8].upper()}",
            'user_id': user_data['id'],
            'account_id': account['id'],
            'amount': round(debit_amount, 2),
            'currency': 'USD',
            'transaction_type': 'transfer',
            'merchant': 'Money Transfer Service',
            'location': random.choice(self.normal_locations),
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'fraud_score': random.uniform(85, 98),
            'fraud_details': {
                'scenario': 'B',
                'original_credit': round(credit_amount, 2),
                'debit_number': random.randint(1, 4),
                'pattern': 'Large credit followed by structured equal debits'
            }
        }

    async def _generate_scenario_c_fraud(self) -> Dict[str, Any]:
        """Generate fraud for Scenario C: Multiple Large ATM Withdrawals"""
        user_data = await self._get_random_user()
        account = random.choice(user_data.get('accounts', []))
        
        # Large ATM withdrawal
        withdrawal_amount = random.uniform(100000, 1000000)
        
        return {
            'id': f"T{uuid.uuid4().hex[:8].upper()}",
            'user_id': user_data['id'],
            'account_id': account['id'],
            'amount': round(withdrawal_amount, 2),
            'currency': 'USD',
            'transaction_type': 'withdrawal',
            'merchant': 'ATM Withdrawal',
            'location': random.choice(self.normal_locations),
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'fraud_score': random.uniform(75, 90),
            'fraud_details': {
                'scenario': 'C',
                'withdrawal_number': random.randint(1, 5),
                'pattern': 'Multiple large ATM withdrawals'
            }
        }

    async def _generate_scenario_d_fraud(self) -> Dict[str, Any]:
        """Generate fraud for Scenario D: High-Frequency Transfers Between Mule Accounts"""
        user_data = await self._get_random_user()
        account = random.choice(user_data.get('accounts', []))
        
        # High-frequency transfer
        transfer_amount = random.uniform(500, 5000)
        
        return {
            'id': f"T{uuid.uuid4().hex[:8].upper()}",
            'user_id': user_data['id'],
            'account_id': account['id'],
            'amount': round(transfer_amount, 2),
            'currency': 'USD',
            'transaction_type': 'transfer',
            'merchant': 'Peer-to-Peer Transfer',
            'location': random.choice(self.normal_locations),
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'fraud_score': random.uniform(80, 95),
            'fraud_details': {
                'scenario': 'D',
                'transfer_number': random.randint(1, 15),
                'pattern': 'High-frequency transfers between mule accounts'
            }
        }

    async def _generate_scenario_e_fraud(self) -> Dict[str, Any]:
        """Generate fraud for Scenario E: Salary-Like Deposits → Suspicious Transfers"""
        user_data = await self._get_random_user()
        account = random.choice(user_data.get('accounts', []))
        
        # Suspicious transfer after salary-like deposit
        transfer_amount = random.uniform(5000, 7000)
        
        return {
            'id': f"T{uuid.uuid4().hex[:8].upper()}",
            'user_id': user_data['id'],
            'account_id': account['id'],
            'amount': round(transfer_amount, 2),
            'currency': 'USD',
            'transaction_type': 'transfer',
            'merchant': 'Online Banking Transfer',
            'location': random.choice(self.normal_locations),
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'fraud_score': random.uniform(75, 90),
            'fraud_details': {
                'scenario': 'E',
                'transfer_number': random.randint(1, 5),
                'pattern': 'Salary-like deposits followed by suspicious transfers'
            }
        }

    async def _generate_scenario_f_fraud(self) -> Dict[str, Any]:
        """Generate fraud for Scenario F: Dormant Account Sudden Activity"""
        user_data = await self._get_random_user()
        account = random.choice(user_data.get('accounts', []))
        
        # Large transaction after dormancy
        transaction_amount = random.uniform(10000, 50000)
        
        return {
            'id': f"T{uuid.uuid4().hex[:8].upper()}",
            'user_id': user_data['id'],
            'account_id': account['id'],
            'amount': round(transaction_amount, 2),
            'currency': 'USD',
            'transaction_type': 'transfer',
            'merchant': 'Account Transfer Service',
            'location': random.choice(self.normal_locations),
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'fraud_score': random.uniform(85, 98),
            'fraud_details': {
                'scenario': 'F',
                'dormancy_days': random.randint(30, 365),
                'pattern': 'Dormant account sudden activity'
            }
        }

    async def _generate_scenario_g_fraud(self) -> Dict[str, Any]:
        """Generate fraud for Scenario G: International Transfers to High-Risk Jurisdictions"""
        user_data = await self._get_random_user()
        account = random.choice(user_data.get('accounts', []))
        
        # International transfer to high-risk jurisdiction
        transfer_amount = random.uniform(500, 5000)
        jurisdiction = random.choice(self.high_risk_jurisdictions)
        
        return {
            'id': f"T{uuid.uuid4().hex[:8].upper()}",
            'user_id': user_data['id'],
            'account_id': account['id'],
            'amount': round(transfer_amount, 2),
            'currency': 'USD',
            'transaction_type': 'transfer',
            'merchant': 'International Transfer Service',
            'location': jurisdiction,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'fraud_score': random.uniform(90, 100),
            'fraud_details': {
                'scenario': 'G',
                'jurisdiction': jurisdiction,
                'transfer_number': random.randint(1, 10),
                'pattern': 'International transfers to high-risk jurisdictions'
            }
        }

    async def _generate_scenario_h_fraud(self) -> Dict[str, Any]:
        """Generate fraud for Scenario H: Region-Specific Fraud (Indian Context)"""
        user_data = await self._get_random_user()
        account = random.choice(user_data.get('accounts', []))
        
        # Large transfer from Indian fraud location
        transfer_amount = random.uniform(10000, 50000)
        fraud_location = random.choice(self.indian_fraud_locations)
        
        return {
            'id': f"T{uuid.uuid4().hex[:8].upper()}",
            'user_id': user_data['id'],
            'account_id': account['id'],
            'amount': round(transfer_amount, 2),
            'currency': 'USD',
            'transaction_type': 'transfer',
            'merchant': 'Regional Transfer Service',
            'location': fraud_location,
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'fraud_score': random.uniform(85, 98),
            'fraud_details': {
                'scenario': 'H',
                'fraud_location': fraud_location,
                'transfer_number': random.randint(1, 5),
                'pattern': 'Region-specific fraud (Indian context)'
            }
        }

    async def _get_random_user(self) -> Optional[Dict[str, Any]]:
        """Get a random user from the graph database"""
        try:
            # Query the graph database for users
            users = await self.graph_service.get_users_paginated(1, 100)  # Get up to 100 users
            if users and users.get('users'):
                user_list = users['users']
                if user_list:
                    return random.choice(user_list)
            return None
        except Exception as e:
            logger.error(f"Error getting random user: {e}")
            return None

    async def _get_random_account(self, user_id: str = None) -> Optional[Dict[str, Any]]:
        """Get a random account from the graph database"""
        try:
            # Get a random user first, then get their accounts
            user = await self._get_random_user()
            if user and user.get('accounts'):
                return random.choice(user['accounts'])
            return None
        except Exception as e:
            logger.error(f"Error getting random account: {e}")
            return None

    def _generate_fallback_transaction(self) -> Dict[str, Any]:
        """Generate a fallback transaction when no users are available"""
        return {
            'id': f"T{uuid.uuid4().hex[:8].upper()}",
            'user_id': 'U000',
            'account_id': 'A000',
            'amount': round(random.uniform(10, 1000), 2),
            'currency': 'USD',
            'transaction_type': 'purchase',
            'merchant': 'Generic Store',
            'location': 'Unknown',
            'timestamp': datetime.now().isoformat(),
            'status': 'completed',
            'fraud_score': random.uniform(0, 30),
            'fraud_type': None,
            'fraud_scenario': None,
            'is_fraud': False
        }

    async def _store_transaction_in_graph(self, transaction: Dict[str, Any]):
        """Store transaction in the graph database"""
        try:
            if self.graph_service.client:
                loop = asyncio.get_event_loop()
                
                # Find sender account vertex
                def find_sender_account():
                    try:
                        logger.info(f"Looking for sender account with ID: {transaction['account_id']}")
                        account = self.graph_service.client.V().has_label("account").has("account_id", transaction['account_id']).next()
                        logger.info(f"Found sender account vertex: {account}")
                        return account
                    except Exception as e:
                        logger.error(f"Error finding sender account {transaction['account_id']}: {e}")
                        return None
                
                # Find receiver account vertex
                def find_receiver_account():
                    try:
                        receiver_account_id = transaction.get('receiver_account_id')
                        if not receiver_account_id or receiver_account_id == 'unknown':
                            logger.warning(f"No valid receiver account ID found: {receiver_account_id}")
                            return None
                        
                        logger.info(f"Looking for receiver account with ID: {receiver_account_id}")
                        account = self.graph_service.client.V().has_label("account").has("account_id", receiver_account_id).next()
                        logger.info(f"Found receiver account vertex: {account}")
                        return account
                    except Exception as e:
                        logger.error(f"Error finding receiver account {transaction.get('receiver_account_id')}: {e}")
                        return None
                
                sender_account_vertex = await loop.run_in_executor(None, find_sender_account)
                receiver_account_vertex = await loop.run_in_executor(None, find_receiver_account)
                
                if sender_account_vertex and receiver_account_vertex:
                    # Create transaction vertex
                    def create_transaction_vertex():
                        return self.graph_service.client.add_v("transaction").property("transaction_id", transaction['id']).property("amount", transaction['amount']).property("currency", transaction['currency']).property("timestamp", transaction['timestamp']).property("location", transaction.get('location', 'Unknown')).property("fraud_score", transaction.get('fraud_score', 0.0)).property("type", transaction['transaction_type']).property("merchant", transaction.get('merchant', 'Unknown')).property("status", transaction.get('status', 'completed')).property("is_fraud", transaction.get('is_fraud', False)).property("fraud_type", transaction.get('fraud_type', '')).property("fraud_scenario", transaction.get('fraud_scenario', '')).next()
                    
                    transaction_vertex = await loop.run_in_executor(None, create_transaction_vertex)
                    
                    # Create edge from sender account to transaction
                    def create_sender_edge():
                        return self.graph_service.client.add_e("INITIATED").from_(sender_account_vertex).to(transaction_vertex).iterate()
                    
                    # Create edge from transaction to receiver account
                    def create_receiver_edge():
                        return self.graph_service.client.add_e("RECEIVED").from_(transaction_vertex).to(receiver_account_vertex).iterate()
                    
                    await loop.run_in_executor(None, create_sender_edge)
                    await loop.run_in_executor(None, create_receiver_edge)
                    
                    logger.info(f"✅ Transaction {transaction['id']} stored in graph database with both sender and receiver edges")
                else:
                    if not sender_account_vertex:
                        logger.warning(f"⚠️ Sender account {transaction['account_id']} not found in graph database, skipping storage")
                    if not receiver_account_vertex:
                        logger.warning(f"⚠️ Receiver account {transaction.get('receiver_account_id')} not found in graph database, skipping storage")
                
        except Exception as e:
            logger.error(f"❌ Error storing transaction in graph: {e}")
            # Don't fail the transaction generation, just log the error

    def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions generated by this service"""
        return self.generated_transactions[-limit:]

    def get_status(self) -> Dict[str, Any]:
        """Get current status of transaction generation"""
        return {
            "status": "running" if self.is_running else "stopped",
            "generation_rate": self.generation_rate,
            "total_generated": len(self.generated_transactions),
            "fraud_count": self.fraud_counter,
            "normal_count": self.normal_counter,
            "last_10_transactions": self.get_recent_transactions(10)
        }

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get detailed generation statistics"""
        return {
            "is_running": self.is_running,
            "generation_rate": self.generation_rate,
            "total_generated": len(self.generated_transactions),
            "fraud_count": self.fraud_counter,
            "normal_count": self.normal_counter,
            "fraud_percentage": (self.fraud_counter / len(self.generated_transactions) * 100) if self.generated_transactions else 0
        }

# Global instance
transaction_generator = None

def get_transaction_generator(graph_service: GraphService) -> TransactionGeneratorService:
    """Get or create the global transaction generator instance"""
    global transaction_generator
    if transaction_generator is None:
        transaction_generator = TransactionGeneratorService(graph_service)
    return transaction_generator 