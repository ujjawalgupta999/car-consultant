# ARCHITECTURE OVERVIEW
## Amulate AI: Car Rental & Purchase Consultant

### 1. Executive Summary
Amulate AI is a production-grade, spec-driven automotive conversational consultant. It merges:
- **Agentic Orchestration**: Explicit 13-stage finite state machine driving an adaptive interview agent.
- **Generative UI (A2UI)**: Declarative, streaming Agent-to-User Interface protocol eliminating code injection vulnerabilities.
- **Model Context Protocol (MCP) & MCP Apps**: Standardized tool interface with embedded, sandboxed micro-apps for vehicle booking (`ui://booking-form`) and mock payment checkout (`ui://checkout-modal`).
- **Deterministic Reliability**: Zero-cost, 100% offline-capable mock mode guaranteeing truthful inventory discovery and repeatable testing.

---

### 2. High-Level Architecture Diagram
```
+--------------------------------------------------------------------------------------+
|                                   REACT CLIENT                                       |
|  +---------------------+  +-----------------------+  +----------------------------+  |
|  |  Chat Container     |  |   A2UI Renderer       |  |  MCP Apps Host Container   |  |
|  |  - Message Stream   |  |   - Declarative Blue- |  |  - ui://booking-form       |  |
|  |  - Timeline Ticker  |  |     prints (JSON)     |  |  - ui://checkout-modal     |  |
|  |  - Quick Scenarios  |  |   - Safe Component Map|  |  - postMessage JSON-RPC    |  |
|  +----------+----------+  +-----------+-----------+  +-------------+--------------+  |
+-------------|-------------------------|----------------------------|-----------------+
              |                         |                            |
         HTTP / REST              A2UI Actions                Recalculation RPC
              |                         |                            |
+-------------v-------------------------v----------------------------v-----------------+
|                                 FASTAPI BACKEND                                      |
|  +--------------------------------------------------------------------------------+  |
|  |                                  API GATEWAY                                   |  |
|  |  /health | /api/sessions | /api/vehicles | /api/bookings | /api/payments       |  |
|  +---------------------------------------+----------------------------------------+  |
|                                          |                                           |
|  +---------------------------------------v----------------------------------------+  |
|  |                             AGENT ORCHESTRATION                                |  |
|  |  - State Machine (NEW -> INTERVIEWING -> SEARCHING -> RANKING -> CONFIRMED)   |  |
|  |  - Adaptive Interview Agent (RENT & BUY natural language extraction)          |  |
|  |  - SSE Event Streamer (Live progress timeline & A2UI surface dispatcher)       |  |
|  +---------------------------------------+----------------------------------------+  |
|                                          |                                           |
|  +-------------------+  +----------------v-------------------+  +-----------------+  |
|  | Ranking Engine    |  |       MCP Server (10 Tools)        |  | Payment Sim     |  |
|  | - Hard Bounds     |  | - search_vehicles                  |  | - Idempotency   |  |
|  | - 0-100 Scoring   |  | - calculate_booking_total          |  | - UPI / Card    |  |
|  | - Explainability  |  | - create_booking / order           |  | - Predefined Scen| |
|  +---------+---------+  +----------------+-------------------+  +--------+--------+  |
+------------|-----------------------------|-------------------------------|-----------+
             |                             |                               |
+------------v-----------------------------v-------------------------------v-----------+
|                           PERSISTENCE & REPOSITORY LAYER                             |
|  - JsonMarketplaceRepository: 120 seeded listings across 10 categories, >=10 brands  |
|  - SessionRepository: In-memory & file-backed state & idempotency tracker            |
|  - MongoMarketplaceRepository: Production containerized MongoDB adapter              |
+--------------------------------------------------------------------------------------+
```

---

### 3. Key Design Decisions

1. **Protocol-Compliant Embedded MCP Apps**:
   Rather than standard external redirect pages, the Booking Form and Mock Checkout are packaged as sandboxed micro-apps conforming to `modelcontextprotocol/ext-apps`. They render within the chat stream, communicate bidirectionally with the host via postMessage, and execute real-time backend pricing recalculations.

2. **A2UI Declarative Interface**:
   The agent streams flat component graphs rather than raw HTML or executable code. The React client maps component IDs (`Card`, `VehicleCard`, `RadioGroup`) to trusted native widgets, preventing XSS and ensuring design cohesion.

3. **Backend-Authoritative Pricing & Zero Hallucination**:
   The LLM cannot invent discounts or rates. Every price line item is verified on the server. If zero vehicles match user criteria, the engine diagnostically identifies the exact binding constraints and suggests controlled relaxations.

4. **Deterministic Mock Mode**:
   Provides 100% test reproducibility and complete offline functionality without paid OpenAI or third-party API dependencies.

