import { create } from 'zustand';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  phone?: string;
  saved_vehicles: string[];
}

interface AuthStore {
  user: UserProfile | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: UserProfile, token: string) => void;
  logout: () => void;
  fetchCurrentUser: () => Promise<void>;
  toggleSaved: (vehicleId: string) => Promise<void>;
  isSaved: (vehicleId: string) => boolean;
}

const savedToken = typeof window !== 'undefined' ? localStorage.getItem('aura_auth_token') || 'token_demo_alex_vance' : 'token_demo_alex_vance';

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: {
    id: 'usr_demo_01',
    name: 'Alex Vance',
    email: 'demo@auramotors.com',
    phone: '+91 98765 43210',
    saved_vehicles: ['CAR-001', 'CAR-021'],
  },
  token: savedToken,
  isAuthenticated: true,

  fetchCurrentUser: async () => {
    const token = get().token || localStorage.getItem('aura_auth_token');
    if (!token) return;
    try {
      const res = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.user) {
          set({ user: data.user, isAuthenticated: true, token });
        }
      }
    } catch (e) {
      console.warn('Failed to fetch user from backend:', e);
    }
  },

  login: (user, token) => {
    localStorage.setItem('aura_auth_token', token);
    set({ user, token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('aura_auth_token');
    set({ user: null, token: null, isAuthenticated: false });
  },

  toggleSaved: async (vehicleId: string) => {
    const { user, token } = get();
    if (!user) return;
    const exists = user.saved_vehicles.includes(vehicleId);
    const updated = exists
      ? user.saved_vehicles.filter((id) => id !== vehicleId)
      : [...user.saved_vehicles, vehicleId];

    // Optimistic local update
    set({ user: { ...user, saved_vehicles: updated } });

    // Sync to MongoDB Atlas backend
    try {
      const authToken = token || localStorage.getItem('aura_auth_token') || 'token_demo_alex_vance';
      const res = await fetch('/api/auth/saved-vehicles/toggle', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`
        },
        body: JSON.stringify({ vehicle_id: vehicleId })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.saved_vehicles) {
          set({ user: { ...user, saved_vehicles: data.saved_vehicles } });
        }
      }
    } catch (err) {
      console.warn('Failed to sync saved vehicle to MongoDB Atlas:', err);
    }

    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('aura_data_refresh', { detail: { resource: 'saved' } }));
    }
  },

  isSaved: (vehicleId: string) => {
    const { user } = get();
    if (!user) return false;
    return user.saved_vehicles.includes(vehicleId);
  },
}));
