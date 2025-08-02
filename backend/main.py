from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
import random
import uuid
import os
import sys
import argparse

from services.graph_service import GraphService
from services.fraud_detection import FraudDetectionService
from services.transaction_generator import get_transaction_generator
from models.schemas import (
    User, Account, Transaction, UserSummary, 
    TransactionDetail, FraudPattern, FraudResult
)
from logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('fraud_detection.api')

# Global variables for command line flags
args = None

# Parse command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='Fraud Detection API Server')
    parser.add_argument('-d', '--delete', action='store_true', 
                       help='Delete all data from the graph database on startup')
    parser.add_argument('-l', '--load-users', action='store_true',
                       help='Load only user data (no transactions) from users.json on startup')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=4000, help='Port to bind to (default: 4000)')
    return parser.parse_args()

# Initialize services
graph_service = GraphService()
fraud_service = FraudDetectionService(graph_service)
transaction_generator = get_transaction_generator(graph_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    global args
    
    # Startup
    logger.info("Starting Fraud Detection API")
    logger.info(f"Command line arguments: {args}")
    await graph_service.connect()
    
    # Handle command line flags
    if args and args.delete:
        logger.info("🗑️  Deleting all data from graph database...")
        try:
            result = await graph_service.delete_all_data()
            if "error" in result:
                logger.error(f"Failed to delete data: {result['error']}")
            else:
                logger.info("✅ All data deleted successfully")
        except Exception as e:
            logger.error(f"Error during data deletion: {e}")
    
    if args and args.load_users:
        logger.info("📂 Loading user data from users.json...")
        try:
            result = await graph_service.load_users_only()
            if "error" in result:
                logger.error(f"Failed to load user data: {result['error']}")
            else:
                logger.info(f"✅ User data loaded successfully: {result['users']} users, {result['accounts']} accounts")
        except Exception as e:
            logger.error(f"Error during user data loading: {e}")
    
    # Only automatically load users.json data if AUTO_LOAD_DATA is set to true and no flags are specified
    auto_load_data = os.getenv('AUTO_LOAD_DATA', 'false').lower() == 'true'
    logger.info(f"AUTO_LOAD_DATA environment variable: {auto_load_data}")
    
    if auto_load_data and (not args or (not args.delete and not args.load_users)):
        logger.info("Loading users.json data into graph database...")
        try:
            result = await graph_service.seed_sample_data()
            if "error" in result:
                logger.error(f"Failed to load data: {result['error']}")
            else:
                logger.info(f"✅ Data loaded successfully: {result['users']} users, {result['accounts']} accounts, {result['transactions']} transactions")
        except Exception as e:
            logger.error(f"Error during data loading: {e}")
    elif not args or (not args.delete and not args.load_users):
        logger.info("Skipping automatic data loading (no flags specified and AUTO_LOAD_DATA=false)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Fraud Detection API")
    await graph_service.close()

app = FastAPI(
    title="Fraud Detection API",
    description="REST API for fraud detection using Aerospike Graph",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Fraud Detection API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    graph_status = "connected" if graph_service.client else "error"
    return {
        "status": "healthy",
        "graph_connection": graph_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/seed-data")
async def seed_data():
    """Load data from users.json file into the graph"""
    try:
        result = await graph_service.seed_sample_data()
        return {
            "message": "Data loaded successfully from users.json",
            "users_created": result["users"],
            "accounts_created": result["accounts"],
            "transactions_created": result["transactions"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")


@app.get("/detect/fraudulent-transactions")
async def detect_fraudulent_transactions():
    """Run Gremlin queries to find suspicious transactions"""
    try:
        fraud_results = await fraud_service.detect_all_patterns()
        return {
            "message": "Fraud detection completed",
            "patterns_found": len(fraud_results),
            "results": fraud_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect fraud: {str(e)}")

@app.get("/user/{user_id}/summary")
async def get_user_summary(user_id: str):
    """Get user's profile, connected accounts, and transaction summary"""
    try:
        user_summary = await graph_service.get_user_summary(user_id)
        if not user_summary:
            raise HTTPException(status_code=404, detail="User not found")
        return user_summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user summary: {str(e)}")

@app.get("/user/{user_id}/transactions")
async def get_user_transactions(
    user_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Number of transactions per page")
):
    """Get paginated list of transactions for a specific user"""
    try:
        transactions = await graph_service.get_user_transactions_paginated(user_id, page, page_size)
        if not transactions:
            raise HTTPException(status_code=404, detail="User not found")
        return transactions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user transactions: {str(e)}")

@app.get("/user/{user_id}/accounts")
async def get_user_accounts(user_id: str):
    """Get all accounts for a specific user"""
    try:
        accounts = await graph_service.get_user_accounts(user_id)
        if not accounts:
            raise HTTPException(status_code=404, detail="User not found")
        return {"user_id": user_id, "accounts": accounts}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user accounts: {str(e)}")

@app.get("/transaction/{transaction_id}")
async def get_transaction_detail(transaction_id: str):
    """Get transaction details and related entities"""
    try:
        transaction_detail = await graph_service.get_transaction_detail(transaction_id)
        if not transaction_detail:
            raise HTTPException(status_code=404, detail="Transaction not found")
        return transaction_detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transaction detail: {str(e)}")

@app.get("/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats = await graph_service.get_dashboard_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard stats: {str(e)}")

@app.get("/users")
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Number of users per page")
):
    """Get paginated list of all users"""
    try:
        results = await graph_service.get_users_paginated(page, page_size)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get users: {str(e)}")

@app.get("/users/search")
async def search_users(
    query: str = Query(..., description="Search term for user name or ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Number of users per page")
):
    """Search users by name or ID with pagination"""
    try:
        results = await graph_service.search_users_paginated(query, page, page_size)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search users: {str(e)}")

@app.get("/transactions")
async def get_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Number of transactions per page")
):
    """Get paginated list of all transactions"""
    try:
        results = await graph_service.get_transactions_paginated(page, page_size)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get transactions: {str(e)}")

@app.get("/transactions/search")
async def search_transactions(
    query: str = Query(..., description="Search term for transaction ID, sender, or receiver"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Number of transactions per page")
):
    """Search transactions by ID, sender, or receiver with pagination"""
    try:
        results = await graph_service.search_transactions_paginated(query, page, page_size)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search transactions: {str(e)}")

@app.post("/fraud-patterns/run")
async def run_fraud_patterns(patterns: List[str]):
    """Run specific fraud detection patterns"""
    try:
        results = await fraud_service.run_specific_patterns(patterns)
        return {
            "message": "Fraud patterns executed",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run fraud patterns: {str(e)}")

@app.put("/transaction/{transaction_id}/status")
async def update_transaction_status(
    transaction_id: str,
    status: str = Query(..., description="New status: reviewed, safe, suspicious")
):
    """Update transaction review status"""
    try:
        result = await graph_service.update_transaction_status(transaction_id, status)
        return {"message": "Transaction status updated", "transaction_id": transaction_id, "status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update transaction status: {str(e)}")

# Transaction Generation Endpoints
@app.post("/transaction-generation/start")
async def start_transaction_generation(rate: int = Query(1, ge=1, le=5, description="Generation rate (1-5 transactions per second)")):
    """Start transaction generation at specified rate"""
    try:
        success = await transaction_generator.start_generation(rate)
        if success:
            logger.info(f"🎯 Transaction generation started at {rate} transactions/second")
            return {
                "message": f"Transaction generation started at {rate} transactions/second",
                "status": "started",
                "rate": rate
            }
        else:
            raise HTTPException(status_code=400, detail="Transaction generation is already running")
    except Exception as e:
        logger.error(f"❌ Failed to start transaction generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start transaction generation: {str(e)}")

@app.post("/transaction-generation/stop")
async def stop_transaction_generation():
    """Stop transaction generation"""
    try:
        success = await transaction_generator.stop_generation()
        if success:
            logger.info("🛑 Transaction generation stopped")
            return {
                "message": "Transaction generation stopped",
                "status": "stopped"
            }
        else:
            raise HTTPException(status_code=400, detail="Transaction generation is not running")
    except Exception as e:
        logger.error(f"❌ Failed to stop transaction generation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop transaction generation: {str(e)}")

@app.get("/transaction-generation/status")
async def get_transaction_generation_status():
    """Get current transaction generation status"""
    try:
        status = transaction_generator.get_status()
        return status
    except Exception as e:
        logger.error(f"❌ Failed to get transaction generation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@app.get("/transaction-generation/recent")
async def get_recent_transactions(limit: int = Query(10, ge=1, le=100, description="Number of recent transactions to return")):
    """Get recent transactions generated by the service"""
    try:
        recent_transactions = transaction_generator.get_recent_transactions(limit)
        return {
            "transactions": recent_transactions,
            "count": len(recent_transactions)
        }
    except Exception as e:
        logger.error(f"❌ Failed to get recent transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent transactions: {str(e)}")

if __name__ == "__main__":
    args = parse_arguments() # Parse arguments here
    logger.info(f"Parsed arguments: delete={args.delete}, load_users={args.load_users}, host={args.host}, port={args.port}")
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port) 