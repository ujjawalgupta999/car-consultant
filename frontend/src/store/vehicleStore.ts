import { create } from 'zustand';
import { Vehicle } from '../types';

export interface VehicleFilters {
  search: string;
  intent: 'all' | 'rent' | 'buy';
  category: string;
  brand: string;
  transmission: string;
  fuelType: string;
  minPrice: number;
  maxPrice: number;
  location: string;
  seats?: number;
  sort: 'relevance' | 'price_asc' | 'price_desc' | 'rating' | 'year';
}

const DEFAULT_FILTERS: VehicleFilters = {
  search: '',
  intent: 'all',
  category: '',
  brand: '',
  transmission: '',
  fuelType: '',
  minPrice: 0,
  maxPrice: 50000000,
  location: '',
  seats: undefined,
  sort: 'relevance',
};

interface VehicleStore {
  vehicles: Vehicle[];
  isLoading: boolean;
  error: string | null;
  filters: VehicleFilters;
  fetchVehicles: () => Promise<void>;
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

  setFilters: (partial) => {
    set((state) => ({
      filters: { ...state.filters, ...partial },
    }));
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

        // 2. Intent
        if (filters.intent === 'rent' && !v.available_for_rent) return false;
        if (filters.intent === 'buy' && !v.available_for_purchase) return false;

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
        if (filters.seats && v.seats < filters.seats) return false;

        // 9. Price Ceiling
        if (filters.maxPrice && filters.maxPrice > 0) {
          if (filters.intent === 'rent') {
            if (v.rental_price_per_day > filters.maxPrice) return false;
          } else if (filters.intent === 'buy') {
            if (v.purchase_price > filters.maxPrice) return false;
          }
        }

        return true;
      })
      .sort((a, b) => {
        if (filters.sort === 'price_asc') {
          const pA = filters.intent === 'rent' ? a.rental_price_per_day : a.purchase_price;
          const pB = filters.intent === 'rent' ? b.rental_price_per_day : b.purchase_price;
          return pA - pB;
        }
        if (filters.sort === 'price_desc') {
          const pA = filters.intent === 'rent' ? a.rental_price_per_day : a.purchase_price;
          const pB = filters.intent === 'rent' ? b.rental_price_per_day : b.purchase_price;
          return pB - pA;
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

