import { create } from 'zustand';
import { Vehicle } from '../types';

interface ComparisonStore {
  comparedVehicles: Vehicle[];
  addVehicle: (vehicle: Vehicle) => boolean;
  removeVehicle: (vehicleId: string) => void;
  clearComparison: () => void;
  hasVehicle: (vehicleId: string) => boolean;
}

export const useComparisonStore = create<ComparisonStore>((set, get) => ({
  comparedVehicles: [],

  addVehicle: (vehicle: Vehicle) => {
    const { comparedVehicles } = get();
    if (comparedVehicles.some((v) => v.id === vehicle.id)) {
      return false; // already added
    }
    if (comparedVehicles.length >= 4) {
      return false; // max 4
    }
    set({ comparedVehicles: [...comparedVehicles, vehicle] });
    return true;
  },

  removeVehicle: (vehicleId: string) => {
    set((state) => ({
      comparedVehicles: state.comparedVehicles.filter((v) => v.id !== vehicleId),
    }));
  },

  clearComparison: () => {
    set({ comparedVehicles: [] });
  },

  hasVehicle: (vehicleId: string) => {
    return get().comparedVehicles.some((v) => v.id === vehicleId);
  },
}));
