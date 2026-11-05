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
  toggleSaved: (vehicleId: string) => void;
  isSaved: (vehicleId: string) => boolean;
}

export const useAuthStore = create<AuthStore>((set, get) => ({
  user: {
    id: 'usr_demo_01',
    name: 'Alex Vance',
    email: 'demo@auramotors.com',
    phone: '+91 98765 43210',
    saved_vehicles: ['CAR-001', 'CAR-021'],
  },
  token: 'token_demo_alex_vance',
  isAuthenticated: true,

  login: (user, token) => {
    localStorage.setItem('aura_auth_token', token);
    set({ user, token, isAuthenticated: true });
  },

  logout: () => {
    localStorage.removeItem('aura_auth_token');
    set({ user: null, token: null, isAuthenticated: false });
  },

  toggleSaved: (vehicleId: string) => {
    const { user } = get();
    if (!user) return;
    const exists = user.saved_vehicles.includes(vehicleId);
    const updated = exists
      ? user.saved_vehicles.filter((id) => id !== vehicleId)
      : [...user.saved_vehicles, vehicleId];

    set({ user: { ...user, saved_vehicles: updated } });
  },

  isSaved: (vehicleId: string) => {
    const { user } = get();
    if (!user) return false;
    return user.saved_vehicles.includes(vehicleId);
  },
}));

