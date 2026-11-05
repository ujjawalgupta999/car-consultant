# 3-MINUTE DEMO VIDEO SCRIPT
## Amulate AI: Car Rental & Purchase Consultant

**Target Runtime**: 03:00  
**Audio**: Professional, confident, clear cadence.  
**Visuals**: Screen recording of the live application running in the browser.

---

### [00:00 - 00:30] Introduction & Problem
- **Visual**: Open browser on `http://localhost:5173`. Show the sleek dark automotive UI with live Agent Timeline at the top and greeting message in the chat thread.
- **Narrator**:
  > *"Welcome to Amulate AI, our submission for the Amulate Summer Hackathon 2026. Finding, booking, or buying a car online usually means jumping through dozens of filter pages, fragmented forms, and external checkout redirects. Today, we are demonstrating an end-to-end automotive consultant that lives entirely within a conversational interface, powered by Generative UI (A2UI) and Model Context Protocol (MCP) Apps."*

---

### [00:30 - 01:15] Scenario A: Adaptive Interview & Rental Discovery
- **Visual**: Click the preset pill: *"🚗 Scenario A: Rental (Delhi SUV 5 Days)"*. Hit Send.
- **Visual**: Watch the live progress timeline pulse: `1. Interview` -> `2. Search` -> `3. Ranking` -> `4. Selection`.
- **Visual**: Show the assistant's reply and the rendered A2UI Vehicle Cards with match score badges (94.5% Match), positive matches, trade-offs, and data-driven explanations.
- **Narrator**:
  > *"With a single natural language request, our adaptive interview agent extracts the intent, city, dates, duration, transmission, and budget. It plans the search, filters our verified inventory of 120 listings across 10 categories, and deterministically ranks the best matches with a normalized 0-to-100 score. Notice the A2UI Vehicle Cards: they don't just display specs, they explain why the Hyundai Creta is recommended and highlight real trade-offs."*

---

### [01:15 - 02:00] Embedded MCP Apps: Booking & Mock Checkout
- **Visual**: Click "Select & Book Vehicle" on the Creta.
- **Visual**: The chat container smoothly renders the embedded `ui://booking-form` MCP App inside the chat thread.
- **Visual**: Toggle the "Zero Depreciation Protection" checkbox. Watch the price summary recalculate authoritatively from the backend via postMessage RPC.
- **Visual**: Click "Proceed to Checkout". The booking form transitions to the `ui://checkout-modal` MCP App.
- **Visual**: Highlight the prominent mock disclaimer banner: *"SIMULATED PAYMENT ENVIRONMENT - No real funds transferred"*.
- **Visual**: Select "Instant Success" and click "Pay ₹18,290 (Mock)".
- **Visual**: Confirmed booking voucher card appears in the chat thread with a unique reference number.
- **Narrator**:
  > *"Here is where our architecture shines. Instead of redirecting to an external booking website, the chat embeds an authentic MCP App running in an isolated container. The user selects coverage options, and prices recalculate authoritatively on the backend. Next, the Mock Checkout MCP App renders directly in conversation, simulating a real UPI transaction. Once confirmed, the state machine finalizes the booking and outputs a verified reservation voucher."*

---

### [02:00 - 02:35] Scenario B, C & D: Purchase, Zero-Result & Recovery
- **Visual**: Click "Reset", then click *"⚠️ Scenario C: Zero Match Relaxation"*. Hit Send.
- **Visual**: Show the assistant explaining that a ₹500 budget cannot afford a convertible, displaying binding constraints and suggested adjustments.
- **Visual**: Quick demonstration of Scenario D: select "Simulated Decline", show that the booking remains unconfirmed with an error message, then retry with "Instant Success" to confirm idempotently.
- **Narrator**:
  > *"Amulate AI handles edge cases with zero hallucination. When a user requests a convertible for ₹500 a day, the engine honestly diagnoses the constraint conflict and suggests realistic alternatives rather than inventing fake rates. If a payment declines, the state machine safely preserves the unconfirmed reservation and allows retry without creating duplicate transactions."*

---

### [02:35 - 03:00] Architecture, Testing & Conclusion
- **Visual**: Switch to terminal showing `pytest backend/tests -v`: 27 passing tests in 0.9s. Show the seed matrix test validating at least 10 brands in all 10 categories.
- **Narrator**:
  > *"Under the hood, Amulate AI is backed by FastAPI, Pydantic, full Docker Compose deployment, and 27 automated tests verifying our ranking engine, state machine, and category-brand seed matrix. It runs 100% offline in deterministic mock mode. Thank you for exploring Amulate AI!"*

