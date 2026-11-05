import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useVehicleStore } from '../store/vehicleStore';
import { useConsultantStore } from '../store/consultantStore';
import { VehicleCard } from '../components/VehicleCard';
import {
  Car,
  Search,
  Sparkles,
  Shield,
  ArrowRight,
  Zap,
  Calendar,
  MapPin,
  ChevronRight,
  Award,
  CheckCircle2,
  Clock
} from 'lucide-react';

const CATEGORIES = [
  { name: 'SUV', image: 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=600&q=80', count: 20 },
  { name: 'Sedan', image: 'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?auto=format&fit=crop&w=600&q=80', count: 12 },
  { name: 'Luxury Sedan', image: 'https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=600&q=80', count: 11 },
  { name: 'Luxury SUV', image: 'https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?auto=format&fit=crop&w=600&q=80', count: 13 },
  { name: 'Electric Vehicle', image: 'https://images.unsplash.com/photo-1560958089-b8a1929cea89?auto=format&fit=crop&w=600&q=80', count: 12 },
  { name: 'Sports Car', image: 'https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=600&q=80', count: 11 },
  { name: 'Convertible', image: 'https://images.unsplash.com/photo-1508974239320-0a029497e820?auto=format&fit=crop&w=600&q=80', count: 10 },
  { name: 'Hybrid', image: 'https://images.unsplash.com/photo-1590362891991-f776e747a588?auto=format&fit=crop&w=600&q=80', count: 10 },
  { name: 'MUV', image: 'https://images.unsplash.com/photo-1502877338535-766e1452684a?auto=format&fit=crop&w=600&q=80', count: 12 },
  { name: 'Hatchback', image: 'https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?auto=format&fit=crop&w=600&q=80', count: 12 },
];

export const Home: React.FC = () => {
  const navigate = useNavigate();
  const { vehicles, fetchVehicles, setFilters } = useVehicleStore();
  const { setIsOpen, addMessage } = useConsultantStore();

  const [activeTab, setActiveTab] = useState<'rent' | 'buy'>('rent');
  const [searchLocation, setSearchLocation] = useState('Delhi');
  const [searchCategory, setSearchCategory] = useState('');

  useEffect(() => {
    if (vehicles.length === 0) {
      fetchVehicles();
    }
  }, [vehicles.length, fetchVehicles]);

  const handleHeroSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setFilters({
      intent: activeTab,
      location: searchLocation,
      category: searchCategory,
    });
    navigate(activeTab === 'rent' ? '/rent' : '/buy');
  };

  const handleAskAIPrompt = (prompt: string) => {
    addMessage({
      id: `msg_prompt_${Date.now()}`,
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString(),
    });
    setIsOpen(true);
  };

  const featuredCars = vehicles.slice(0, 6);

  return (
    <div className="flex flex-col min-h-screen bg-background">
      {/* 1. Cinematic Hero Section */}
      <section className="relative min-h-[85vh] flex items-center justify-center overflow-hidden border-b border-surface-border">
        {/* Background Image with Cinematic Overlays */}
        <div className="absolute inset-0 z-0">
          <img
            src="https://images.unsplash.com/photo-1617788138017-80ad40651399?auto=format&fit=crop&w=2000&q=90"
            alt="Luxury Automotive Hero"
            className="h-full w-full object-cover object-center filter brightness-[0.4] scale-105 animate-pulse duration-1000"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-black/60" />
        </div>

        {/* Content Container */}
        <div className="relative z-10 mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8 text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 backdrop-blur-md text-xs font-bold tracking-widest text-cyan-300 uppercase mb-6 shadow-2xl">
            <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
            Amulate Summer Hackathon 2026 Premiere
          </div>

          {/* Headline */}
          <h1 className="text-4xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white uppercase font-sans max-w-4xl mx-auto leading-none">
            The Future of Driving,{' '}
            <span className="bg-gradient-to-r from-primary-accent via-cyan-400 to-white bg-clip-text text-transparent">
              Found by Intelligence.
            </span>
          </h1>

          <p className="mt-6 text-base sm:text-lg text-gray-300 max-w-2xl mx-auto font-normal leading-relaxed">
            Discover, rent, or purchase verified luxury and performance vehicles. 
            Powered by our deep conversational AI consultant that dynamically curates your drive.
          </p>

          {/* Tabbed Search Interface */}
          <div className="mt-10 mx-auto max-w-3xl rounded-2xl border border-surface-border bg-surface/90 backdrop-blur-xl p-4 sm:p-5 shadow-2xl text-left">
            {/* Rent vs Buy Tabs */}
            <div className="flex gap-2 border-b border-surface-border/80 pb-3 mb-4">
              <button
                type="button"
                onClick={() => setActiveTab('rent')}
                className={`rounded-xl px-5 py-2 text-xs font-bold uppercase tracking-wider transition-all ${
                  activeTab === 'rent'
                    ? 'bg-primary text-white shadow-lg shadow-primary/25'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                🚗 Rent a Vehicle
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('buy')}
                className={`rounded-xl px-5 py-2 text-xs font-bold uppercase tracking-wider transition-all ${
                  activeTab === 'buy'
                    ? 'bg-primary text-white shadow-lg shadow-primary/25'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                🏷️ Buy a Vehicle
              </button>
            </div>

            {/* Form Fields */}
            <form onSubmit={handleHeroSearch} className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                  Location / City
                </label>
                <div className="flex items-center gap-2 rounded-xl bg-background border border-surface-border px-3 py-2.5">
                  <MapPin className="w-4 h-4 text-primary-accent" />
                  <select
                    value={searchLocation}
                    onChange={(e) => setSearchLocation(e.target.value)}
                    className="w-full bg-transparent text-xs text-white outline-none cursor-pointer"
                  >
                    <option value="Delhi" className="bg-surface">Delhi NCR</option>
                    <option value="Mumbai" className="bg-surface">Mumbai</option>
                    <option value="Bangalore" className="bg-surface">Bangalore</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
                  Vehicle Category
                </label>
                <div className="flex items-center gap-2 rounded-xl bg-background border border-surface-border px-3 py-2.5">
                  <Car className="w-4 h-4 text-cyan-400" />
                  <select
                    value={searchCategory}
                    onChange={(e) => setSearchCategory(e.target.value)}
                    className="w-full bg-transparent text-xs text-white outline-none cursor-pointer"
                  >
                    <option value="" className="bg-surface">All Categories</option>
                    <option value="SUV" className="bg-surface">SUV</option>
                    <option value="Sedan" className="bg-surface">Sedan</option>
                    <option value="Luxury SUV" className="bg-surface">Luxury SUV</option>
                    <option value="Luxury Sedan" className="bg-surface">Luxury Sedan</option>
                    <option value="Electric Vehicle" className="bg-surface">Electric Vehicle (EV)</option>
                    <option value="Sports Car" className="bg-surface">Sports Car</option>
                    <option value="Convertible" className="bg-surface">Convertible</option>
                  </select>
                </div>
              </div>

              <div className="flex items-end">
                <button
                  type="submit"
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-cyan-500 py-3 text-xs font-bold text-white uppercase tracking-wider shadow-lg hover:opacity-95 transition-all active:scale-95"
                >
                  <Search className="w-4 h-4" />
                  <span>Find My Vehicle</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>

      {/* 2. Featured Vehicles Section */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10">
          <div>
            <span className="text-xs font-bold text-primary-accent uppercase tracking-widest">
              Curated Selection
            </span>
            <h2 className="text-2xl sm:text-4xl font-extrabold text-white mt-1 tracking-tight">
              Featured Inventory Spotlight
            </h2>
          </div>
          <Link
            to="/explore"
            className="mt-4 md:mt-0 inline-flex items-center gap-2 text-xs font-bold text-cyan-400 hover:text-cyan-300 uppercase tracking-wider"
          >
            <span>Explore All 120 Vehicles</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featuredCars.map((car) => (
            <VehicleCard key={car.id} vehicle={car} />
          ))}
        </div>
      </section>

      {/* 3. Explore by 10 Categories */}
      <section className="py-16 bg-surface border-y border-surface-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <span className="text-xs font-bold text-cyan-400 uppercase tracking-widest">
              Automotive Diversity
            </span>
            <h2 className="text-2xl sm:text-4xl font-extrabold text-white mt-1">
              Explore by Vehicle Class
            </h2>
            <p className="text-xs text-gray-400 mt-2">
              Every category features at least 10 world-renowned brands with guaranteed availability.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
            {CATEGORIES.map((cat) => (
              <div
                key={cat.name}
                onClick={() => {
                  setFilters({ category: cat.name });
                  navigate('/explore');
                }}
                className="group relative cursor-pointer overflow-hidden rounded-xl border border-surface-border bg-background aspect-[4/3] transition-all hover:border-primary/60 hover:-translate-y-1 shadow-lg"
              >
                <img
                  src={cat.image}
                  alt={cat.name}
                  className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background via-background/40 to-transparent" />
                <div className="absolute bottom-3 left-3 right-3">
                  <h4 className="text-xs font-bold text-white group-hover:text-primary-accent transition-colors">
                    {cat.name}
                  </h4>
                  <p className="text-[10px] text-gray-400">{cat.count}+ Models</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. AI Consultant Promotional Banner */}
      <section className="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
        <div className="relative overflow-hidden rounded-3xl border border-primary/40 bg-gradient-to-br from-surface via-background to-surface p-8 sm:p-12 shadow-2xl">
          <div className="relative z-10 max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-cyan-500/10 border border-cyan-500/30 px-3 py-1 text-xs font-bold text-cyan-400 uppercase tracking-widest mb-4">
              <Sparkles className="w-3.5 h-3.5" /> Generative UI & MCP Apps
            </div>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight leading-tight">
              Meet Your Personal Automotive Strategist
            </h2>
            <p className="mt-4 text-sm text-gray-300 leading-relaxed">
              Don't browse menus — talk naturally. Tell our AI consultant your budget, city, passenger count, and preferred body style. 
              Watch the website automatically navigate, apply filters, compare options, and launch booking forms right in your conversation.
            </p>

            <div className="mt-6 flex flex-wrap gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleAskAIPrompt("I need an automatic SUV in Delhi for five days starting 15 December 2026. My budget is ₹3,000 per day.")}
                className="rounded-full border border-surface-border bg-surface px-3 py-1.5 text-gray-300 hover:border-cyan-400 hover:text-white transition-all"
              >
                🚗 Try Scenario A: Rental in Delhi
              </button>
              <button
                type="button"
                onClick={() => handleAskAIPrompt("I want to buy a used automatic SUV in Delhi with a maximum budget of ₹15 lakh.")}
                className="rounded-full border border-surface-border bg-surface px-3 py-1.5 text-gray-300 hover:border-cyan-400 hover:text-white transition-all"
              >
                🏷️ Try Scenario B: Used SUV ₹15L
              </button>
              <button
                type="button"
                onClick={() => handleAskAIPrompt("Compare the two best options for family trips.")}
                className="rounded-full border border-surface-border bg-surface px-3 py-1.5 text-gray-300 hover:border-cyan-400 hover:text-white transition-all"
              >
                ⚖️ Try Scenario C: Compare Best Cars
              </button>
            </div>

            <div className="mt-8 flex items-center gap-4">
              <button
                type="button"
                onClick={() => setIsOpen(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-cyan-500 px-6 py-3 text-xs font-bold text-white uppercase tracking-wider shadow-lg hover:opacity-95 transition-all active:scale-95"
              >
                <Sparkles className="w-4 h-4" />
                <span>Launch AI Consultant</span>
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 5. Why Choose Aura Motors */}
      <section className="py-16 bg-surface border-t border-surface-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="space-y-3 p-6 rounded-2xl border border-surface-border bg-background/50">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <Shield className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">100% Truthful Marketplace</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                No phantom discounts or fabricated availability. Every vehicle, rental interval, and ex-showroom price is authoritatively verified.
              </p>
            </div>

            <div className="space-y-3 p-6 rounded-2xl border border-surface-border bg-background/50">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary-accent border border-primary/30">
                <Award className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Embedded MCP Apps</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Experience protocol-compliant Model Context Protocol mini-apps for driver booking and checkout directly in chat without external redirects.
              </p>
            </div>

            <div className="space-y-3 p-6 rounded-2xl border border-surface-border bg-background/50">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                <Clock className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold text-white">Transparent 0–100 Ranking</h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Every AI recommendation comes with an explicit score breakdown, highlighting positives and genuine compromises before you commit.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
