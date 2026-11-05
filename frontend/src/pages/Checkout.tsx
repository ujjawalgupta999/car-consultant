import React, { useState } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import { executeMockPayment } from '../services/api';
import {
  CreditCard,
  QrCode,
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  RotateCcw,
} from 'lucide-react';

export const Checkout: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  // Booking or order details passed via location state or defaults
  const passedBooking = location.state?.booking;
  const passedVehicle = location.state?.vehicle;

  const totalAmount = passedBooking?.pricing?.total_amount || passedBooking?.total_amount || 26845;
  const targetId = id || passedBooking?.booking_id || passedBooking?.id || `bk_aura_${Date.now()}`;

  const [paymentMethod, setPaymentMethod] = useState<'card' | 'upi'>('upi');
  const [upiId, setUpiId] = useState('alex@okaxis');
  const [cardNumber, setCardNumber] = useState('4242 •••• •••• 4242');
  const [cardExpiry, setCardExpiry] = useState('12/28');
  const [cardCvv, setCardCvv] = useState('999');

  // Test rail scenario
  const [simScenario, setSimScenario] = useState<'success' | 'failure' | 'timeout'>('success');
  const [isProcessing, setIsProcessing] = useState(false);
  const [paymentResult, setPaymentResult] = useState<{
    status: 'CONFIRMED' | 'FAILED' | 'TIMEOUT';
    txId?: string;
    message?: string;
  } | null>(null);

  const handleSubmitPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);
    setPaymentResult(null);

    const payload = {
      booking_id: targetId.startsWith('bk_') || targetId.startsWith('BOOK-') ? targetId : undefined,
      order_id: targetId.startsWith('ord_') || targetId.startsWith('ORD-') ? targetId : undefined,
      amount: totalAmount,
      currency: 'INR',
      method: paymentMethod,
      scenario: simScenario,
    };

    try {
      const res = await executeMockPayment(payload);
      if (res.status === 'CONFIRMED') {
        setPaymentResult({
          status: 'CONFIRMED',
          txId: res.transaction_id || `TXN-AURA-${Date.now()}`,
          message: 'Payment simulation succeeded! Fleet unit has been reserved.',
        });
      } else {
        setPaymentResult({
          status: 'FAILED',
          message: res.error_message || 'Simulated payment was declined by the issuer bank.',
        });
      }
    } catch (err: any) {
      if (simScenario === 'timeout') {
        setPaymentResult({
          status: 'TIMEOUT',
          message: 'Gateway timed out while awaiting bank authorization (Simulated Scenario).',
        });
      } else {
        setPaymentResult({
          status: 'FAILED',
          message: err.message || 'Payment processing failed.',
        });
      }
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-28 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="border-b border-slate-800 pb-6 mb-8 text-center sm:text-left">
          <span className="text-xs font-semibold tracking-widest uppercase text-cyan-400">
            Payment Simulator
          </span>
          <h1 className="text-3xl md:text-4xl font-light tracking-tight mt-1">
            Simulated <span className="font-semibold text-white">Checkout Rails</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Official Amulate Hackathon 2026 Payment Sandbox with deterministic verification scenarios.
          </p>
        </div>

        {/* Mandatory Mock Disclaimer */}
        <div className="mb-8 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start space-x-3">
          <ShieldAlert className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-200/90 leading-relaxed">
            <strong className="text-amber-300 font-semibold uppercase tracking-wider block mb-0.5">
              Mandatory Mock Mode Notice
            </strong>
            This is an isolated test environment. No real money, payment gateways, or real banking rails are accessed.
            Please do not enter real credit card numbers or banking passwords.
          </div>
        </div>

        {/* Success confirmation state */}
        {paymentResult?.status === 'CONFIRMED' ? (
          <div className="bg-slate-900/60 border border-emerald-500/30 rounded-2xl p-8 text-center shadow-2xl shadow-emerald-950/20">
            <div className="w-16 h-16 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-emerald-500/30">
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            </div>

            <span className="text-xs font-bold uppercase tracking-widest text-emerald-400">
              Transaction Successful
            </span>
            <h2 className="text-2xl font-semibold text-white mt-1">Reservation Confirmed</h2>
            <p className="text-slate-400 text-sm max-w-md mx-auto mt-2">
              Your mock payment has been cleared by the Aura Motors settlement simulator. Your vehicle has been allocated.
            </p>

            {/* Receipt Box */}
            <div className="my-6 max-w-md mx-auto bg-slate-950 border border-slate-800 rounded-xl p-5 text-left text-xs space-y-2.5">
              <div className="flex justify-between text-slate-400">
                <span>Reference ID:</span>
                <span className="font-mono text-white">{targetId}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Transaction Ref:</span>
                <span className="font-mono text-cyan-400">{paymentResult.txId}</span>
              </div>
              <div className="flex justify-between text-slate-400">
                <span>Payment Mode:</span>
                <span className="text-white capitalize">{paymentMethod} (Simulated)</span>
              </div>
              <div className="flex justify-between text-slate-400 pt-2 border-t border-slate-800">
                <span className="text-sm font-semibold text-white">Amount Settled:</span>
                <span className="text-sm font-bold text-emerald-400">₹{totalAmount.toLocaleString()}</span>
              </div>
            </div>

            <div className="flex flex-wrap justify-center gap-4">
              <Link
                to="/dashboard"
                className="px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium transition"
              >
                Go to User Dashboard
              </Link>
              <Link
                to="/explore"
                className="px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-sm font-medium transition"
              >
                Explore More Vehicles
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
            {/* Form column (7 cols) */}
            <div className="md:col-span-7 space-y-6">
              {paymentResult && (
                <div className="p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-300 text-sm flex items-start space-x-3">
                  <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold">
                      {paymentResult.status === 'TIMEOUT' ? 'Gateway Timeout' : 'Transaction Declined'}
                    </p>
                    <p className="text-xs text-rose-300/80 mt-1">{paymentResult.message}</p>
                  </div>
                </div>
              )}

              {/* Payment Methods */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                <h3 className="text-base font-semibold text-white mb-4">Choose Mock Payment Method</h3>

                <div className="grid grid-cols-2 gap-3 mb-6">
                  <button
                    type="button"
                    onClick={() => setPaymentMethod('upi')}
                    className={`py-3 px-4 rounded-xl border flex items-center justify-center space-x-2 text-sm font-medium transition ${
                      paymentMethod === 'upi'
                        ? 'border-cyan-500 bg-cyan-950/30 text-white'
                        : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <QrCode className="w-4 h-4 text-cyan-400" />
                    <span>Instant UPI</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setPaymentMethod('card')}
                    className={`py-3 px-4 rounded-xl border flex items-center justify-center space-x-2 text-sm font-medium transition ${
                      paymentMethod === 'card'
                        ? 'border-cyan-500 bg-cyan-950/30 text-white'
                        : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <CreditCard className="w-4 h-4 text-cyan-400" />
                    <span>Credit / Debit Card</span>
                  </button>
                </div>

                {paymentMethod === 'upi' ? (
                  <div className="space-y-3">
                    <label className="block text-xs font-medium text-slate-400">Virtual Payment Address (VPA)</label>
                    <input
                      type="text"
                      value={upiId}
                      onChange={(e) => setUpiId(e.target.value)}
                      placeholder="username@okhdfcbank"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                    />
                    <p className="text-[11px] text-slate-400">Supported: GPay, PhonePe, Paytm, BHIM</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1">Card Number (Simulated)</label>
                      <input
                        type="text"
                        value={cardNumber}
                        onChange={(e) => setCardNumber(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Expiry</label>
                        <input
                          type="text"
                          value={cardExpiry}
                          onChange={(e) => setCardExpiry(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">CVV</label>
                        <input
                          type="password"
                          value={cardCvv}
                          onChange={(e) => setCardCvv(e.target.value)}
                          maxLength={3}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 font-mono"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Hackathon Test Rail Selector */}
              <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-white flex items-center">
                    <AlertTriangle className="w-4 h-4 text-amber-400 mr-2" />
                    Deterministic Hackathon Test Scenarios
                  </h3>
                  <span className="text-[10px] text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                    Grading Tool
                  </span>
                </div>
                <p className="text-xs text-slate-400 mb-4">
                  Select how the mock payment gateway should respond to this transaction:
                </p>

                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => setSimScenario('success')}
                    className={`py-2 px-3 rounded-lg border text-xs font-medium transition ${
                      simScenario === 'success'
                        ? 'border-emerald-500 bg-emerald-950/30 text-emerald-300'
                        : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-white'
                    }`}
                  >
                    ✓ Instant Success
                  </button>
                  <button
                    type="button"
                    onClick={() => setSimScenario('failure')}
                    className={`py-2 px-3 rounded-lg border text-xs font-medium transition ${
                      simScenario === 'failure'
                        ? 'border-rose-500 bg-rose-950/30 text-rose-300'
                        : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-white'
                    }`}
                  >
                    ✕ Decline Error
                  </button>
                  <button
                    type="button"
                    onClick={() => setSimScenario('timeout')}
                    className={`py-2 px-3 rounded-lg border text-xs font-medium transition ${
                      simScenario === 'timeout'
                        ? 'border-amber-500 bg-amber-950/30 text-amber-300'
                        : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:text-white'
                    }`}
                  >
                    ⏱ Timeout Error
                  </button>
                </div>
              </div>

              <button
                type="button"
                onClick={handleSubmitPayment}
                disabled={isProcessing}
                className="w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-slate-950 font-bold rounded-xl transition shadow-lg shadow-cyan-950/30 flex items-center justify-center space-x-2"
              >
                {isProcessing ? (
                  <>
                    <RotateCcw className="w-4 h-4 animate-spin text-slate-950" />
                    <span>Communicating with Simulator...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-5 h-5 text-slate-950" />
                    <span>Simulate Payment of ₹{totalAmount.toLocaleString()}</span>
                  </>
                )}
              </button>
            </div>

            {/* Sidebar Summary (5 cols) */}
            <div className="md:col-span-5">
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sticky top-28">
                <h3 className="text-sm font-semibold text-white mb-4 uppercase tracking-wider text-slate-400">
                  Payment Summary
                </h3>

                {passedVehicle && (
                  <div className="flex space-x-3 pb-4 mb-4 border-b border-slate-800">
                    <img
                      src={passedVehicle.images[0]}
                      alt={passedVehicle.model}
                      className="w-16 h-14 object-cover rounded-lg bg-slate-950 border border-slate-800"
                    />
                    <div>
                      <p className="text-xs text-cyan-400 font-bold uppercase">{passedVehicle.brand}</p>
                      <p className="text-sm font-semibold text-white">{passedVehicle.model}</p>
                    </div>
                  </div>
                )}

                <div className="space-y-2.5 text-xs text-slate-300">
                  <div className="flex justify-between">
                    <span>Reference ID:</span>
                    <span className="font-mono text-white">{targetId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Target Service:</span>
                    <span className="text-white">Aura Motors Fleet Allocation</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <span className="text-amber-400 font-medium">Pending Settlement</span>
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-800 flex justify-between items-baseline">
                  <span className="text-xs uppercase text-slate-400">Total Payable</span>
                  <span className="text-2xl font-bold text-cyan-400">₹{totalAmount.toLocaleString()}</span>
                </div>

                <div className="mt-6 p-3 bg-slate-950/60 rounded-xl border border-slate-800/80 text-[11px] text-slate-400 space-y-1">
                  <p className="font-medium text-slate-300">💡 Hackathon Reviewer Tip:</p>
                  <p>
                    Switching the test scenario toggle to Decline or Timeout allows testing of error recovery workflows without modifying source code.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
