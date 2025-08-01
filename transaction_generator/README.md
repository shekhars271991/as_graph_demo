# Transaction Generator Microservice

A standalone microservice for generating realistic financial transactions and injecting fraudulent patterns for testing fraud detection systems.

## Overview

This microservice generates both normal and fraudulent transactions at configurable rates, storing them in an Aerospike Graph database. It implements 8 different fraud scenarios based on real-world patterns.

## Features

- **Real-time Transaction Generation**: Configurable rates (1-5 transactions/second)
- **Fraud Pattern Injection**: Automatically injects fraud every 10-15 transactions
- **8 Fraud Scenarios**: Complete implementation of all fraud patterns
- **Graph Database Integration**: Stores transactions in Aerospike Graph
- **REST API**: Full API for controlling generation and monitoring
- **Real-time Monitoring**: Live statistics and transaction feeds
- **Comprehensive Logging**: Detailed logs for every transaction
- **Docker Support**: Fully containerized deployment

## Fraud Scenarios Implemented

1. **Scenario A**: Multiple Small Credits → Large Debit
2. **Scenario B**: Large Credit → Structured Equal Debits
3. **Scenario C**: Multiple Large ATM Withdrawals
4. **Scenario D**: High-Frequency Mule Account Transfers
5. **Scenario E**: Salary-Like Deposits → Suspicious Transfers
6. **Scenario F**: Dormant Account Sudden Activity
7. **Scenario G**: International High-Risk Transfers
8. **Scenario H**: Region-Specific Indian Fraud

## Quick Start

### Prerequisites

- Docker and Docker Compose running
- Main application started (`./run_app.sh`)
- Python 3.9+ (for local development)

### Option 1: Docker Deployment (Recommended)

```bash
# From the DemoApp root directory
./run_transaction_generator_docker.sh
```

### Option 2: Local Development

```bash
# From the DemoApp root directory
./run_transaction_generator.sh
```

The service will be available at:
- **Service**: http://localhost:4002
- **API Docs**: http://localhost:4002/docs
- **Health Check**: http://localhost:4002/health

## Logging System

The microservice provides comprehensive logging with multiple log files:

### Log Files

- **`logs/transactions.log`** - All transactions (normal and fraud)
- **`logs/fraud_transactions.log`** - Fraud transactions only
- **`logs/normal_transactions.log`** - Normal transactions only
- **`logs/statistics.log`** - Generation statistics and metrics
- **`logs/transaction_generator.log`** - Application logs

### Log Monitoring

```bash
# Monitor all transaction logs in real-time
./monitor_transaction_logs.sh

# Or monitor specific logs directly
tail -f transaction_generator/logs/transactions.log
tail -f transaction_generator/logs/fraud_transactions.log
tail -f transaction_generator/logs/statistics.log
```

### Log Format Examples

**Transaction Log:**
```
2024-01-15 10:30:45 - INFO - TRANSACTION: {
  "timestamp": "2024-01-15 10:30:45",
  "transaction_id": "T1A2B3C4D",
  "user_id": "U001",
  "account_id": "A001",
  "amount": 1250.50,
  "currency": "USD",
  "transaction_type": "transfer",
  "merchant": "Online Transfer Service",
  "location": "New York",
  "fraud_score": 85.5,
  "is_fraud": true,
  "fraud_type": "Multiple Small Credits Followed by Large Debit",
  "fraud_scenario": "SCENARIO_A",
  "status": "completed"
}
```

**Statistics Log:**
```
2024-01-15 10:30:45 - STATS - STATISTICS: {
  "timestamp": "2024-01-15 10:30:45",
  "total_transactions": 150,
  "normal_transactions": 135,
  "fraud_transactions": 15,
  "fraud_percentage": 10.0,
  "generation_rate": 3,
  "is_running": true,
  "fraud_scenarios": {
    "Multiple Small Credits Followed by Large Debit": 3,
    "Large Credit Followed by Structured Equal Debits": 2
  }
}
```

## API Endpoints

### Health & Status
- `GET /` - Service health check
- `GET /health` - Detailed health status

### Transaction Generation Control
- `POST /transaction-generation/start?rate={1-5}` - Start generation
- `POST /transaction-generation/stop` - Stop generation
- `GET /transaction-generation/status` - Get real-time status
- `GET /transaction-generation/recent?limit={1-100}` - Get recent transactions

### Data Management
- `POST /seed-data` - Load users.json data into graph

## API Examples

### Start Transaction Generation
```bash
curl -X POST "http://localhost:4002/transaction-generation/start?rate=3"
```

### Get Status
```bash
curl "http://localhost:4002/transaction-generation/status"
```

### Stop Generation
```bash
curl -X POST "http://localhost:4002/transaction-generation/stop"
```

## Response Format

