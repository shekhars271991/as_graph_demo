# Fraud Detection Application

A comprehensive fraud detection system built with FastAPI backend and Next.js frontend, utilizing Aerospike Graph for real-time graph-based fraud detection.

## 🏗️ Architecture

### Backend (Python + FastAPI)
- **Framework**: FastAPI with async support
- **Graph Database**: Aerospike Graph Service (AGS) via Gremlin queries
- **Features**:
  - RESTful API endpoints for fraud detection
  - Real-time Gremlin query execution
  - Sample data seeding
  - User and transaction management
  - Fraud pattern detection algorithms

### Frontend (Next.js + TailwindCSS)
- **Framework**: Next.js 14 with App Router
- **Styling**: TailwindCSS with dark/light theme support
- **Features**:
  - Modern, responsive dashboard
  - Real-time data visualization
  - User and transaction exploration
  - Fraud pattern analysis
  - Interactive graph visualization (Phase 2)

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **Node.js 16+**
3. **Aerospike Graph Service** running on `localhost:8182`



### Installation & Running

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DemoApp
   ```

2. **Run the application**
   ```bash
   # Basic startup
   ./run_app.sh
   
   # With data management options
   ./run_app.sh --help                    # Show all options
   ./run_app.sh --fresh-start             # Delete data and load data from users.json
   ./run_app.sh -d -l                     # Delete data and load data from users.json
   ./run_app.sh --load-sample             # Load data from users.json
   ```

   **Command Line Options:**
   - `-h, --help` - Show help message
   - `-d, --delete-data` - Delete all existing data before starting
   - `-l, --load-sample` - Load data from users.json after starting applications
   - `--fresh-start` - Delete data and load data from users.json (equivalent to -d -l)

   This script will:
   - Install Python dependencies and create virtual environment
   - Install Node.js dependencies
   - Start the FastAPI backend on port 4000
   - Start the Next.js frontend on port 4001
   - Optionally delete existing data and load data from users.json

3. **Access the application**
   - Frontend: http://localhost:4001
- Backend API: http://localhost:4000
- API Documentation: http://localhost:4000/docs

## 📁 Project Structure

```
DemoApp/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── models/
│   │   └── schemas.py         # Pydantic data models
│   └── services/
│       ├── graph_service.py   # Aerospike Graph interactions
│       └── fraud_detection.py # Fraud detection algorithms
├── frontend/
│   ├── package.json           # Node.js dependencies
│   ├── next.config.js         # Next.js configuration
│   ├── tailwind.config.js     # TailwindCSS configuration
│   ├── app/
│   │   ├── layout.tsx         # Root layout component
│   │   ├── page.tsx           # Dashboard page
│   │   └── globals.css        # Global styles
│   ├── components/
│   │   ├── ui/                # Reusable UI components
│   │   ├── Navbar.tsx         # Navigation component
│   │   └── ThemeProvider.tsx  # Theme management
│   └── lib/
│       ├── api.ts             # API client
│       └── utils.ts           # Utility functions
└── run_app.sh                 # Application runner script
```

## 🔧 Backend API Endpoints

### Core Endpoints
- `GET /` - Health check
- `POST /seed-data` - Load data from users.json file
- `GET /detect/fraudulent-transactions` - Run fraud detection
- `GET /dashboard/stats` - Get dashboard statistics

### User Management
- `GET /user/{user_id}/summary` - Get user summary
- `GET /users` - Get paginated list of all users
- `GET /users/search` - Search users with pagination

### Transaction Management
- `GET /transaction/{transaction_id}` - Get transaction details
- `GET /transactions/search` - Search transactions
- `PUT /transaction/{transaction_id}/status` - Update transaction status

### Fraud Detection
- `POST /fraud-patterns/run` - Run specific fraud patterns

## 🕵️ Fraud Detection Patterns

The system implements several fraud detection patterns using Gremlin queries:

1. **Circular Transaction Flow**
   - Detects circular money flows between users
   - Identifies potential money laundering schemes

2. **Shared Device Transactions**
   - Detects transactions from the same device by different users
   - Indicates potential account takeover or shared credentials

3. **Transaction Burst**
   - Identifies rapid successive transactions from the same user
   - Flags unusual activity patterns

4. **High Amount Transactions**
   - Detects unusually high transaction amounts
   - Configurable threshold-based detection

5. **Cross-Location Transactions**
   - Identifies transactions between users in different locations
   - Geographic anomaly detection

6. **New User High Activity**
   - Detects new users with high transaction activity
   - Potential fake account creation

## 🎨 Frontend Features

### Dashboard
- Real-time statistics overview
- Quick action buttons
- System health monitoring
- Fraud detection rate tracking

### User Explorer
- Search users by ID or name
- View user profiles and risk scores
- Display connected accounts and transactions
- Color-coded fraud risk indicators

### Transaction Explorer
- Search transactions by ID
- Detailed transaction information
- Sender/receiver details
- Suspicious pattern highlighting

### Fraud Patterns
- Trigger predefined fraud detection queries
- View detected anomalies
- Mark transactions as reviewed/safe/suspicious
- Pattern-specific risk scoring

## 🔒 Security Features

- CORS configuration for frontend-backend communication
- Input validation using Pydantic models
- Error handling and logging
- Transaction status management
- Risk scoring algorithms

## 🛠️ Development

### Backend Development
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Testing
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## 📊 Data Models

### User
- ID, name, email, age
- Signup date, location
- Risk score, flagged status

### Account
- ID, user ID, account type
- Balance, created date
- Active status

### Transaction
- ID, sender/receiver IDs
- Amount, currency, timestamp
- Location, device ID
- Status, fraud score

## 🔮 Future Enhancements (Phase 2)

- Interactive graph visualization
- Real-time transaction monitoring
- Machine learning-based fraud detection
- Advanced analytics dashboard
- Multi-tenant support
- API rate limiting
- Enhanced security features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at http://localhost:4000/docs
- Review the backend logs for debugging information 