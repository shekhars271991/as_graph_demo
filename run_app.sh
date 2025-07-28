#!/bin/bash

# Fraud Detection Application Runner with Logging
# This script starts both the backend (FastAPI) and frontend (Next.js) applications

echo "🚀 Starting Fraud Detection Application with Logging..."

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down applications..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
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

# Clean up old logs before starting
cleanup_logs

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

echo "✅ Applications started successfully!"
echo ""
echo "🌐 Frontend: http://localhost:4001"
echo "🔌 Backend API: http://localhost:4000"
echo "📚 API Documentation: http://localhost:4000/docs"
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
echo "Press Ctrl+C to stop both applications"

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID 