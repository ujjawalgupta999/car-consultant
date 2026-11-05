# AMULATE SUMMER HACKATHON 2026: CONSTITUTION
## AI-Powered Car Rental and Purchase Consultant

This document establishes the inviolable core principles, ethical guidelines, and architectural laws governing the design, implementation, and operation of the AI-Powered Car Rental and Purchase Consultant.

---

### Article I: Determinism and Truthfulness in Automotive Commerce

1. **Zero Hallucination of Inventory & Pricing**:
   - The agent shall never invent, hallucinate, or alter vehicle specifications, prices, availability dates, or ratings.
   - All vehicle data presented to the user must originate from validated repository records.
   - The agent is strictly prohibited from promising discounts, availability, or terms not backed by deterministic backend rules.

2. **Verifiable Explanations**:
   - Every recommendation must include an explainable scoring breakdown based on deterministic weights.
   - Trade-offs, missing features, and compromises must be explicitly surfaced to the user.
   - If a strict filter returns zero results, the system shall honestly explain which constraint eliminated the listings and never fabricate substitute inventory.

3. **Separation of Intent**:
   - Rental and purchase operations have distinct business logic, legal agreements, pricing models, and availability mechanics.
   - The system shall never mix rental daily rates with purchase prices or conflate rental dates with vehicle ownership transfers.

---

### Article II: Safety and Mock Financial Operations

1. **Absolute Prohibition of Real Financial Processing**:
   - The application is an educational, hackathon-grade system. Under no circumstances shall real payment gateways, credit card processing networks, or banking APIs be connected.
   - Real credit card numbers, CVVs, expiration dates, bank accounts, or UPI PINs shall never be collected, stored, or processed.

2. **Explicit User Communication**:
   - All checkout and payment interfaces must prominently display the disclaimer:
     > *"SIMULATED ENVIRONMENT: No real money is charged. Do not enter real payment credentials."*
   - Payment simulations must be deterministic, supporting predefined test scenarios (e.g., successful authorization, card decline, timeout).

3. **Backend-Authoritative Pricing & Idempotency**:
   - The client UI shall never dictate the final payable amount. All totals, taxes, and fees must be recalculated and cryptographically verified or signed by the backend.
   - All booking creation and mock payment submissions must enforce idempotency keys to prevent duplicate transactions.

---

### Article III: User Privacy, Session Ownership, and Security

1. **Session Ownership & Data Isolation**:
   - Each conversation session is private to its authenticated or token-holding user.
   - Cross-session leakage or unauthorized access to another user's preferences, booking details, or order status is strictly prohibited.

2. **Protection Against Injection**:
   - External vehicle descriptions and user inputs must be treated as untrusted data.
   - Input sanitization and prompt injection defenses must be active at the orchestration layer.

3. **Zero Leaked Secrets**:
   - Frontend client bundles shall never contain private API keys, database credentials, or secret tokens.
   - Configuration must be strictly driven by environment variables with fallback mock mode when external credentials are absent.

---

### Article IV: Protocol Compliance and Architectural Integrity

1. **Standardized Protocols (A2UI & MCP)**:
   - Dynamic UI elements must strictly adhere to the A2UI declarative specification (surfaces, flat component arrays, data model separation, safe component catalogues).
   - Dynamic interfaces must never execute raw arbitrary JavaScript received from an LLM.
   - Embedded interactive checkout and booking workflows must implement the Model Context Protocol (MCP) Apps specification with sandboxed isolation and standard lifecycle events.

2. **Graceful Degradation (Deterministic Mock Mode)**:
   - If third-party LLM providers (e.g., OpenAI API) or database services (e.g., MongoDB) are unavailable, the application must switch cleanly and deterministically to local fallback modes.
   - The system must explicitly report when deterministic mock mode is active and never deceive users or evaluators by masquerading mock responses as live AI generations.

---

*Adopted for the Amulate Summer Hackathon 2026 by the Autonomous Senior Engineering Agent.*

