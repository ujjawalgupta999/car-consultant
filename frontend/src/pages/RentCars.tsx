import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useVehicleStore } from '../store/vehicleStore';
import { useConsultantStore } from '../store/consultantStore';
import { VehicleCard } from '../components/VehicleCard';
import { Calendar, MapPin, Search, ShieldCheck, Zap, SlidersHorizontal } from 'lucide-react';

export const RentCars: React.FC = () => {
  const navigate = useNavigate();
  const { vehicles, fetchVehicles, filters, setFilters, getFilteredVehicles } = useVehicleStore();
  const { setIsOpen, setActiveMcpApp, addMessage } = useConsultantStore();

  const [pickupCity, setPickupCity] = useState(filters.location || 'Delhi');
  const [pickupDate, setPickupDate] = useState('2026-12-15');
  const [returnDate, setReturnDate] = useState('2026-12-20');
  const [category, setCategory] = useState(filters.category || '');
  const [dailyBudget, setDailyBudget] = useState(filters.maxPrice < 50000 ? filters.maxPrice : 15000);

  useEffect(() => {
    setFilters({ intent: 'rent' });
    if (vehicles.length === 0) {
      fetchVehicles();
    }
  }, [vehicles.length, fetchVehicles, setFilters]);

  // Synchronize with external AI Consultant filter actions
  useEffect(() => {
    if (filters.category !== undefined) setCategory(filters.category);
    if (filters.location) setPickupCity(filters.location);
    if (filters.maxPrice && filters.maxPrice < 50000) setDailyBudget(filters.maxPrice);
  }, [filters.category, filters.location, filters.maxPrice]);

  const handleApplyRentalSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setFilters({
      intent: 'rent',
      location: pickupCity,
      category: category,
      maxPrice: dailyBudget,
    });
  };

  const handleCategoryChange = (newCat: string) => {
    setCategory(newCat);
    setFilters({
      intent: 'rent',
      category: newCat,
    });
  };

  const rentalListings = getFilteredVehicles().filter((v) => v.available_for_rent);

  return (
    <div className="min-h-screen bg-background py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Banner Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Zap className="w-3.5 h-3.5" /> Self-Drive Rentals
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight">
            Rent a Verified Luxury Vehicle
          </h1>
          <p className="text-xs text-gray-400 mt-2">
            Transparent daily rates, inclusive GST, zero hidden fees, and doorstep delivery across Delhi NCR, Mumbai, and Bangalore.
          </p>
        </div>

        {/* Rental Filter Bar */}
        <div className="mb-10 rounded-2xl border border-surface-border bg-surface p-5 shadow-2xl">
          <form onSubmit={handleApplyRentalSearch} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div>
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                Pickup City
              </label>
              <div className="flex items-center gap-2 rounded-xl bg-background border border-surface-border px-3 py-2.5">
                <MapPin className="w-4 h-4 text-primary-accent shrink-0" />
                <select
                  value={pickupCity}
                  onChange={(e) => setPickupCity(e.target.value)}
                  className="w-full bg-transparent text-xs text-white outline-none cursor-pointer"
                >
                  <option value="Delhi" className="bg-surface">Delhi NCR</option>
                  <option value="Mumbai" className="bg-surface">Mumbai</option>
                  <option value="Bangalore" className="bg-surface">Bangalore</option>
                </select>
              </div>
            </div>

            <div>
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                Pickup Date
              </label>
              <div className="flex items-center gap-2 rounded-xl bg-background border border-surface-border px-3 py-2.5">
                <Calendar className="w-4 h-4 text-cyan-400 shrink-0" />
                <input
                  type="date"
                  value={pickupDate}
                  onChange={(e) => setPickupDate(e.target.value)}
                  className="w-full bg-transparent text-xs text-white outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                Return Date
              </label>
              <div className="flex items-center gap-2 rounded-xl bg-background border border-surface-border px-3 py-2.5">
                <Calendar className="w-4 h-4 text-cyan-400 shrink-0" />
                <input
                  type="date"
                  value={returnDate}
                  onChange={(e) => setReturnDate(e.target.value)}
                  className="w-full bg-transparent text-xs text-white outline-none"
                />
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

            <div className="flex items-end">
              <button
                type="submit"
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-cyan-500 py-3 text-xs font-bold text-white uppercase tracking-wider shadow-lg hover:opacity-95 transition-all active:scale-95"
              >
                <Search className="w-4 h-4" />
                <span>Search Rentals</span>
              </button>
            </div>
          </form>

          {/* Quick Rental Guarantee Strip */}
          <div className="mt-4 pt-4 border-t border-surface-border/60 flex flex-wrap items-center justify-between gap-4 text-xs text-gray-400">
            <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
              <ShieldCheck className="w-4 h-4" /> Comprehensive Zero-Deductible Insurance
            </span>
            <span>• Unlimited Kilometres on 3+ Days Bookings</span>
            <span>• Free Cancellation up to 24 Hours Before Pickup</span>
          </div>
        </div>

        {/* Results Header & Active Filters */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-6">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-xs text-gray-400">
              Found <span className="font-bold text-white">{rentalListings.length}</span> eligible self-drive rental vehicles
            </p>
            {filters.category && (
              <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 border border-cyan-500/40 text-cyan-400 text-xs font-semibold">
                Category: {filters.category}
              </span>
            )}
            {filters.seats && (
              <span className="px-2.5 py-0.5 rounded-full bg-primary/20 border border-primary/40 text-primary-accent text-xs font-semibold">
                {filters.seats}-Seater
              </span>
            )}
            {filters.fuelType && (
              <span className="px-2.5 py-0.5 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-400 text-xs font-semibold">
                {filters.fuelType}
              </span>
            )}
            {filters.transmission && (
              <span className="px-2.5 py-0.5 rounded-full bg-purple-500/20 border border-purple-500/40 text-purple-400 text-xs font-semibold">
                {filters.transmission}
              </span>
            )}
          </div>
          {(filters.category || filters.seats || filters.fuelType || filters.transmission) && (
            <button
              onClick={() => {
                setCategory('');
                setFilters({ category: '', seats: undefined, fuelType: '', transmission: '' });
              }}
              className="text-xs text-gray-400 hover:text-white underline cursor-pointer"
            >
              Clear AI Filters
            </button>
          )}
        </div>

        {/* Listings Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {rentalListings.map((car) => (
            <VehicleCard key={car.id} vehicle={car} priorityIntent="rent" />
          ))}
        </div>
      </div>
    </div>
  );
};

