import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useVehicleStore } from '../store/vehicleStore';
import { useAuthStore } from '../store/authStore';
import { calculateBookingTotal, createBooking } from '../services/api';
import { Calendar, MapPin, ShieldCheck, CheckCircle2, ChevronRight, AlertCircle, CreditCard } from 'lucide-react';

const ADDON_OPTIONS = [
  { id: 'zero_dep', label: 'Zero-Dep Comprehensive Protection', pricePerDay: 750, desc: 'Zero liability for accidental scratches or dents' },
  { id: 'child_seat', label: 'Child Safety ISOFIX Seat', pricePerDay: 250, desc: 'ECE R44/04 certified safety seat' },
  { id: 'gps_device', label: 'High-Precision Live GPS Tracker', pricePerDay: 200, desc: 'Real-time telemetry and navigation unit' },
  { id: 'express_delivery', label: 'Doorstep Concierge Delivery', flatPrice: 999, desc: 'Handover at your exact address' },
];

export const Booking: React.FC = () => {
  const { vehicleId } = useParams<{ vehicleId: string }>();
  const navigate = useNavigate();
  const { getVehicleById } = useVehicleStore();
  const { user } = useAuthStore();

  const vehicle = vehicleId ? getVehicleById(vehicleId) : undefined;

  // Booking form state
  const [pickupDate, setPickupDate] = useState('2026-12-15');
  const [returnDate, setReturnDate] = useState('2026-12-20');
  const [selectedAddons, setSelectedAddons] = useState<string[]>(['zero_dep']);
  const [driverName, setDriverName] = useState(user?.name || 'Alex Vance');
  const [driverEmail, setDriverEmail] = useState(user?.email || 'demo@auramotors.com');
  const [driverPhone, setDriverPhone] = useState(user?.phone || '+91 98765 43210');
  const [licenseNumber, setLicenseNumber] = useState('DL-04-20220019283');
  const [pickupLocation, setPickupLocation] = useState(vehicle?.location || 'Delhi');

  // Calculation state
  const [pricingSummary, setPricingSummary] = useState<{
    duration_days: number;
    base_price: number;
    addons_total: number;
    deposit_amount: number;
    tax_amount: number;
    total_amount: number;
  } | null>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Recalculate price whenever dates or addons change
  useEffect(() => {
    if (!vehicle) return;

    const p = new Date(pickupDate).getTime();
    const r = new Date(returnDate).getTime();
    let days = Math.max(1, Math.round((r - p) / (1000 * 60 * 60 * 24)));
    if (isNaN(days) || days < 1) days = 1;

    calculateBookingTotal(vehicle.id, days, selectedAddons)
      .then((res) => {
        setPricingSummary(res);
      })
      .catch(() => {
        // Local calculation fallback
        const base = vehicle.rental_price_per_day * days;
        let addonsCost = 0;
        selectedAddons.forEach((aid) => {
          const opt = ADDON_OPTIONS.find((o) => o.id === aid);
          if (opt) {
            addonsCost += opt.flatPrice ? opt.flatPrice : (opt.pricePerDay || 0) * days;
          }
        });
        const deposit = 10000;
        const tax = Math.round((base + addonsCost) * 0.18);
        setPricingSummary({
          duration_days: days,
          base_price: base,
          addons_total: addonsCost,
          deposit_amount: deposit,
          tax_amount: tax,
          total_amount: base + addonsCost + deposit + tax,
        });
      });
  }, [vehicle, pickupDate, returnDate, selectedAddons]);

  const toggleAddon = (id: string) => {
    setSelectedAddons((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const handleProceedToPayment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!vehicle || !pricingSummary) return;

    setLoading(true);
    setError(null);

    const payload = {
      vehicle_id: vehicle.id,
      customer_name: driverName,
      customer_email: driverEmail,
      customer_phone: driverPhone,
      license_number: licenseNumber,
      pickup_city: pickupLocation,
      pickup_date: pickupDate,
      return_date: returnDate,
      duration_days: pricingSummary.duration_days,
      selected_addons: selectedAddons,
      total_amount: pricingSummary.total_amount,
    };

    try {
      const res = await createBooking(payload);
      const bookingId = res.booking_id || res.id;
      navigate(`/checkout/${bookingId}`, { state: { booking: res, vehicle } });
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Unable to confirm booking. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!vehicle) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 pt-32 pb-20 flex items-center justify-center">
        <div className="text-center p-8 bg-slate-900 border border-slate-800 rounded-2xl max-w-md">
          <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold mb-2">Vehicle Not Found</h2>
          <p className="text-slate-400 text-sm mb-6">
            The vehicle you are trying to reserve could not be located in our fleet registry.
          </p>
          <Link
            to="/rent"
            className="px-6 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg font-medium text-sm transition"
          >
            Explore Rental Fleet
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-28 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <div className="flex items-center space-x-2 text-xs text-slate-400 mb-6">
          <Link to="/" className="hover:text-white transition">Home</Link>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
          <Link to="/rent" className="hover:text-white transition">Rent Fleet</Link>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
          <Link to={`/vehicles/${vehicle.id}`} className="hover:text-white transition">{vehicle.brand} {vehicle.model}</Link>
          <ChevronRight className="w-3.5 h-3.5 text-slate-600" />
          <span className="text-cyan-400">Reservation</span>
        </div>

        <div className="mb-8 border-b border-slate-800 pb-6">
          <span className="text-xs font-semibold tracking-widest uppercase text-cyan-400">
            Secure Fleet Reservation
          </span>
          <h1 className="text-3xl md:text-4xl font-light tracking-tight mt-1">
            Complete Your <span className="font-semibold text-white">Booking</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Confirm your journey schedule, driver credentials, and concierge protection.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-300 text-sm flex items-center">
            <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleProceedToPayment} className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Form Details (7 cols) */}
          <div className="lg:col-span-7 space-y-8">
            {/* Step 1: Dates & City */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                <Calendar className="w-5 h-5 text-cyan-400 mr-2.5" />
                Journey Schedule & City
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Pickup Date</label>
                  <input
                    type="date"
                    value={pickupDate}
                    onChange={(e) => setPickupDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Return Date</label>
                  <input
                    type="date"
                    value={returnDate}
                    onChange={(e) => setReturnDate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1.5">Pickup Hub / City</label>
                <div className="relative">
                  <MapPin className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <select
                    value={pickupLocation}
                    onChange={(e) => setPickupLocation(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="Delhi">Delhi NCR (Aerocity / IGI Airport Fleet Terminal)</option>
                    <option value="Mumbai">Mumbai (BKC & Chhatrapati Shivaji Int'l Hub)</option>
                    <option value="Bengaluru">Bengaluru (Indiranagar & Kempegowda Int'l Hub)</option>
                    <option value="Hyderabad">Hyderabad (Gachibowli Financial District Hub)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Step 2: Protection & Add-ons */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-medium text-white mb-2 flex items-center">
                <ShieldCheck className="w-5 h-5 text-cyan-400 mr-2.5" />
                Concierge Protection & Upgrades
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                Tailor your reservation with comprehensive zero-dep coverage and accessories.
              </p>

              <div className="space-y-3">
                {ADDON_OPTIONS.map((addon) => {
                  const isChecked = selectedAddons.includes(addon.id);
                  return (
                    <div
                      key={addon.id}
                      onClick={() => toggleAddon(addon.id)}
                      className={`p-4 rounded-xl border cursor-pointer transition flex items-center justify-between ${
                        isChecked
                          ? 'bg-cyan-950/20 border-cyan-500/50'
                          : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div
                          className={`w-5 h-5 rounded mt-0.5 flex items-center justify-center border transition ${
                            isChecked
                              ? 'bg-cyan-500 border-cyan-500 text-slate-950'
                              : 'border-slate-600 bg-slate-900'
                          }`}
                        >
                          {isChecked && <CheckCircle2 className="w-3.5 h-3.5" />}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white">{addon.label}</p>
                          <p className="text-xs text-slate-400">{addon.desc}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="text-sm font-semibold text-cyan-300">
                          {addon.flatPrice ? `₹${addon.flatPrice} flat` : `₹${addon.pricePerDay}/day`}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Step 3: Driver Details */}
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-lg font-medium text-white mb-4 flex items-center">
                <CheckCircle2 className="w-5 h-5 text-cyan-400 mr-2.5" />
                Driver Credentials
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Full Name (as on DL)</label>
                  <input
                    type="text"
                    value={driverName}
                    onChange={(e) => setDriverName(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Email Address</label>
                  <input
                    type="email"
                    value={driverEmail}
                    onChange={(e) => setDriverEmail(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Phone Number</label>
                  <input
                    type="tel"
                    value={driverPhone}
                    onChange={(e) => setDriverPhone(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-400 mb-1.5">Driver's License Number</label>
                  <input
                    type="text"
                    value={licenseNumber}
                    onChange={(e) => setLicenseNumber(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                    required
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Order Summary (5 cols) */}
          <div className="lg:col-span-5">
            <div className="sticky top-28 bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
              {/* Vehicle preview card */}
              <div className="flex space-x-4 pb-6 border-b border-slate-800">
                <img
                  src={vehicle.image_url || 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=400&q=80'}
                  alt={vehicle.model}
                  className="w-24 h-20 rounded-xl object-cover bg-slate-950 border border-slate-800"
                />
                <div>
                  <span className="text-[10px] font-bold tracking-widest uppercase text-cyan-400">
                    {vehicle.brand}
                  </span>
                  <h4 className="text-base font-semibold text-white">{vehicle.model}</h4>
                  <p className="text-xs text-slate-400 mt-1 capitalize">
                    {vehicle.category} • {vehicle.transmission}
                  </p>
                  <p className="text-xs text-slate-300 font-medium mt-1">
                    ₹{vehicle.rental_price_per_day.toLocaleString()} <span className="text-slate-400 font-normal">/ day</span>
                  </p>
                </div>
              </div>

              {/* Price Details */}
              <div className="py-6 space-y-3 text-sm border-b border-slate-800">
                <div className="flex justify-between text-slate-300">
                  <span>
                    Rental Base ({pricingSummary?.duration_days || 1} day{pricingSummary?.duration_days === 1 ? '' : 's'})
                  </span>
                  <span className="text-white font-medium">₹{pricingSummary?.base_price.toLocaleString()}</span>
                </div>

                {pricingSummary && pricingSummary.addons_total > 0 && (
                  <div className="flex justify-between text-slate-300">
                    <span>Selected Add-ons & Coverage</span>
                    <span className="text-white font-medium">₹{pricingSummary.addons_total.toLocaleString()}</span>
                  </div>
                )}

                <div className="flex justify-between text-slate-300">
                  <span className="flex items-center">
                    Refundable Security Deposit
                    <span className="ml-1 text-[10px] text-cyan-400 bg-cyan-950/60 px-1.5 py-0.5 rounded border border-cyan-800/40">Refundable</span>
                  </span>
                  <span className="text-white font-medium">₹{pricingSummary?.deposit_amount.toLocaleString()}</span>
                </div>

                <div className="flex justify-between text-slate-300">
                  <span>GST (18%)</span>
                  <span className="text-white font-medium">₹{pricingSummary?.tax_amount.toLocaleString()}</span>
                </div>
              </div>

              {/* Total Due */}
              <div className="py-4 flex justify-between items-baseline">
                <div>
                  <span className="text-xs uppercase tracking-wider text-slate-400">Total Payable</span>
                  <p className="text-xs text-slate-400">Includes refundable deposit & taxes</p>
                </div>
                <div className="text-right">
                  <span className="text-2xl font-bold text-cyan-400">
                    ₹{pricingSummary?.total_amount.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Submit CTA */}
              <button
                type="submit"
                disabled={loading}
                className="w-full mt-4 py-3.5 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 text-slate-950 font-bold rounded-xl transition shadow-lg shadow-cyan-950/40 flex items-center justify-center space-x-2"
              >
                <CreditCard className="w-5 h-5" />
                <span>{loading ? 'Securing Fleet Unit...' : 'Proceed to Mock Checkout'}</span>
              </button>

              <div className="mt-4 pt-4 border-t border-slate-800/60 text-center">
                <p className="text-[11px] text-slate-400 leading-relaxed">
                  🔒 Secured with 256-bit simulated encryption. In accordance with hackathon guidelines, all financial transactions are purely simulated.
                </p>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
