#!/bin/bash

# Fraud Detection Application Runner with Logging
# This script starts both the backend (FastAPI) and frontend (Next.js) applications
# along with Docker Compose containers (Aerospike Graph, Graph Service, Zipkin)

# Default values
DELETE_DATA=false
LOAD_SAMPLE_DATA=false
BACKEND_PID=""
FRONTEND_PID=""
DOCKER_COMPOSE_STARTED=false

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -d, --delete-data       Delete all existing data before starting"
    echo "  -l, --load-sample       Load data from users.json after starting applications"
    echo "  --fresh-start           Delete data and load data from users.json (equivalent to -d -l)"
    echo ""
    echo "Examples:"
    echo "  $0                      # Start applications normally"
    echo "  $0 --delete-data        # Delete all data and start"
    echo "  $0 --load-sample        # Start and load data from users.json"
    echo "  $0 --fresh-start        # Delete data and load data from users.json"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -d|--delete-data)
            DELETE_DATA=true
            shift
            ;;
        -l|--load-sample)
            LOAD_SAMPLE_DATA=true
            shift
            ;;
        --fresh-start)
            DELETE_DATA=true
            LOAD_SAMPLE_DATA=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

echo "🚀 Starting Fraud Detection Application with Logging..."

# Function to check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed. Please install Docker"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "❌ Docker is not running. Please start Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose"
        exit 1
    fi
}

# Function to start Docker Compose containers
start_docker_containers() {
    echo "🐳 Starting Docker Compose containers..."
    
    # Check if docker-compose.yaml exists
    if [ ! -f "docker-compose.yaml" ]; then
        echo "❌ docker-compose.yaml not found in current directory"
        return 1
    fi
    
    # Start containers in detached mode
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo "✅ Docker containers started successfully"
        DOCKER_COMPOSE_STARTED=true
    else
        echo "❌ Failed to start Docker containers"
        return 1
    fi
    
    # Wait for containers to be healthy
    echo "⏳ Waiting for containers to be ready..."
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep -q "healthy"; then
            echo "✅ All containers are healthy"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - Waiting for containers to be healthy..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    echo "⚠️  Some containers may not be fully ready, continuing anyway..."
    return 0
}

# Function to stop Docker Compose containers
stop_docker_containers() {
    if [ "$DOCKER_COMPOSE_STARTED" = true ]; then
        echo "🐳 Stopping Docker Compose containers..."
        docker-compose down
        echo "✅ Docker containers stopped"
    fi
}

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down applications..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    stop_docker_containers
    exit 0
}

