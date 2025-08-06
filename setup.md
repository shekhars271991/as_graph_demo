# Setup Instructions

This guide will help you set up the Fraud Detection Application on your local machine.

## 📋 Prerequisites

### Required Software
1. **Docker & Docker Compose** - For Aerospike Graph Service and related services
   - [Install Docker Desktop](https://docs.docker.com/get-docker/) (includes Docker Compose)
   - Ensure Docker is running before starting the application
2. **Python 3.8+** - Backend runtime
3. **Node.js 16+** - Frontend runtime
4. **Git** - Version control

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space for Docker images
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)

## 🐳 Containerized Services

The application uses Docker Compose to automatically provide:
- **Aerospike Database Server** - Graph data storage (ports 3000-3002)
- **Aerospike Graph Service (AGS)** - Graph query engine (port 8182)
- **Zipkin** - Distributed tracing (port 9411)

**No manual service installation required!** 🎉

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd DemoApp
```

### 2. Run the Application (Recommended)
The `run_app.sh` script handles everything automatically:

```bash
# Basic startup (starts Docker services + backend + frontend)
./run_app.sh

# Show all available options
./run_app.sh --help

# Load sample data from users.json
./run_app.sh -l
```

**Command Line Options:**
- `-h, --help` - Show help message
- `-l, --load-users` - Delete all data and load users, accounts, devices from users.json

The script will automatically:
1. **Check Docker availability** and start Docker Compose services
2. **Wait for services to be healthy** (Aerospike DB, Graph Service, Zipkin)
3. **Create Python virtual environment** and install dependencies
4. **Install Node.js dependencies**
5. **Start the FastAPI backend** on port 4000
6. **Start the Next.js frontend** on port 4001
7. **Optionally load sample data**

### 3. Access the Application
Once setup is complete, you can access:
- **Frontend**: http://localhost:4001
- **Backend API**: http://localhost:4000
- **API Documentation**: http://localhost:4000/docs
- **Zipkin Tracing**: http://localhost:9411 (optional)

## 🛠️ Manual Setup (Advanced)

If you prefer to run services manually:

### 1. Start Docker Services
```bash
# Start containerized services
docker-compose up -d

# Check service health
docker-compose ps

# Wait for services to be ready (look for "healthy" status)
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Start the backend server
python main.py
```
The backend will be available at http://localhost:4000

### 3. Frontend Setup

```bash
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```
The frontend will be available at http://localhost:3000 (or port 4001 with custom config)

## 📊 Sample Data Setup

### Loading Sample Data
The application includes sample data in `data/users.json`. To load this data:

1. **Using the API endpoint**
   ```bash
   curl -X POST http://localhost:4000/seed-data
   ```

2. **Using the run script**
   ```bash
   ./run_app.sh --load-sample
   ```

### Sample Data Structure
The sample data includes:
- **Users**: 100+ sample users with realistic profiles
- **Accounts**: Multiple accounts per user (savings, checking, etc.)
- **Devices**: User devices with fingerprints and login history
- **Fraud Flags**: Some accounts and devices are pre-flagged for testing

## �� Configuration

### Docker Services Configuration
The Docker Compose setup provides production-ready services:

**Aerospike Database:**
- Image: `aerospike/aerospike-server-enterprise:8.0.0.7`
- Ports: 3000-3002
- Namespace: `test`

**Aerospike Graph Service:**
- Image: `aerospike/aerospike-graph-service:latest`
- Ports: 8182 (Gremlin), 9090 (metrics)
- Connected to Aerospike DB and Zipkin

**Zipkin (Tracing):**
- Image: `openzipkin/zipkin`
- Port: 9411
- Optional for monitoring graph query performance

### Environment Variables
Create a `.env` file in the backend directory for custom configuration:

```env
# Backend Configuration
HOST=localhost
PORT=4000
DEBUG=true

# Graph Service Configuration (automatically provided by Docker)
GRAPH_HOST=localhost
GRAPH_PORT=8182

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:4000
```

### Port Configuration
Default ports used by the application:
- **Frontend**: 4001 (configured in run_app.sh)
- **Backend**: 4000
- **Aerospike Graph Service**: 8182 (Docker)
- **Aerospike Database**: 3000-3002 (Docker)
- **Zipkin**: 9411 (Docker)

To change ports:
1. **Backend Port**: Modify `main.py` or environment variables
2. **Frontend Port**: Modify the run_app.sh script
3. **Docker Services**: Modify `docker-compose.yaml` port mappings

## 🧪 Development Setup

### Backend Development
```bash
cd backend
source venv/bin/activate

# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 4000

# Run tests (if available)
pytest

# Code formatting
black .
flake8 .
```

### Frontend Development
```bash
cd frontend

# Start development server with hot reload
npm run dev

# Run tests
npm test

# Run linter
npm run lint

# Build for production
npm run build

# Type checking
npm run type-check
```

### Docker Development
```bash
# View logs from all services
docker-compose logs -f

# View logs from specific service
docker-compose logs -f aerospike-graph-service

# Restart services
docker-compose restart

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

## 🔍 Fraud Detection Services

### RT1 - Flagged Account Detection
Detects transactions involving previously flagged accounts.

