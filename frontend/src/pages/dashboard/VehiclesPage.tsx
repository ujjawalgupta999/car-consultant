import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConsultantStore } from '../../store/consultantStore';
import {
  Car,
  PlusCircle,
  ShieldCheck,
  Tag,
  Clock,
  Sparkles,
  ExternalLink,
  AlertCircle,
  FileText,
  DollarSign,
} from 'lucide-react';

export interface OwnedVehicle {
  id: string;
  userId: string;
  vehicleId: string;
  brand: string;
  model: string;
  variant?: string;
  year: number;
  registrationNumber?: string;
  source: 'PURCHASED_PLATFORM' | 'MANUALLY_ADDED' | 'LISTED_FOR_SALE' | 'SOLD';
  purchaseDate?: string;
  purchasePrice?: number;
  currentEstimatedValue: number;
  image: string;
  status: string;
}

export const VehiclesPage: React.FC = () => {
  const navigate = useNavigate();
  const { setSellDraft } = useConsultantStore();
  const [vehicles, setVehicles] = useState<OwnedVehicle[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const fetchVehicles = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/dashboard/vehicles');
      if (!res.ok) throw new Error('Failed to load owned vehicle garage');
      const data = await res.json();
      setVehicles(data.vehicles || []);
    } catch (err: any) {
      setError(err.message || 'Error fetching garage vehicles');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchVehicles();
    const handleRefresh = (e: any) => {
      if (!e.detail?.resource || e.detail.resource === 'myVehicles') {
        fetchVehicles();
      }
    };
    window.addEventListener('aura_data_refresh', handleRefresh);
    return () => window.removeEventListener('aura_data_refresh', handleRefresh);
  }, []);

  const formatPrice = (val?: number) => {
    if (!val || val === 0) return '₹0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakh`;
    return `₹${val.toLocaleString('en-IN')}`;
  };

  const handleSellVehicle = (veh: OwnedVehicle) => {
    // Pre-fill sell draft with vehicle details
    setSellDraft({
      brand: veh.brand,
      model: veh.model,
      variant: veh.variant || '',
      year: veh.year,
      expected_price: veh.currentEstimatedValue || 1000000,
      is_registered_in_user_name: true,
      location: 'Delhi NCR',
    });
    navigate('/sell-car');
  };

  const filtered = vehicles.filter((v) => {
    if (categoryFilter === 'PURCHASED') return v.source === 'PURCHASED_PLATFORM';
    if (categoryFilter === 'GARAGE') return v.source === 'MANUALLY_ADDED';
    if (categoryFilter === 'LISTED') return v.source === 'LISTED_FOR_SALE';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-bold uppercase tracking-wider mb-1">
            <Car className="w-3.5 h-3.5" /> Digital Garage Portfolio
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">My Vehicles</h2>
          <p className="text-xs text-slate-400">
            Vehicles in your personal ownership garage, certified platform purchases, and listed assets.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate('/sell-car')}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-all shadow-md self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Sell a Car</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        {[
          { key: 'ALL', label: `All Vehicles (${vehicles.length})` },
          { key: 'PURCHASED', label: `Purchased on Aura (${vehicles.filter((v) => v.source === 'PURCHASED_PLATFORM').length})` },
          { key: 'GARAGE', label: `Garage Assets (${vehicles.filter((v) => v.source === 'MANUALLY_ADDED').length})` },
          { key: 'LISTED', label: `Active Listings (${vehicles.filter((v) => v.source === 'LISTED_FOR_SALE').length})` },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setCategoryFilter(tab.key)}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
              categoryFilter === tab.key
                ? 'bg-slate-800 text-cyan-400 border border-cyan-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <div className="inline-block animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mb-3"></div>
          <p className="text-xs text-slate-400">Loading your vehicle portfolio...</p>
        </div>
      )}

      {/* Error */}
      {!isLoading && error && (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-white">Error fetching garage</h3>
          <p className="text-xs text-red-300 mt-1">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && filtered.length === 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <Car className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-white">No vehicles found in this category</h3>
          <p className="text-xs text-slate-400 mt-1">
            Purchase a car from the marketplace or list your current vehicle for sale to populate your garage.
          </p>
        </div>
      )}

      {/* Vehicle Grid */}
      {!isLoading && !error && filtered.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((veh) => {
            const isPlatform = veh.source === 'PURCHASED_PLATFORM';
            const isListed = veh.source === 'LISTED_FOR_SALE';
            return (
              <div
                key={veh.id}
                className="rounded-2xl border border-slate-800/80 bg-slate-900/60 hover:bg-slate-900 transition-all p-5 shadow-xl flex flex-col justify-between"
              >
                <div>
                  <div className="relative mb-4">
                    <img
                      src={veh.image}
                      alt={`${veh.brand} ${veh.model}`}
                      className="w-full h-44 object-cover rounded-xl border border-slate-800"
                    />
                    <div className="absolute top-3 left-3 flex gap-2">
                      {isPlatform && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-cyan-950/90 border border-cyan-500/40 text-cyan-300 shadow">
                          <ShieldCheck className="w-3 h-3 text-cyan-400" /> Purchased on Aura
                        </span>
                      )}
                      {isListed && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-amber-950/90 border border-amber-500/40 text-amber-300 shadow">
                          <Tag className="w-3 h-3 text-amber-400" /> Listed For Sale
                        </span>
                      )}
                      {!isPlatform && !isListed && (
                        <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-full bg-emerald-950/90 border border-emerald-500/40 text-emerald-300 shadow">
                          <Car className="w-3 h-3 text-emerald-400" /> Personal Garage
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h3 className="text-base font-bold text-white">
                        {veh.brand} {veh.model}
                      </h3>
                      <p className="text-xs text-slate-400">{veh.variant || 'Standard'}</p>
                    </div>
                    <span className="text-xs font-bold text-slate-300 bg-slate-800 px-2 py-0.5 rounded-md">
                      {veh.year}
                    </span>
                  </div>

                  <div className="space-y-1.5 text-xs text-slate-300 border-t border-slate-800/80 pt-3 mb-4">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Reg Number:</span>
                      <span className="font-mono text-slate-200">{veh.registrationNumber || 'In Verification'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Estimated Market Value:</span>
                      <span className="font-bold text-emerald-400">{formatPrice(veh.currentEstimatedValue)}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => handleSellVehicle(veh)}
                    className="flex-1 py-2 px-3 rounded-xl bg-slate-800 hover:bg-cyan-500/20 hover:border-cyan-500/40 border border-slate-700 text-xs font-bold text-white hover:text-cyan-300 transition-all flex items-center justify-center gap-1.5"
                  >
                    <PlusCircle className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Sell on Aura Marketplace</span>
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

