import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useVehicleStore } from '../store/vehicleStore';
import { useComparisonStore } from '../store/comparisonStore';
import { useConsultantStore } from '../store/consultantStore';
import { useAuthStore } from '../store/authStore';
import { VehicleCard } from '../components/VehicleCard';
import { EMICalculator } from '../components/EMICalculator';
import {
  Car,
  Star,
  Gauge,
  Fuel,
  Users,
  Calendar,
  MapPin,
  Scale,
  Sparkles,
  Heart,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  Zap,
  Tag
} from 'lucide-react';

export const VehicleDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { vehicles, fetchVehicles, getVehicleById } = useVehicleStore();
  const { addVehicle, removeVehicle, hasVehicle } = useComparisonStore();
  const { isSaved, toggleSaved } = useAuthStore();
  const { setIsOpen, addMessage, setActiveContext, setActiveMcpApp } = useConsultantStore();

  const [activeImage, setActiveImage] = useState<string>('');

  useEffect(() => {
    if (vehicles.length === 0) {
      fetchVehicles();
    }
  }, [vehicles.length, fetchVehicles]);

  const vehicle = id ? getVehicleById(id) : undefined;

  useEffect(() => {
    if (vehicle) {
      setActiveImage(vehicle.image_url || 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=1200&q=80');
      // Synchronize active context with AI consultant
      setActiveContext({
        currentRoute: `/vehicles/${vehicle.id}`,
        vehicleId: vehicle.id,
        vehicleName: `${vehicle.brand} ${vehicle.model}`,
      });
    }
  }, [vehicle, setActiveContext]);

  if (!vehicle) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
        <Car className="w-12 h-12 text-gray-500 mb-3 animate-spin" />
        <h2 className="text-xl font-bold text-white">Loading Vehicle Profile...</h2>
        <p className="text-xs text-gray-400 mt-1">Retrieving authoritative records from marketplace database.</p>
      </div>
    );
  }

  const isCompared = hasVehicle(vehicle.id);
  const isFavorite = isSaved(vehicle.id);

  const handleAskAIAboutCar = () => {
    addMessage({
      id: `msg_details_q_${Date.now()}`,
      role: 'user',
      content: `Give me an honest review of the ${vehicle.year} ${vehicle.brand} ${vehicle.model}. What are the trade-offs and is the ₹${vehicle.rental_price_per_day}/day rental rate worth it?`,
      timestamp: new Date().toISOString(),
    });
    setIsOpen(true);
  };

  const handleStartBookingMCP = () => {
    setActiveMcpApp({
      name: 'booking',
      context: {
        sessionId: 'sess_default',
        vehicle: vehicle,
        vehicleId: vehicle.id,
        intent: 'rent',
      },
    });
    setIsOpen(true);
  };

  const handleStartPurchaseMCP = () => {
    setActiveMcpApp({
      name: 'booking',
      context: {
        sessionId: 'sess_default',
        vehicle: vehicle,
        vehicleId: vehicle.id,
        intent: 'buy',
      },
    });
    setIsOpen(true);
  };

  const similarCars = vehicles.filter((v) => v.category === vehicle.category && v.id !== vehicle.id).slice(0, 3);

  return (
    <div className="min-h-screen bg-background py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb Navigation */}
        <div className="flex items-center gap-2 text-xs text-gray-400 mb-6">
          <Link to="/" className="hover:text-white transition-colors">Home</Link>
          <span>/</span>
          <Link to="/explore" className="hover:text-white transition-colors">Explore</Link>
          <span>/</span>
          <span className="text-gray-200">{vehicle.brand}</span>
          <span>/</span>
          <span className="text-primary-accent font-semibold">{vehicle.model}</span>
        </div>

        {/* Hero Gallery & Quick Purchase Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {/* Main Gallery (2 Cols) */}
          <div className="lg:col-span-2 space-y-4">
            <div className="relative aspect-[16/10] w-full overflow-hidden rounded-2xl border border-surface-border bg-surface shadow-2xl">
              <img
                src={activeImage}
                alt={`${vehicle.brand} ${vehicle.model}`}
                className="h-full w-full object-cover"
              />
              <div className="absolute top-4 left-4 flex gap-2">
                <span className="rounded-full bg-background/80 backdrop-blur-md px-3 py-1 text-xs font-bold text-white border border-white/10 uppercase tracking-wider">
                  {vehicle.category}
                </span>
                <span className="rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 px-3 py-1 text-xs font-bold uppercase tracking-wider">
                  {vehicle.condition}
                </span>
              </div>
            </div>

            {/* Gallery Thumbnails */}
            <div className="flex gap-3 overflow-x-auto pb-2">
              {[
                vehicle.image_url,
                'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=400&q=80',
                'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=400&q=80',
                'https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=400&q=80'
              ].map((img, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => img && setActiveImage(img)}
                  className={`relative aspect-[16/10] w-24 shrink-0 overflow-hidden rounded-xl border transition-all ${
                    activeImage === img ? 'border-primary ring-2 ring-primary/40' : 'border-surface-border opacity-70 hover:opacity-100'
                  }`}
                >
                  <img src={img || ''} alt="Thumbnail" className="h-full w-full object-cover" />
                </button>
              ))}
            </div>
          </div>

          {/* Pricing & Decision Card (1 Col) */}
          <div className="rounded-2xl border border-surface-border bg-surface p-6 shadow-2xl flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                  {vehicle.brand}
                </span>
                <div className="flex items-center gap-1 text-amber-400 text-xs font-bold">
                  <Star className="w-3.5 h-3.5 fill-current" />
                  <span>{vehicle.rating.toFixed(1)}</span>
                  <span className="text-gray-400 font-normal">({vehicle.review_count} reviews)</span>
                </div>
              </div>

              <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight mb-2">
                {vehicle.model} ({vehicle.year})
              </h1>
              <p className="text-xs text-gray-400 mb-6 flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-primary-accent" />
                <span>Stationed in {vehicle.location} • Verified Clean Inspection</span>
              </p>

              {/* Dual Rates Breakdown */}
              <div className="space-y-4 rounded-xl bg-background/60 border border-surface-border p-4 mb-6">
                <div>
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">
                    Self-Drive Rental Rate
                  </div>
                  <div className="text-2xl font-black text-cyan-400">
                    ₹{vehicle.rental_price_per_day.toLocaleString('en-IN')}{' '}
                    <span className="text-xs text-gray-400 font-normal">/ day (GST incl)</span>
                  </div>
                </div>

                <div className="pt-3 border-t border-surface-border/60">
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider font-semibold">
                    Ex-Showroom Purchase Price
                  </div>
                  <div className="text-2xl font-black text-white">
                    ₹{vehicle.purchase_price.toLocaleString('en-IN')}
                  </div>
                  <div className="text-[11px] text-emerald-400 mt-0.5">
                    Estimated EMI starting at ₹{Math.round((vehicle.purchase_price * 0.8 * 0.095) / 12).toLocaleString('en-IN')}/mo
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="space-y-3">
                <button
                  type="button"
                  onClick={handleStartBookingMCP}
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-cyan-500 py-3 text-xs font-bold text-white uppercase tracking-wider shadow-lg hover:opacity-95 transition-all active:scale-95"
                >
                  <Zap className="w-4 h-4" />
                  <span>Rent This Car (MCP App)</span>
                </button>

                <button
                  type="button"
                  onClick={handleStartPurchaseMCP}
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-surface-muted hover:bg-surface-hover border border-surface-border py-3 text-xs font-bold text-white uppercase tracking-wider transition-all"
                >
                  <Tag className="w-4 h-4" />
                  <span>Reserve to Purchase (₹25k Token)</span>
                </button>

                <div className="flex gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => (isCompared ? removeVehicle(vehicle.id) : addVehicle(vehicle))}
                    className={`flex-1 flex items-center justify-center gap-2 rounded-xl border py-2.5 text-xs font-semibold transition-all ${
                      isCompared
                        ? 'bg-primary/20 border-primary text-primary-accent'
                        : 'border-surface-border bg-surface-muted text-gray-300 hover:text-white'
                    }`}
                  >
                    <Scale className="w-3.5 h-3.5" />
                    <span>{isCompared ? 'In Compare List' : 'Add to Compare'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => toggleSaved(vehicle.id)}
                    className={`flex h-10 w-10 items-center justify-center rounded-xl border transition-all ${
                      isFavorite
                        ? 'bg-rose-500/20 border-rose-500/40 text-rose-400'
                        : 'border-surface-border bg-surface-muted text-gray-400 hover:text-white'
                    }`}
                  >
                    <Heart className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`} />
                  </button>
                </div>
              </div>
            </div>

            {/* AI Advisor Card Trigger */}
            <div className="mt-6 pt-4 border-t border-surface-border/60">
              <button
                type="button"
                onClick={handleAskAIAboutCar}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 py-2.5 text-xs font-bold text-cyan-400 hover:bg-cyan-500/20 transition-all"
              >
                <Sparkles className="w-4 h-4" />
                <span>Ask AI About This Car</span>
              </button>
            </div>
          </div>
        </div>

        {/* Specifications & Features Tabs/Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {/* Tech Specs Table (2 Cols) */}
          <div className="lg:col-span-2 rounded-2xl border border-surface-border bg-surface p-6 shadow-xl">
            <h3 className="text-base font-bold text-white uppercase tracking-wider mb-4 border-b border-surface-border/60 pb-3">
              Technical Specifications & Metrics
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-3 rounded-xl bg-background/50 border border-surface-border">
                <span className="text-gray-400 block mb-1">Transmission</span>
                <span className="font-bold text-white capitalize">{vehicle.transmission}</span>
              </div>
              <div className="p-3 rounded-xl bg-background/50 border border-surface-border">
                <span className="text-gray-400 block mb-1">Powertrain</span>
                <span className="font-bold text-white capitalize">{vehicle.fuel_type}</span>
              </div>
              <div className="p-3 rounded-xl bg-background/50 border border-surface-border">
                <span className="text-gray-400 block mb-1">Seating</span>
                <span className="font-bold text-white">{vehicle.seats} Passengers</span>
              </div>
              <div className="p-3 rounded-xl bg-background/50 border border-surface-border">
                <span className="text-gray-400 block mb-1">Odometer</span>
                <span className="font-bold text-white">{vehicle.odometer_km.toLocaleString('en-IN')} KM</span>
              </div>
              <div className="p-3 rounded-xl bg-background/50 border border-surface-border">
                <span className="text-gray-400 block mb-1">Mileage / Range</span>
                <span className="font-bold text-white">
                  {vehicle.fuel_type === 'electric' ? `${vehicle.range_km || 450} KM Range` : `${vehicle.mileage_kmpl || 16.5} KMPL`}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-background/50 border border-surface-border">
                <span className="text-gray-400 block mb-1">Warranty</span>
                <span className="font-bold text-emerald-400">1-Year Aura Comprehensive</span>
              </div>
            </div>

            {/* Features Pill Tags */}
            <div className="mt-6 pt-6 border-t border-surface-border/60">
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">
                Key Standard Equipment & Features
              </h4>
              <div className="flex flex-wrap gap-2">
                {vehicle.features.map((feat, idx) => (
                  <span
                    key={idx}
                    className="flex items-center gap-1.5 rounded-lg border border-surface-border bg-background px-3 py-1.5 text-xs text-gray-200"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>{feat}</span>
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Interactive EMI Calculator (1 Col) */}
          <div className="lg:col-span-1">
            <EMICalculator vehiclePrice={vehicle.purchase_price} />
          </div>
        </div>

        {/* Similar Vehicles Carousel */}
        {similarCars.length > 0 && (
          <div className="mt-16">
            <h3 className="text-xl font-bold text-white tracking-tight mb-6">
              Similar Vehicles in {vehicle.category}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {similarCars.map((car) => (
                <VehicleCard key={car.id} vehicle={car} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

