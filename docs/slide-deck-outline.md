# AMULATE SUMMER HACKATHON 2026: SLIDE DECK OUTLINE
## AI-Powered Car Rental & Purchase Consultant

---

### Slide 1: Title & Vision
- **Header**: Amulate AI — The Conversational Automotive Consultant
- **Subtitle**: Reimagining Car Rental and Purchase with Generative UI (A2UI) & Model Context Protocol (MCP) Apps
- **Presenter**: Senior Autonomous Engineering Agent
- **Theme**: Premium Automotive Dark Theme (Onyx & Cyber Cyan)

### Slide 2: The Problem Space
- **Fragmented User Journeys**: Traditional car rental and purchasing sites force users through dozens of dropdowns, filters, and external checkout pages.
- **Generic Chatbots Fall Short**: Text-only LLM chat cannot securely collect driver licenses, recalculate insurance add-ons, or authenticate transactions without redirecting away.
- **The Code-Injection Risk**: Emitting raw HTML/JS from agents exposes users to XSS and hallucinations.

### Slide 3: Our Solution
- **Adaptive Conversational Interview**: Natural language understanding that extracts location, dates, category, and budgets without repetitive questions.
- **Zero-Hallucination Inventory**: Strict hard-bound filtering and explainable 0-100 match scoring based on actual vehicle specs.
- **In-Chat Interactive MCP Apps**: Embedded, sandboxed Booking Form and Mock Checkout rendering seamlessly within the conversation.
- **Declarative Generative UI (A2UI)**: Safe, platform-agnostic UI streaming over Server-Sent Events.

### Slide 4: System Architecture
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, A2UI Component Renderer, Sandboxed MCP App Host.
- **Backend**: Python 3.11, FastAPI, Pydantic v2, SSE Event Streamer.
- **Orchestration**: 13-stage validated Finite State Machine + Adaptive Interview Agent.
- **Protocols**: Model Context Protocol (10 tools) + A2UI Generative Protocol.
- **Storage**: Seeded marketplace (120 listings, 10 categories, >=10 brands each) with MongoDB / JSON repository.

### Slide 5: Core Innovations
1. **MCP Apps Integration**:
   - `ui://booking-form`: Interactive add-on selection, driver verification, dynamic backend price recalculation.
   - `ui://checkout-modal`: Multi-rail simulation (UPI & Card) with deterministic scenarios (Instant Success, Decline, Timeout).
2. **Explainable AI Ranking**:
   - Transparent scoring breakdown (Budget 30%, Category 25%, Preferences 20%, Rating 15%, Brand 10%).
   - Diagnostic relaxation recommendations when zero inventory matches strict filters.

### Slide 6: Demonstration Journeys
- **Scenario A (Rental)**: 5-Day SUV in Delhi under ₹3,000/day -> Booking MCP App -> Mock UPI Payment -> Confirmed Voucher.
- **Scenario B (Purchase)**: Used SUV in Delhi under ₹15 Lakhs -> Purchase Reservation MCP App -> Token Deposit -> Order Confirmed.
- **Scenario C (Relaxation)**: Convertible under ₹500/day -> Clear explanation of binding constraints with suggested adjustments.
- **Scenario D (Safe Recovery)**: Simulated card decline -> safe retry without duplicate charge -> confirmed booking.

### Slide 7: Quality, Reliability & Testing
- **100% Automated Test Coverage**: 27 pytest backend tests + 4 frontend contract tests passing in < 2 seconds.
- **Category-Brand Matrix Guaranteed**: Seed matrix unit test verifies >=10 distinct brands in every single category.
- **Deterministic Mock Mode**: Operates 100% offline without requiring paid API tokens.
- **Idempotency & Security**: Full replay protection and strict mock payment sandboxing.

### Slide 8: Future Roadmap & Conclusion
- **Real-time Marketplace Telematics**: Fleet tracking and smart contract deposit escrow.
- **Multi-modal Agent Inspection**: Vision analysis of exterior paint and wear for used car buying.
- **Antigravity 2.0 Deployment**: Ready for containerized cloud deployment on Google Cloud Run and Kubernetes.

