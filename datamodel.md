# Fraud Detection Graph Data Model

This document defines the vertices and edges used in a graph database for modeling a fraud detection system.

---

## Vertices

### 1. User
- **Label:** `user`
- **Properties:**
  - `user_id` (string)
  - `name` (string)
  - `email` (string)
  - `phone` (string)
  - `age` (int)
  - `location` (string)
  - `occupation` (string)
  - `risk_score` (float)
  - `signup_date` (datetime)


---

### 2. Account
- **Label:** `account`
- **Properties:**
  - `account_id` (string)
  - `type` (string)
  - `balance` (float)
  - `status` (string)
  - `bank_name` (string)
  - `created_date` (datetime)

---

### 3. Transaction
- **Label:** `transaction`
- **Properties:**
  - `transaction_id` (string)
  - `amount` (float)
  - `timestamp` (datetime)
  - `status` (string)
  - `method` (string)
  - `ip_address` (string)
  - `location_city` (string)
  - `location_country` (string)
  - `latitude` (float)
  - `longitude` (float)

---

### 4. Device
- **Label:** `device`
- **Properties:**
  - `device_id` (string)
  - `os` (string)
  - `model` (string)
  - `imei` (string)

---

### 5. IP
- **Label:** `ip`
- **Properties:**
  - `ip_address` (string)
  - `geo_location` (string)
  - `isp` (string)

---

### 6. Merchant
- **Label:** `merchant`
- **Properties:**
  - `merchant_id` (string)
  - `name` (string)
  - `category` (string)
  - `location` (string)

---

## Edges

### 1. OWNS
- **From:** `user`
- **To:** `account`
- **Properties:**
  - `since` (datetime)

---

### 2. TRANSFERS_TO
- **From:** `account`
- **To:** `account`
- **Properties:**
  - `transaction_id` (string)
  - `amount` (float)
  - `timestamp` (datetime)
  - `status` (string)
  - `method` (string)

---

### 3. INITIATED
- **From:** `account`
- **To:** `transaction`

---

### 4. USES
- **From:** `user`
- **To:** `device`
- **Properties:**
  - `first_used_at` (datetime)

---

### 5. CONNECTED_FROM
- **From:** `device`
- **To:** `ip`

---

### 6. PAYS
- **From:** `transaction`
- **To:** `merchant`

---

### 7. OCCURRED_AT
- **From:** `transaction`
- **To:** `location`

