import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ListOrdered,
  PlusCircle,
  Tag,
  CheckCircle2,
  Trash2,
  AlertCircle,
  Clock,
  Car,
  MapPin,
  Eye,
} from 'lucide-react';

export interface VehicleListing {
  id: string;
  sellerId: string;
  brand: string;
  model: string;
  variant?: string;
  year: number;
  fuel_type: string;
  transmission: string;
  kms_driven: number;
  condition: string;
  location: string;
  expected_price: number;
  images: string[];
  contact_phone?: string;
  contact_email?: string;
  status: 'DRAFT' | 'PENDING_REVIEW' | 'ACTIVE' | 'SOLD' | 'REJECTED' | 'REMOVED';
  approval_status: string;
  created_at: string;
}

export const ListingsPage: React.FC = () => {
  const navigate = useNavigate();
  const [listings, setListings] = useState<VehicleListing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchListings = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/listings');
      if (!res.ok) throw new Error('Failed to load listings');
      const data = await res.json();
      setListings(data.listings || []);
    } catch (err: any) {
      setError(err.message || 'Error fetching listings');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchListings();
  }, []);

  const formatPrice = (val?: number) => {
    if (!val) return '₹0';
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakh`;
    return `₹${val.toLocaleString('en-IN')}`;
  };

  const handleMarkAsSold = async (listingId: string) => {
    try {
      const res = await fetch(`/api/listings/${listingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: 'SOLD' }),
      });
      if (res.ok) {
        fetchListings();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDeleteListing = async (listingId: string) => {
    if (!window.confirm('Are you sure you want to remove this vehicle listing?')) return;
    try {
      const res = await fetch(`/api/listings/${listingId}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        fetchListings();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
            <CheckCircle2 className="w-3 h-3" /> Active on Marketplace
          </span>
        );
      case 'SOLD':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400">
            <CheckCircle2 className="w-3 h-3" /> Sold
          </span>
        );
      case 'PENDING_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <Clock className="w-3 h-3" /> Pending Review
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-800 text-slate-300">
            {status}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-[11px] font-bold uppercase tracking-wider mb-1">
            <Tag className="w-3.5 h-3.5" /> Seller Dashboard
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">My Listings</h2>
          <p className="text-xs text-slate-400">
            Manage your vehicles currently listed for sale across Aura Motors automotive network.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate('/sell-car')}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-all shadow-md self-start sm:self-auto"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Create New Listing</span>
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <div className="inline-block animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mb-3"></div>
          <p className="text-xs text-slate-400">Loading your marketplace listings...</p>
        </div>
      )}

      {/* Error */}
      {!isLoading && error && (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-white">Error loading listings</h3>
          <p className="text-xs text-red-300 mt-1">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && listings.length === 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <ListOrdered className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-white">No active vehicle listings</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-5">
            You don't have any cars listed for sale. Use our AI Consultant or listing wizard to publish your vehicle in 2 minutes.
          </p>
          <button
            type="button"
            onClick={() => navigate('/sell-car')}
            className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-lg"
          >
            List a Car Now
          </button>
        </div>
      )}

      {/* Listings Cards */}
      {!isLoading && !error && listings.length > 0 && (
        <div className="space-y-4">
          {listings.map((item) => (
            <div
              key={item.id}
              className="rounded-2xl border border-slate-800/80 bg-slate-900/60 hover:bg-slate-900 transition-all p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-5"
            >
              <div className="flex items-center space-x-4">
                <img
                  src={item.images[0] || 'https://images.unsplash.com/photo-1590362891988-f77804702088?auto=format&fit=crop&w=400&q=80'}
                  alt={`${item.brand} ${item.model}`}
                  className="w-24 h-20 rounded-xl object-cover border border-slate-800"
                />
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white">
                      {item.brand} {item.model}
                    </h3>
                    <span className="text-[10px] font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-md">
                      {item.year}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {item.variant || 'Standard'} • {item.fuel_type} • {item.transmission} • {item.kms_driven?.toLocaleString('en-IN')} km
                  </p>
                  <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-slate-500" />
                    <span>{item.location}</span>
                  </div>
                </div>
              </div>

              {/* Price & Status */}
              <div className="flex flex-col items-start md:items-end gap-1">
                <span className="text-xs text-slate-400">Asking Price:</span>
                <span className="text-lg font-black text-cyan-400">{formatPrice(item.expected_price)}</span>
                {getStatusBadge(item.status)}
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 w-full md:w-auto justify-end border-t md:border-t-0 border-slate-800 pt-3 md:pt-0">
                {item.status === 'ACTIVE' && (
                  <button
                    type="button"
                    onClick={() => handleMarkAsSold(item.id)}
                    className="px-3 py-1.5 rounded-xl bg-purple-500/10 hover:bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs font-bold transition-all"
                  >
                    Mark as Sold
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => handleDeleteListing(item.id)}
                  title="Remove Listing"
                  className="p-2 rounded-xl bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 border border-slate-700 transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

