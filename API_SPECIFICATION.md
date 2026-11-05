# AURA MOTORS: API SPECIFICATION
## AI-Powered Automotive Marketplace + Full-Stack Dynamic AI Consultant

---

## 1. Authentication & User APIs

### `POST /api/auth/signup`
Creates a new customer account.
- **Request**:
  ```json
  {
    "name": "Rohan Sharma",
    "email": "rohan.sharma@example.com",
    "password": "Password123!",
    "phone": "+91 98765 43210"
  }
  ```
- **Response `201 Created`**:
  ```json
  {
    "user": { "id": "usr_9912", "name": "Rohan Sharma", "email": "rohan.sharma@example.com" },
    "token": "jwt_token_sample"
  }
  ```

### `POST /api/auth/login`
Authenticates an existing customer.
- **Request**: `{ "email": "rohan.sharma@example.com", "password": "Password123!" }`
- **Response `200 OK`**: `{ "user": { ... }, "token": "jwt_token_sample" }`

### `GET /api/auth/me`
Retrieves currently logged-in user profile with saved cars, active rentals, and purchase enquiries.

---

## 2. Vehicles & Marketplace APIs

### `GET /api/vehicles`
Retrieves all 120 vehicle listings with optional query params (`category`, `intent`, `location`, `limit`, `sort`).

### `GET /api/vehicles/{id}`
Returns complete specifications, image galleries, features, rental rates, and purchase price.

### `POST /api/vehicles/compare`
Accepts `{ "vehicle_ids": ["CAR-001", "CAR-002", "CAR-003"] }` and returns side-by-side spec comparison matrix.

### `POST /api/search`
Searches vehicles with budget, transmission, fuel, dates, and intent filtering.

---

## 3. AI Consultant & Website Controller APIs

### `POST /api/sessions/{session_id}/messages`
Processes user conversational turns and returns:
- Assistant message content.
- Updated `workflow_state`.
- Declarative `a2ui_surfaces`.
- Ranked `recommendations`.
- Structured `website_actions` (directives to control the frontend interface).

**Response Example with Website Actions**:
```json
{
  "message_id": "msg_001",
  "role": "assistant",
  "content": "I've navigated you to our rental catalogue and applied filters for automatic SUVs under ₹3,000/day in Delhi.",
  "workflow_state": "RECOMMENDATIONS_READY",
  "a2ui_surfaces": ["surf_rec_123"],
  "recommendations": [ ... ],
  "website_actions": [
    {
      "type": "NAVIGATE_TO_PAGE",
      "payload": { "path": "/rent" }
    },
    {
      "type": "APPLY_FILTERS",
      "payload": {
        "category": "SUV",
        "transmission": "automatic",
        "location": "Delhi",
        "maxPrice": 3000,
        "intent": "rent"
      }
    }
  ]
}
```

### `GET /api/sessions/{session_id}/events`
Server-Sent Events (SSE) stream emitting:
1. `event: progress`: `{ "stage": "SEARCHING", "step": 3, "message": "..." }`
2. `event: a2ui`: `{ "type": "createSurface", "surfaceId": "...", "components": [...] }`
3. `event: website_action`: Directives streamed to frontend controller.

---

## 4. Bookings & Mock Checkout APIs

### `POST /api/bookings/calculate`
Authoritative backend price calculation.
- **Request**: `{ "vehicle_id": "CAR-001", "duration_days": 5, "addon_ids": ["addon_insurance_zero_dep"] }`
- **Response `200 OK`**: `{ "subtotal": 14000, "addons_total": 1500, "taxes": 2790, "total_amount": 18290 }`

### `POST /api/bookings`
Creates rental booking with enforced idempotency key header (`Idempotency-Key`).

### `POST /api/orders`
Creates purchase order reservation with token deposit (`Idempotency-Key`).

### `POST /api/payments/mock`
Executes simulated payment via UPI or Card simulator.
- **Scenarios**: `success`, `failure`, `timeout`.
- **Response**: Updates booking status to `CONFIRMED` upon success.

