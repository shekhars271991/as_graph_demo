# Fraud Detection Graph Data Model

This document defines the vertices and edges used in a graph database for modeling a fraud detection system.

---

## Vertices

### 1. User
- **Label:** `user`
- **Properties:**
  - `user_id` (string) - Unique identifier for the user
  - `name` (string) - Full name of the user
  - `email` (string) - Email address
  - `phone` (string) - Phone number (optional)
  - `age` (int) - Age of the user
  - `location` (string) - User's location/city
  - `occupation` (string) - User's occupation (default: "Unknown")
  - `risk_score` (float) - Risk assessment score (default: 0.0)
  - `signup_date` (datetime) - Date when user signed up

---

### 2. Account
- **Label:** `account`
- **Properties:**
  - `account_id` (string) - Unique identifier for the account
  - `type` (string) - Account type (e.g., "checking", "savings")
  - `balance` (float) - Current account balance
  - `status` (string) - Account status (default: "active")
  - `bank_name` (string) - Name of the bank (default: "Demo Bank")
  - `created_date` (datetime) - Date when account was created

---

### 3. Transaction
- **Label:** `transaction`
- **Properties:**
  - `transaction_id` (string) - Unique identifier for the transaction
  - `amount` (float) - Transaction amount
  - `currency` (string) - Currency code (e.g., "USD")
  - `timestamp` (datetime) - When the transaction occurred
  - `location` (string) - Geographic location of the transaction
  - `fraud_score` (float) - Fraud risk score for this transaction
  - `type` (string) - Transaction type (e.g., "transfer", "payment", "deposit", "withdrawal")
  - `merchant` (string) - Merchant name where transaction occurred
  - `status` (string) - Transaction status (e.g., "completed", "pending")
  - `is_fraud` (boolean) - Whether this transaction is flagged as fraudulent
  - `fraud_type` (string) - Type of fraud if detected (optional)
  - `fraud_scenario` (string) - Fraud scenario classification (optional)

**Note:** For transactions created during data seeding, additional properties may include:
  - `method` (string) - Payment method (default: "transfer")
  - `ip_address` (string) - IP address from which transaction was initiated
  - `location_city` (string) - City where transaction occurred
  - `location_country` (string) - Country where transaction occurred
  - `latitude` (float) - Geographic latitude
  - `longitude` (float) - Geographic longitude

---

## Edges

### 1. OWNS
- **From:** `user`
- **To:** `account`
- **Properties:**
  - `since` (datetime) - Date when ownership relationship started (for seeded data)

**Description:** Represents the ownership relationship between a user and their accounts.

---

### 2. INITIATED
- **From:** `account`
- **To:** `transaction`
- **Properties:** None

**Description:** Represents that an account initiated/sent a transaction. This edge connects the sender account to the transaction.

---

### 3. RECEIVED
- **From:** `transaction`
- **To:** `account`
- **Properties:** None

**Description:** Represents that a transaction was received by an account. This edge connects the transaction to the receiver account.

---

### 4. TRANSFERS_TO (Legacy - Used in Seeded Data Only)
- **From:** `account`
- **To:** `account`
- **Properties:**
  - `transaction_id` (string) - Reference to the transaction
  - `amount` (float) - Amount transferred
  - `timestamp` (datetime) - When the transfer occurred
  - `status` (string) - Transfer status
  - `method` (string) - Transfer method

**Description:** Direct transfer relationship between accounts (used only in initial data seeding, not in generated transactions).

---

## Data Flow

### Transaction Model
The transaction model uses a vertex-centric approach:

1. **Sender Account** → **Transaction** (via `INITIATED` edge)
2. **Transaction** → **Receiver Account** (via `RECEIVED` edge)

This allows for:
- Easy traversal to find all transactions initiated by an account
- Easy traversal to find all transactions received by an account
- Rich transaction properties stored on the transaction vertex
- Support for complex fraud detection patterns

### Query Patterns
- **Find sender of a transaction:** `V(transaction).in('INITIATED')`
- **Find receiver of a transaction:** `V(transaction).out('RECEIVED')`
- **Find all transactions sent by an account:** `V(account).out('INITIATED')`
- **Find all transactions received by an account:** `V(account).in('RECEIVED')`
- **Find all user's transactions:** `V(user).out('OWNS').both('INITIATED', 'RECEIVED')`

