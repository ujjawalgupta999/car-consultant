import React, { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import {
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  RotateCcw,
  ShoppingBag,
  CreditCard,
  Download,
  ShieldCheck,
  Compass,
  FileText
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useVehicleStore } from '../store/vehicleStore';

export const PaymentResultPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = useAuthStore();

  const stateData = location.state || {};
  const [status, setStatus] = useState<'SUCCESS' | 'FAILED' | 'PENDING'>(stateData.status || 'SUCCESS');
  const [payment, setPayment] = useState<any>(stateData.payment || null);
  const [isLoading, setIsLoading] = useState(!stateData.payment);
  const [errorMessage, setErrorMessage] = useState<string>(
    stateData.errorMessage || 'Transaction could not be confirmed.'
  );

  const { getVehicleById, vehicles } = useVehicleStore();
  const showcaseVehicle =
    stateData.vehicle ||
    payment?.vehicleSnapshot ||
    payment?.vehicle ||
    (payment?.vehicleId ? getVehicleById(payment.vehicleId) : null) ||
    vehicles[0];

  const isRent = (orderId || '').startsWith('BK-') || (orderId || '').startsWith('bk_');

  // Authoritative fetch from database if not passed via state or after refresh
  const fetchAuthoritativeStatus = async () => {
    if (!orderId) return;
    setIsLoading(true);
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`/api/payments/order/${orderId}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setPayment(data);
        setStatus(data.paymentStatus === 'SUCCESS' ? 'SUCCESS' : data.paymentStatus === 'FAILED' ? 'FAILED' : 'PENDING');
      } else {
        // If not found in payments, check if order is pending
        setStatus('PENDING');
      }
    } catch (e) {
      console.error('Failed to fetch payment status:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!payment) {
      fetchAuthoritativeStatus();
    }
  }, [orderId]);

  const handleRecheck = async () => {
    if (payment?.id) {
      try {
        const headers: Record<string, string> = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        const res = await fetch(`/api/payments/${payment.id}/recheck`, { method: 'POST', headers });
        if (res.ok) {
          const data = await res.json();
          setPayment(data.payment);
          setStatus(data.status === 'SUCCESS' ? 'SUCCESS' : 'PENDING');
        }
      } catch (e) {
        console.error(e);
      }
    } else {
      fetchAuthoritativeStatus();
    }
  };

  const handleDownloadReceipt = () => {
    window.print();
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-28 pb-20 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full">
        {status === 'SUCCESS' ? (
          /* ================= SUCCESS STATE ================= */
          <div className="bg-slate-900 border border-emerald-500/30 rounded-3xl p-8 sm:p-10 shadow-2xl relative overflow-hidden text-center">
            <div className="w-20 h-20 rounded-3xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto mb-6 text-emerald-400 shadow-inner">
              <CheckCircle2 className="w-10 h-10" />
            </div>

            <span className="text-xs uppercase font-bold tracking-widest text-emerald-400 bg-emerald-950/80 px-3 py-1 rounded-full border border-emerald-800/40">
              Payment Confirmed &amp; Synchronized
            </span>

            <h1 className="text-3xl font-bold text-white tracking-tight mt-3">
              {isRent ? 'Rental Reservation Confirmed!' : 'Vehicle Purchase Confirmed!'}
            </h1>
            <p className="text-slate-400 text-sm mt-2 max-w-md mx-auto">
              Your mock payment has been settled. The authoritative record has been synchronized with your account dashboard and Aura AI Consultant.
            </p>

            {/* Post-Transaction Purchased / Reserved Vehicle Showcase Card */}
            {showcaseVehicle && (
              <div className="my-6 rounded-2xl border-2 border-emerald-500/80 bg-gradient-to-br from-slate-950 via-slate-900 to-emerald-950/30 p-5 text-left shadow-2xl relative overflow-hidden">
                <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-3">
                    {(showcaseVehicle.image_url || showcaseVehicle.image) && (
                      <img
                        src={showcaseVehicle.image_url || showcaseVehicle.image}
                        alt={showcaseVehicle.model || 'Vehicle'}
                        className="w-24 h-16 object-cover rounded-xl border border-slate-700 shrink-0"
                      />
                    )}
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">
                        {showcaseVehicle.brand || 'Aura Motors'}
                      </span>
                      <h3 className="text-base font-black text-white">
                        {showcaseVehicle.brand} {showcaseVehicle.model}{' '}
                        <span className="text-gray-400 text-xs font-normal">({showcaseVehicle.year || 2024})</span>
                      </h3>
                      <p className="text-xs text-slate-400">
                        Ref: <span className="font-mono text-emerald-400">{orderId}</span>
                      </p>
                    </div>
                  </div>

                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500 text-slate-950 text-xs font-black px-3 py-1 shadow-lg uppercase tracking-wider">
                    <ShieldCheck className="w-3.5 h-3.5" /> {isRent ? 'ACTIVE RENTAL PASS' : 'OWNED / IN GARAGE'}
                  </span>
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs">
                  <div className="text-slate-300">
                    <span className="text-slate-500">Ownership Status:</span>{' '}
                    <strong className="text-emerald-400 font-bold">{isRent ? 'Rental Reserved' : 'Added to Digital Garage'}</strong>
                  </div>
                  <div className="flex items-center gap-2">
                    <Link
                      to="/dashboard/vehicles"
                      className="px-3 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 text-xs font-bold transition flex items-center gap-1.5"
                    >
                      <span>View in My Garage</span>
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                    <Link
                      to={isRent ? '/dashboard/rentals' : '/dashboard/purchases'}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold transition"
                    >
                      {isRent ? 'View Rental Pass' : 'View Purchases'}
                    </Link>
                  </div>
                </div>
              </div>
            )}

            {/* Authoritative Receipt Card */}
            <div className="my-8 bg-slate-950 border border-slate-800 rounded-2xl p-6 text-left text-xs space-y-3 shadow-xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                  <FileText className="w-4 h-4 text-cyan-400" /> Transaction Receipt
                </span>
                <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-800/40">
                  Authoritative
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-slate-500 block text-[11px]">Order Reference:</span>
                  <span className="font-mono text-white font-semibold">{orderId}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px]">Transaction ID:</span>
                  <span className="font-mono text-cyan-400 font-semibold">{payment?.transactionId || `TXN-MOCK-${(orderId || '').slice(-6)}`}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 pt-2 border-t border-slate-800/60">
                <div>
                  <span className="text-slate-500 block text-[11px]">Service Type:</span>
                  <span className="text-white font-medium">{isRent ? 'Self-Drive Fleet Rental' : 'Certified Purchase Token Deposit'}</span>
                </div>
                <div>
                  <span className="text-slate-500 block text-[11px]">Payment Method:</span>
                  <span className="text-white capitalize">{payment?.paymentMethod || 'UPI Instant'} (Mock)</span>
                </div>
              </div>

              <div className="flex justify-between items-center pt-3 border-t border-slate-800">
                <div>
                  <span className="text-slate-500 block text-[11px]">Total Settled:</span>
                  <span className="text-xl font-bold text-emerald-400">
                    ₹{(payment?.amount || stateData.amount || 25000).toLocaleString()}
                  </span>
                </div>
                <div className="text-right">
                  <span className="text-slate-500 block text-[11px]">Timestamp:</span>
                  <span className="text-slate-400 text-[11px]">{new Date().toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row justify-center gap-3">
              <Link
                to={isRent ? '/dashboard/rentals' : '/dashboard/purchases'}
                className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl text-sm transition shadow-lg shadow-cyan-950/30 flex items-center justify-center gap-2"
              >
                <ShoppingBag className="w-4 h-4" />
                <span>{isRent ? 'View My Rentals' : 'View My Purchases'}</span>
              </Link>

              <Link
                to="/dashboard/payments"
                className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition flex items-center justify-center gap-2"
              >
                <CreditCard className="w-4 h-4 text-cyan-400" />
                <span>Payment History</span>
              </Link>

              <button
                type="button"
                onClick={handleDownloadReceipt}
                className="px-5 py-3 bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white rounded-xl text-sm font-semibold transition flex items-center justify-center gap-2"
              >
                <Download className="w-4 h-4" />
                <span>Print Receipt</span>
              </button>
            </div>

            <div className="mt-8 text-center">
              <Link to="/explore" className="text-xs text-slate-400 hover:text-cyan-400 transition inline-flex items-center gap-1">
                <Compass className="w-3.5 h-3.5" />
                <span>Continue Exploring Vehicles →</span>
              </Link>
            </div>
          </div>
        ) : status === 'FAILED' ? (
          /* ================= FAILED STATE ================= */
          <div className="bg-slate-900 border border-rose-500/30 rounded-3xl p-8 sm:p-10 shadow-2xl relative text-center">
            <div className="w-20 h-20 rounded-3xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center mx-auto mb-6 text-rose-400 shadow-inner">
              <XCircle className="w-10 h-10" />
            </div>

            <span className="text-xs uppercase font-bold tracking-widest text-rose-400 bg-rose-950/80 px-3 py-1 rounded-full border border-rose-800/40">
              Transaction Declined
            </span>

            <h1 className="text-3xl font-bold text-white tracking-tight mt-3">
              Payment Could Not Be Confirmed
            </h1>
            <p className="text-slate-400 text-sm mt-2 max-w-md mx-auto">
              The simulated banking gateway reported a decline. Your order remains pending and no funds were debited.
            </p>

            <div className="my-6 p-4 rounded-xl bg-slate-950 border border-rose-900/40 text-left text-xs space-y-2">
              <div className="flex justify-between text-slate-400">
                <span>Order ID:</span>
                <span className="font-mono text-white">{orderId}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Reason:</span>
                <span className="text-rose-300 font-medium">{errorMessage}</span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row justify-center gap-3">
              <button
                type="button"
                onClick={() => navigate(`/checkout/${orderId}`)}
                className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold rounded-xl text-sm transition flex items-center justify-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Retry Payment</span>
              </button>
              <Link
                to="/explore"
                className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition flex items-center justify-center gap-2"
              >
                <span>Return to Catalogue</span>
              </Link>
            </div>
          </div>
        ) : (
          /* ================= PENDING STATE ================= */
          <div className="bg-slate-900 border border-amber-500/30 rounded-3xl p-8 sm:p-10 shadow-2xl relative text-center">
            <div className="w-20 h-20 rounded-3xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center mx-auto mb-6 text-amber-400 shadow-inner">
              <Clock className="w-10 h-10 animate-pulse" />
            </div>

            <span className="text-xs uppercase font-bold tracking-widest text-amber-400 bg-amber-950/80 px-3 py-1 rounded-full border border-amber-800/40">
              Settlement In Progress
            </span>

            <h1 className="text-2xl font-bold text-white tracking-tight mt-3">
              Awaiting Gateway Confirmation
            </h1>
            <p className="text-slate-400 text-sm mt-2 max-w-md mx-auto">
              Your payment is currently undergoing asynchronous clearance. You can recheck the status below or visit your payment ledger.
            </p>

            <div className="my-6 p-4 rounded-xl bg-slate-950 border border-slate-800 text-left text-xs space-y-2">
              <div className="flex justify-between text-slate-400">
                <span>Reference:</span>
                <span className="font-mono text-white">{orderId}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Status:</span>
                <span className="text-amber-400 font-semibold">Pending Authorization</span>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row justify-center gap-3">
              <button
                type="button"
                onClick={handleRecheck}
                className="px-6 py-3 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl text-sm transition flex items-center justify-center gap-2"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Recheck Status</span>
              </button>
              <Link
                to="/dashboard/payments"
                className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-sm font-semibold transition"
              >
                Go to Payment History
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

