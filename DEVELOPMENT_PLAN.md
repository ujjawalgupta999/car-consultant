# AURA MOTORS: DEVELOPMENT & EXECUTION PLAN
## AI-Powered Automotive Marketplace + Full-Stack Dynamic AI Consultant

---

## Milestone 1: Planning & Specifications (COMPLETED)
- [x] Define multi-page automotive website architecture inspired by BMW aesthetic.
- [x] Design the Website Controller protocol (`NAVIGATE_TO_PAGE`, `APPLY_FILTERS`, `OPEN_VEHICLE_DETAILS`, `ADD_TO_COMPARISON`, etc.).
- [x] Author `ARCHITECTURE.md`, `API_SPECIFICATION.md`, and `DEVELOPMENT_PLAN.md`.

---

## Milestone 2: Backend Authentication & Controller Endpoints
- [ ] Implement JWT Authentication endpoints (`/api/auth/signup`, `/api/auth/login`, `/api/auth/me`).
- [ ] Enhance agent orchestrator in `backend/app/orchestration/orchestrator.py` to generate structured `website_actions` based on user intent.
- [ ] Add comparison and user favorites endpoints.
- [ ] Verify backend tests pass.

---

## Milestone 3: Centralized Frontend State (Zustand)
- [ ] Create `frontend/src/store/vehicleStore.ts` (vehicle catalog, active filters, sorting, computed search).
- [ ] Create `frontend/src/store/consultantStore.ts` (chat messages, drawer open/close, active website context, current MCP app).
- [ ] Create `frontend/src/store/comparisonStore.ts` (2 to 4 compared cars, difference highlights).
- [ ] Create `frontend/src/store/authStore.ts` (user session, token, saved cars, active bookings).

---

## Milestone 4: Premium Automotive Website Pages & Navigation
- [ ] Global Navigation Bar (`Navbar.tsx`): Brand logo ("AURA MOTORS"), Links (Explore, Rent, Buy, Compare, Offers, About, Contact), Compare Badge, Login/Profile, and persistent "AI Consultant" button.
- [ ] Homepage (`pages/Home.tsx`):
  - Cinematic hero backdrop with headline "The Future of Driving, Found by Intelligence".
  - Tabbed search widget (Rent & Buy modes, city, dates, category).
  - Featured vehicles grid with quick specs.
  - Explore by 10 Categories.
  - Brand prestige showcase.
  - Special Rental & Purchase offers.
  - AI Consultant interactive spotlight banner.
  - Testimonials & Luxury Footer.
- [ ] Explore Cars Page (`pages/ExploreCars.tsx`):
  - 120-vehicle catalogue.
  - Sidebar filters (Category, Brand, Budget Slider, Transmission, Fuel, Seats).
  - Sorting and Rent/Buy mode toggles.
- [ ] Rent a Car Page (`pages/RentCars.tsx`):
  - Rental booking filters (Location, Pickup/Return dates, daily budget).
  - Rental rate calculations and terms.
- [ ] Buy a Car Page (`pages/BuyCars.tsx`):
  - Purchase filters (New / Used, Price ceiling, EMI estimates, warranty).
- [ ] Vehicle Details Page (`pages/VehicleDetails.tsx`):
  - Large image gallery, technical specs, interactive EMI calculator, "Rent This Car", "Buy This Car", "Add to Compare", and "Ask AI About This Car".
- [ ] Compare Cars Page (`pages/CompareCars.tsx`):
  - Side-by-side comparison table (2 to 4 cars) with specs diffs and AI recommendation.
- [ ] Dedicated Booking Page (`pages/Booking.tsx`) & Checkout Page (`pages/Checkout.tsx`).
- [ ] Authentication Pages (`pages/Login.tsx`, `pages/Signup.tsx`).
- [ ] User Dashboard (`pages/Dashboard.tsx`).
- [ ] About Page (`pages/About.tsx`) & Contact Page (`pages/Contact.tsx`).

---

## Milestone 5: Deep AI Consultant Website Controller Integration
- [ ] Build Floating AI Consultant Drawer (`components/consultant/FloatingConsultantDrawer.tsx`):
  - Available across every single page via persistent FAB or navbar click.
  - Does not destroy page context.
  - Executes `website_actions` to navigate routes, apply filters, and populate comparison tables live!
- [ ] Dedicated Consultant Route (`pages/ConsultantPage.tsx`).
- [ ] Synchronize route context into AI consultant (e.g. current page, selected car).
- [ ] Embed Booking MCP App (`ui://booking-form`) and Mock Payment MCP App (`ui://checkout-modal`) within the conversational stream.
- [ ] Render A2UI dynamic surfaces natively.

---

## Milestone 6: End-to-End Verification of Demo Scenarios
- [ ] Scenario 1: Rental in Delhi via AI (navigates to `/rent`, filters SUVs, opens booking MCP App, simulates checkout).
- [ ] Scenario 2: Purchase under ₹20 Lakh (navigates to `/buy`, filters automatic SUVs, opens details, calculates EMI).
- [ ] Scenario 3: Comparison (AI adds top 2 cars to comparison, opens `/compare`, displays table).
- [ ] Scenario 4: Changing requirements (updates budget to ₹25L and fuel to EV, refreshes catalogue).
- [ ] Scenario 5: Website and conversation synchronization (visiting car detail page informs the AI).

---

## Milestone 7: Testing, Docker & Final Documentation
- [ ] Run backend pytest suite.
- [ ] Run frontend TypeScript compilation & build (`npm run build`).
- [ ] Update `README.md` with complete architecture, commands, and screenshots.
