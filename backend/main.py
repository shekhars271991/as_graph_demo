from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime, timedelta
import random
import uuid

from services.graph_service import GraphService
from services.fraud_detection import FraudDetectionService
from models.schemas import (
    User, Account, Transaction, UserSummary, 
    TransactionDetail, FraudPattern, FraudResult
)
from logging_config import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger('fraud_detection.api')

# Initialize services
graph_service = GraphService()
fraud_service = FraudDetectionService(graph_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Fraud Detection API")
    await graph_service.connect()
    
    # Automatically load users.json data on startup
    logger.info("Loading users.json data into graph database...")
    try:
        result = await graph_service.seed_sample_data()
        if "error" in result:
            logger.error(f"Failed to load data: {result['error']}")
        else:
            logger.info(f"✅ Data loaded successfully: {result['users']} users, {result['accounts']} accounts, {result['transactions']} transactions")
    except Exception as e:
        logger.error(f"Error during data loading: {e}")
    
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
    graph_status = "connected" if graph_service.client else "mock_mode"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4000) 