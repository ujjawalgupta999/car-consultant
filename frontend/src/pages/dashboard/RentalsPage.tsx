import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  Clock,
  MapPin,
  CheckCircle2,
  Car,
  AlertCircle,
  ExternalLink,
} from 'lucide-react';

export interface RentalRecord {
  id: string;
  vehicle_id: string;
  customer_name: string;
  pickup_date: string;
  return_date: string;
  duration_days: number;
  pickup_location: string;
  total_amount: number;
  status: string;
  payment_reference?: string;
  created_at: string;
}

export const RentalsPage: React.FC = () => {
  const navigate = useNavigate();
  const [rentals, setRentals] = useState<RentalRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRentals = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/dashboard/rentals');
      if (!res.ok) throw new Error('Failed to load rental bookings');
      const data = await res.json();
      setRentals(data.rentals || []);
    } catch (err: any) {
      setError(err.message || 'Error fetching rentals');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRentals();
  }, []);

  const formatPrice = (val?: number) => {
    if (!val) return '₹0';
    return `₹${val.toLocaleString('en-IN')}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-[11px] font-bold uppercase tracking-wider mb-1">
            <Calendar className="w-3.5 h-3.5" /> Rental Reservations
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">My Rentals</h2>
          <p className="text-xs text-slate-400">
            Active and confirmed car rental bookings, duration schedules, and pickup voucher details.
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate('/rent')}
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-all shadow-md self-start sm:self-auto"
        >
          <Car className="w-4 h-4" />
          <span>Rent a Car</span>
        </button>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <div className="inline-block animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mb-3"></div>
          <p className="text-xs text-slate-400">Loading your rentals...</p>
        </div>
      )}

      {/* Error */}
      {!isLoading && error && (
        <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-center">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <h3 className="text-sm font-bold text-white">Error fetching rentals</h3>
          <p className="text-xs text-red-300 mt-1">{error}</p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && rentals.length === 0 && (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <Calendar className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-white">No active car rentals</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-5">
            You don't have any vehicle rental reservations on record. Explore our fleet of luxury sedans, electric vehicles, and premium SUVs.
          </p>
          <button
            type="button"
            onClick={() => navigate('/rent')}
            className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-lg"
          >
            Explore Rental Fleet
          </button>
        </div>
      )}

      {/* Rentals List */}
      {!isLoading && !error && rentals.length > 0 && (
        <div className="space-y-4">
          {rentals.map((r) => (
            <div
              key={r.id}
              className="rounded-2xl border border-slate-800/80 bg-slate-900/60 hover:bg-slate-900 transition-all p-5 shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-5"
            >
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-white">Vehicle ID: {r.vehicle_id}</h3>
                  <span className="inline-flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                    <CheckCircle2 className="w-3 h-3" /> {r.status}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Dates: <span className="text-slate-200 font-semibold">{r.pickup_date} – {r.return_date}</span> ({r.duration_days} Days)
                </p>
                <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-slate-500" />
                  <span>Pickup: {r.pickup_location}</span>
                </div>
              </div>

              <div className="flex flex-col items-start md:items-end gap-1">
                <span className="text-xs text-slate-400">Total Rental Cost:</span>
                <span className="text-lg font-black text-cyan-400">{formatPrice(r.total_amount)}</span>
                <span className="text-[10px] text-slate-500 font-mono">Ref: {r.payment_reference || 'TXN-CONFIRMED'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

