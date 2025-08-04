import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import local modules
from graph_service import GraphService
from services.transaction_generator import get_transaction_generator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/transaction_generator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize services
graph_service = GraphService()
transaction_generator = get_transaction_generator(graph_service)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Transaction Generator Microservice")
    await graph_service.connect()
    
    # Automatically load users.json data on startup
    logger.info("📊 Loading users.json data into graph database...")
    try:
        result = await graph_service.seed_sample_data()
        if "error" in result:
            logger.error(f"❌ Failed to load data: {result['error']}")
        else:
            logger.info(f"✅ Data loaded successfully: {result['users']} users, {result['accounts']} accounts, {result['transactions']} transactions")
    except Exception as e:
        logger.error(f"❌ Error during data loading: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Transaction Generator Microservice")
    await graph_service.close()

# Create FastAPI app
app = FastAPI(
    title="Transaction Generator Microservice",
    description="Microservice for generating transactions and fraud patterns",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Transaction Generator Microservice is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check graph service connection
        graph_healthy = graph_service.client is not None
        
        return {
            "status": "healthy",
            "graph_service": "connected" if graph_healthy else "disconnected",
            "transaction_generator": "ready",
            "users_loaded": len(graph_service.users_data) if graph_service.users_data else 0
        }
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

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
    """Get transaction generation status and statistics"""
    try:
        stats = transaction_generator.get_generation_stats()
        return {
            "status": "running" if stats["is_running"] else "stopped",
            "generation_rate": stats["generation_rate"],
            "total_generated": stats["total_generated"],
            "normal_transactions": stats["normal_transactions"],
            "fraud_transactions": stats["fraud_transactions"],
            "fraud_scenarios_generated": {
                scenario.value: count for scenario, count in stats["fraud_scenarios_generated"].items() if count > 0
            },
            "last_10_transactions": stats["last_10_transactions"]
        }
    except Exception as e:
        logger.error(f"❌ Failed to get generation status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get generation status: {str(e)}")

@app.get("/transaction-generation/recent")
async def get_recent_transactions(limit: int = Query(10, ge=1, le=100, description="Number of recent transactions to return")):
    """Get recent generated transactions"""
    try:
        transactions = transaction_generator.get_recent_transactions(limit)
        return {
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        logger.error(f"❌ Failed to get recent transactions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent transactions: {str(e)}")

@app.post("/seed-data")
async def seed_data():
    """Load data from users.json file into the graph"""
    try:
        result = await graph_service.seed_sample_data()
        logger.info(f"✅ Data loaded successfully: {result['users']} users, {result['accounts']} accounts, {result['transactions']} transactions")
        return {
            "message": "Data loaded successfully from users.json",
            "users_created": result["users"],
            "accounts_created": result["accounts"],
            "devices_created": result["devices"],
            "transactions_created": result["transactions"]
        }
    except Exception as e:
        logger.error(f"❌ Failed to load data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=4002,  # Different port from main backend
        reload=False,  # Disable reload in Docker
        log_level="info"
    ) 