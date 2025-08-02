# Fraud Detection PoC Plan (Graph-Driven)

## Overview

This document outlines a hybrid fraud detection approach leveraging Aerospike Graph DB, demonstrating both real-time and batch-based detection. The goal is to showcase the power of graph traversal, pattern recognition, and risk scoring using transaction data.

---

## 🎯 Goals

* Highlight **graph traversal capabilities** for fraud detection
* Split detection into **Realtime (low-latency)** and **Batch (deep pattern mining)**
* Use **graph-native queries** to uncover suspicious patterns

---

## 🔁 Detection Modes

### Realtime Detection

**Objective:** Assess each incoming transaction using:

* 1–2 hop graph lookups
* Cached fraud scores
* Lightweight risk signals

### Batch Detection

**Objective:** Periodic scan of full transaction graph to:

* Identify multi-transaction and multi-hop fraud patterns
* Score accounts based on graph analytics

---

## 🧩 Scenario Categorization

| Scenario ID | Description                          | Graph Use              | Detection Mode | Notes                              |
| ----------- | ------------------------------------ | ---------------------- | -------------- | ---------------------------------- |
| RT1         | Transaction to flagged account       | 1-hop lookup           | Realtime       | Immediate threat detection         |
| RT2         | Repeated small ring interactions     | 2-hop neighborhood     | Realtime       | Identify mule rings                |
| RT3         | Supernode detection (high-degree)    | Centrality check       | Realtime       | Alert on highly connected accounts |
| RT4         | High-risk batch score                | Vertex property lookup | Realtime       | Use batch score inline             |
| BT1         | Multiple small credits → large debit | Time window path sum   | Batch          | Pattern A (structuring)            |
| BT2         | 1 large credit → 4 equal debits      | Fan-out structure      | Batch          | Pattern B                          |
| BT3         | Dormant account → sudden activity    | Temporal + path        | Batch          | Pattern F                          |
| BT4         | 3-hop transfer in short time         | Timed path             | Batch          | Rapid hops between accounts        |
| BT5         | Circular transactions                | Cycle detection        | Batch          | Detect fraud rings                 |
| BT6         | Region-based risky connections       | Geo-tagged edges       | Batch          | Pattern H (India-specific)         |

---

## 🛠 Realtime Detection Plan

### Flow:

1. Receive transaction via API
2. Lookup `fraud_score:{account_id}`
3. Run 1-hop Gremlin query:

```gremlin
g.V(account_id).out('transfers_to').has('flagged', true).limit(1)
```

4. Optionally check:

```gremlin
g.V(account_id).out('transfers_to').groupCount().unfold().count()
```

5. Compute risk score and flag if threshold is crossed

### Fast Signals:

* Connection to known fraudsters
* Abnormally high out-degree
* Cached fraud score from batch

---

## 🗃 Batch Detection Plan

### Flow:

1. Ingest all transactions (past 1–6 hrs)
2. Traverse the graph to:

   * Find multi-hop suspicious paths
   * Detect cycles
   * Identify fan-out / structuring
3. Annotate vertex properties:

   * `fraud_score`
   * `cycle_score`
   * `dormancy_flag`
4. Persist results for realtime lookup

### Example Queries:

**BT4 - Money hop in 3 hops within 1 hour**

```gremlin
g.V().hasLabel('account')
 .repeat(__.outE('transfers_to').has('timestamp', P.gt(cutoff)).inV())
 .times(3)
 .path()
 .limit(100)
```

**BT5 - Cycle detection**

```gremlin
g.V().hasLabel('account')
 .repeat(__.out('transfers_to').simplePath()).emit().times(4)
 .where(__.loops().is(P.gte(3)))
 .path()
```

---

## 📊 Visualization (Optional but Recommended)

* Use D3.js or Vis.js to show:

  * Flagged account neighborhood
  * Suspicious path traversals
  * Heatmap of fraud clusters

---

## 📦 PoC Deliverables

### Backend

* Realtime fraud scoring API (Python)
* Batch fraud scoring job (Python/Cron/Airflow)
* Graph queries integrated via Gremlin

### Data

* Simulated transactions (with fraud seeds)
* Seed graph with users, accounts, and edges

### Frontend (Optional)

* Dashboard: flagged transactions, scores, graphs
* Account drill-down: neighbors, transactions, alerts

---

## ✅ Summary

| Type     | Scenario | Graph Query             | Action           |
| -------- | -------- | ----------------------- | ---------------- |
| Realtime | RT1      | 1-hop lookup            | Flag transaction |
| Realtime | RT2      | 2-hop cycle             | Warn user        |
| Batch    | BT1      | Path + timestamp filter | Score account    |
| Batch    | BT5      | Cycle detection         | Label fraud ring |

This plan helps demonstrate how graph DB enables both **responsive fraud detection** and **deep pattern mining**, critical for modern financial systems.