### RT2 - Flagged Device Connection
Detects transactions involving accounts connected to flagged devices.

### Configuration
Enable/disable fraud detection services via the Admin Panel:
- Navigate to http://localhost:4001/admin
- Go to "Real Time Fraud Scenarios" tab
- Toggle RT1 and RT2 services as needed

## 🐛 Troubleshooting

### Common Issues

1. **Docker Not Running**
   ```bash
   # Check if Docker is running
   docker --version
   docker-compose --version
   
   # Start Docker Desktop (macOS/Windows)
   # Or start Docker service (Linux)
   sudo systemctl start docker
   ```

2. **Port Already in Use**
   ```bash
   # Kill processes on conflicting ports
   sudo lsof -ti:4000 | xargs kill -9  # Backend
   sudo lsof -ti:4001 | xargs kill -9  # Frontend
   sudo lsof -ti:8182 | xargs kill -9  # Graph Service
   
   # Or stop Docker services
   docker-compose down
   ```

3. **Docker Services Not Healthy**
   ```bash
   # Check service status
   docker-compose ps
   
   # View service logs
   docker-compose logs aerospike-db
   docker-compose logs aerospike-graph-service
   
   # Restart services
   docker-compose restart
   ```

4. **Python Virtual Environment Issues**
   ```bash
   # Remove and recreate virtual environment
   rm -rf backend/venv
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Node.js Dependency Issues**
   ```bash
   # Clear npm cache and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm cache clean --force
   npm install
   ```

6. **Graph Service Connection Issues**
   ```bash
   # Test Graph Service connectivity
   curl http://localhost:8182
   
   # Check if services are running
   docker-compose ps
   
   # View detailed logs
   docker-compose logs -f aerospike-graph-service
   ```

7. **CORS Issues**
   - Ensure frontend URL is in backend CORS settings
   - Check browser console for specific CORS errors
   - Verify API calls are using correct URLs

### Service Health Monitoring

```bash
# Check all service health
docker-compose ps

# Monitor service logs in real-time
docker-compose logs -f

# Check specific service health
docker-compose exec aerospike-graph-service curl http://localhost:8182
```

### Performance Issues
- **Slow Graph Queries**: Check Docker container resource limits
- **Memory Issues**: Increase Docker Desktop memory allocation
- **Container Issues**: Check Docker logs and restart services

### Logging
- **Backend logs**: Console output from `python main.py`
- **Frontend logs**: Browser console and terminal output
- **Docker services**: `docker-compose logs -f`
- **Individual service**: `docker-compose logs <service-name>`

## 📝 Verification

After setup, verify everything is working:

### 1. Docker Services Health Check
```bash
# Check all services are running and healthy
docker-compose ps

# Should show services with "healthy" status:
# - aerospike-db (healthy)
# - aerospike-graph-service (Up)
# - asgraph-zipkin (Up)
```

### 2. Graph Service Connectivity
```bash
# Test Aerospike Graph Service
curl http://localhost:8182
# Should return Gremlin server information

# Alternative test
telnet localhost 8182
```

### 3. Backend Health Check
```bash
curl http://localhost:4000/
# Should return: {"status": "Fraud Detection API is running"}
```

### 4. Frontend Access
- Navigate to http://localhost:4001
- Should see the dashboard with navigation
- Check browser console for any errors

### 5. Sample Data Loading
```bash
curl -X POST http://localhost:4000/seed-data
# Should return success message about loading users/accounts/devices
```

### 6. Fraud Detection Status
```bash
curl http://localhost:4000/fraud-detection/status
# Should return RT1 and RT2 status information
```

### 7. Complete Application Test
1. Access frontend at http://localhost:4001
2. Navigate to Users page and search for a user
3. View user details and recent transactions
4. Go to Admin panel and test manual transaction creation
5. Check fraud detection controls work

## 🆘 Getting Help

If you encounter issues:

1. **Check Docker services first**:
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

2. **Verify prerequisites**:
   - Docker Desktop is running
   - No port conflicts (8182, 4000, 4001)
   - Sufficient system resources

3. **Check the logs** for specific error messages
4. **Review the API documentation** at http://localhost:4000/docs
5. **Create an issue** in the repository with:
   - Docker service status (`docker-compose ps`)
   - Error messages from logs
   - Setup environment details
   - Steps to reproduce

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Aerospike Graph Documentation](https://docs.aerospike.com/graph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

## ⚡ Production Deployment

For production deployment:

### Docker Configuration
1. **Use production images**: Update `docker-compose.yaml`
2. **Environment variables**: Set production values
3. **Resource limits**: Configure memory/CPU limits
4. **Persistent volumes**: Add data persistence
5. **Network security**: Configure secure networking

### Application Configuration
1. **HTTPS**: Configure SSL certificates
2. **Authentication**: Enable user authentication
3. **Monitoring**: Set up comprehensive logging and monitoring
4. **Backup**: Configure data backup strategies
5. **Scaling**: Use Docker Swarm or Kubernetes for scaling

### Security Considerations
1. **Container security**: Scan images for vulnerabilities
2. **Network isolation**: Use custom Docker networks
3. **Secret management**: Use Docker secrets or external vaults
4. **Access control**: Implement proper access controls 