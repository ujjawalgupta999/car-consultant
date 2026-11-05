# SCREENSHOTS INVENTORY & CAPTURE GUIDE
## Amulate AI: Car Rental & Purchase Consultant

This document specifies the exact screenshots representing the critical user journeys and technical implementations for submission review.

---

### Screenshot 1: Application Shell & Live Agent Timeline
- **File Name**: `screenshot-01-app-shell.png`
- **Location**: Top of page (`Header` + `AgentTimeline` + `ChatContainer`)
- **Key Elements**:
  - Dark automotive styling (`#090A0F` background, onyx card surfaces).
  - "Hackathon 2026" and "Mock Engine Active" status pills.
  - Live 6-stage agent timeline with active step indicator.
  - Welcoming consultant greeting in the chat stream.

### Screenshot 2: A2UI Dynamic Recommendations & Explainable Match Cards
- **File Name**: `screenshot-02-a2ui-recommendations.png`
- **Location**: Mid-chat after Scenario A query
- **Key Elements**:
  - Natural language message: *"I need an automatic SUV in Delhi for five days..."*
  - Rendered A2UI `VehicleCard` components for Hyundai Creta, Kia Seltos, Tata Harrier.
  - Match Score badge (e.g. `94.5% Match`).
  - Positive matches with green checkmarks.
  - Trade-offs with amber caution badges.
  - Transparent calculation explanation paragraph.

### Screenshot 3: Embedded Booking MCP App (`ui://booking-form`)
- **File Name**: `screenshot-03-mcp-app-booking.png`
- **Location**: Rendered inside chat thread
- **Key Elements**:
  - Sandboxed host frame with URI tag `ui://booking-form`.
  - Vehicle summary strip with thumbnail and daily rate.
  - Interactive inputs: driver details, date range, pickup location.
  - Interactive add-ons checkboxes (Zero-Depreciation, Roadside Assistance).
  - Dynamic backend price recalculation summary table.

### Screenshot 4: Embedded Mock Checkout MCP App (`ui://checkout-modal`)
- **File Name**: `screenshot-04-mcp-app-checkout.png`
- **Location**: Rendered inside chat thread
- **Key Elements**:
  - Sandboxed host frame with URI tag `ui://checkout-modal`.
  - Prominent amber banner: *"MOCK PAYMENT SIMULATOR: No real funds transferred"*.
  - Payment method tabs (UPI Simulation / Test Card Simulator).
  - Test scenario selector (🟢 Instant Success, 🔴 Simulated Decline, 🟡 Timeout).
  - "Pay ₹18,290 (Mock)" primary action button.

### Screenshot 5: Confirmed Booking Voucher & Reference
- **File Name**: `screenshot-05-confirmed-voucher.png`
- **Location**: Bottom of chat thread
- **Key Elements**:
  - Assistant celebration message.
  - Green-bordered booking voucher with booking reference `BK-2026-XXXX`.
  - Authorized mock transaction receipt `TXN-MOCK-XXXX`.
  - Itemized total paid and vehicle model.

### Screenshot 6: Zero-Result Constraint Diagnosis & Relaxation (Scenario C)
- **File Name**: `screenshot-06-zero-result-relaxation.png`
- **Location**: Chat thread upon submitting impossible criteria
- **Key Elements**:
  - Input: *"I need a convertible in Delhi for 5 days with a daily budget of ₹500"*.
  - Truthful diagnosis: explains ₹500 budget is below entry rate for Convertibles (₹5,800/day).
  - Controlled relaxation suggestions offered without hallucinating inventory.

### Screenshot 7: Full Automated Test Suite Execution
- **File Name**: `screenshot-07-test-suite-success.png`
- **Location**: Terminal output
- **Key Elements**:
  - `pytest backend/tests -v` showing 27/27 tests passing.
  - `node frontend/tests/frontend_contracts.test.mjs` showing 4/4 passing tests.
  - Seed matrix test ensuring >= 10 brands in all 10 categories.