# Function to clean up old logs
cleanup_logs() {
    echo "🧹 Cleaning up old logs..."
    if [ -d "backend/logs" ]; then
        rm -rf backend/logs/*
        echo "   ✅ Backend logs cleaned"
    fi
    if [ -d "frontend/logs" ]; then
        rm -rf frontend/logs/*
        echo "   ✅ Frontend logs cleaned"
    fi
}

# Function to delete all data from Aerospike Graph
delete_all_data() {
    echo "🗑️  Deleting all data from Aerospike Graph..."
    
    # Create a simple script to delete all data
    cat > delete_data.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
    from gremlin_python.process.anonymous_traversal import traversal
    print("🗑️  Connecting to Aerospike Graph to delete all data...")
    
    # Try to connect with retries
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Connect to graph
            connection = DriverRemoteConnection("ws://localhost:8182/gremlin", "g")
            client = traversal().with_remote(connection)
            
            # Test connection
            test_result = client.inject(0).next()
            if test_result != 0:
                print("❌ Failed to connect to graph instance")
                if attempt < max_retries - 1:
                    print(f"   Retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(2)
                    continue
                else:
                    sys.exit(1)
            
            print("✅ Connected to Aerospike Graph")
            
            # Delete all vertices and edges
            print("🗑️  Deleting all vertices and edges...")
            client.V().drop().iterate()
            
            print("✅ All data deleted successfully")
            
            # Close connection
            connection.close()
            print("✅ Disconnected from Aerospike Graph")
            break
            
        except Exception as e:
            print(f"❌ Connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                print(f"   Retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
            else:
                print("❌ All connection attempts failed")
                sys.exit(1)
    
except ImportError:
    print("❌ Gremlin Python not available")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error deleting data: {e}")
    sys.exit(1)
EOF
    
    # Run the delete script
    python3 delete_data.py
    
    # Clean up the temporary script
    rm delete_data.py
    
    if [ $? -eq 0 ]; then
        echo "✅ Data deletion completed"
    else
        echo "❌ Data deletion failed"
        return 1
    fi
}

# Function to wait for backend to be ready
wait_for_backend() {
    echo "⏳ Waiting for backend to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s http://localhost:4000/health > /dev/null 2>&1; then
            echo "✅ Backend is ready"
            return 0
        fi
        
        echo "   Attempt $attempt/$max_attempts - Backend not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Backend failed to start within expected time"
    return 1
}

# Function to load sample data using backend API
load_sample_data() {
    echo "🌱 Loading data from users.json..."
    
    # Wait for backend to be ready
    wait_for_backend
    if [ $? -ne 0 ]; then
        echo "❌ Backend not ready, cannot load data"
        return 1
    fi
    
    # Load data from users.json
    echo "🌱 Loading data from users.json file..."
    response=$(curl -s -X POST "http://localhost:4000/seed-data")
    
    if [ $? -eq 0 ]; then
        echo "✅ Data loaded successfully from users.json"
        echo "   Response: $response"
    else
        echo "❌ Failed to load data from users.json"
        return 1
    fi
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm"
    exit 1
fi

# Check if curl is installed
if ! command -v curl &> /dev/null; then
    echo "❌ curl is not installed. Please install curl"
    exit 1
fi

# Check Docker requirements
check_docker

# Clean up old logs before starting
cleanup_logs

# Start Docker Compose containers
start_docker_containers
if [ $? -ne 0 ]; then
    echo "❌ Failed to start Docker Compose containers. Exiting."
    exit 1
fi

# Delete data if requested
if [ "$DELETE_DATA" = true ]; then
    delete_all_data
    if [ $? -ne 0 ]; then
        echo "❌ Failed to delete data. Continuing anyway..."
    fi
fi

echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install -r requirements.txt

# Create logs directory
mkdir -p logs

echo "🔧 Starting backend server with logging..."
python main.py > logs/backend_console.log 2>&1 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

echo "📦 Setting up frontend..."
cd ../frontend

# Install dependencies
npm install

# Create logs directory
mkdir -p logs

echo "🎨 Starting frontend development server with logging..."
npm run dev > logs/frontend_console.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

# Load sample data if requested
if [ "$LOAD_SAMPLE_DATA" = true ]; then
    load_sample_data
    if [ $? -ne 0 ]; then
        echo "❌ Failed to load sample data"
    fi
fi

echo "✅ Applications started successfully!"
echo ""
echo "🐳 Docker Containers:"
echo "   Aerospike Database: localhost:3000-3002"
echo "   Graph Service: localhost:8182 (Gremlin), localhost:9090 (Prometheus)"
echo "   Zipkin Tracing: localhost:9411"
echo ""
echo "🌐 Frontend: http://localhost:4001"
echo "🔌 Backend API: http://localhost:4000"
echo "📚 API Documentation: http://localhost:4000/docs"
echo ""

if [ "$DELETE_DATA" = true ]; then
    echo "🗑️  Data was deleted before startup"
fi

if [ "$LOAD_SAMPLE_DATA" = true ]; then
    echo "🌱 Data from users.json was loaded"
fi

echo ""
echo "📋 Log Files:"
echo "   Backend logs: backend/logs/"
echo "   Frontend logs: frontend/logs/"
echo "   Backend console: backend/logs/backend_console.log"
echo "   Frontend console: frontend/logs/frontend_console.log"
echo ""
echo "🔍 To monitor logs in real-time:"
echo "   Backend: tail -f backend/logs/all.log"
echo "   Graph connection: tail -f backend/logs/graph.log"
echo "   Errors: tail -f backend/logs/errors.log"
echo ""
echo "🐳 Docker Container Management:"
echo "   View container status: docker-compose ps"
echo "   View container logs: docker-compose logs -f"
echo "   Stop containers only: docker-compose down"
echo ""
echo "Press Ctrl+C to stop all applications and containers"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 