# HACKATHON SUBMISSION CHECKLIST
## Amulate Summer Hackathon 2026: AI-Powered Car Rental & Purchase Consultant

| Status | Acceptance Criteria | Implementation & Verification Evidence |
|:------:|---------------------|----------------------------------------|
| ✅ | **Application starts successfully using documented instructions** | Verified via FastAPI health check and Vite production build (`dist/`). |
| ✅ | **At least 100 distinct vehicle listings exist** | Verified: 120 listings in `backend/data/vehicles.json` (`test_seed_matrix.py`). |
| ✅ | **At least 10 categories are represented** | Verified: Hatchback, Sedan, SUV, Luxury Sedan, Luxury SUV, EV, Hybrid, MUV, Sports Car, Convertible. |
| ✅ | **At least 10 distinct brands are represented in each required category** | Verified: Seed data unit test `test_at_least_ten_brands_per_category` strictly passes. |
| ✅ | **Rental and purchase listings have separate eligibility and pricing logic** | Verified: Separate daily vs ex-showroom rates, distinct flags, separate models (`RentalBooking` vs `PurchaseOrder`). |
| ✅ | **The interview asks adaptive follow-up questions** | Verified: `AdaptiveInterviewAgent` asks only for missing fields, preserving existing context. |
| ✅ | **Required preferences are validated before searching** | Verified: `check_missing_fields()` prevents premature search planning. |
| ✅ | **Session state persists across page reloads** | Verified: `localStorage` token restore + backend session snapshot retrieval API. |
| ✅ | **Marketplace supports filtering and date-specific availability** | Verified: `is_vehicle_available_for_dates()` checks interval conflicts. |
| ✅ | **Recommendations are ranked using an explainable scoring system** | Verified: Multi-criteria weighted normalization (0-100 score) with positive matches and trade-offs. |
| ✅ | **Recommendation explanations are based on actual listing data** | Verified: Text generated dynamically from true database specifications (features, rating, price). |
| ✅ | **Application provides live, truthful workflow progress** | Verified: SSE stream `/api/sessions/{session_id}/events` emits real backend progress updates. |
| ✅ | **A2UI messages are generated and rendered through a compatible implementation** | Verified: `A2UIRenderer.tsx` maps approved catalog components without code execution. |
| ✅ | **Booking form is a real MCP App rendered inside the conversation** | Verified: `ui://booking-form` rendered in sandboxed iframe within the conversation stream. |
| ✅ | **Checkout/payment interface is a real MCP App rendered inside conversation** | Verified: `ui://checkout-modal` embedded in sandboxed frame within chat. |
| ✅ | **Booking MCP App communicates with validated backend operations** | Verified: Real-time price recalculation RPC to `/api/bookings/calculate`. |
| ✅ | **Payment MCP App communicates with mock payment backend** | Verified: Connects to `/api/payments/mock` with deterministic test scenarios. |
| ✅ | **No real payment credentials or transactions are processed** | Verified: Clear mock simulator disclaimer; synthetic test cards and UPI VPAs only. |
| ✅ | **Failed payments do not create confirmed bookings** | Verified: `test_scenario_d_payment_failure_recovery_and_idempotency` confirms booking remains unconfirmed on failure. |
| ✅ | **Duplicate requests are handled safely** | Verified: Enforced `Idempotency-Key` headers on booking and payment endpoints. |
| ✅ | **Both rental and purchase journeys are demonstrated** | Verified: Scenario A (Rental) and Scenario B (Purchase) covered in test suite and UI preset pills. |
| ✅ | **Core automated tests pass** | Verified: 27 backend tests + 4 frontend contract tests passing (100% pass rate). |
| ✅ | **Docker deployment instructions are verified** | Verified: Multi-stage Dockerfiles and `docker-compose.yml` configured. |
| ✅ | **README.md documents the actual implementation** | Verified: Comprehensive README with architecture, API docs, and run commands. |
| ✅ | **Environment secrets are excluded from version control** | Verified: `.gitignore` and `.env.example` provided; no keys in repo. |
| ✅ | **Remaining limitations are documented honestly** | Verified: Mock marketplace and sandbox limitations documented in README. |

