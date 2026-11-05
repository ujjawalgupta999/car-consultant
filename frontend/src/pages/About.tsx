import React from 'react';
import { Link } from 'react-router-dom';
import { ShieldCheck, Award, Sparkles, Cpu, Clock, Compass, ArrowRight } from 'lucide-react';

export const About: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-28 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="text-center max-w-3xl mx-auto mb-20">
          <span className="text-xs font-semibold tracking-widest uppercase text-cyan-400">
            Automotive Excellence Reimagined
          </span>
          <h1 className="text-4xl md:text-6xl font-light tracking-tight text-white mt-3">
            The Science of <span className="font-semibold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">Uncompromising Motion</span>
          </h1>
          <p className="text-slate-400 text-sm md:text-base mt-6 leading-relaxed">
            Founded to bridge high-end engineering and cognitive artificial intelligence, Aura Motors is a next-generation automotive marketplace where digital precision meets the joy of driving.
          </p>
        </div>

        {/* Pillars Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-24">
          <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-8 hover:border-slate-700 transition">
            <div className="w-12 h-12 rounded-xl bg-cyan-950/80 border border-cyan-800/40 flex items-center justify-center mb-6">
              <ShieldCheck className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">200-Point Inspection</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Every vehicle in our rental and purchase catalogue undergoes certified diagnostic teardowns covering powertrain integrity, structural geometry, and digital telemetry.
            </p>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-8 hover:border-slate-700 transition">
            <div className="w-12 h-12 rounded-xl bg-cyan-950/80 border border-cyan-800/40 flex items-center justify-center mb-6">
              <Cpu className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Cognitive AI Strategist</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              Powered by model context protocol and generative interface engines, our AI Consultant interviews drivers, decodes preferences, and dynamically navigates the catalogue in real time.
            </p>
          </div>

          <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-8 hover:border-slate-700 transition">
            <div className="w-12 h-12 rounded-xl bg-cyan-950/80 border border-cyan-800/40 flex items-center justify-center mb-6">
              <Award className="w-6 h-6 text-cyan-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">Curated Luxury Tier</h3>
            <p className="text-slate-400 text-xs leading-relaxed">
              From track-tuned BMW M divisions and Porsche GTs to sustainable long-range EVs and luxury executive cruisers, our fleet features only premier global automakers.
            </p>
          </div>
        </div>

        {/* Brand Story Statement */}
        <div className="bg-gradient-to-r from-slate-900 via-slate-900/80 to-cyan-950/30 border border-slate-800 rounded-3xl p-8 md:p-12 mb-24">
          <div className="max-w-2xl">
            <span className="text-xs font-bold uppercase tracking-widest text-cyan-400">Our Heritage</span>
            <h2 className="text-3xl font-light text-white mt-2 mb-4">
              Where Technology Serves <span className="font-semibold">The Enthusiast</span>
            </h2>
            <p className="text-slate-300 text-sm leading-relaxed mb-6">
              Traditional automotive marketplaces force users through rigid filter menus and tedious sales calls. We believed there was a more sophisticated way: an intelligent consultant that listens to your lifestyle needs, evaluates dynamic telemetry, and handles everything from test drives to paperwork.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link
                to="/explore"
                className="px-6 py-3 bg-white text-slate-950 font-semibold rounded-xl text-xs hover:bg-slate-200 transition"
              >
                Browse Our Fleet
              </Link>
              <Link
                to="/consultant"
                className="px-6 py-3 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded-xl text-xs transition flex items-center space-x-2"
              >
                <Sparkles className="w-4 h-4 text-cyan-200" />
                <span>Meet AI Consultant</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Flagship Showrooms */}
        <div>
          <div className="text-center mb-10">
            <span className="text-xs font-semibold tracking-widest uppercase text-cyan-400">
              Physical Hubs
            </span>
            <h2 className="text-2xl md:text-3xl font-semibold text-white mt-1">
              Flagship Experience Lounges
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6">
              <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Delhi NCR Hub</span>
              <h4 className="text-base font-semibold text-white mt-1">Aerocity VIP Terminal</h4>
              <p className="text-xs text-slate-400 mt-2">Asset 8, Hospitality District, IGI Airport, New Delhi</p>
              <p className="text-xs text-cyan-400/80 mt-3 font-mono">+91 11 4092 1100</p>
            </div>

            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6">
              <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Mumbai Hub</span>
              <h4 className="text-base font-semibold text-white mt-1">Bandra Kurla Complex</h4>
              <p className="text-xs text-slate-400 mt-2">G Block, Financial District, Bandra East, Mumbai</p>
              <p className="text-xs text-cyan-400/80 mt-3 font-mono">+91 22 6184 2200</p>
            </div>

            <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6">
              <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-wider">Bengaluru Hub</span>
              <h4 className="text-base font-semibold text-white mt-1">Indiranagar Experience Center</h4>
              <p className="text-xs text-slate-400 mt-2">100 Feet Road, HAL 2nd Stage, Indiranagar, Bengaluru</p>
              <p className="text-xs text-cyan-400/80 mt-3 font-mono">+91 80 4410 3300</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

