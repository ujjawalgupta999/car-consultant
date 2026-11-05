# AMULATE SUMMER HACKATHON 2026: API CONTRACTS SPECIFICATION
## AI-Powered Car Rental and Purchase Consultant

---

## 1. Global Standards & Status Codes

- **Base URL**: `/api`
- **Content-Type**: `application/json` (except SSE endpoints which use `text/event-stream`)
- **Error Format**:
  ```json
  {
    "error": {
      "code": "INVALID_STATE_TRANSITION",
      "message": "Cannot initiate checkout when state is INTERVIEWING.",
      "details": { ... }
    }
  }
  ```
- **Standard HTTP Codes**:
  - `200 OK`: Request succeeded.
  - `201 Created`: Resource successfully created.
  - `202 Accepted`: Asynchronous operation initiated (e.g., agent message processing).
  - `400 Bad Request`: Validation failure or business logic rejection.
  - `404 Not Found`: Entity not found.
  - `409 Conflict`: Idempotency violation or concurrent modification.
  - `422 Unprocessable Entity`: Pydantic schema validation failure.
  - `500 Internal Error`: Server execution fault.

---

## 2. Endpoints

### 2.1 Health Check
- **`GET /health`**
- **Response `200 OK`**:
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "agent_mode": "mock", 
    "storage_backend": "json_fallback",
    "total_listings": 120,
    "categories_supported": 10,
    "timestamp": "2026-11-04T16:15:00Z"
  }
  ```

### 2.2 Sessions
- **`POST /api/sessions`**
  - **Request**: `{ "user_id": "optional_user_123" }`
  - **Response `201 Created`**:
    ```json
    {
      "session_id": "sess_89a3f2b1",
      "workflow_state": "NEW",
      "created_at": "2026-11-04T16:15:00Z",
      "preferences": {
        "intent": "rent",
        "interview_complete": false
      }
    }
    ```

- **`GET /api/sessions/{session_id}`**
  - **Response `200 OK`**: Complete session snapshot including message history, current preferences, active recommendations, selected vehicle, pending booking, and workflow state.

- **`DELETE /api/sessions/{session_id}`**
  - **Response `200 OK`**: `{ "status": "deleted", "session_id": "sess_89a3f2b1" }`

### 2.3 Conversational Messaging & SSE
- **`POST /api/sessions/{session_id}/messages`**
  - **Request**:
    ```json
    {
      "content": "I need an automatic SUV in Delhi for 5 days starting Dec 15, 2026 with budget ₹3000/day",
      "client_timestamp": "2026-11-04T16:15:02Z"
    }
    ```
  - **Response `200 OK`**:
    ```json
    {
      "message_id": "msg_001",
      "role": "assistant",
      "content": "I found 5 great automatic SUVs matching your ₹3,000/day budget in Delhi from Dec 15 to Dec 20.",
      "workflow_state": "RECOMMENDATIONS_READY",
      "a2ui_surfaces": ["rec-surface-1"],
      "recommendations": [ ... ]
    }
    ```

- **`GET /api/sessions/{session_id}/events`**
  - **Transport**: Server-Sent Events (`text/event-stream`)
  - **Events Emitted**:
    1. `event: progress`
       ```json
       {
         "stage": "SEARCHING",
         "step_number": 3,
         "total_steps": 10,
         "message": "Querying marketplace for automatic SUVs in Delhi...",
         "timestamp": "2026-11-04T16:15:03Z"
       }
       ```
    2. `event: a2ui`
       ```json
       {
         "type": "createSurface",
         "surfaceId": "rec-surface-1",
         "catalogId": "automotive-v1"
       }
       ```
    3. `event: mcp_trigger`
       ```json
       {
         "app": "booking",
         "uri": "ui://booking-form",
         "vehicle_id": "CAR-001"
       }
       ```

### 2.4 Structured Preference Updates
- **`PATCH /api/sessions/{session_id}/preferences`**
  - **Request**:
    ```json
    {
      "intent": "rent",
      "category": "Sedan",
      "budget": { "amount": 3500, "currency": "INR", "period": "per_day" }
    }
    ```
  - **Response `200 OK`**: Updated preferences object and invalidation confirmation.

### 2.5 Marketplace & Vehicles
- **`POST /api/search`**
  - **Request**:
    ```json
    {
      "intent": "rent",
      "category": "SUV",
      "location": "Delhi",
      "max_price": 3000,
      "transmission": "automatic",
      "fuel_type": "any",
      "seats": 5,
      "start_date": "2026-12-15",
      "end_date": "2026-12-20",
      "limit": 5
    }
    ```
  - **Response `200 OK`**:
    ```json
    {
      "total_matching": 12,
      "recommendations": [
        {
          "vehicle": { ... },
          "match_score": 94.5,
          "estimated_total_cost": 15000,
          "positive_matches": [...],
          "trade_offs": [...],
          "explanation": "..."
        }
      ]
    }
    ```

- **`GET /api/vehicles/{vehicle_id}`**
  - **Response `200 OK`**: Complete vehicle listing details.

- **`POST /api/vehicles/compare`**
  - **Request**: `{ "vehicle_ids": ["CAR-001", "CAR-002", "CAR-003"] }`
  - **Response `200 OK`**: Side-by-side comparison matrix of specs, features, and prices.

- **`POST /api/availability/check`**
  - **Request**: `{ "vehicle_id": "CAR-001", "start_date": "2026-12-15", "end_date": "2026-12-20" }`
  - **Response `200 OK`**: `{ "vehicle_id": "CAR-001", "is_available": true, "conflicting_dates": [] }`

### 2.6 Bookings & Price Recalculation
- **`POST /api/bookings/calculate`**
  - **Request**:
    ```json
    {
      "vehicle_id": "CAR-001",
      "duration_days": 5,
      "addon_ids": ["addon_insurance_full"]
    }
    ```
  - **Response `200 OK`**:
    ```json
    {
      "vehicle_id": "CAR-001",
      "base_rate": 2800,
      "duration_days": 5,
      "subtotal": 14000,
      "addons_total": 1500,
      "taxes": 1860,
      "total_amount": 17360,
      "currency": "INR"
    }
    ```

- **`POST /api/bookings`**
  - **Headers**: `Idempotency-Key: idemp_bk_89a3f2b1_1`
  - **Request**:
    ```json
    {
      "session_id": "sess_89a3f2b1",
      "vehicle_id": "CAR-001",
      "customer_name": "Rohan Sharma",
      "customer_email": "rohan.sharma@example.com",
      "customer_phone": "+91 98765 43210",
      "driver_license_number": "DL-1420110012345",
      "pickup_date": "2026-12-15",
      "return_date": "2026-12-20",
      "pickup_location": "Delhi Airport T3",
      "return_location": "Delhi Airport T3",
      "addon_ids": ["addon_insurance_full"]
    }
    ```
  - **Response `201 Created`**:
    ```json
    {
      "booking_id": "BK-2026-90412",
      "status": "PENDING_PAYMENT",
      "total_amount": 17360,
      "currency": "INR",
      "workflow_state": "CHECKOUT_READY"
    }
    ```

### 2.7 Purchase Orders
- **`POST /api/orders`**
  - **Headers**: `Idempotency-Key: idemp_ord_91b4c3d2_1`
  - **Request**:
    ```json
    {
      "session_id": "sess_91b4c3d2",
      "vehicle_id": "CAR-001",
      "customer_name": "Priya Patel",
      "customer_email": "priya.patel@example.com",
      "customer_phone": "+91 98111 22334",
      "pan_or_id": "ABCDE1234F",
      "financing_selected": true,
      "deposit_amount": 25000
    }
    ```
  - **Response `201 Created`**: Purchase order with status `PENDING_PAYMENT`.

### 2.8 Mock Payment Processing
- **`POST /api/payments/mock`**
  - **Headers**: `Idempotency-Key: idemp_pay_89a3f2b1_1`
  - **Request**:
    ```json
    {
      "order_or_booking_id": "BK-2026-90412",
      "amount": 17360,
      "currency": "INR",
      "payment_method": "upi_simulator",
      "simulated_scenario": "success"
    }
    ```
  - **Response `200 OK`** (or `402 Payment Required` if scenario was failure):
    ```json
    {
      "payment_id": "PAY-2026-55192",
      "transaction_reference": "TXN-MOCK-782910",
      "status": "SUCCESS",
      "workflow_state": "CONFIRMED",
      "booking_reference": "BK-2026-90412",
      "disclaimer": "Simulated payment transaction - No actual financial charge."
    }
    ```

### 2.9 A2UI Action Endpoint
- **`POST /api/a2ui/action`**
  - **Request**:
    ```json
    {
      "session_id": "sess_89a3f2b1",
      "surface_id": "interview-form",
      "action_id": "select_category",
      "data": { "category": "SUV" }
    }
    ```
  - **Response `200 OK`**: Next state, surfaces, and agent response.

