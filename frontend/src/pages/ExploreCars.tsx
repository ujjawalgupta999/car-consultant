import React, { useEffect } from 'react';
import { useVehicleStore } from '../store/vehicleStore';
import { VehicleCard } from '../components/VehicleCard';
import { Filter, Search, RotateCcw, SlidersHorizontal, Car } from 'lucide-react';

const CATEGORIES = [
  'All',
  'SUV',
  'Sedan',
  'Luxury Sedan',
  'Luxury SUV',
  'Electric Vehicle',
  'Hybrid',
  'MUV',
  'Sports Car',
  'Convertible',
  'Hatchback',
];

const TRANSMISSIONS = ['All', 'Automatic', 'Manual'];
const FUELS = ['All', 'Petrol', 'Diesel', 'Electric', 'Hybrid', 'CNG'];
const LOCATIONS = ['All', 'Delhi', 'Mumbai', 'Bangalore'];

export const ExploreCars: React.FC = () => {
  const { vehicles, fetchVehicles, filters, setFilters, resetFilters, getFilteredVehicles, isLoading } =
    useVehicleStore();

  useEffect(() => {
    if (vehicles.length === 0) {
      fetchVehicles();
    }
  }, [vehicles.length, fetchVehicles]);

  const filtered = getFilteredVehicles();

  return (
    <div className="min-h-screen bg-background py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <span className="text-xs font-bold text-primary-accent uppercase tracking-widest">
            Aura Marketplace
          </span>
          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight mt-1">
            Explore All Vehicles
          </h1>
          <p className="text-xs text-gray-400 mt-2">
            Browse our complete fleet of 120 verified vehicles across 10 distinct categories.
          </p>
        </div>

        {/* Top Controls Bar */}
        <div className="mb-8 flex flex-col md:flex-row gap-4 items-center justify-between rounded-2xl border border-surface-border bg-surface p-4 shadow-xl">
          {/* Search Input */}
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by model, brand, or category..."
              value={filters.search}
              onChange={(e) => setFilters({ search: e.target.value })}
              className="w-full rounded-xl bg-background border border-surface-border pl-10 pr-4 py-2.5 text-xs text-white placeholder-gray-500 outline-none focus:border-primary"
            />
          </div>

          {/* Sort Selector */}
          <div className="flex items-center gap-2 w-full md:w-auto">
            <span className="text-xs text-gray-400 whitespace-nowrap">Sort By:</span>
            <select
              value={filters.sort}
              onChange={(e) => setFilters({ sort: e.target.value as any })}
              className="rounded-xl bg-background border border-surface-border px-3 py-2 text-xs text-white outline-none cursor-pointer"
            >
              <option value="relevance">Relevance</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="rating">Customer Rating</option>
              <option value="year">Newest Model Year</option>
            </select>
          </div>
        </div>

        {/* Main Content Layout (Sidebar Filters + Vehicle Grid) */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Filters */}
          <aside className="lg:col-span-1 space-y-6 rounded-2xl border border-surface-border bg-surface p-5 h-fit shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="w-4 h-4 text-cyan-400" />
                <h3 className="text-sm font-bold text-white uppercase tracking-wider">Filters</h3>
              </div>
              <button
                type="button"
                onClick={resetFilters}
                className="flex items-center gap-1 text-[11px] font-semibold text-gray-400 hover:text-white transition-colors"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset</span>
              </button>
            </div>

            {/* Category Filter */}
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">
                Category
              </label>
              <select
                value={filters.category}
                onChange={(e) => setFilters({ category: e.target.value === 'All' ? '' : e.target.value })}
                className="w-full rounded-xl bg-background border border-surface-border px-3 py-2.5 text-xs text-white outline-none cursor-pointer"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            {/* Transmission Filter */}
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">
                Transmission
              </label>
              <div className="grid grid-cols-3 gap-1.5">
                {TRANSMISSIONS.map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setFilters({ transmission: t === 'All' ? '' : t.toLowerCase() })}
                    className={`rounded-lg px-2 py-1.5 text-xs font-semibold border transition-all ${
                      (filters.transmission === '' && t === 'All') ||
                      filters.transmission.toLowerCase() === t.toLowerCase()
                        ? 'bg-primary border-primary text-white'
                        : 'bg-background border-surface-border text-gray-400 hover:text-white'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>

            {/* Fuel Type */}
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">
                Fuel Type
              </label>
              <select
                value={filters.fuelType}
                onChange={(e) => setFilters({ fuelType: e.target.value === 'All' ? '' : e.target.value.toLowerCase() })}
                className="w-full rounded-xl bg-background border border-surface-border px-3 py-2.5 text-xs text-white outline-none cursor-pointer"
              >
                {FUELS.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </select>
            </div>

            {/* Location */}
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block">
                City / Location
              </label>
              <select
                value={filters.location}
                onChange={(e) => setFilters({ location: e.target.value === 'All' ? '' : e.target.value })}
                className="w-full rounded-xl bg-background border border-surface-border px-3 py-2.5 text-xs text-white outline-none cursor-pointer"
              >
                {LOCATIONS.map((l) => (
                  <option key={l} value={l}>
                    {l}
                  </option>
                ))}
              </select>
            </div>
          </aside>

          {/* Vehicle Cards Grid */}
          <main className="lg:col-span-3">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs text-gray-400">
                Showing <span className="font-bold text-white">{filtered.length}</span> matching vehicles
              </p>
            </div>

            {filtered.length === 0 ? (
              <div className="rounded-2xl border border-surface-border bg-surface p-12 text-center">
                <Car className="w-12 h-12 text-gray-600 mx-auto mb-3" />
                <h3 className="text-base font-bold text-white">No vehicles match these specific filters</h3>
                <p className="text-xs text-gray-400 mt-1 max-w-sm mx-auto">
                  Try clearing or relaxing your filters, or ask our AI consultant to find alternative options.
                </p>
                <button
                  type="button"
                  onClick={resetFilters}
                  className="mt-4 rounded-xl bg-primary px-5 py-2 text-xs font-bold text-white uppercase tracking-wider"
                >
                  Reset All Filters
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filtered.map((car) => (
                  <VehicleCard key={car.id} vehicle={car} priorityIntent={filters.intent} />
                ))}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

