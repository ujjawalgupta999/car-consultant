import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConsultantStore } from '../store/consultantStore';
import { useAuthStore } from '../store/authStore';
import {
  Car,
  Tag,
  CheckCircle2,
  ShieldCheck,
  ChevronRight,
  ChevronLeft,
  Sparkles,
  DollarSign,
  MapPin,
  Camera,
  User,
  Phone,
  Mail,
  AlertCircle,
} from 'lucide-react';

export const SellCarPage: React.FC = () => {
  const navigate = useNavigate();
  const { sellDraft, setSellDraft } = useConsultantStore();
  const { user } = useAuthStore();

  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Form State initialized with AI sellDraft if available
  const [formData, setFormData] = useState({
    brand: sellDraft?.brand || 'Honda',
    model: sellDraft?.model || 'City',
    variant: sellDraft?.variant || 'ZX 1.5 i-VTEC',
    year: sellDraft?.year || 2021,
    registration_year: sellDraft?.year || 2021,
    fuel_type: sellDraft?.fuel_type || 'Petrol',
    transmission: sellDraft?.transmission || 'Automatic',
    kms_driven: sellDraft?.kms_driven || 32000,
    condition: 'Excellent',
    ownership_count: 1,
    expected_price: sellDraft?.expected_price ? sellDraft.expected_price / 100000 : 11.8,
    location: sellDraft?.location || 'Delhi NCR',
    is_registered_in_user_name: sellDraft?.is_registered_in_user_name ?? true,
    images: [
      'https://images.unsplash.com/photo-1590362891988-f77804702088?auto=format&fit=crop&w=800&q=80',
    ],
    contact_name: user?.name || 'Alex Vance',
    contact_phone: user?.phone || '+91 98765 43210',
    contact_email: user?.email || 'demo@auramotors.com',
  });

  // Sync if sellDraft arrives after component mount
  useEffect(() => {
    if (sellDraft) {
      setFormData((prev) => ({
        ...prev,
        brand: sellDraft.brand || prev.brand,
        model: sellDraft.model || prev.model,
        variant: sellDraft.variant || prev.variant,
        year: sellDraft.year || prev.year,
        registration_year: sellDraft.year || prev.registration_year,
        fuel_type: sellDraft.fuel_type || prev.fuel_type,
        transmission: sellDraft.transmission || prev.transmission,
        kms_driven: sellDraft.kms_driven || prev.kms_driven,
        expected_price: sellDraft.expected_price ? sellDraft.expected_price / 100000 : prev.expected_price,
        location: sellDraft.location || prev.location,
        is_registered_in_user_name: sellDraft.is_registered_in_user_name ?? prev.is_registered_in_user_name,
      }));
    }
  }, [sellDraft]);

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmitListing = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    const payload = {
      brand: formData.brand,
      model: formData.model,
      variant: formData.variant,
      year: Number(formData.year),
      registration_year: Number(formData.registration_year),
      fuel_type: formData.fuel_type,
      transmission: formData.transmission,
      kms_driven: Number(formData.kms_driven),
      condition: formData.condition,
      ownership_count: Number(formData.ownership_count),
      location: formData.location,
      expected_price: Number(formData.expected_price) * 100000,
      images: formData.images,
      contact_name: formData.contact_name,
      contact_phone: formData.contact_phone,
      contact_email: formData.contact_email,
      is_registered_in_user_name: formData.is_registered_in_user_name,
    };

    try {
      const res = await fetch('/api/listings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to submit vehicle listing');
      }

      const data = await res.json();
      setSuccessMessage('Vehicle listing created successfully!');
      // Clear sell draft
      setSellDraft(null);
      setTimeout(() => {
        navigate('/dashboard/listings');
      }, 1200);
    } catch (err: any) {
      setErrorMessage(err.message || 'Error publishing listing');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-24 pb-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 text-center sm:text-left">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-xs font-bold uppercase tracking-wider mb-2">
            <Tag className="w-3.5 h-3.5" /> Sell Your Car on Aura Motors
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
            Certified Vehicle Seller Portal
          </h1>
          <p className="text-xs text-slate-400 mt-2">
            Get instant market exposure to over 40,000 verified buyers with digital RC verification and escrow payments.
          </p>
        </div>

        {/* AI Prefill Notice if active */}
        {sellDraft && (
          <div className="mb-6 rounded-2xl border border-cyan-500/40 bg-cyan-950/30 p-4 flex items-center justify-between shadow-xl">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-cyan-500/20 text-cyan-300 flex items-center justify-center">
                <Sparkles className="w-5 h-5" />
              </div>
              <div className="text-xs">
                <span className="font-bold text-white block">Pre-filled by Aura AI Consultant</span>
                Extracted specifications from your conversation have been populated below.
              </div>
            </div>
            <span className="text-[10px] font-bold uppercase tracking-wider bg-cyan-500/20 text-cyan-300 px-2.5 py-1 rounded-full">
              AI Active
            </span>
          </div>
        )}

        {/* Step Indicator */}
        <div className="mb-8 flex items-center justify-between border-b border-slate-800 pb-4">
          {[
            { num: 1, label: 'Basics' },
            { num: 2, label: 'Condition' },
            { num: 3, label: 'Pricing' },
            { num: 4, label: 'Verification' },
            { num: 5, label: 'Review' },
          ].map((s) => (
            <div key={s.num} className="flex items-center space-x-2">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  step === s.num
                    ? 'bg-cyan-500 text-slate-950 shadow-md shadow-cyan-500/30'
                    : step > s.num
                    ? 'bg-emerald-500 text-slate-950'
                    : 'bg-slate-800 text-slate-400'
                }`}
              >
                {step > s.num ? '✓' : s.num}
              </div>
              <span
                className={`text-xs font-semibold hidden sm:inline ${
                  step === s.num ? 'text-white' : 'text-slate-400'
                }`}
              >
                {s.label}
              </span>
            </div>
          ))}
        </div>

        {/* Form Card */}
        <div className="rounded-3xl border border-slate-800 bg-slate-900/60 p-6 sm:p-10 shadow-2xl backdrop-blur-xl">
          {errorMessage && (
            <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400" />
              <span>{errorMessage}</span>
            </div>
          )}

          {successMessage && (
            <div className="mb-6 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{successMessage} Redirecting to your listings...</span>
            </div>
          )}

          <form onSubmit={handleSubmitListing}>
            {/* STEP 1: Vehicle Basics */}
            {step === 1 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-white mb-2">Step 1: Vehicle Brand & Model</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Brand / Make</label>
                    <input
                      type="text"
                      value={formData.brand}
                      onChange={(e) => handleChange('brand', e.target.value)}
                      required
                      placeholder="e.g. Honda, Hyundai, Tata"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Model Name</label>
                    <input
                      type="text"
                      value={formData.model}
                      onChange={(e) => handleChange('model', e.target.value)}
                      required
                      placeholder="e.g. City, Creta, Harrier"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Variant / Trim</label>
                    <input
                      type="text"
                      value={formData.variant}
                      onChange={(e) => handleChange('variant', e.target.value)}
                      placeholder="e.g. ZX 1.5 i-VTEC CVT"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Manufacturing Year</label>
                    <select
                      value={formData.year}
                      onChange={(e) => handleChange('year', Number(e.target.value))}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    >
                      {[2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016].map((yr) => (
                        <option key={yr} value={yr}>
                          {yr}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2: Technical & Condition */}
            {step === 2 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-white mb-2">Step 2: Technical Specifications & Condition</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Fuel Type</label>
                    <select
                      value={formData.fuel_type}
                      onChange={(e) => handleChange('fuel_type', e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    >
                      <option value="Petrol">Petrol</option>
                      <option value="Diesel">Diesel</option>
                      <option value="Electric">Electric</option>
                      <option value="Hybrid">Hybrid</option>
                      <option value="CNG">CNG</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Transmission</label>
                    <select
                      value={formData.transmission}
                      onChange={(e) => handleChange('transmission', e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    >
                      <option value="Automatic">Automatic</option>
                      <option value="Manual">Manual</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Kilometers Driven</label>
                    <input
                      type="number"
                      value={formData.kms_driven}
                      onChange={(e) => handleChange('kms_driven', Number(e.target.value))}
                      placeholder="e.g. 32000"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Overall Condition</label>
                    <select
                      value={formData.condition}
                      onChange={(e) => handleChange('condition', e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    >
                      <option value="Excellent">Excellent (Showroom condition)</option>
                      <option value="Good">Good (Minor cosmetic wear)</option>
                      <option value="Fair">Fair (Needs routine service)</option>
                    </select>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: Pricing & Location */}
            {step === 3 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-white mb-2">Step 3: Expected Pricing & Location</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">
                      Expected Selling Price (₹ in Lakhs)
                    </label>
                    <div className="relative">
                      <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-cyan-400 font-bold text-xs">
                        ₹
                      </span>
                      <input
                        type="number"
                        step="0.1"
                        value={formData.expected_price}
                        onChange={(e) => handleChange('expected_price', Number(e.target.value))}
                        className="w-full pl-8 pr-12 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500 font-bold"
                      />
                      <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-xs">
                        Lakh
                      </span>
                    </div>
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Location City / Hub</label>
                    <input
                      type="text"
                      value={formData.location}
                      onChange={(e) => handleChange('location', e.target.value)}
                      placeholder="e.g. Delhi NCR, Mumbai, Bangalore"
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* STEP 4: Verification & Ownership */}
            {step === 4 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-white mb-2">Step 4: Ownership & Contact Verification</h3>

                {/* Registration Checkbox */}
                <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex items-start space-x-3">
                  <input
                    type="checkbox"
                    id="is_reg"
                    checked={formData.is_registered_in_user_name}
                    onChange={(e) => handleChange('is_registered_in_user_name', e.target.checked)}
                    className="mt-1 w-4 h-4 accent-cyan-500 rounded cursor-pointer"
                  />
                  <label htmlFor="is_reg" className="text-xs cursor-pointer">
                    <span className="font-bold text-white block">
                      Vehicle is registered in my name (First / Second Owner)
                    </span>
                    <span className="text-slate-400">
                      I confirm that I hold valid RC title ownership and authority to list this vehicle.
                    </span>
                  </label>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Seller Contact Name</label>
                    <input
                      type="text"
                      value={formData.contact_name}
                      onChange={(e) => handleChange('contact_name', e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-bold text-slate-400 block mb-1">Contact Phone</label>
                    <input
                      type="text"
                      value={formData.contact_phone}
                      onChange={(e) => handleChange('contact_phone', e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* STEP 5: Review & Submit */}
            {step === 5 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-white mb-2">Step 5: Review & Confirm Listing</h3>
                <div className="rounded-2xl bg-slate-950 border border-slate-800 p-5 space-y-3 text-xs">
                  <div className="flex justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-500">Vehicle:</span>
                    <span className="font-bold text-white">
                      {formData.year} {formData.brand} {formData.model} ({formData.variant})
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-500">Powertrain:</span>
                    <span className="text-slate-200">
                      {formData.fuel_type} • {formData.transmission} • {Number(formData.kms_driven).toLocaleString('en-IN')} km
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-500">Asking Price:</span>
                    <span className="text-cyan-400 font-black text-sm">
                      ₹{formData.expected_price} Lakh (₹{(Number(formData.expected_price) * 100000).toLocaleString('en-IN')})
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-slate-800/80 pb-2">
                    <span className="text-slate-500">Location:</span>
                    <span className="text-slate-200">{formData.location}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Ownership:</span>
                    <span className="font-semibold text-emerald-400">
                      {formData.is_registered_in_user_name ? 'Registered in User Name' : 'Third Party / Company'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Form Controls / Navigation */}
            <div className="flex items-center justify-between pt-6 border-t border-slate-800 mt-6">
              {step > 1 ? (
                <button
                  type="button"
                  onClick={() => setStep((s) => s - 1)}
                  className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white transition-all"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span>Previous</span>
                </button>
              ) : (
                <div></div>
              )}

              {step < 5 ? (
                <button
                  type="button"
                  onClick={() => setStep((s) => s + 1)}
                  className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 text-xs font-bold transition-all shadow-md"
                >
                  <span>Continue</span>
                  <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 text-xs font-black uppercase tracking-wider transition-all shadow-lg hover:brightness-110 disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <span>Publishing Listing...</span>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Submit & Publish Listing</span>
                    </>
                  )}
                </button>
              )}
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

