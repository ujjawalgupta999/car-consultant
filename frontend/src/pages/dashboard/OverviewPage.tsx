import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShoppingBag,
  Calendar,
  Car,
  ListOrdered,
  TrendingUp,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  PlusCircle,
  Clock,
} from 'lucide-react';

interface SummaryData {
  total_purchases: number;
  total_rentals: number;
  active_rentals: number;
  vehicles_owned: number;
  active_selling_listings: number;
  total_spent_inr: number;
  portfolio_valuation_inr: number;
}

export const OverviewPage: React.FC = () => {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<SummaryData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setIsLoading(true);
        const res = await fetch('/api/dashboard/summary');
        if (!res.ok) throw new Error('Failed to load dashboard metrics');
        const data = await res.json();
        setSummary(data.summary);
      } catch (err: any) {
        setError(err.message || 'Error fetching metrics');
      } finally {
        setIsLoading(false);
      }
    };
    fetchSummary();
  }, []);

  const formatPrice = (val?: number) => {
    if (!val || val === 0) return '₹0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakh`;
    return `₹${val.toLocaleString('en-IN')}`;
  };

  return (
    <div className="space-y-6">
      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Purchases Stat */}
        <div
          onClick={() => navigate('/dashboard/purchases')}
          className="cursor-pointer bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-5 transition-all shadow-xl group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">My Purchases</span>
            <div className="w-8 h-8 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center group-hover:scale-110 transition-transform">
              <ShoppingBag className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">
            {isLoading ? '...' : summary?.total_purchases ?? 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
            <span>Spent: {formatPrice(summary?.total_spent_inr)}</span>
            <ArrowRight className="w-3.5 h-3.5 text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Rentals Stat */}
        <div
          onClick={() => navigate('/dashboard/rentals')}
          className="cursor-pointer bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-5 transition-all shadow-xl group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">My Rentals</span>
            <div className="w-8 h-8 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center group-hover:scale-110 transition-transform">
              <Calendar className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">
            {isLoading ? '...' : summary?.total_rentals ?? 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
            <span>Active bookings: {summary?.active_rentals ?? 0}</span>
            <ArrowRight className="w-3.5 h-3.5 text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Owned Vehicles Stat */}
        <div
          onClick={() => navigate('/dashboard/vehicles')}
          className="cursor-pointer bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-5 transition-all shadow-xl group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">My Garage</span>
            <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center group-hover:scale-110 transition-transform">
              <Car className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">
            {isLoading ? '...' : summary?.vehicles_owned ?? 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
            <span>Valuation: {formatPrice(summary?.portfolio_valuation_inr)}</span>
            <ArrowRight className="w-3.5 h-3.5 text-emerald-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>

        {/* Selling Listings Stat */}
        <div
          onClick={() => navigate('/dashboard/listings')}
          className="cursor-pointer bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/40 rounded-2xl p-5 transition-all shadow-xl group"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Selling Listings</span>
            <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center group-hover:scale-110 transition-transform">
              <ListOrdered className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-black text-white">
            {isLoading ? '...' : summary?.active_selling_listings ?? 0}
          </div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center justify-between">
            <span>Active marketplace ads</span>
            <ArrowRight className="w-3.5 h-3.5 text-amber-400 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </div>

      {/* Quick Action Shortcuts Banner */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950/20 p-6 shadow-xl">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400" /> Concierge Shortcuts
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <button
            type="button"
            onClick={() => navigate('/buy')}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 hover:bg-cyan-500/10 border border-slate-800 hover:border-cyan-500/40 transition-all text-left"
          >
            <div>
              <div className="text-xs font-bold text-white">Purchase a Car</div>
              <div className="text-[10px] text-slate-400">Certified pre-owned & new</div>
            </div>
            <ArrowRight className="w-4 h-4 text-cyan-400" />
          </button>

          <button
            type="button"
            onClick={() => navigate('/sell-car')}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 hover:bg-cyan-500/10 border border-slate-800 hover:border-cyan-500/40 transition-all text-left"
          >
            <div>
              <div className="text-xs font-bold text-white">Sell Your Car</div>
              <div className="text-[10px] text-slate-400">Instant AI listing wizard</div>
            </div>
            <PlusCircle className="w-4 h-4 text-cyan-400" />
          </button>

          <button
            type="button"
            onClick={() => navigate('/rent')}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 hover:bg-cyan-500/10 border border-slate-800 hover:border-cyan-500/40 transition-all text-left"
          >
            <div>
              <div className="text-xs font-bold text-white">Rent a Car</div>
              <div className="text-[10px] text-slate-400">Daily luxury & SUV rentals</div>
            </div>
            <ArrowRight className="w-4 h-4 text-cyan-400" />
          </button>

          <button
            type="button"
            onClick={() => navigate('/compare')}
            className="flex items-center justify-between p-3.5 rounded-xl bg-slate-950/60 hover:bg-cyan-500/10 border border-slate-800 hover:border-cyan-500/40 transition-all text-left"
          >
            <div>
              <div className="text-xs font-bold text-white">Compare Specs</div>
              <div className="text-[10px] text-slate-400">Side-by-side benchmark</div>
            </div>
            <ArrowRight className="w-4 h-4 text-cyan-400" />
          </button>
        </div>
      </div>

      {/* Account Highlights & Benefits */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-5">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-8 h-8 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Aura Ownership Assurance</h3>
              <p className="text-[11px] text-slate-400">All purchased cars carry full historical service snapshots</p>
            </div>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Every vehicle acquired through Aura Motors includes 12-month drivetrain warranty, nationwide roadside assistance, and instant digital title transfer verification.
          </p>
        </div>

        <div className="rounded-2xl border border-slate-800/80 bg-slate-900/40 p-5">
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-8 h-8 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Clock className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Rental Concierge Service</h3>
              <p className="text-[11px] text-slate-400">Contactless doorstep delivery and Airport VIP pickup</p>
            </div>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Active reservations feature zero security deposit hold for verified members and comprehensive zero-depreciation insurance cover included.
          </p>
        </div>
      </div>
    </div>
  );
};