### Status Response
```json
{
  "status": "running",
  "generation_rate": 3,
  "total_generated": 150,
  "normal_transactions": 135,
  "fraud_transactions": 15,
  "fraud_scenarios_generated": {
    "Multiple Small Credits Followed by Large Debit": 3,
    "Large Credit Followed by Structured Equal Debits": 2
  },
  "last_10_transactions": [...]
}
```

### Transaction Format
```json
{
  "id": "T1A2B3C4D",
  "user_id": "U001",
  "account_id": "A001",
  "amount": 1250.50,
  "currency": "USD",
  "transaction_type": "transfer",
  "merchant": "Online Transfer Service",
  "location": "New York",
  "timestamp": "2024-01-15T10:30:00",
  "status": "completed",
  "fraud_score": 85.5,
  "fraud_type": "Multiple Small Credits Followed by Large Debit",
  "fraud_scenario": "SCENARIO_A",
  "is_fraud": true
}
```

## Architecture

```
transaction_generator/
├── main.py                 # FastAPI application
├── services/
│   └── transaction_generator.py  # Core generation logic
├── models/                 # Data models (shared with main backend)
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker Compose configuration
└── README.md              # This file
```

## Configuration

### Generation Rates
- **Minimum**: 1 transaction/second
- **Maximum**: 5 transactions/second
- **Default**: 1 transaction/second

### Fraud Injection
- **Frequency**: Every 10-15 transactions (randomized)
- **Distribution**: All 8 scenarios generated equally over time
- **Realism**: Fraud transactions look like normal transactions with high fraud scores

### Data Storage
- **Database**: Aerospike Graph
- **Retention**: Last 1000 transactions in memory
- **Persistence**: All transactions stored in graph database

## Monitoring

### Real-time Monitoring
- Live transaction counters
- Fraud scenario distribution
- Generation rate and uptime
- Comprehensive logging

### Log Monitoring Tools
```bash
# Interactive log monitor
./monitor_transaction_logs.sh

# Direct log viewing
tail -f transaction_generator/logs/transactions.log
tail -f transaction_generator/logs/fraud_transactions.log
tail -f transaction_generator/logs/statistics.log

# Docker container logs
cd transaction_generator && docker-compose logs -f
```

## Docker Management

### Container Commands
```bash
# Start the service
./run_transaction_generator_docker.sh

# View container status
cd transaction_generator && docker-compose ps

# View container logs
cd transaction_generator && docker-compose logs -f

# Stop the service
cd transaction_generator && docker-compose down

# Restart the service
cd transaction_generator && docker-compose restart

# Rebuild and restart
cd transaction_generator && docker-compose up --build -d
```

### Docker Health Checks
The container includes health checks that monitor:
- Service availability on port 4002
- Health endpoint responsiveness
- Automatic restart on failure

## Integration

### Frontend Integration
The frontend admin panel automatically connects to this microservice on port 4002.

### Main Backend
This microservice shares the same graph database as the main backend but operates independently.

## Development

### Local Development
```bash
cd transaction_generator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Testing
```bash
# Test the microservice
./test_transaction_generator.sh

# Manual testing
curl http://localhost:4002/health
curl -X POST "http://localhost:4002/transaction-generation/start?rate=1"
sleep 10
curl http://localhost:4002/transaction-generation/status
curl -X POST "http://localhost:4002/transaction-generation/stop"
```

## Troubleshooting

### Common Issues

1. **Port 4002 already in use**
   - Check if another instance is running
   - Kill existing process: `lsof -ti:4002 | xargs kill`

2. **Graph database connection failed**
   - Ensure main application is running: `./run_app.sh`
   - Check Docker containers: `docker-compose ps`

3. **No users data loaded**
   - Call seed endpoint: `curl -X POST http://localhost:4002/seed-data`

4. **Docker container not starting**
   - Check Docker logs: `cd transaction_generator && docker-compose logs`
   - Ensure Docker is running and has sufficient resources

### Logs
Check logs for detailed error information:
```bash
# Application logs
tail -f transaction_generator/logs/transaction_generator.log

# Docker logs
cd transaction_generator && docker-compose logs -f

# Transaction logs
tail -f transaction_generator/logs/transactions.log
```

## Security Notes

- CORS is enabled for all origins (configure for production)
- No authentication implemented (add for production use)
- Logs may contain sensitive transaction data
- Docker container runs as non-root user

## Performance

### Resource Requirements
- **CPU**: Minimal (single core sufficient)
- **Memory**: ~100MB base + transaction storage
- **Storage**: ~50MB for application + log files
- **Network**: Low bandwidth (local connections only)

### Scaling
- Multiple instances can run simultaneously
- Each instance maintains its own transaction counters
- Shared database ensures no conflicts

## License

This microservice is part of the Fraud Detection Demo Application. 