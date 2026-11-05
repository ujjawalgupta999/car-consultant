# AMULATE SUMMER HACKATHON 2026: MCP & MCP APPS SPECIFICATION
## AI-Powered Car Rental and Purchase Consultant

---

## 1. Overview and Standards

This specification details:
1. **MCP Tool Server**: Implementing standard tools compliant with the Model Context Protocol (MCP).
2. **MCP Apps**: Interactive mini-applications (`ui://booking-form` and `ui://checkout-modal`) rendered inside sandboxed host containers in the chat thread.

MIME Type for MCP Apps: `text/html;profile=mcp-app`

---

## 2. MCP Tools Specification

### 2.1 Tool Catalog

| Tool Name | Type | Description |
|-----------|------|-------------|
| `search_vehicles` | Read-only | Filter vehicle repository by category, location, budget, fuel, dates, and intent |
| `get_vehicle_details` | Read-only | Fetch full vehicle specifications, features, and condition |
| `check_vehicle_availability` | Read-only | Verify date conflict intervals for vehicle rentals |
| `compare_vehicles` | Read-only | Provide side-by-side spec and value comparison for 2-4 vehicles |
| `calculate_booking_total` | Read-only | Authoritative backend price recalculation with fees, taxes, and add-ons |
| `create_booking` | Transactional | Reserve a rental vehicle (requires customer info and idempotency key) |
| `create_purchase_order` | Transactional | Reserve a vehicle purchase (requires customer info and token amount) |
| `get_booking_status` | Read-only | Retrieve current state of a booking or order |
| `simulate_mock_payment` | Transactional | Execute deterministic mock payment scenario (success, failure, timeout) |
| `get_order_confirmation` | Read-only | Retrieve finalized booking voucher or purchase order confirmation |

### 2.2 Tool Argument Schemas (Excerpts)

```json
{
  "name": "calculate_booking_total",
  "description": "Calculates authoritative rental subtotal, insurance add-ons, taxes, and final total.",
  "parameters": {
    "type": "object",
    "properties": {
      "vehicle_id": { "type": "string" },
      "duration_days": { "type": "integer", "minimum": 1 },
      "addon_ids": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["vehicle_id", "duration_days"]
  }
}
```

```json
{
  "name": "simulate_mock_payment",
  "description": "Simulates a payment transaction without processing real money.",
  "parameters": {
    "type": "object",
    "properties": {
      "order_or_booking_id": { "type": "string" },
      "amount": { "type": "number" },
      "payment_method": { "type": "string", "enum": ["upi", "card", "netbanking"] },
      "scenario": { "type": "string", "enum": ["success", "failure", "timeout"] },
      "idempotency_key": { "type": "string" }
    },
    "required": ["order_or_booking_id", "amount", "payment_method", "scenario", "idempotency_key"]
  }
}
```

---

## 3. Mandatory MCP App: Booking Form (`ui://booking-form`)

### 3.1 Purpose & Host Integration
The Booking MCP App renders directly in the conversation when a user selects a vehicle to rent or purchase. It runs inside a sandboxed iframe or isolated web component container provided by the host.

### 3.2 Protocol Lifecycle
1. **Mount & Handshake (`mcp-app:init`)**:
   - Host sends initial context:
     ```json
     {
       "type": "mcp-app:init",
       "protocolVersion": "1.0",
       "context": {
         "vehicleId": "CAR-001",
         "vehicle": { ... },
         "intent": "rent",
         "prefilled": {
           "startDate": "2026-12-15",
           "endDate": "2026-12-20",
           "durationDays": 5,
           "location": "Delhi"
         },
         "theme": { "mode": "dark" }
       }
     }
     ```
2. **Interactive Recalculation (`mcp-app:action`)**:
   - When the user selects or deselects optional add-ons (e.g. Zero-Depreciation Insurance ₹300/day, Child Seat ₹150/day), the MCP App sends an RPC call to the host:
     ```json
     {
       "type": "mcp-app:action",
       "action": "recalculate",
       "payload": { "vehicleId": "CAR-001", "durationDays": 5, "addonIds": ["addon_insurance_full"] }
     }
     ```
   - Host responds with `mcp-app:update` containing verified calculations.
3. **Submission (`mcp-app:finish`)**:
   - User reviews and confirms booking details.
   - App dispatches completion payload to Host:
     ```json
     {
       "type": "mcp-app:finish",
       "status": "submitted",
       "data": {
         "customerName": "Rohan Sharma",
         "customerEmail": "rohan@example.com",
         "customerPhone": "+91 98765 43210",
         "driverLicense": "DL-1420110012345",
         "addonIds": ["addon_insurance_full"],
         "pickupLocation": "Delhi Airport T3",
         "returnLocation": "Delhi Airport T3"
       }
     }
     ```
4. **Cancellation**:
   - User can click "Cancel and return to chat", which dispatches `{ "type": "mcp-app:finish", "status": "cancelled" }`.

---

## 4. Mandatory MCP App: Mock Checkout (`ui://checkout-modal`)

### 4.1 Purpose & Host Integration
The Mock Checkout MCP App handles the final authorization simulation without ever contacting a live banking network or asking for genuine payment secrets.

### 4.2 UI Display Requirements
- Order / Booking summary and reference ID.
- Itemized line items: Base Rental / Vehicle Deposit, Insurance / Options, GST / Platform Fee, Total Payable.
- Prominent **Mock Environment Banner**:
  > ⚠️ **MOCK PAYMENT SIMULATOR**: This is a test demonstration. No real currency is charged. Do not enter actual card numbers or UPI PINs.
- Interactive Payment Method Tabs:
  - **UPI Simulator**: Simulates Google Pay / PhonePe / Paytm authorization.
  - **Card Simulator**: Pre-populated mock test card numbers (e.g. `4000 0000 0000 0001`).
  - **Test Scenarios**:
    - `🟢 Instant Success`: Confirms transaction immediately.
    - `🔴 Simulated Decline`: Tests payment failure and safe recovery.
    - `🟡 Gateway Timeout`: Tests transient failure handling.

### 4.3 Protocol Lifecycle
1. **Handshake (`mcp-app:init`)**:
   - Context provided: `bookingId` or `orderId`, `vehicle`, `totalAmount`, `currency`, `breakdown`.
2. **Execution (`mcp-app:action`)**:
   - App sends `mcp-app:action` with simulated method and chosen test scenario.
   - Host proxies to backend `/api/payments/mock`.
3. **Completion (`mcp-app:finish`)**:
   - On success: Dispatches `{ "type": "mcp-app:finish", "status": "paid", "paymentId": "PAY-55192" }`.
   - On failure: Displays clear error message with "Retry Payment" button.

---

## 5. Security & Isolation Constraints

1. **Sandboxed Iframes**:
   - Attributes: `sandbox="allow-scripts allow-forms allow-same-origin"` (or equivalent native host boundary).
   - Content Security Policy (CSP): `default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self';`
2. **Server-Side Price Authority**:
   - The MCP App sends selections; the backend calculates currency amounts. Client-submitted prices are discarded.
3. **Idempotency Guarantee**:
   - Every submission generates a UUIDv4 idempotency key. Repeating submissions will not create duplicate bookings or duplicate transactions.

