import { create } from 'zustand';
import { Vehicle } from '../types';

export interface VehicleFilters {
  search: string;
  intent: 'buy';
  category: string;
  brand: string;
  transmission: string;
  fuelType: string;
  minPrice: number;
  maxPrice: number;
  location: string;
  seats?: number;
  seatsMatchType?: 'exact' | 'min' | 'max';
  sort: 'relevance' | 'price_asc' | 'price_desc' | 'rating' | 'year';
}

const DEFAULT_FILTERS: VehicleFilters = {
  search: '',
  intent: 'buy',
  category: '',
  brand: '',
  transmission: '',
  fuelType: '',
  minPrice: 0,
  maxPrice: 50000000,
  location: '',
  seats: undefined,
  seatsMatchType: undefined,
  sort: 'relevance',
};

interface VehicleStore {
  vehicles: Vehicle[];
  isLoading: boolean;
  error: string | null;
  filters: VehicleFilters;
  purchasedVehicleIds: string[];
  purchases: any[];
  // Deprecated compatibility fields
  rentedVehicleIds: string[];
  rentals: any[];
  fetchVehicles: () => Promise<void>;
  fetchUserOwnership: () => Promise<void>;
  setFilters: (partial: Partial<VehicleFilters>) => void;
  resetFilters: () => void;
  getFilteredVehicles: () => Vehicle[];
  getVehicleById: (id: string) => Vehicle | undefined;
}

export const useVehicleStore = create<VehicleStore>((set, get) => ({
  vehicles: [],
  isLoading: false,
  error: null,
  filters: DEFAULT_FILTERS,
  purchasedVehicleIds: [],
  purchases: [],
  rentedVehicleIds: [],
  rentals: [],

  fetchVehicles: async () => {
    set({ isLoading: true, error: null });
    try {
      const res = await fetch('/api/vehicles?limit=150');
      if (!res.ok) throw new Error('Failed to fetch marketplace catalogue');
      const data = await res.json();
      set({ vehicles: data.vehicles || [], isLoading: false });
    } catch (err: any) {
      set({ error: err.message, isLoading: false });
    }
  },

  fetchUserOwnership: async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('aura_auth_token') || 'token_demo_alex_vance' : 'token_demo_alex_vance';
      const purchasesRes = await fetch('/api/purchases', {
        headers: { Authorization: `Bearer ${token}` }
      }).catch(() => null);

      const purchasedIds: string[] = [];
      let purchasesData: any[] = [];
      if (purchasesRes && purchasesRes.ok) {
        const pJson = await purchasesRes.json();
        purchasesData = pJson.purchases || [];
        purchasesData.forEach((p: any) => {
          const vId = p.vehicleId || p.vehicleSnapshot?.id;
          if (vId && !purchasedIds.includes(vId)) purchasedIds.push(vId);
        });
      }

      set({
        purchasedVehicleIds: purchasedIds,
        purchases: purchasesData,
        rentedVehicleIds: [],
        rentals: [],
      });
    } catch (e) {
      console.warn('Could not fetch user purchase ownership state:', e);
    }
  },

  setFilters: (partial) => {
    set((state) => {
      const merged = { ...state.filters, ...partial, intent: 'buy' as const };
      return { filters: merged };
    });
  },

  resetFilters: () => {
    set({ filters: DEFAULT_FILTERS });
  },

  getVehicleById: (id: string) => {
    return get().vehicles.find((v) => v.id === id);
  },

  getFilteredVehicles: () => {
    const { vehicles, filters } = get();

    return vehicles
      .filter((v) => {
        // 1. Search Query
        if (filters.search.trim()) {
          const query = filters.search.toLowerCase();
          const matchName = `${v.brand} ${v.model}`.toLowerCase().includes(query);
          const matchCat = v.category.toLowerCase().includes(query);
          if (!matchName && !matchCat) return false;
        }

        // 2. Intent: strictly purchase
        if (!v.available_for_purchase) return false;

        // 3. Category
        if (filters.category && filters.category.toLowerCase() !== 'all' && filters.category !== '') {
          if (v.category.toLowerCase() !== filters.category.toLowerCase()) return false;
        }

        // 4. Brand
        if (filters.brand && filters.brand.toLowerCase() !== 'all' && filters.brand !== '') {
          if (v.brand.toLowerCase() !== filters.brand.toLowerCase()) return false;
        }

        // 5. Transmission
        if (filters.transmission && filters.transmission.toLowerCase() !== 'all' && filters.transmission !== '') {
          if (v.transmission.toLowerCase() !== filters.transmission.toLowerCase()) return false;
        }

        // 6. Fuel Type
        if (filters.fuelType && filters.fuelType.toLowerCase() !== 'all' && filters.fuelType !== '') {
          if (v.fuel_type.toLowerCase() !== filters.fuelType.toLowerCase()) return false;
        }

        // 7. Location
        if (filters.location && filters.location.toLowerCase() !== 'all' && filters.location !== '') {
          if (!v.location.toLowerCase().includes(filters.location.toLowerCase())) return false;
        }

        // 8. Seating
        if (filters.seats !== undefined && filters.seats > 0) {
          const matchType = filters.seatsMatchType || 'exact';
          if (matchType === 'exact' && v.seats !== filters.seats) return false;
          if (matchType === 'min' && v.seats < filters.seats) return false;
          if (matchType === 'max' && v.seats > filters.seats) return false;
        }

        // 8.5 Minimum Price
        if (filters.minPrice !== undefined && filters.minPrice > 0) {
          if (v.purchase_price < filters.minPrice) return false;
        }

        // 9. Price Ceiling
        if (filters.maxPrice && filters.maxPrice > 0) {
          if (v.purchase_price > filters.maxPrice) return false;
        }

        return true;
      })
      .sort((a, b) => {
        if (filters.sort === 'price_asc') {
          return a.purchase_price - b.purchase_price;
        }
        if (filters.sort === 'price_desc') {
          return b.purchase_price - a.purchase_price;
        }
        if (filters.sort === 'rating') {
          return b.rating - a.rating;
        }
        if (filters.sort === 'year') {
          return b.year - a.year;
        }
        return 0; // relevance
      });
  },
}));
