import React, { useEffect, useState } from 'react';
import { useVehicleStore } from '../store/vehicleStore';
import { VehicleCard } from '../components/VehicleCard';
import { Award, ShieldCheck, Search, SlidersHorizontal, Tag, CheckCircle2 } from 'lucide-react';

export const BuyCars: React.FC = () => {
  const { vehicles, fetchVehicles, filters, setFilters, getFilteredVehicles } = useVehicleStore();
  const [condition, setCondition] = useState<'all' | 'new' | 'used'>('all');
  const [category, setCategory] = useState(filters.category || '');
  const [maxBudget, setMaxBudget] = useState(filters.maxPrice < 100000 ? 25000000 : filters.maxPrice);

  useEffect(() => {
    setFilters({ intent: 'buy' });
    if (vehicles.length === 0) {
      fetchVehicles();
    }
  }, [vehicles.length, fetchVehicles, setFilters]);

  // Synchronize with external AI Consultant filter actions
  useEffect(() => {
    if (filters.category !== undefined) {
      setCategory(filters.category);
    }
    if (filters.maxPrice && filters.maxPrice > 100000) {
      setMaxBudget(filters.maxPrice);
    }
  }, [filters.category, filters.maxPrice]);

  const handleApplyBuySearch = (e: React.FormEvent) => {
    e.preventDefault();
    setFilters({
      intent: 'buy',
      category: category,
      maxPrice: maxBudget,
    });
  };

  const handleCategoryChange = (newCat: string) => {
    setCategory(newCat);
    setFilters({
      intent: 'buy',
      category: newCat,
    });
  };

  const buyListings = getFilteredVehicles().filter((v) => {
    if (!v.available_for_purchase) return false;
    if (condition !== 'all' && v.condition !== condition) return false;
    return true;
  });

  return (
    <div className="min-h-screen bg-background py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Banner Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary/10 border border-primary/30 text-primary-accent text-xs font-bold uppercase tracking-wider mb-2">
            <Tag className="w-3.5 h-3.5" /> Certified Purchase Catalogue
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
            Purchase Brand-New & Certified Pre-Owned
          </h1>
          <p className="text-xs text-gray-400 mt-2">
            Transparent pricing, 200-point mechanical inspection, full service records, and refundable token reservation.
          </p>
        </div>

        {/* Purchase Filter Bar */}
        <div className="mb-10 rounded-2xl border border-surface-border bg-surface p-5 shadow-2xl">
          <form onSubmit={handleApplyBuySearch} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                Vehicle Condition
              </label>
              <div className="flex rounded-xl bg-background border border-surface-border p-1">
                <button
                  type="button"
                  onClick={() => setCondition('all')}
                  className={`flex-1 rounded-lg py-1.5 text-xs font-bold uppercase transition-all ${
                    condition === 'all' ? 'bg-primary text-white shadow' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  All
                </button>
                <button
                  type="button"
                  onClick={() => setCondition('new')}
                  className={`flex-1 rounded-lg py-1.5 text-xs font-bold uppercase transition-all ${
                    condition === 'new' ? 'bg-primary text-white shadow' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  New
                </button>
                <button
                  type="button"
                  onClick={() => setCondition('used')}
                  className={`flex-1 rounded-lg py-1.5 text-xs font-bold uppercase transition-all ${
                    condition === 'used' ? 'bg-primary text-white shadow' : 'text-gray-400 hover:text-white'
                  }`}
                >
                  Pre-Owned
                </button>
              </div>
            </div>

            <div>
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                Category
              </label>
              <select
                value={category}
                onChange={(e) => handleCategoryChange(e.target.value)}
                className="w-full rounded-xl bg-background border border-surface-border px-3 py-2.5 text-xs text-white outline-none cursor-pointer"
              >
                <option value="">All Categories</option>
                <option value="SUV">SUV</option>
                <option value="Sedan">Sedan</option>
                <option value="Luxury SUV">Luxury SUV</option>
                <option value="Luxury Sedan">Luxury Sedan</option>
                <option value="Electric Vehicle">Electric Vehicle</option>
                <option value="Sports Car">Sports Car</option>
                <option value="Convertible">Convertible</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                Maximum Budget: ₹{(maxBudget / 100000).toFixed(0)} Lakh
              </label>
              <input
                type="range"
                min="500000"
                max="30000000"
                step="500000"
                value={maxBudget}
                onChange={(e) => setMaxBudget(Number(e.target.value))}
                className="w-full accent-primary h-2 bg-background rounded-lg appearance-none cursor-pointer mt-2"
              />
            </div>

            <div className="flex items-end">
              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-cyan-500 py-3 text-xs font-bold text-white uppercase tracking-wider shadow-lg hover:opacity-95 transition-all active:scale-95"
              >
                <Search className="w-4 h-4" />
                <span>Search Vehicles</span>
              </button>
            </div>
          </form>

          {/* Guarantee Highlights */}
          <div className="mt-4 pt-4 border-t border-surface-border/60 flex flex-wrap items-center justify-between gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <ShieldCheck className="w-4 h-4" /> 1-Year Comprehensive Warranty Included
            </span>
            <span>• 100% Refundable ₹25,000 Reservation Token</span>
            <span>• Verified Clean Title & Non-Accidental Guarantee</span>
          </div>
        </div>

        {/* Results Header */}
        <div className="flex items-center justify-between mb-6">
          <p className="text-xs text-gray-400">
            Showing <span className="font-bold text-white">{buyListings.length}</span> purchase-eligible vehicles
          </p>
        </div>

        {/* Listings Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {buyListings.map((car) => (
            <VehicleCard key={car.id} vehicle={car} priorityIntent="buy" />
          ))}
        </div>
      </div>
    </div>
  );
};

