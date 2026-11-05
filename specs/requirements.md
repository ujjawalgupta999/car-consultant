# AMULATE SUMMER HACKATHON 2026: REQUIREMENTS SPECIFICATION
## AI-Powered Car Rental and Purchase Consultant

---

## 1. Overview and Scope

The system is a full-stack, AI-powered automotive consultant supporting two distinct user journeys:
1. **Vehicle Rental**: Daily rental discovery, date and duration availability checks, dynamic booking, and simulated checkout.
2. **Vehicle Purchase**: New and used vehicle purchase discovery, budget constraint matching, purchase order reservation, and simulated deposit/full checkout.

All interactions occur in an embedded conversational interface utilizing:
- **A2UI**: Declarative, streaming, dynamic agent-driven user interfaces.
- **MCP Apps**: Sandboxed, protocol-compliant embedded interactive applications for booking and checkout.

---

## 2. Functional Requirements (FR)

### FR-1: Intent and Category Support
- **FR-1.1**: Support two core intents: `RENT` and `BUY`.
- **FR-1.2**: Support 10 distinct vehicle categories:
  1. Hatchback
  2. Sedan
  3. SUV
  4. Luxury Sedan
  5. Luxury SUV
  6. Electric Vehicle (EV)
  7. Hybrid
  8. MUV (Multi-Utility Vehicle)
  9. Sports Car
  10. Convertible
- **FR-1.3**: The mock marketplace dataset must contain at least 100 listings, with at least 10 distinct brands represented in each of the 10 categories (validated by seed data tests).

### FR-2: Adaptive Interview Agent
- **FR-2.1**: Dynamically extract user preferences from natural language.
- **FR-2.2**: Collect common attributes: Intent, Location, Category, Budget, Fuel Type, Transmission, Seating Capacity, Preferred Brands, Additional Preferences.
- **FR-2.3**: Collect rental-specific attributes: Pickup Date, Return Date, Rental Duration (days), Daily/Total Budget, Pickup/Return Locations.
- **FR-2.4**: Collect purchase-specific attributes: Purchase Budget, Target Purchase Date, Condition (New/Used), Financing Preference, Ownership Use.
- **FR-2.5**: Do not ask for attributes already provided.
- **FR-2.6**: Allow user to update or correct preferences at any point, invalidating stale search results.
- **FR-2.7**: Enforce required fields before initiating search planning.

### FR-3: Multistep Agent Orchestration & State Machine
- **FR-3.1**: Explicit state machine managing:
  `NEW` -> `INTERVIEWING` -> `READY_TO_SEARCH` -> `SEARCHING` -> `RANKING` -> `RECOMMENDATIONS_READY` -> `VEHICLE_SELECTED` -> `BOOKING_IN_PROGRESS` -> `CHECKOUT_READY` -> `PAYMENT_PROCESSING` -> `CONFIRMED` (or `PAYMENT_FAILED` / `CANCELLED`).
- **FR-3.2**: Backend validates all state transitions. Disallow unauthorized client state overrides.
- **FR-3.3**: Emit live agent progress events (via SSE) corresponding to actual backend execution stages.

### FR-4: Marketplace & Availability Engine
- **FR-4.1**: Filter listings by Intent (`available_for_rent` vs `available_for_purchase`), Location, Category, Budget, Fuel, Transmission, Seats.
- **FR-4.2**: Validate date-specific rental availability against blocked rental date intervals.
- **FR-4.3**: Provide repository abstraction enabling easy migration between local JSON and MongoDB.

### FR-5: Explainable Recommendation Engine
- **FR-5.1**: Apply hard constraints first (Intent, Location, Price ceiling, Date availability, Mandatory seats).
- **FR-5.2**: Rank eligible vehicles with normalized scoring (0–100):
  - Budget compatibility: 30%
  - Category match: 25%
  - Preference compatibility (fuel/transmission/features): 20%
  - Vehicle rating: 15%
  - Brand preference: 10% (normalized when no brand preference is specified).
- **FR-5.3**: Present up to 5 recommendations with detailed trade-offs, pros, cons, and deterministic calculation breakdowns.
- **FR-5.4**: When zero matches exist, identify the exact binding constraints and suggest controlled relaxations.

### FR-6: A2UI Dynamic Interface Generation
- **FR-6.1**: Backend streams declarative A2UI messages (`createSurface`, `updateComponents`, `updateDataModel`, `deleteSurface`).
- **FR-6.2**: Frontend renderer maps approved components (`Card`, `Button`, `FormField`, `RadioGroup`, `Badge`, `ProgressTimeline`, `VehicleCard`) without executing arbitrary script code.
- **FR-6.3**: Dispatch client-to-agent `actionResponse` payloads upon user interaction.

