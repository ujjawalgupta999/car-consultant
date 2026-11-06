import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShoppingBag,
  Search,
  Filter,
  ArrowUpDown,
  CheckCircle2,
  Clock,
  ExternalLink,
  ShieldCheck,
  Calendar,
  DollarSign,
  X,
  FileText,
  AlertCircle,
  Car,
} from 'lucide-react';

export interface VehicleSnapshot {
  brand: string;
  model: string;
  variant?: string;
  year?: number;
  condition?: string;
  fuel_type?: string;
  transmission?: string;
  image?: string;
  location?: string;
  seats?: number;
  mileage_kmpl?: number;
  features?: string[];
}

export interface PurchaseRecord {
  id: string;
  userId: string;
  vehicleId: string;
  orderId: string;
  vehicleSnapshot: VehicleSnapshot;
  purchasePrice: number;
  paymentStatus: string;
  purchaseStatus: string;
  purchaseDate: string;
  transactionReference: string;
  tokenAmountPaid?: number;
  demo_mode?: boolean;
}

export const PurchasesPage: React.FC = () => {
  const navigate = useNavigate();
  const [purchases, setPurchases] = useState<PurchaseRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Sorting state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [sortBy, setSortBy] = useState<'date_desc' | 'date_asc' | 'price_desc' | 'price_asc'>('date_desc');
  const [selectedPurchase, setSelectedPurchase] = useState<PurchaseRecord | null>(null);

  const fetchPurchases = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/purchases');
      if (!res.ok) throw new Error('Failed to load purchases portfolio');
      const data = await res.json();
      setPurchases(data.purchases || []);
    } catch (err: any) {
      setError(err.message || 'Error loading purchase history');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPurchases();
    const handleRefresh = (e: any) => {
      if (!e.detail?.resource || e.detail.resource === 'myPurchases') {
        fetchPurchases();
      }
    };
    window.addEventListener('aura_data_refresh', handleRefresh);
    return () => window.removeEventListener('aura_data_refresh', handleRefresh);
  }, []);

  const formatPrice = (amount: number) => {
    if (amount >= 10000000) return `₹${(amount / 10000000).toFixed(2)} Cr`;
    if (amount >= 100000) return `₹${(amount / 100000).toFixed(2)} Lakh`;
    return `₹${amount.toLocaleString('en-IN')}`;
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  // Filter and sort purchases in memory
  const filteredPurchases = purchases
    .filter((p) => {
      // 1. Search Query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const brandMatch = p.vehicleSnapshot.brand.toLowerCase().includes(q);
        const modelMatch = p.vehicleSnapshot.model.toLowerCase().includes(q);
        const orderMatch = p.orderId.toLowerCase().includes(q);
        const txnMatch = p.transactionReference.toLowerCase().includes(q);
        if (!brandMatch && !modelMatch && !orderMatch && !txnMatch) return false;
      }
      // 2. Status Filter
      if (statusFilter !== 'ALL' && p.purchaseStatus !== statusFilter) {
        return false;
      }
      return true;
    })
    .sort((a, b) => {
      if (sortBy === 'date_desc') {
        return new Date(b.purchaseDate).getTime() - new Date(a.purchaseDate).getTime();
      }
      if (sortBy === 'date_asc') {
        return new Date(a.purchaseDate).getTime() - new Date(b.purchaseDate).getTime();
      }
      if (sortBy === 'price_desc') {
        return b.purchasePrice - a.purchasePrice;
      }
      if (sortBy === 'price_asc') {
        return a.purchasePrice - b.purchasePrice;
      }
      return 0;
    });

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[11px] font-bold uppercase tracking-wider mb-1">
            <ShoppingBag className="w-3.5 h-3.5" /> Verified Purchase Ledger
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">My Purchases</h2>
          <p className="text-xs text-slate-400">
            Immutable records of vehicles purchased through Aura Motors with certified ownership snapshots.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate('/buy')}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-all shadow-md self-start sm:self-auto"
        >
          <Car className="w-4 h-4" />
          <span>Explore Cars to Buy</span>
        </button>
      </div>

      {/* Filter and Search Controls */}
      <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-4 shadow-xl flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by brand, model, order ID, or transaction ref..."
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 outline-none focus:border-cyan-500 transition-colors"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 outline-none cursor-pointer focus:border-cyan-500"
          >
            <option value="ALL">All Statuses</option>
            <option value="CONFIRMED">Confirmed</option>
            <option value="DELIVERED">Delivered</option>
            <option value="PROCESSING">Processing</option>
          </select>

          {/* Sort By */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 outline-none cursor-pointer focus:border-cyan-500"
          >
            <option value="date_desc">Latest First</option>
            <option value="date_asc">Oldest First</option>
            <option value="price_desc">Price: High to Low</option>
            <option value="price_asc">Price: Low to High</option>
          </select>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <div className="inline-block animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mb-3"></div>
          <p className="text-xs text-slate-400">Loading your verified purchase history...</p>
        </div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-white">Unable to retrieve purchases</h3>
          <p className="text-xs text-red-300 mt-1">{error}</p>
          <button
            type="button"
            onClick={fetchPurchases}
            className="mt-3 px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white transition-all"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && filteredPurchases.length === 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 flex items-center justify-center mx-auto mb-4">
            <ShoppingBag className="w-8 h-8" />
          </div>
          <h3 className="text-base font-bold text-white">No vehicle purchases found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto mt-1 mb-6">
            {purchases.length === 0
              ? 'You have not completed any car purchases yet. Browse our certified new and pre-owned marketplace inventory with instant token checkout.'
              : 'No purchase records match your search or filter criteria.'}
          </p>
          {purchases.length === 0 ? (
            <button
              type="button"
              onClick={() => navigate('/buy')}
              className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-lg"
            >
              Browse Buy Portal
            </button>
          ) : (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setStatusFilter('ALL');
              }}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white transition-all"
            >
              Clear Filters
            </button>
          )}
        </div>
      )}

      {/* Purchases List */}
      {!isLoading && !error && filteredPurchases.length > 0 && (
        <div className="space-y-4">
          {filteredPurchases.map((purchase) => {
            const snap = purchase.vehicleSnapshot;
            return (
              <div
                key={purchase.id}
                className="rounded-2xl border border-slate-800/80 bg-slate-900/60 hover:bg-slate-900 hover:border-slate-700 transition-all p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-5"
              >
                {/* Left: Thumbnail & Specs */}
                <div className="flex items-center space-x-4">
                  <img
                    src={snap.image || 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=400&q=80'}
                    alt={`${snap.brand} ${snap.model}`}
                    className="w-24 h-20 rounded-xl object-cover border border-slate-800 shadow-md"
                  />
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-white">
                        {snap.brand} {snap.model}
                      </h3>
                      {snap.year && (
                        <span className="text-[10px] font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-md">
                          {snap.year}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {snap.variant || 'Standard'} • {snap.fuel_type || 'Petrol'} • {snap.transmission || 'Automatic'}
                    </p>
                    <div className="text-[11px] text-slate-500 mt-1 font-mono">
                      Order ID: <span className="text-slate-400">{purchase.orderId}</span>
                    </div>
                  </div>
                </div>

                {/* Middle: Financial & Dates */}
                <div className="flex flex-wrap md:flex-col items-start gap-2 md:gap-1 text-left">
                  <div className="text-xs text-slate-400">
                    Purchase Price: <span className="text-base font-black text-cyan-400">{formatPrice(purchase.purchasePrice)}</span>
                  </div>
                  <div className="text-[11px] text-slate-400">
                    Purchased on: <span className="text-slate-300 font-medium">{formatDate(purchase.purchaseDate)}</span>
                  </div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    Ref: <span className="text-slate-400 truncate max-w-[150px] inline-block">{purchase.transactionReference}</span>
                  </div>
                </div>

                {/* Right: Badges & View Details */}
                <div className="flex items-center space-x-3 w-full md:w-auto justify-between md:justify-end border-t md:border-t-0 border-slate-800 pt-3 md:pt-0">
                  <div className="flex flex-col gap-1 items-start md:items-end">
                    <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                      <CheckCircle2 className="w-3 h-3" /> {purchase.purchaseStatus}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Payment: <span className="text-emerald-400 font-bold">{purchase.paymentStatus}</span>
                    </span>
                  </div>

                  <button
                    type="button"
                    onClick={() => setSelectedPurchase(purchase)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white transition-all border border-slate-700"
                  >
                    <span>View Details</span>
                    <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Purchase Details Modal */}
      {selectedPurchase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
          <div className="relative w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl overflow-y-auto max-h-[90vh]">
            <button
              type="button"
              onClick={() => setSelectedPurchase(null)}
              className="absolute top-6 right-6 p-2 rounded-full bg-slate-800 text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Modal Header */}
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 flex items-center justify-center">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold tracking-widest text-cyan-400">
                  Certified Vehicle Ownership Record
                </span>
                <h3 className="text-xl font-bold text-white">
                  {selectedPurchase.vehicleSnapshot.brand} {selectedPurchase.vehicleSnapshot.model}
                </h3>
              </div>
            </div>

            {/* Vehicle Snapshot Card */}
            <div className="rounded-2xl border border-slate-800 bg-slate-950 p-4 mb-6 flex flex-col sm:flex-row gap-4 items-center">
              <img
                src={selectedPurchase.vehicleSnapshot.image || 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=600&q=80'}
                alt="Vehicle"
                className="w-full sm:w-44 h-28 object-cover rounded-xl border border-slate-800"
              />
              <div className="space-y-1 text-xs text-slate-300 w-full">
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span className="text-slate-500">Variant:</span>
                  <span className="font-semibold text-white">{selectedPurchase.vehicleSnapshot.variant || 'Standard'}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span className="text-slate-500">Year / Condition:</span>
                  <span className="font-semibold text-white">
                    {selectedPurchase.vehicleSnapshot.year || 2024} • {selectedPurchase.vehicleSnapshot.condition || 'Certified Pre-Owned'}
                  </span>
                </div>
                <div className="flex justify-between border-b border-slate-800/80 pb-1">
                  <span className="text-slate-500">Powertrain:</span>
                  <span className="font-semibold text-white">
                    {selectedPurchase.vehicleSnapshot.fuel_type || 'Petrol'} ({selectedPurchase.vehicleSnapshot.transmission || 'Automatic'})
                  </span>
                </div>
                <div className="flex justify-between pt-1">
                  <span className="text-slate-500">Delivery Hub:</span>
                  <span className="font-semibold text-cyan-400">{selectedPurchase.vehicleSnapshot.location || 'Delhi Aerocity Hub'}</span>
                </div>
              </div>
            </div>

            {/* Financial & Order Ledger Details */}
            <div className="space-y-3 mb-6">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Transaction Ledger</h4>
              <div className="rounded-2xl bg-slate-950 border border-slate-800 p-4 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Order ID:</span>
                  <span className="font-mono text-white">{selectedPurchase.orderId}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Transaction Reference:</span>
                  <span className="font-mono text-cyan-400">{selectedPurchase.transactionReference}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Payment Status:</span>
                  <span className="font-bold text-emerald-400">{selectedPurchase.paymentStatus}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Purchase Date:</span>
                  <span className="text-slate-300">{formatDate(selectedPurchase.purchaseDate)}</span>
                </div>
                <div className="flex justify-between pt-2 border-t border-slate-800 text-sm">
                  <span className="font-bold text-white">Total Amount Paid:</span>
                  <span className="font-black text-cyan-400">{formatPrice(selectedPurchase.purchasePrice)}</span>
                </div>
              </div>
            </div>

            {/* Support Concierge Hotline */}
            <div className="flex items-center justify-between p-4 rounded-2xl bg-cyan-950/20 border border-cyan-800/40 text-xs">
              <div className="text-slate-300">
                <span className="font-bold text-white block">Dedicated Concierge Assigned</span>
                Delivery scheduling and RC title documentation active.
              </div>
              <button
                type="button"
                onClick={() => {
                  setSelectedPurchase(null);
                  navigate('/dashboard/vehicles');
                }}
                className="px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold transition-all shadow"
              >
                View in Garage
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

