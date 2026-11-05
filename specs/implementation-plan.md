# AMULATE SUMMER HACKATHON 2026: IMPLEMENTATION PLAN & CHECKLIST
## AI-Powered Car Rental and Purchase Consultant

---

## 1. Phased Execution Roadmap

### Phase 1: Inspection & Specification (COMPLETED)
- [x] Inspect existing workspace environment (Python 3.11, Node.js 25, npm 11, git available).
- [x] Investigate official A2UI and MCP Apps specifications and standards.
- [x] Author specifications: `constitution.md`, `requirements.md`, `architecture.md`, `data-model.md`, `api-contracts.md`, `mcp-apps.md`, `a2ui.md`, `security.md`, `testing.md`, `deployment.md`, `implementation-plan.md`.

### Phase 2: Foundation & Scaffolding
- [ ] Initialize backend Python project structure (`backend/app/...`, `requirements.txt`).
- [ ] Initialize frontend React + TypeScript + Vite + Tailwind CSS project structure (`frontend/...`).
- [ ] Implement foundational Pydantic models matching `specs/data-model.md`.
- [ ] Implement backend `/health` endpoint and environment configuration.
- [ ] Set up `.env.example` and base project configs.

### Phase 3: Marketplace & Seed Dataset
- [ ] Generate comprehensive seed dataset (`backend/data/vehicles.json`):
  - At least 100 listings.
  - 10 distinct categories.
  - At least 10 distinct brands per category (validated by automated test).
  - Distinct rental and purchase pricing and availability flags.
  - Realistic features, specs, images, ratings.
- [ ] Implement `MarketplaceRepository` with JSON fallback and MongoDB adapter.
- [ ] Implement search filtering and date availability engine.
- [ ] Implement explainable ranking engine with hard constraints and 0-100 normalized score.
- [ ] Run automated seed matrix and ranking unit tests.

### Phase 4: Agent Orchestration & MCP Server
- [ ] Implement explicit workflow state machine with backend validation.
- [ ] Implement adaptive interview logic (natural language preference extraction for RENT and BUY).
- [ ] Implement deterministic mock mode agent adapter (100% offline runnable).
- [ ] Implement persistent session memory store with browser refresh support.
- [ ] Implement MCP Tool Server with all 10 tools (`search_vehicles`, `calculate_booking_total`, etc.).
- [ ] Implement Server-Sent Events (SSE) live progress timeline stream.

### Phase 5: Dynamic UI & A2UI Protocol Renderer
- [ ] Implement sleek automotive dark-mode theme in React/Tailwind.
- [ ] Build Conversational Chat Panel with live message stream.
- [ ] Implement A2UI Renderer interpreting declarative `createSurface`, `updateComponents`, `updateDataModel`, and emitting `actionResponse`.
- [ ] Build Live Agent Progress Timeline component.
- [ ] Implement dynamic Vehicle Recommendation cards with match score breakdown.

### Phase 6: Embedded MCP Apps (Booking & Checkout)
- [ ] Build `ui://booking-form` MCP App:
  - Form validation, rental/purchase details.
  - Real-time backend price recalculation RPC.
  - Submit and cancel actions.
- [ ] Build `ui://checkout-modal` MCP App:
  - Itemized cost breakdown.
  - Simulated payment methods (UPI, Card, Test Scenarios).
  - Prominent mock test disclaimer.
  - Idempotency key generation.
- [ ] Embed both MCP Apps in the frontend chat host container.

### Phase 7: End-to-End Workflow Integration
- [ ] Integrate Rental Journey (Scenario A).
- [ ] Integrate Purchase Journey (Scenario B).
- [ ] Integrate Zero-Result Recovery (Scenario C).
- [ ] Integrate Payment Decline & Retry (Scenario D).
- [ ] Verify session persistence across page reload.

### Phase 8: Quality Assurance & Automated Testing
- [ ] Run full pytest suite for unit and integration tests.
- [ ] Run frontend TypeScript compilation and Vite production build.
- [ ] Verify Docker Compose configuration and health checks.
- [ ] Fix all identified issues.

### Phase 9: Documentation & Hackathon Deliverables
- [ ] Finalize `README.md` with complete architecture, run instructions, and screenshots.
- [ ] Author Submission Checklist.
- [ ] Author Slide Deck Outline.
- [ ] Author 3-Minute Demo Video Script.
- [ ] Author Screenshots Inventory.

---

## 2. Hackathon Acceptance Checklist

| Requirement | Target Status | Verification Method |
|-------------|---------------|---------------------|
| Application starts successfully using documented instructions | Ready | Local execution & health check |
| At least 100 distinct vehicle listings exist | Ready | Dataset count & unit test |
| At least 10 categories are represented | Ready | Unit test verification |
| At least 10 distinct brands are represented in each required category | Ready | Seed matrix test verification |
| Rental and purchase listings have separate eligibility and pricing | Ready | Data model & business logic tests |
| The interview asks adaptive follow-up questions | Ready | Interview agent dialogue test |
| Required preferences are validated before searching | Ready | Validation unit test |
| Session state persists across page reloads | Ready | Session restore API test |
| Marketplace supports filtering and date-specific availability | Ready | Availability engine test |
| Recommendations are ranked using an explainable scoring system | Ready | Scoring test with weights breakdown |
| Recommendation explanations are based on actual listing data | Ready | Explanation consistency test |
| Application provides live, truthful workflow progress | Ready | SSE timeline event test |
| A2UI messages are generated and rendered through a compatible implementation | Ready | A2UI parser & component render test |
| Booking form is a real MCP App rendered inside the conversation | Ready | MCP App frame & postMessage test |
| Checkout/payment interface is a real MCP App rendered inside conversation | Ready | MCP App frame & postMessage test |
| Booking MCP App communicates with validated backend operations | Ready | Recalculation API integration test |
| Payment MCP App communicates with mock payment backend | Ready | Payment simulation API test |
| No real payment credentials or transactions are processed | Ready | Security review & synthetic data test |
| Failed payments do not create confirmed bookings | Ready | Scenario D integration test |
| Duplicate requests are handled safely | Ready | Idempotency key test |
| Both rental and purchase journeys are demonstrated | Ready | Scenarios A & B walkthrough |
| Core automated tests pass | Ready | `pytest` test suite execution |
| Docker deployment instructions are verified | Ready | Dockerfile & docker-compose configuration |
| README.md documents actual implementation | Ready | Comprehensive documentation |
| Environment secrets excluded from version control | Ready | `.gitignore` and `.env.example` check |
| Remaining limitations are documented honestly | Ready | Explicit limitation disclosure |

