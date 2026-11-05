const API_BASE = '';

export async function createSession() {
  const res = await fetch(`${API_BASE}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function getSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
  if (!res.ok) throw new Error('Failed to fetch session');
  return res.json();
}

export async function deleteSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to reset session');
  return res.json();
}

export async function sendMessage(sessionId: string, content: string) {
  const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content })
  });
  if (!res.ok) throw new Error('Failed to send message');
  return res.json();
}

export async function sendA2uiAction(sessionId: string, surfaceId: string, actionId: string, data: any) {
  const res = await fetch(`${API_BASE}/api/a2ui/action`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      surface_id: surfaceId,
      action_id: actionId,
      data: data || {}
    })
  });
  if (!res.ok) throw new Error('Failed to process A2UI action');
  return res.json();
}

export async function calculateBookingTotal(vehicleId: string, durationDays: number, addonIds: string[]) {
  const res = await fetch(`${API_BASE}/api/bookings/calculate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      vehicle_id: vehicleId,
      duration_days: durationDays,
      addon_ids: addonIds
    })
  });
  if (!res.ok) throw new Error('Failed to calculate booking total');
  return res.json();
}

export async function createBooking(payload: any) {
  const res = await fetch(`${API_BASE}/api/bookings`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': `idemp_bk_${Date.now()}`
    },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to create booking');
  return res.json();
}

export async function createOrder(payload: any) {
  const res = await fetch(`${API_BASE}/api/orders`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': `idemp_ord_${Date.now()}`
    },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to create purchase order');
  return res.json();
}

export async function executeMockPayment(payload: any) {
  const res = await fetch(`${API_BASE}/api/payments/mock`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Idempotency-Key': `idemp_pay_${Date.now()}`
    },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error('Failed to process mock payment');
  return res.json();
}

export async function loginUser(payload: { email: string; password: string }) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(err.detail || 'Login failed');
  }
  return res.json();
}

export async function signupUser(payload: { name: string; email: string; password: string; phone?: string }) {
  const res = await fetch(`${API_BASE}/api/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Signup failed' }));
    throw new Error(err.detail || 'Signup failed');
  }
  return res.json();
}

export async function getMe(token?: string) {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}/api/auth/me`, { headers });
  if (!res.ok) throw new Error('Failed to fetch user');
  return res.json();
}