### FR-7: MCP Apps Integration (Booking and Checkout)
- **FR-7.1**: **Booking MCP App** (`ui://booking-form`):
  - Renders inside chat thread.
  - Receives selected vehicle context.
  - Validates dates, driver details, options.
  - Recalculates total cost via backend API.
  - Returns structured booking payload or cancellation.
- **FR-7.2**: **Mock Checkout MCP App** (`ui://checkout-modal`):
  - Renders inside chat thread.
  - Shows complete itemized cost breakdown.
  - Simulates UPI, Card, and Test Scenarios (Instant Success, Simulated Decline, Timeout).
  - Enforces idempotency keys on payment submission.
  - Displays prominent mock disclaimer.

### FR-8: Multistep Persistence & Session Memory
- **FR-8.1**: Persist sessions, messages, preferences, search history, bookings, and payments in MongoDB or local JSON storage.
- **FR-8.2**: Support browser refresh and session resumption.
- **FR-8.3**: Enforce session ownership via cryptographic session tokens.

---

## 3. Nonfunctional Requirements (NFR)

- **NFR-1: Performance**: Initial page load < 1.5s; SSE progress events rendered < 100ms from emission; local search & ranking queries < 50ms.
- **NFR-2: Reliability**: 100% deterministic operation in Mock Mode when OpenAI API keys or MongoDB are absent.
- **NFR-3: Security**: Zero credentials in frontend code; CSP applied to MCP App frames; no real financial data allowed; idempotency on all POST write actions.
- **NFR-4: Accessibility & Design**: Premium dark automotive aesthetic (`#0A0A0C` to `#18181B`); WCAG AA contrast; responsive layout down to mobile viewports.
- **NFR-5: Testability**: Automated unit, integration, and scenario tests runnable via standard CLI commands without network dependency.

---

## 4. User Stories & Acceptance Criteria

### Story 1: Rental Journey (Scenario A)
*As a customer traveling to Delhi,*
*I want to find and rent an automatic SUV for 5 days starting Dec 15, 2026 within ₹3,000/day,*
*So that I have verified transportation ready upon arrival.*
- **Criteria**:
  1. Agent gathers date, location, category, budget.
  2. Filter returns eligible SUVs available for requested dates.
  3. Ranked options display daily and total cost (₹3,000 * 5 = ₹15,000 + taxes/fees).
  4. User clicks "Select" on a car -> Booking MCP App opens inside chat.
  5. User submits booking details -> Total recalculated by backend.
  6. Payment MCP App opens inside chat -> User selects mock payment method -> Success -> Confirmed reference generated.

### Story 2: Purchase Journey (Scenario B)
*As an urban car buyer,*
*I want to explore used automatic SUVs in Delhi under ₹15,00,000,*
*So that I can compare suitable options and reserve one with a refundable token.*
- **Criteria**:
  1. Agent gathers purchase intent, used condition, budget limit.
  2. Filter selects purchase-eligible vehicles ≤ ₹15,00,000.
  3. Recommendations detail odometer/year, condition, and purchase score.
  4. Selection triggers purchase reservation MCP App.
  5. Mock checkout calculates refundable booking deposit (e.g. ₹25,000) or full price.
  6. Mock payment confirms order and outputs reference number.

### Story 3: Zero Matching Filter Recovery (Scenario C)
*As an unconventional user with strict contradictory criteria (e.g., Convertible under ₹500/day),*
*I want the agent to explain why no cars match and recommend realistic alternatives,*
*So that I can adjust my expectations without being deceived.*
- **Criteria**:
  1. System detects 0 results.
  2. Explains that daily budget ₹500 is below the minimum Convertible rate (e.g., ₹8,000/day).
  3. Suggests relaxing category or increasing budget.
  4. Requires user confirmation before applying relaxation.

### Story 4: Payment Failure & Safe Recovery (Scenario D)
*As a customer whose card simulation fails,*
*I want to be notified of the failure and given an option to retry without duplicating the order,*
*So that I can successfully complete the booking with another payment method.*
- **Criteria**:
  1. Test failure simulation triggers `PAYMENT_FAILED` state.
  2. Booking status remains `UNCONFIRMED`.
  3. MCP App shows retry prompt.
  4. User retries with successful simulation -> status updates to `CONFIRMED`.
  5. Database records exactly one confirmed booking.

