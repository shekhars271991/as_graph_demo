# Fraud Detection Scenarios Plan

## Overview
This document outlines the fraud detection scenarios that will be implemented in the Aerospike Graph-based fraud detection system. Each scenario represents a specific pattern of suspicious financial activity that could indicate fraudulent behavior.

## Scenario A: Multiple Small Credits Followed by Large Debit
**Pattern Description:** A sophisticated money laundering technique where an account receives multiple small credit transactions followed by a single large debit transaction.

**Key Indicators:**
- Multiple credit transactions occur within a 24-hour window before the debit
- Total amount of credits approximately equals the debit amount (90-100% match)
- At least 2 credit transactions are involved
- The pattern suggests structured deposits to avoid detection thresholds

**Risk Level:** High
**Common Use Case:** Money laundering, structuring transactions to avoid reporting requirements

---

## Scenario B: Large Credit Followed by Structured Equal Debits
**Pattern Description:** A pattern where a large credit is immediately followed by exactly 4 equal-sized debit transactions, typically indicating money distribution to multiple accounts.

**Key Indicators:**
- One large credit transaction ($10,000-$50,000)
- Followed by exactly 4 equal-sized debits within 4 hours
- Each debit is approximately 1/4 of the original credit amount
- All debits are directed to the same destination account
- Suggests organized distribution of funds

**Risk Level:** High
**Common Use Case:** Money mule operations, organized fraud rings

---

## Scenario C: Multiple Large ATM Withdrawals
**Pattern Description:** A pattern of multiple large ATM withdrawals that could indicate cash extraction for illicit purposes.

**Key Indicators:**
- 3 or more ATM withdrawal transactions
- Each withdrawal between $5,000-$10,000
- Self-directed transactions (account holder withdrawing from their own account)
- Suggests systematic cash extraction

**Risk Level:** Medium-High
**Common Use Case:** Cash extraction for money laundering, avoiding digital trails

---

## Scenario D: High-Frequency Transfers Between Mule Accounts
**Pattern Description:** Rapid-fire transactions between multiple accounts, indicating money mule activity or account takeover.

**Key Indicators:**
- 10 or more transactions within a short time period
- Transaction amounts between $500-$5,000 each
- Mix of credit and debit transactions within 1-hour windows
- High velocity of money movement
- Suggests coordinated account activity

**Risk Level:** High
**Common Use Case:** Money mule networks, account takeover fraud, rapid money movement

---

## Scenario E: Salary-Like Deposits Followed by Suspicious Transfers
**Pattern Description:** A pattern mimicking legitimate salary deposits but followed by suspicious outgoing transfers.

**Key Indicators:**
- Initial credit transaction resembling salary ($5,000-$10,000)
- Followed by 3 or more outgoing transfers
- Transfer amounts between $5,000-$7,000 each
- Suggests account takeover or identity theft

**Risk Level:** Medium-High
**Common Use Case:** Account takeover, identity theft, fraudulent salary deposits

---

## Scenario F: Dormant Account Sudden Activity
**Pattern Description:** A previously inactive account suddenly receives a large deposit followed by structured withdrawals.

**Key Indicators:**
- Account shows no activity for an extended period (30+ days)
- Sudden large credit transaction ($10,000-$50,000)
- Followed by exactly 4 equal debit transactions
- Total debits approximately equal the credit amount
- Suggests account compromise or takeover

**Risk Level:** High
**Common Use Case:** Account takeover, dormant account exploitation, identity theft

---

## Scenario G: International Transfers to High-Risk Jurisdictions
**Pattern Description:** Multiple transfers to specific international locations known for financial crime or money laundering.

**Key Indicators:**
- 5 or more international transfer transactions
- Transfer amounts between $500-$5,000 each
- Destinations include high-risk jurisdictions (Dubai, Bahrain, Thailand)
- Suggests international money laundering networks

**Risk Level:** High
**Common Use Case:** International money laundering, terrorist financing, cross-border fraud

---

## Scenario H: Region-Specific Fraud (Indian Context)
**Pattern Description:** Fraud patterns specific to the Indian financial landscape, targeting known fraud-prone regions.

**Key Indicators:**
- 3 or more large transfer transactions
- Transfer amounts between $10,000-$50,000
- Originating from specific high-risk locations (Jamtara, Bharatpur, Alwar)
- Transactions flagged with fraud indicators
- Region-specific fraud patterns

**Risk Level:** High
**Common Use Case:** Regional fraud networks, location-based scams, organized crime

---

## Implementation Priority

### Phase 1 (High Priority)
- Scenario A: Multiple Small Credits Followed by Large Debit
- Scenario B: Large Credit Followed by Structured Equal Debits
- Scenario D: High-Frequency Transfers Between Mule Accounts

### Phase 2 (Medium Priority)
- Scenario C: Multiple Large ATM Withdrawals
- Scenario E: Salary-Like Deposits Followed by Suspicious Transfers
- Scenario F: Dormant Account Sudden Activity

### Phase 3 (Lower Priority)
- Scenario G: International Transfers to High-Risk Jurisdictions
- Scenario H: Region-Specific Fraud (Indian Context)

## Technical Considerations

### Data Requirements
- Transaction timestamps with millisecond precision
- Transaction amounts and types (credit/debit)
- Account identifiers and relationships
- Geographic location data
- Transaction metadata (ATM withdrawals, international transfers)

### Performance Considerations
- Time-window based queries for pattern detection
- Efficient graph traversal for account relationships
- Real-time processing capabilities
- Scalable pattern matching algorithms

### Monitoring and Alerting
- Real-time fraud score calculation
- Configurable threshold adjustments
- Alert prioritization based on risk levels
- False positive reduction mechanisms

## Success Metrics
- Detection accuracy (true positive rate)
- False positive rate reduction
- Processing latency for real-time detection
- Coverage of known fraud patterns
- Adaptability to new fraud patterns 