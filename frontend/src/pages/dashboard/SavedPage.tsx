import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { useVehicleStore } from '../../store/vehicleStore';
import { useConsultantStore } from '../../store/consultantStore';
import { sendMessage } from '../../services/api';
import { Heart, Sparkles, Trash2, ArrowRight } from 'lucide-react';

export const SavedPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, toggleSaved } = useAuthStore();
  const { vehicles } = useVehicleStore();
  const { setIsOpen, sessionId, addMessage } = useConsultantStore();

  const savedVehiclesList = vehicles.filter((v) =>
    user?.saved_vehicles?.includes(v.id)
  );

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

  const formatPrice = (val?: number) => {
    if (!val) return '₹0';
    if (val >= 10000000) return `₹${(val / 10000000).toFixed(2)} Cr`;
    if (val >= 100000) return `₹${(val / 100000).toFixed(2)} Lakh`;
    return `₹${val.toLocaleString('en-IN')}`;
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/30 text-rose-400 text-[11px] font-bold uppercase tracking-wider mb-1">
          <Heart className="w-3.5 h-3.5" /> Saved Shortlist
        </div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Saved Vehicles</h2>
        <p className="text-xs text-slate-400">
          Vehicles you have bookmarked for comparison, purchase token reserve, or future rental booking.
        </p>
      </div>

      {savedVehiclesList.length === 0 ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-12 text-center">
          <Heart className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-white">Your shortlist is empty</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-5">
            Click the heart icon on any vehicle card in the catalogue to save it to your dashboard.
          </p>
          <button
            type="button"
            onClick={() => navigate('/explore')}
            className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-lg"
          >
            Explore Catalogue
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {savedVehiclesList.map((car) => (
            <div
              key={car.id}
              className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-4 shadow-xl flex flex-col justify-between"
            >
              <div>
                <img
                  src={car.images?.[0] || 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=400&q=80'}
                  alt={`${car.brand} ${car.model}`}
                  className="w-full h-40 object-cover rounded-xl border border-slate-800 mb-3"
                />
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-sm font-bold text-white">{car.brand} {car.model}</h3>
                    <p className="text-xs text-slate-400">{car.category} • {car.year}</p>
                  </div>
                  <span className="text-sm font-black text-cyan-400">{formatPrice(car.purchase_price)}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-3 border-t border-slate-800 mt-4">
                <button
                  type="button"
                  onClick={() => handleAskAiAboutSaved(`${car.brand} ${car.model}`)}
                  className="flex-1 py-2 px-3 rounded-xl bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-xs font-bold transition-all flex items-center justify-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Ask AI Briefing</span>
                </button>
                <button
                  type="button"
                  onClick={() => toggleSaved(car.id)}
                  title="Remove from saved"
                  className="p-2 rounded-xl bg-slate-800 hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-colors"
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
