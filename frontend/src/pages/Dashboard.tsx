import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { useVehicleStore } from '../store/vehicleStore';
import { useConsultantStore } from '../store/consultantStore';
import { sendMessage } from '../services/api';
import {
  User,
  Calendar,
  Heart,
  FileText,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Clock,
  ArrowRight,
  LogOut,
  Car,
  Trash2,
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout, toggleSaved } = useAuthStore();
  const { vehicles } = useVehicleStore();
  const { setIsOpen, sessionId, addMessage } = useConsultantStore();

  const [activeTab, setActiveTab] = useState<'bookings' | 'saved' | 'enquiries'>('bookings');

  const savedVehiclesList = vehicles.filter((v) =>
    user?.saved_vehicles?.includes(v.id)
  );

  const mockActiveBookings = [
    {
      id: 'BK-2026-91823',
      vehicleId: 'CAR-001',
      vehicleName: 'BMW M3 Competition xDrive',
      image: 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=600&q=80',
      dates: '15 Dec 2026 – 20 Dec 2026',
      city: 'Delhi NCR (Aerocity VIP Hub)',
      status: 'CONFIRMED',
      total: 75000,
    },
    {
      id: 'BK-2026-88102',
      vehicleId: 'CAR-021',
      vehicleName: 'Audi RS6 Avant Quattro',
      image: 'https://images.unsplash.com/photo-1603584173870-7f23fdae1b7a?auto=format&fit=crop&w=600&q=80',
      dates: '02 Jan 2027 – 05 Jan 2027',
      city: 'Mumbai (BKC Hub)',
      status: 'CONFIRMED',
      total: 54000,
    },
  ];

  const handleAskAiAboutSaved = async (vehicleName: string) => {
    setIsOpen(true);
    const prompt = `Give me a full concierge briefing on my saved vehicle: ${vehicleName}. What are its ownership highlights, resale stability, and current rental demand?`;
    addMessage({
      id: `msg_user_${Date.now()}`,
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString(),
    });
    try {
      const res = await sendMessage(sessionId, prompt);
      if (res && res.response) {
        addMessage({
          id: `msg_ai_${Date.now()}`,
          role: 'assistant',
          content: res.response,
          timestamp: new Date().toISOString(),
        });
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-28 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* User Banner */}
        <div className="bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 border border-slate-800 rounded-3xl p-8 mb-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center space-x-5">
            <div className="w-16 h-16 rounded-2xl bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-300 font-bold text-2xl">
              {user?.name ? user.name.charAt(0) : 'U'}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl font-bold text-white">{user?.name || 'Aura Guest'}</h1>
                <span className="text-[10px] uppercase font-bold tracking-widest text-cyan-400 bg-cyan-950/80 px-2.5 py-0.5 rounded-full border border-cyan-800/40">
                  Verified Member
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">{user?.email || 'demo@auramotors.com'} • {user?.phone || '+91 98765 43210'}</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setIsOpen(true)}
              className="px-4 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-semibold transition flex items-center space-x-2"
            >
              <Sparkles className="w-4 h-4 text-cyan-200" />
              <span>Launch AI Consultant</span>
            </button>
            <button
              onClick={() => {
                logout();
                navigate('/login');
              }}
              className="p-2.5 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white rounded-xl transition"
              title="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-2 border-b border-slate-800 mb-8">
          <button
            onClick={() => setActiveTab('bookings')}
            className={`pb-4 px-4 text-sm font-medium border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'bookings'
                ? 'border-cyan-400 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>Active Reservations ({mockActiveBookings.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('saved')}
            className={`pb-4 px-4 text-sm font-medium border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'saved'
                ? 'border-cyan-400 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Heart className="w-4 h-4" />
            <span>Saved Fleet ({savedVehiclesList.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('enquiries')}
            className={`pb-4 px-4 text-sm font-medium border-b-2 transition flex items-center space-x-2 ${
              activeTab === 'enquiries'
                ? 'border-cyan-400 text-cyan-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Purchase Enquiries (1)</span>
          </button>
        </div>

        {/* Tab 1: Bookings */}
        {activeTab === 'bookings' && (
          <div className="space-y-4">
            {mockActiveBookings.map((b) => (
              <div
                key={b.id}
                className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-6 hover:border-slate-700 transition"
              >
                <div className="flex items-center space-x-4">
                  <img
                    src={b.image}
                    alt={b.vehicleName}
                    className="w-24 h-20 object-cover rounded-xl bg-slate-950 border border-slate-800"
                  />
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono text-cyan-400 font-semibold">{b.id}</span>
                      <span className="text-[10px] bg-emerald-950/80 text-emerald-400 border border-emerald-800/40 px-2 py-0.5 rounded-full font-semibold">
                        {b.status}
                      </span>
                    </div>
                    <h3 className="text-base font-semibold text-white mt-1">{b.vehicleName}</h3>
                    <p className="text-xs text-slate-400 mt-1 flex items-center">
                      <Clock className="w-3.5 h-3.5 mr-1 text-slate-500" />
                      {b.dates} • {b.city}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between md:justify-end md:space-x-6 border-t md:border-t-0 pt-4 md:pt-0 border-slate-800">
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Total Settled</span>
                    <p className="text-base font-bold text-white">₹{b.total.toLocaleString()}</p>
                  </div>
                  <Link
                    to={`/vehicles/${b.vehicleId}`}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-medium transition"
                  >
                    View Fleet Unit
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Tab 2: Saved Vehicles */}
        {activeTab === 'saved' && (
          <div>
            {savedVehiclesList.length === 0 ? (
              <div className="text-center py-16 bg-slate-900/40 rounded-2xl border border-slate-800/80 p-8">
                <Car className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h3 className="text-lg font-medium text-white">No saved vehicles</h3>
                <p className="text-xs text-slate-400 mt-1 mb-6">
                  Click the heart icon on any vehicle card to save it to your client garage.
                </p>
                <Link
                  to="/explore"
                  className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold transition"
                >
                  Browse Catalogue
                </Link>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {savedVehiclesList.map((v) => (
                  <div
                    key={v.id}
                    className="bg-slate-900/50 border border-slate-800 rounded-2xl overflow-hidden hover:border-slate-700 transition flex flex-col"
                  >
                    <div className="relative h-44 bg-slate-950">
                      <img src={v.image_url || 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=600&q=80'} alt={v.model} className="w-full h-full object-cover" />
                      <button
                        onClick={() => toggleSaved(v.id)}
                        className="absolute top-3 right-3 p-2 bg-slate-900/80 hover:bg-rose-950 text-rose-400 rounded-lg transition"
                        title="Remove from saved"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>

                    <div className="p-5 flex-1 flex flex-col justify-between">
                      <div>
                        <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">
                          {v.brand}
                        </span>
                        <h4 className="text-base font-semibold text-white">{v.model}</h4>
                        <p className="text-xs text-slate-400 mt-1 capitalize">
                          {v.category} • {v.transmission} • {v.fuel_type}
                        </p>
                      </div>

                      <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between">
                        <div>
                          <span className="text-xs text-slate-400">Rent</span>
                          <p className="text-sm font-bold text-white">₹{v.rental_price_per_day.toLocaleString()}/d</p>
                        </div>
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleAskAiAboutSaved(`${v.brand} ${v.model}`)}
                            className="p-2 bg-cyan-950/60 border border-cyan-800/40 text-cyan-400 hover:bg-cyan-900/60 rounded-lg text-xs transition"
                            title="Ask AI Strategist about this car"
                          >
                            <Sparkles className="w-4 h-4" />
                          </button>
                          <Link
                            to={`/vehicles/${v.id}`}
                            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-medium transition"
                          >
                            Details
                          </Link>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Purchase Enquiries */}
        {activeTab === 'enquiries' && (
          <div className="space-y-4">
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono text-cyan-400 font-semibold">ORD-2026-PUR-401</span>
                    <span className="text-[10px] bg-cyan-950 text-cyan-400 border border-cyan-800/40 px-2 py-0.5 rounded-full font-semibold">
                      Underwriter Review
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-white mt-1">
                    Porsche 911 Carrera (2024 Model Year)
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Direct Purchase • Quoted: ₹1,85,00,000 • Down Payment: ₹37,00,000 • 60-Month EMI: ₹3,12,000/mo
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => {
                      setIsOpen(true);
                      addMessage({
                        id: `msg_user_${Date.now()}`,
                        role: 'user',
                        content: 'Check the delivery timeline and registration paper status for order ORD-2026-PUR-401.',
                        timestamp: new Date().toISOString(),
                      });
                    }}
                    className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-medium transition flex items-center space-x-1.5"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Check AI Status</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
