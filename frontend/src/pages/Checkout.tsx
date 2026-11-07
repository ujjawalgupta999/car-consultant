import React, { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
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
  Calendar,
  MapPin,
  Building2,
  Tag
} from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useConsultantStore } from '../store/consultantStore';

export const Checkout: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const { token, user } = useAuthStore();
  const { checkoutDraft, acknowledgeManualTransaction } = useConsultantStore();

  const passedBooking = location.state?.booking;
  const passedVehicle = location.state?.vehicle;
  const passedIntent = location.state?.intent || (id && id.startsWith('BK-') ? 'rent' : 'buy');

  const [orderId, setOrderId] = useState<string>(
    id || passedBooking?.booking_id || passedBooking?.id || `ORD-2026-${Date.now().toString().slice(-6)}`
  );
  const [vehicle, setVehicle] = useState<any>(passedVehicle || null);
  const [orderDetails, setOrderDetails] = useState<any>(null);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);

  // Form states
  const [customerName, setCustomerName] = useState(user?.name || 'Alex Vance');
  const [customerEmail, setCustomerEmail] = useState(user?.email || 'demo@auramotors.com');
  const [customerPhone, setCustomerPhone] = useState(user?.phone || '+91 98765 43210');
  const [deliveryCity, setDeliveryCity] = useState('Delhi NCR');

  // Rental specific dates
  const [pickupDate, setPickupDate] = useState('2026-12-15');
  const [returnDate, setReturnDate] = useState('2026-12-20');
  const [durationDays, setDurationDays] = useState(5);

  // Payment states
  const [paymentMethod, setPaymentMethod] = useState<'upi' | 'card' | 'netbanking'>('upi');
  const [upiId, setUpiId] = useState('alex@okaxis');
  const [cardNumber, setCardNumber] = useState('4242 •••• •••• 4242');
  const [cardExpiry, setCardExpiry] = useState('12/28');
  const [cardCvv, setCardCvv] = useState('999');
  const [bankName, setBankName] = useState('HDFC Bank');

  // Test rail scenario
  const [simScenario, setSimScenario] = useState<'success' | 'failure' | 'timeout'>('success');

  // Real-time live background auto-fill from Aura AI Consultant
  useEffect(() => {
    if (!checkoutDraft) return;
    if (checkoutDraft.customerName) setCustomerName(checkoutDraft.customerName);
    if (checkoutDraft.customerEmail) setCustomerEmail(checkoutDraft.customerEmail);
    if (checkoutDraft.customerPhone) setCustomerPhone(checkoutDraft.customerPhone);
    if (checkoutDraft.deliveryCity) setDeliveryCity(checkoutDraft.deliveryCity);
    if (checkoutDraft.pickupLocation) setDeliveryCity(checkoutDraft.pickupLocation);
    if (checkoutDraft.pickupDate) setPickupDate(checkoutDraft.pickupDate);
    if (checkoutDraft.returnDate) setReturnDate(checkoutDraft.returnDate);
    if (checkoutDraft.durationDays) setDurationDays(checkoutDraft.durationDays);
    if (checkoutDraft.paymentMethod) {
      const m = String(checkoutDraft.paymentMethod).toLowerCase();
      if (m === 'upi' || m === 'card' || m === 'netbanking') {
        setPaymentMethod(m as any);
      }
    }
    if (checkoutDraft.upiId) setUpiId(checkoutDraft.upiId);
    if (checkoutDraft.cardNumber) setCardNumber(checkoutDraft.cardNumber);
    if (checkoutDraft.cardExpiry) setCardExpiry(checkoutDraft.cardExpiry);
    if (checkoutDraft.cardCvv) setCardCvv(checkoutDraft.cardCvv);
    if (checkoutDraft.bankName) setBankName(checkoutDraft.bankName);
  }, [checkoutDraft]);

  // Fetch authoritative details if orderId is provided
  useEffect(() => {
    if (id) {
      const fetchOrder = async () => {
        setIsLoadingDetails(true);
        try {
          const res = await fetch(`/api/checkout/${id}`);
          if (res.ok) {
            const data = await res.json();
            setOrderDetails(data);
            if (data.vehicle) setVehicle(data.vehicle);
            if (data.customer) {
              if (data.customer.name) setCustomerName(data.customer.name);
              if (data.customer.email) setCustomerEmail(data.customer.email);
              if (data.customer.phone) setCustomerPhone(data.customer.phone);
            }
            if (data.rentalDetails) {
              if (data.rentalDetails.pickupDate) setPickupDate(data.rentalDetails.pickupDate);
              if (data.rentalDetails.returnDate) setReturnDate(data.rentalDetails.returnDate);
              if (data.rentalDetails.durationDays) setDurationDays(data.rentalDetails.durationDays);
            }
          }
        } catch (e) {
          console.error('Failed to fetch checkout details:', e);
        } finally {
          setIsLoadingDetails(false);
        }
      };
      fetchOrder();
    }
  }, [id]);

  const isRent = passedIntent === 'rent' || orderId.startsWith('BK-') || orderId.startsWith('bk_');

  // Pricing calculations
  const dailyRate = vehicle?.rental_price_per_day || 3500;
  const purchasePrice = vehicle?.purchase_price || 1500000;
  const rentalSubtotal = dailyRate * durationDays;
  const rentalTaxes = rentalSubtotal * 0.18;
  const securityDeposit = 5000;
  const payableAmount = isRent ? rentalSubtotal + rentalTaxes : 25000; // 25,000 reservation deposit for buy

  const handleStartPayment = (e: React.FormEvent) => {
    e.preventDefault();

    // Route to dedicated processing page
    navigate(`/payment/processing/${orderId}`, {
      state: {
        orderId,
        amount: payableAmount,
        paymentMethod,
        simScenario,
        vehicle,
        isRent,
        customerName,
        customerEmail
      }
    });
  };

  // Autonomous execution: listen for Aura AI controller checkout submit action
  useEffect(() => {
    const handleExecuteSubmit = (e: any) => {
      console.log('[Aura Controller] Auto-executing checkout submission...', e?.detail);
      navigate(`/payment/processing/${orderId}`, {
        state: {
          orderId,
          amount: payableAmount,
          paymentMethod,
          simScenario: 'success',
          vehicle,
          isRent,
          customerName,
          customerEmail
        }
      });
    };
    window.addEventListener('aura_execute_checkout_submit', handleExecuteSubmit);
    return () => {
      window.removeEventListener('aura_execute_checkout_submit', handleExecuteSubmit);
    };
  }, [orderId, payableAmount, paymentMethod, vehicle, isRent, customerName, customerEmail, navigate]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-28 pb-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="border-b border-slate-800 pb-6 mb-8 text-center sm:text-left">
          <div className="inline-flex items-center gap-2 text-xs font-bold tracking-widest uppercase text-cyan-400 bg-cyan-950/80 px-3 py-1 rounded-full border border-cyan-800/40 mb-2">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Unified Checkout &amp; Settlement</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
            {isRent ? 'Rental Reservation Checkout' : 'Vehicle Purchase Checkout'}
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Authoritative transactional checkout shared across Aura AI Consultant and marketplace catalogue.
          </p>
        </div>

        {/* Mandatory Mock Mode Banner */}
        <div className="mb-8 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-start space-x-3 shadow-lg">
          <ShieldAlert className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-200/90 leading-relaxed">
            <strong className="text-amber-300 font-bold uppercase tracking-wider block mb-0.5">
              Simulated Mock Payment Environment (Amulate Hackathon 2026)
            </strong>
            This is an isolated test environment. Simulated mock payments generate authentic transaction receipts without deducting real bank funds. Do not enter authentic passwords or private cards.
          </div>
        </div>

        <form onSubmit={handleStartPayment} className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Main Checkout Form (7 cols) */}
          <div className="lg:col-span-7 space-y-6">
            {/* Customer Information */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
                <span>1. Customer &amp; Delivery Information</span>
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <label className="block font-semibold text-slate-400 mb-1">Full Legal Name</label>
                  <input
                    type="text"
                    required
                    value={customerName}
                    onChange={(e) => setCustomerName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-400 mb-1">Email Address</label>
                  <input
                    type="email"
                    required
                    value={customerEmail}
                    onChange={(e) => setCustomerEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-400 mb-1">Phone Number</label>
                  <input
                    type="tel"
                    required
                    value={customerPhone}
                    onChange={(e) => setCustomerPhone(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-400 mb-1">
                    {isRent ? 'Pickup City' : 'Delivery City'}
                  </label>
                  <input
                    type="text"
                    required
                    value={deliveryCity}
                    onChange={(e) => setDeliveryCity(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>
            </div>

            {/* Rental Duration Selector (If Rental) */}
            {isRent && (
              <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-cyan-400" />
                  <span>2. Rental Period &amp; Schedule</span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div>
                    <label className="block font-semibold text-slate-400 mb-1">Pickup Date</label>
                    <input
                      type="date"
                      value={pickupDate}
                      onChange={(e) => setPickupDate(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-400 mb-1">Return Date</label>
                    <input
                      type="date"
                      value={returnDate}
                      onChange={(e) => setReturnDate(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                  <div>
                    <label className="block font-semibold text-slate-400 mb-1">Duration (Days)</label>
                    <input
                      type="number"
                      min={1}
                      max={30}
                      value={durationDays}
                      onChange={(e) => setDurationDays(Math.max(1, parseInt(e.target.value) || 1))}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Payment Method Selection */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
                <span>{isRent ? '3.' : '2.'} Select Mock Payment Method</span>
              </h3>

              <div className="grid grid-cols-3 gap-3 mb-6">
                <button
                  type="button"
                  onClick={() => setPaymentMethod('upi')}
                  className={`py-3 px-3 rounded-xl border flex flex-col items-center justify-center gap-1.5 text-xs font-semibold transition ${
                    paymentMethod === 'upi'
                      ? 'border-cyan-500 bg-cyan-950/30 text-white shadow-md shadow-cyan-500/20'
                      : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <QrCode className="w-5 h-5 text-cyan-400" />
                  <span>Instant UPI</span>
                </button>

                <button
                  type="button"
                  onClick={() => setPaymentMethod('card')}
                  className={`py-3 px-3 rounded-xl border flex flex-col items-center justify-center gap-1.5 text-xs font-semibold transition ${
                    paymentMethod === 'card'
                      ? 'border-cyan-500 bg-cyan-950/30 text-white shadow-md shadow-cyan-500/20'
                      : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <CreditCard className="w-5 h-5 text-cyan-400" />
                  <span>Card Simulator</span>
                </button>

                <button
                  type="button"
                  onClick={() => setPaymentMethod('netbanking')}
                  className={`py-3 px-3 rounded-xl border flex flex-col items-center justify-center gap-1.5 text-xs font-semibold transition ${
                    paymentMethod === 'netbanking'
                      ? 'border-cyan-500 bg-cyan-950/30 text-white shadow-md shadow-cyan-500/20'
                      : 'border-slate-800 bg-slate-950/60 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  <Building2 className="w-5 h-5 text-cyan-400" />
                  <span>NetBanking</span>
                </button>
              </div>

              {paymentMethod === 'upi' ? (
                <div className="space-y-2 text-xs">
                  <label className="block font-semibold text-slate-400">Virtual Payment Address (VPA)</label>
                  <input
                    type="text"
                    value={upiId}
                    onChange={(e) => setUpiId(e.target.value)}
                    placeholder="user@okhdfcbank"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white font-mono focus:outline-none focus:border-cyan-500"
                  />
                  <p className="text-[11px] text-slate-500">Instant sandbox authorization via Google Pay, PhonePe, or BHIM.</p>
                </div>
              ) : paymentMethod === 'card' ? (
                <div className="space-y-3 text-xs">
                  <div>
                    <label className="block font-semibold text-slate-400 mb-1">Simulated Card Number</label>
                    <input
                      type="text"
                      value={cardNumber}
                      onChange={(e) => setCardNumber(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block font-semibold text-slate-400 mb-1">Expiry</label>
                      <input
                        type="text"
                        value={cardExpiry}
                        onChange={(e) => setCardExpiry(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white font-mono focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                    <div>
                      <label className="block font-semibold text-slate-400 mb-1">CVV</label>
                      <input
                        type="password"
                        maxLength={3}
                        value={cardCvv}
                        onChange={(e) => setCardCvv(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white font-mono focus:outline-none focus:border-cyan-500"
                      />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-2 text-xs">
                  <label className="block font-semibold text-slate-400">Select Bank</label>
                  <select
                    value={bankName}
                    onChange={(e) => setBankName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option>HDFC Bank</option>
                    <option>State Bank of India (SBI)</option>
                    <option>ICICI Bank</option>
                    <option>Axis Bank</option>
                    <option>Kotak Mahindra Bank</option>
                  </select>
                </div>
              )}
            </div>

            {/* Deterministic Hackathon Test Rail Scenarios */}
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <span>Deterministic Hackathon Verification Rail</span>
                </h3>
                <span className="text-[10px] uppercase font-bold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800/50">
                  Grading Switch
                </span>
              </div>
              <p className="text-xs text-slate-400 mb-4">
                Select desired outcome to test idempotent settlement and error-recovery behaviors:
              </p>

              <div className="grid grid-cols-3 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => setSimScenario('success')}
                  className={`py-2 px-3 rounded-xl border font-semibold transition ${
                    simScenario === 'success'
                      ? 'border-emerald-500 bg-emerald-950/30 text-emerald-300 shadow-sm'
                      : 'border-slate-800 bg-slate-950 text-slate-400 hover:text-white'
                  }`}
                >
                  ✓ Instant Success
                </button>

                <button
                  type="button"
                  onClick={() => setSimScenario('failure')}
                  className={`py-2 px-3 rounded-xl border font-semibold transition ${
                    simScenario === 'failure'
                      ? 'border-rose-500 bg-rose-950/30 text-rose-300 shadow-sm'
                      : 'border-slate-800 bg-slate-950 text-slate-400 hover:text-white'
                  }`}
                >
                  ✕ Bank Decline
                </button>

                <button
                  type="button"
                  onClick={() => setSimScenario('timeout')}
                  className={`py-2 px-3 rounded-xl border font-semibold transition ${
                    simScenario === 'timeout'
                      ? 'border-amber-500 bg-amber-950/30 text-amber-300 shadow-sm'
                      : 'border-slate-800 bg-slate-950 text-slate-400 hover:text-white'
                  }`}
                >
                  ⏱ Gateway Timeout
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              id="checkout-submit-btn"
              data-action="submit-checkout"
              className="w-full py-4 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-2xl text-base transition shadow-xl shadow-cyan-950/40 flex items-center justify-center gap-2"
            >
              <ShieldCheck className="w-5 h-5 text-slate-950" />
              <span>Confirm &amp; Settle ₹{payableAmount.toLocaleString()} (Mock)</span>
            </button>
          </div>

          {/* Order Summary Sidebar (5 cols) */}
          <div className="lg:col-span-5">
            <div className="bg-slate-900/60 border border-slate-800 rounded-3xl p-6 sticky top-28 shadow-2xl space-y-6">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                Order &amp; Vehicle Summary
              </h3>

              {vehicle && (
                <div className="space-y-4 pb-5 border-b border-slate-800">
                  <div className="flex gap-4 items-center">
                    <img
                      src={vehicle.image_url || (vehicle.images ? vehicle.images[0] : 'https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80')}
                      alt={vehicle.model}
                      className="w-20 h-16 object-cover rounded-xl bg-slate-950 border border-slate-800 shrink-0"
                    />
                    <div>
                      <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-400">
                        {vehicle.brand}
                      </span>
                      <h4 className="text-base font-bold text-white">{vehicle.model}</h4>
                      <p className="text-xs text-slate-400">
                        {vehicle.year} • {vehicle.transmission?.value || vehicle.transmission} • {vehicle.fuel_type?.value || vehicle.fuel_type}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Price Breakdown */}
              <div className="space-y-3 text-xs text-slate-300">
                <div className="flex justify-between">
                  <span className="text-slate-400">Order Reference:</span>
                  <span className="font-mono text-white font-semibold">{orderId}</span>
                </div>

                {isRent ? (
                  <>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Daily Fleet Rate:</span>
                      <span className="font-medium text-white">₹{dailyRate.toLocaleString()} / day</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Duration:</span>
                      <span className="font-medium text-white">{durationDays} Days</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Rental Subtotal:</span>
                      <span className="font-medium text-white">₹{rentalSubtotal.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Taxes &amp; Fees (GST 18%):</span>
                      <span className="font-medium text-white">₹{rentalTaxes.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Refundable Security Deposit:</span>
                      <span className="text-emerald-400 font-semibold">₹{securityDeposit.toLocaleString()} (Hold)</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Vehicle Total Price:</span>
                      <span className="font-medium text-white">₹{purchasePrice.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Certification &amp; Inspection:</span>
                      <span className="text-emerald-400 font-semibold">Complimentary</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Reservation Token Deposit:</span>
                      <span className="font-medium text-white">₹25,000</span>
                    </div>
                  </>
                )}

                <div className="pt-4 border-t border-slate-800 flex justify-between items-baseline">
                  <div>
                    <span className="text-xs uppercase font-bold text-slate-400 block">Total Due Now</span>
                    <span className="text-[11px] text-slate-500">Inclusive of all applicable sandbox taxes</span>
                  </div>
                  <span className="text-2xl font-bold text-cyan-400">₹{payableAmount.toLocaleString()}</span>
                </div>
              </div>

              <div className="p-3 bg-slate-950/80 rounded-2xl border border-slate-800/80 text-[11px] text-slate-400 leading-relaxed">
                🛡️ <strong>Authoritative Guarantee:</strong> Completing this mock payment immediately updates your persistent MongoDB account records and notifies Aura AI Consultant via real-time SSE.
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
