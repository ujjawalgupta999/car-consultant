import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Vehicle } from '../types';
import { useComparisonStore } from '../store/comparisonStore';
import { useAuthStore } from '../store/authStore';
import { useConsultantStore } from '../store/consultantStore';
import { Gauge, Fuel, Users, Star, Heart, Scale, Sparkles, ArrowRight, ShieldCheck } from 'lucide-react';

interface VehicleCardProps {
  vehicle: Vehicle;
  priorityIntent?: 'rent' | 'buy' | 'all';
}

export const VehicleCard: React.FC<VehicleCardProps> = ({ vehicle, priorityIntent = 'all' }) => {
  const navigate = useNavigate();
  const { addVehicle, removeVehicle, hasVehicle } = useComparisonStore();
  const { isSaved, toggleSaved } = useAuthStore();
  const { setIsOpen, addMessage, setActiveContext } = useConsultantStore();

  const isCompared = hasVehicle(vehicle.id);
  const isFavorite = isSaved(vehicle.id);

  const handleToggleCompare = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (isCompared) {
      removeVehicle(vehicle.id);
    } else {
      addVehicle(vehicle);
    }
  };

  const handleAskAI = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setActiveContext({
      currentRoute: `/vehicles/${vehicle.id}`,
      vehicleId: vehicle.id,
      vehicleName: `${vehicle.brand} ${vehicle.model}`,
    });
    addMessage({
      id: `msg_ai_q_${Date.now()}`,
      role: 'user',
      content: `Tell me about the ${vehicle.year} ${vehicle.brand} ${vehicle.model}. What are its main strengths and is it good for daily driving?`,
      timestamp: new Date().toISOString(),
    });
    setIsOpen(true);
  };

  return (
    <div className="group relative flex flex-col overflow-hidden rounded-2xl border border-surface-border bg-surface shadow-xl transition-all duration-300 hover:-translate-y-1 hover:border-primary/50 hover:shadow-2xl">
      {/* Thumbnail with overlay badges */}
      <div className="relative aspect-[16/10] w-full overflow-hidden bg-background">
        <img
          src={vehicle.image_url || 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80'}
          alt={`${vehicle.brand} ${vehicle.model}`}
          className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-surface via-transparent to-transparent opacity-80" />

        {/* Category Pill */}
        <div className="absolute top-3 left-3 flex items-center gap-1.5 rounded-full bg-background/80 backdrop-blur-md px-2.5 py-1 text-[11px] font-bold text-white border border-white/10 uppercase tracking-wider">
          {vehicle.category}
        </div>

        {/* Favorite & Compare Quick Icons */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5">
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              toggleSaved(vehicle.id);
            }}
            title={isFavorite ? 'Remove from Saved' : 'Save Vehicle'}
            className={`flex h-8 w-8 items-center justify-center rounded-full backdrop-blur-md transition-all ${
              isFavorite
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                : 'bg-background/70 text-gray-400 hover:text-white border border-white/10'
            }`}
          >
            <Heart className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />
          </button>
        </div>

        {/* Year and Rating */}
        <div className="absolute bottom-3 left-3 flex items-center gap-2 text-xs">
          <span className="font-mono text-gray-300">{vehicle.year}</span>
          <span className="text-gray-500">•</span>
          <div className="flex items-center gap-1 text-amber-400 font-bold">
            <Star className="w-3.5 h-3.5 fill-current" />
            <span>{vehicle.rating.toFixed(1)}</span>
            <span className="text-gray-400 font-normal">({vehicle.review_count})</span>
          </div>
        </div>
      </div>

      {/* Body Details */}
      <div className="flex flex-1 flex-col p-4 sm:p-5">
        <div className="mb-3">
          <h3 className="text-base font-bold text-white group-hover:text-primary-accent transition-colors">
            {vehicle.brand} {vehicle.model}
          </h3>
          <p className="text-xs text-gray-400 mt-0.5">{vehicle.location} • {vehicle.condition.toUpperCase()}</p>
        </div>

        {/* Specs Pill Strip */}
        <div className="grid grid-cols-3 gap-2 py-2.5 my-2 border-y border-surface-border/60 text-xs text-gray-300">
          <div className="flex items-center gap-1.5">
            <Gauge className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
            <span className="truncate">{vehicle.transmission}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Fuel className="w-3.5 h-3.5 text-amber-400 shrink-0" />
            <span className="truncate capitalize">{vehicle.fuel_type}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-primary-accent shrink-0" />
            <span>{vehicle.seats} Seats</span>
          </div>
        </div>

        {/* Price Section */}
        <div className="mt-auto pt-3">
          <div className="flex items-end justify-between mb-3">
            <div>
              <div className="text-[10px] text-gray-400 uppercase tracking-wider">
                {priorityIntent === 'buy' ? 'Ex-Showroom Price' : 'Daily Rental'}
              </div>
              <div className="text-lg font-black text-white">
                {priorityIntent === 'buy'
                  ? `₹${(vehicle.purchase_price).toLocaleString('en-IN')}`
                  : `₹${(vehicle.rental_price_per_day).toLocaleString('en-IN')} / day`}
              </div>
            </div>

            {priorityIntent === 'all' && (
              <div className="text-right">
                <div className="text-[10px] text-gray-400 uppercase tracking-wider">Buy At</div>
                <div className="text-xs font-bold text-gray-200">
                  ₹{(vehicle.purchase_price / 100000).toFixed(1)} Lakh
                </div>
              </div>
            )}
          </div>

          {/* Action Row */}
          <div className="flex items-center gap-2">
            <Link
              to={`/vehicles/${vehicle.id}`}
              className="flex-1 flex items-center justify-center gap-1.5 rounded-xl bg-surface-muted hover:bg-surface-hover border border-surface-border px-3 py-2 text-xs font-semibold text-white transition-all"
            >
              <span>Details</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

            <button
              type="button"
              onClick={handleToggleCompare}
              title={isCompared ? 'Remove from Compare' : 'Add to Compare'}
              className={`flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold border transition-all ${
                isCompared
                  ? 'bg-primary/20 border-primary text-primary-accent'
                  : 'bg-surface-muted border-surface-border text-gray-400 hover:text-white'
              }`}
            >
              <Scale className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{isCompared ? 'Added' : 'Compare'}</span>
            </button>

            <button
              type="button"
              onClick={handleAskAI}
              title="Ask AI about this car"
              className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 hover:bg-cyan-500/20 transition-all"
            >
              <Sparkles className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

