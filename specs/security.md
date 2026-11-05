# AMULATE SUMMER HACKATHON 2026: SECURITY SPECIFICATION
## AI-Powered Car Rental and Purchase Consultant

---

## 1. Threat Model & Risk Analysis

| Threat | Risk Level | Mitigation Strategy |
|--------|------------|---------------------|
| **Prompt Injection** (Attacker commands agent to give free cars or bypass rules) | High | System prompts use strict instruction boundaries. Agent orchestrator enforces deterministic code-level guards; pricing and booking cannot be overridden by LLM output. |
| **Client-Side Price Tampering** (User alters rental rate in request) | Critical | Client prices are strictly ignored. All line items and totals are computed authoritatively on the backend from stored database rates. |
| **Payment Credential Harvesting** | Critical | Explicit prohibition of real card/UPI collection. Mock checkout utilizes synthetic fake numbers and clear test disclaimers. |
| **XSS via A2UI Dynamic Interface** | High | A2UI renderer implements strict component registry mapping. No arbitrary HTML or `eval()` is executed. |
| **MCP App Frame Escape** | Medium | MCP Apps run inside sandboxed iframes with restrictive `sandbox` attributes and Content Security Policy (CSP). |
| **Duplicate Booking/Payment** | Medium | Enforced `Idempotency-Key` headers on `/api/bookings` and `/api/payments/mock`. |
| **Cross-Session Data Leakage** | High | Cryptographically generated session IDs (`uuidv4`). Validation on every state query. |
| **Secret Exposure** | Critical | Environment variables stored in `.env` (gitignored). `.env.example` provided with safe defaults. Frontend bundle never receives server secrets. |

---

## 2. Server-Side Transaction Integrity

### 2.1 Authoritative Price Calculation
```python
def calculate_authoritative_total(vehicle: Vehicle, days: int, addon_ids: list[str]) -> PriceBreakdown:
    base_rate = vehicle.rental_price_per_day
    subtotal = base_rate * days
    addons_total = sum(ADDON_CATALOG[aid].price_per_day * days for aid in addon_ids if aid in ADDON_CATALOG)
    tax_rate = 0.18 # 18% GST
    taxes = round((subtotal + addons_total) * tax_rate, 2)
    total = subtotal + addons_total + taxes
    return PriceBreakdown(
        base_rate=base_rate,
        subtotal=subtotal,
        addons_total=addons_total,
        taxes=taxes,
        total_amount=total
    )
```
*Note*: No client-provided amount is ever trusted.

### 2.2 Idempotency Engine
- Clients generate a unique `Idempotency-Key` (UUIDv4) for each booking creation and payment attempt.
- The server records the key with an expiration TTL (24 hours).
- If a duplicate request arrives with the same key, the cached result is returned without re-executing the transaction.

---

## 3. Sandboxed MCP App Security

### 3.1 Iframe Sandbox Configuration
The Host renders the MCP App inside:
```html
<iframe
  src="/mcp-apps/booking/index.html"
  sandbox="allow-scripts allow-forms allow-same-origin"
  referrerpolicy="no-referrer"
  csp="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self';"
/>
```

### 3.2 PostMessage Origin Validation
- The Host verifies `event.origin === window.location.origin` before accepting messages from embedded apps.
- The MCP App verifies messages arrive from the recognized Host.

---

## 4. Input Sanitization & Untrusted Listing Protection

1. **Marketplace Descriptions**:
   - Vehicle listings are treated as untrusted text.
   - When injecting listing context into agent prompts, descriptions are escaped and encapsulated in designated XML/JSON boundaries to avoid prompt leakage or injection.
2. **User Inputs**:
   - Strings are trimmed, validated against length limits, and checked against regex patterns for dates, currency amounts, and phone/email structures.

