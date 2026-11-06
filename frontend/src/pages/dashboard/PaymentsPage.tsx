import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../../store/authStore';
import {
  CreditCard,
  Search,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowUpRight,
  Filter,
  Download,
  ShieldCheck,
  RefreshCw,
  QrCode,
  Calendar,
  DollarSign
} from 'lucide-react';

interface PaymentItem {
  id: string;
  userId: string;
  orderId: string;
  transactionId: string;
  vehicleId: string;
  transactionType: 'BUY' | 'RENT';
  amount: number;
  currency: string;
  paymentMethod: string;
  paymentStatus: 'SUCCESS' | 'FAILED' | 'PENDING' | 'CANCELLED' | 'REFUNDED';
  paymentProvider: string;
  paymentReference: string;
  errorMessage?: string;
  createdAt: string;
  updatedAt: string;
}

export const PaymentsPage: React.FC = () => {
  const { token } = useAuthStore();
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<string>('ALL'); // ALL, SUCCESS, FAILED, PENDING, BUY, RENT
  const [sortBy, setSortBy] = useState('date_desc');
  const [selectedPayment, setSelectedPayment] = useState<PaymentItem | null>(null);

  const fetchPayments = async () => {
    setIsLoading(true);
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      let url = `/api/payments?sort=${sortBy}`;
      if (filterType === 'SUCCESS' || filterType === 'FAILED' || filterType === 'PENDING') {
        url += `&status=${filterType}`;
      } else if (filterType === 'BUY' || filterType === 'RENT') {
        url += `&transaction_type=${filterType}`;
      }
      if (search.trim()) {
        url += `&search=${encodeURIComponent(search.trim())}`;
      }

      const res = await fetch(url, { headers });
      if (res.ok) {
        const data = await res.json();
        setPayments(data.payments || []);
      }
    } catch (e) {
      console.error('Failed to fetch payments:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPayments();
    const handleRefresh = (e: any) => {
      if (!e.detail?.resource || e.detail.resource === 'myPayments') {
        fetchPayments();
      }
    };
    window.addEventListener('aura_data_refresh', handleRefresh);
    return () => window.removeEventListener('aura_data_refresh', handleRefresh);
  }, [filterType, sortBy, token]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchPayments();
  };

  // KPI Metrics
  const totalSettled = payments
    .filter((p) => p.paymentStatus === 'SUCCESS')
    .reduce((acc, p) => acc + p.amount, 0);
  const successCount = payments.filter((p) => p.paymentStatus === 'SUCCESS').length;
  const failedCount = payments.filter((p) => p.paymentStatus === 'FAILED').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2.5">
            <CreditCard className="w-5 h-5 text-cyan-400" />
            <span>Authoritative Payment History</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative transactional ledger synchronized across website and Aura AI Consultant.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchPayments}
          className="inline-flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs font-semibold hover:border-slate-700 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Sync Ledger</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Settled Volume (Mock)
          </span>
          <div className="text-2xl font-bold text-white">₹{totalSettled.toLocaleString()}</div>
          <p className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> {successCount} successful transaction{successCount === 1 ? '' : 's'}
          </p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Total Invoices
          </span>
          <div className="text-2xl font-bold text-cyan-400">{payments.length}</div>
          <p className="text-[11px] text-slate-400 mt-1">Verified sandbox operations</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
            Declined / Timeouts
          </span>
          <div className="text-2xl font-bold text-rose-400">{failedCount}</div>
          <p className="text-[11px] text-slate-400 mt-1">Test rail simulation error logs</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-4 space-y-3">
        <div className="flex flex-col md:flex-row gap-3 justify-between items-center">
          {/* Filter Pills */}
          <div className="flex flex-wrap gap-1.5 w-full md:w-auto">
            {[
              { id: 'ALL', label: 'All Transactions' },
              { id: 'SUCCESS', label: 'Successful' },
              { id: 'PENDING', label: 'Pending' },
              { id: 'FAILED', label: 'Declined' },
              { id: 'BUY', label: 'Purchases' },
              { id: 'RENT', label: 'Rentals' }
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setFilterType(tab.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                  filterType === tab.id
                    ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/20 font-bold'
                    : 'bg-slate-950 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search Form */}
          <form onSubmit={handleSearchSubmit} className="flex gap-2 w-full md:w-72">
            <div className="relative flex-1">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search Txn ID, Order ID..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <button
              type="submit"
              className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold transition"
            >
              Filter
            </button>
          </form>
        </div>
      </div>

      {/* Transactions Table / List */}
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        {isLoading ? (
          <div className="py-16 text-center text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-cyan-400" />
            <p className="text-sm font-medium">Synchronizing payment ledger...</p>
          </div>
        ) : payments.length === 0 ? (
          <div className="py-16 text-center text-slate-400">
            <CreditCard className="w-10 h-10 mx-auto mb-3 text-slate-600" />
            <p className="text-sm font-semibold text-white">No payment transactions found</p>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              Any vehicle purchase or rental reservation confirmed on Aura Motors will appear here in real time.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-4">Transaction / Order</th>
                  <th className="py-3 px-4">Service</th>
                  <th className="py-3 px-4">Method</th>
                  <th className="py-3 px-4">Amount</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {payments.map((p) => {
                  const isSuccess = p.paymentStatus === 'SUCCESS';
                  const isFailed = p.paymentStatus === 'FAILED';

                  return (
                    <tr key={p.id} className="hover:bg-slate-800/30 transition">
                      <td className="py-3.5 px-4">
                        <div className="font-mono text-cyan-400 font-semibold">{p.transactionId}</div>
                        <div className="text-[11px] text-slate-400 font-mono">Ref: {p.orderId}</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            p.transactionType === 'BUY'
                              ? 'bg-blue-500/10 border border-blue-500/30 text-blue-400'
                              : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-400'
                          }`}
                        >
                          {p.transactionType === 'BUY' ? 'Vehicle Purchase' : 'Fleet Rental'}
                        </span>
                        <div className="text-[11px] text-slate-300 mt-0.5">{p.vehicleId}</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="capitalize text-slate-300 font-medium">
                          {p.paymentMethod === 'upi' ? 'UPI Instant' : p.paymentMethod === 'card' ? 'Credit/Debit Card' : 'Netbanking'}
                        </span>
                        <div className="text-[10px] text-slate-400">Sandbox Rail</div>
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="font-bold text-white text-sm">
                          ₹{p.amount.toLocaleString()}
                        </span>
                        <div className="text-[10px] text-slate-400">{p.currency}</div>
                      </td>

                      <td className="py-3.5 px-4">
                        {isSuccess ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
                            <CheckCircle2 className="w-3 h-3" /> Success
                          </span>
                        ) : isFailed ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-rose-500/10 border border-rose-500/30 text-rose-400">
                            <XCircle className="w-3 h-3" /> Declined
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-500/10 border border-amber-500/30 text-amber-400">
                            <Clock className="w-3 h-3" /> Pending
                          </span>
                        )}
                      </td>

                      <td className="py-3.5 px-4 text-slate-400 text-[11px]">
                        {new Date(p.createdAt).toLocaleDateString('en-IN', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button
                          type="button"
                          onClick={() => setSelectedPayment(p)}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-[11px] font-semibold transition"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Transaction Details Modal */}
      {selectedPayment && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-lg w-full p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
                  <CreditCard className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">Payment Receipt</h3>
                  <p className="text-xs text-slate-400 font-mono">{selectedPayment.transactionId}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedPayment(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
              >
                ✕
              </button>
            </div>

            <div className="my-5 space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Order Reference:</span>
                <span className="font-mono text-white font-semibold">{selectedPayment.orderId}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Transaction Type:</span>
                <span className="text-white font-bold">{selectedPayment.transactionType === 'BUY' ? 'Vehicle Purchase Token' : 'Fleet Rental Booking'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Target Vehicle:</span>
                <span className="text-cyan-400 font-semibold">{selectedPayment.vehicleId}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Payment Status:</span>
                <span className={`font-bold ${selectedPayment.paymentStatus === 'SUCCESS' ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {selectedPayment.paymentStatus}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Payment Channel:</span>
                <span className="text-white capitalize">{selectedPayment.paymentMethod} (Sandbox Rail)</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Settled Amount:</span>
                <span className="text-base font-bold text-emerald-400">₹{selectedPayment.amount.toLocaleString()}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Provider & Protocol:</span>
                <span className="text-slate-300">{selectedPayment.paymentProvider} • ISO 20022 Mock</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-400">Settlement Timestamp:</span>
                <span className="text-slate-300">{new Date(selectedPayment.createdAt).toLocaleString()}</span>
              </div>

              {selectedPayment.errorMessage && (
                <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
                  <strong>Decline Reason:</strong> {selectedPayment.errorMessage}
                </div>
              )}
            </div>

            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-[11px] text-slate-400 mb-5">
              🛡️ <strong>Simulated Sandbox Transaction:</strong> This receipt certifies a mock transaction executed in the Amulate Hackathon 2026 verification environment.
            </div>

            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={() => window.print()}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-xl text-xs font-semibold transition flex items-center gap-2"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Print / Save</span>
              </button>
              <button
                type="button"
                onClick={() => setSelectedPayment(null)}
                className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold rounded-xl text-xs transition"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

