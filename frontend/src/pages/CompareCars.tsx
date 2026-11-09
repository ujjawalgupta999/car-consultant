import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useComparisonStore } from '../store/comparisonStore';
import { useVehicleStore } from '../store/vehicleStore';
import { useConsultantStore } from '../store/consultantStore';
import { sendMessage } from '../services/api';
import { Sparkles, Trash2, Plus, Check, Zap } from 'lucide-react';

export const CompareCars: React.FC = () => {
  const { comparedVehicles, removeVehicle, clearComparison, addVehicle } = useComparisonStore();
  const { vehicles } = useVehicleStore();
  const { setIsOpen, sessionId, addMessage } = useConsultantStore();
  const [selectedAddId, setSelectedAddId] = useState('');
  const [isAskingAi, setIsAskingAi] = useState(false);

  const availableToAdd = vehicles.filter(
    (v) => !comparedVehicles.some((cv) => cv.id === v.id)
  );

  const handleAddFromDropdown = () => {
    if (!selectedAddId) return;
    const vehicle = vehicles.find((v) => v.id === selectedAddId);
    if (vehicle) {
      addVehicle(vehicle);
      setSelectedAddId('');
    }
  };

  const handleAskAiRecommendation = async () => {
    if (comparedVehicles.length < 2) return;
    setIsAskingAi(true);
    setIsOpen(true);

    const vehicleNames = comparedVehicles.map((v) => `${v.brand} ${v.model} (${v.year})`).join(' vs ');
    const prompt = `Please provide an objective, expert comparison between: ${vehicleNames}. Highlight their driving dynamics, fuel efficiency, ownership costs, and give me a clear verdict on which is the superior choice for daily urban driving vs long highway tours.`;

    addMessage({
      id: `msg_user_${Date.now()}`,
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString(),
    });

    try {
      const res = await sendMessage(sessionId, prompt);
      if (res && res.message) {
        addMessage(res.message);
      } else if (res && res.response) {
        addMessage({
          id: `msg_ai_${Date.now()}`,
          role: 'assistant',
          content: res.response,
          timestamp: new Date().toISOString(),
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsAskingAi(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-28 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-slate-800 pb-8 mb-8">
          <div>
            <span className="text-xs font-semibold tracking-widest uppercase text-cyan-400">
              Specification Benchmarking
            </span>
            <h1 className="text-3xl md:text-5xl font-light tracking-tight mt-1">
              Compare <span className="font-semibold text-white">Vehicles</span>
            </h1>
            <p className="text-slate-400 text-sm mt-2">
              Side-by-side technical evaluation and AI-assisted intelligence for your next drive.
            </p>
          </div>

          <div className="mt-4 md:mt-0 flex items-center space-x-3">
            {comparedVehicles.length > 0 && (
              <button
                onClick={clearComparison}
                className="px-4 py-2 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white rounded-lg text-sm transition"
              >
                Clear All
              </button>
            )}
            {comparedVehicles.length >= 2 && (
              <button
                onClick={handleAskAiRecommendation}
                disabled={isAskingAi}
                className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-lg text-sm font-medium transition shadow-lg shadow-cyan-900/30 flex items-center space-x-2"
              >
                <Sparkles className="w-4 h-4 text-cyan-200" />
                <span>{isAskingAi ? 'Analyzing...' : 'Ask AI Verdict'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Empty state */}
        {comparedVehicles.length === 0 ? (
          <div className="text-center py-24 bg-slate-900/40 rounded-2xl border border-slate-800/80 p-8">
            <div className="w-16 h-16 rounded-full bg-slate-800/60 flex items-center justify-center mx-auto mb-4 text-slate-400">
              <Zap className="w-8 h-8 text-cyan-400" />
            </div>
            <h3 className="text-xl font-medium text-white mb-2">No vehicles in comparison</h3>
            <p className="text-slate-400 max-w-md mx-auto text-sm mb-6">
              Select up to 4 vehicles from our catalogue or let our AI consultant assemble a custom comparison set for you.
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link
                to="/explore"
                className="px-6 py-2.5 bg-white text-slate-950 font-medium rounded-lg text-sm hover:bg-slate-200 transition"
              >
                Explore Catalogue
              </Link>
              <button
                onClick={() => {
                  setIsOpen(true);
                  handleAskAiRecommendation();
                }}
                className="px-6 py-2.5 bg-slate-800 text-white font-medium rounded-lg text-sm hover:bg-slate-700 transition flex items-center space-x-2"
              >
                <Sparkles className="w-4 h-4 text-cyan-400" />
                <span>Consult AI Strategist</span>
              </button>
            </div>
          </div>
        ) : (
          <div>
            {/* Quick add bar if fewer than 4 cars */}
            {comparedVehicles.length < 4 && (
              <div className="mb-6 bg-slate-900/60 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
                <span className="text-xs text-slate-400 flex items-center">
                  <Plus className="w-4 h-4 text-cyan-400 mr-1.5" />
                  Add another vehicle to compare ({comparedVehicles.length}/4 selected):
                </span>
                <div className="flex items-center space-x-2 w-full sm:w-auto">
                  <select
                    value={selectedAddId}
                    onChange={(e) => setSelectedAddId(e.target.value)}
                    className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 w-full sm:w-64"
                  >
                    <option value="">Select vehicle...</option>
                    {availableToAdd.map((v) => (
                      <option key={v.id} value={v.id}>
                        {v.brand} {v.model} ({v.category}) - ₹{(v.purchase_price / 100000).toFixed(2)} Lakh
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleAddFromDropdown}
                    disabled={!selectedAddId}
                    className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white rounded-lg text-xs font-medium transition"
                  >
                    Add
                  </button>
                </div>
              </div>
            )}

            {/* Comparison Grid Table */}
            <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/30">
              <table className="w-full border-collapse text-left">
                {/* Vehicle Cards Header */}
                <thead>
                  <tr className="border-b border-slate-800">
                    <th className="p-4 sm:p-6 w-48 text-xs font-semibold text-slate-400 uppercase tracking-wider bg-slate-900/60 align-bottom">
                      Model / Specs
                    </th>
                    {comparedVehicles.map((v) => (
                      <th key={v.id} className="p-4 sm:p-6 min-w-[240px] max-w-[320px] align-top relative">
                        <div className="relative group mb-3 rounded-lg overflow-hidden h-36 bg-slate-950 border border-slate-800">
                          <img
                            src={v.image_url || 'https://images.unsplash.com/photo-1555215695-3004980ad54e?auto=format&fit=crop&w=800&q=80'}
                            alt={v.model}
                            className="w-full h-full object-cover group-hover:scale-105 transition duration-500"
                          />
                          <button
                            onClick={() => removeVehicle(v.id)}
                            className="absolute top-2 right-2 p-1.5 bg-slate-900/80 hover:bg-rose-900/80 text-slate-300 hover:text-white rounded-md transition"
                            title="Remove from comparison"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                        <span className="text-[10px] font-semibold text-cyan-400 uppercase tracking-wider">
                          {v.brand}
                        </span>
                        <h4 className="text-base font-semibold text-white truncate">{v.model}</h4>
                        <div className="mt-2 flex flex-col gap-1">
                          <span className="text-xs text-slate-400">
                            Purchase: <strong className="text-white">₹{(v.purchase_price / 100000).toFixed(2)} Lakh</strong>
                          </span>
                        </div>
                        <div className="mt-3 flex items-center space-x-2">
                          <Link
                            to={`/vehicles/${v.id}`}
                            className="flex-1 py-1.5 text-center text-xs font-medium bg-slate-800 hover:bg-slate-700 text-white rounded transition"
                          >
                            Details
                          </Link>
                          <Link
                            to={`/checkout/${v.id}`}
                            className="flex-1 py-1.5 text-center text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white rounded transition"
                          >
                            Reserve
                          </Link>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-800/60 text-sm">
                  {/* Category */}
                  <tr className="hover:bg-slate-800/20">
                    <td className="p-4 font-medium text-slate-400 bg-slate-900/40 text-xs uppercase tracking-wider">
                      Segment / Category
                    </td>
                    {comparedVehicles.map((v) => (
                      <td key={v.id} className="p-4 text-slate-200 capitalize font-medium">
                        {v.category}
                      </td>
                    ))}
                  </tr>

                  {/* Year */}
                  <tr className="hover:bg-slate-800/20">
                    <td className="p-4 font-medium text-slate-400 bg-slate-900/40 text-xs uppercase tracking-wider">
                      Model Year
                    </td>
                    {comparedVehicles.map((v) => (
                      <td key={v.id} className="p-4 text-slate-300">
                        {v.year}
                      </td>
                    ))}
                  </tr>

                  {/* Transmission */}
                  <tr className="hover:bg-slate-800/20">
                    <td className="p-4 font-medium text-slate-400 bg-slate-900/40 text-xs uppercase tracking-wider">
                      Transmission
                    </td>
                    {comparedVehicles.map((v) => (
                      <td key={v.id} className="p-4 text-slate-300 capitalize">
                        {v.transmission}
                      </td>
                    ))}
                  </tr>

                  {/* Fuel Type */}
                  <tr className="hover:bg-slate-800/20">
                    <td className="p-4 font-medium text-slate-400 bg-slate-900/40 text-xs uppercase tracking-wider">
                      Fuel System
                    </td>
                    {comparedVehicles.map((v) => (
                      <td key={v.id} className="p-4 text-slate-300 capitalize">
                        {v.fuel_type}
                      </td>
                    ))}
                  </tr>

                  {/* Seating Capacity */}
                  <tr className="hover:bg-slate-800/20">
                    <td className="p-4 font-medium text-slate-400 bg-slate-900/40 text-xs uppercase tracking-wider">
                      Seating Capacity
                    </td>
                    {comparedVehicles.map((v) => (
                      <td key={v.id} className="p-4 text-slate-300">
                        {v.seats} Occupants
                      </td>
                    ))}
                  </tr>

                  {/* Fuel Efficiency / Range */}
                  <tr className="hover:bg-slate-800/20">
                    <td className="p-4 font-medium text-slate-400 bg-slate-900/40 text-xs uppercase tracking-wider">
                      Efficiency / Range
                    </td>
                    {comparedVehicles.map((v) => (
                      <td key={v.id} className="p-4 text-slate-300">
                        {v.fuel_type === 'electric'
                          ? `${v.range_km || 450} KM Range`
                          : `${v.mileage_kmpl || 16.5} KMPL`}
                      </td>
                    ))}
                  </tr>

                  {/* Location Availability */}
                  <tr className="hover:bg-slate-800/20">
                    <td className="p-4 font-medium text-slate-400 bg-slate-900/40 text-xs uppercase tracking-wider">
                      Fleet Hub
                    </td>
                    {comparedVehicles.map((v) => (
                      <td key={v.id} className="p-4 text-slate-300 capitalize">
                        {v.location} Fleet Hub
                      </td>
                    ))}
                  </tr>

                  {/* Key Features */}
                  <tr className="hover:bg-slate-800/20">
                    <td className="p-4 font-medium text-slate-400 bg-slate-900/40 text-xs uppercase tracking-wider">
                      Key Highlights
                    </td>
                    {comparedVehicles.map((v) => (
                      <td key={v.id} className="p-4 text-slate-300">
                        <ul className="space-y-1.5 text-xs">
                          {v.features.slice(0, 4).map((f, i) => (
                            <li key={i} className="flex items-center text-slate-300">
                              <Check className="w-3.5 h-3.5 text-cyan-400 mr-1.5 flex-shrink-0" />
                              <span>{f}</span>
                            </li>
                          ))}
                        </ul>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>

            {/* AI Advisor Banner */}
            <div className="mt-8 bg-gradient-to-r from-cyan-950/40 to-slate-900 border border-cyan-800/30 rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center space-x-4">
                <div className="w-12 h-12 rounded-xl bg-cyan-600/20 border border-cyan-500/30 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-6 h-6 text-cyan-400" />
                </div>
                <div>
                  <h3 className="text-base font-semibold text-white">Need an unbiased recommendation?</h3>
                  <p className="text-slate-400 text-xs mt-1">
                    Our AI Consultant analyzes power-to-weight ratios, real-world maintenance, and total cost of ownership across your compared vehicles.
                  </p>
                </div>
              </div>
              <button
                onClick={handleAskAiRecommendation}
                disabled={isAskingAi}
                className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-sm rounded-lg transition whitespace-nowrap"
              >
                {isAskingAi ? 'Evaluating...' : 'Generate AI Comparison'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
