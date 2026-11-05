import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import { loginUser } from '../services/api';
import { Lock, Mail, ArrowRight, ShieldCheck, UserCheck } from 'lucide-react';

export const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();

  const [email, setEmail] = useState('demo@auramotors.com');
  const [password, setPassword] = useState('Password123!');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await loginUser({ email, password });
      login(res.user, res.token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleInstantDemoLogin = () => {
    login(
      {
        id: 'usr_demo_01',
        name: 'Alex Vance',
        email: 'demo@auramotors.com',
        phone: '+91 98765 43210',
        saved_vehicles: ['CAR-001', 'CAR-021'],
      },
      'token_demo_alex_vance'
    );
    navigate('/dashboard');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-28 pb-20 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-slate-900/60 border border-slate-800 rounded-3xl p-8 backdrop-blur-xl shadow-2xl relative overflow-hidden">
        {/* Subtle decorative glow */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-cyan-950/80 border border-cyan-800/40 flex items-center justify-center mx-auto mb-3">
            <Lock className="w-5 h-5 text-cyan-400" />
          </div>
          <span className="text-[10px] font-bold tracking-widest uppercase text-cyan-400">
            Aura Client Portal
          </span>
          <h1 className="text-2xl font-light tracking-tight text-white mt-1">
            Access Your <span className="font-semibold">Account</span>
          </h1>
          <p className="text-slate-400 text-xs mt-1">
            Sign in to manage your vehicle bookings, test drives, and saved fleet.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-3 bg-rose-950/40 border border-rose-800/80 rounded-xl text-rose-300 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1.5">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                required
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between items-center mb-1.5">
              <label className="block text-xs font-medium text-slate-400">Password</label>
              <span className="text-[11px] text-cyan-400 hover:underline cursor-pointer">
                Forgot password?
              </span>
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl transition shadow-lg shadow-cyan-950/40 flex items-center justify-center space-x-2 text-sm mt-2"
          >
            <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
            <ArrowRight className="w-4 h-4 text-slate-950" />
          </button>
        </form>

        {/* Demo Fast Login */}
        <div className="mt-6 pt-6 border-t border-slate-800/80">
          <button
            type="button"
            onClick={handleInstantDemoLogin}
            className="w-full py-2.5 bg-slate-800/80 hover:bg-slate-700 border border-slate-700/80 text-cyan-300 font-medium rounded-xl text-xs transition flex items-center justify-center space-x-2"
          >
            <UserCheck className="w-4 h-4 text-cyan-400" />
            <span>Instant Demo Sign-in (Alex Vance)</span>
          </button>
        </div>

        <div className="mt-6 text-center text-xs text-slate-400">
          Don't have an Aura account?{' '}
          <Link to="/signup" className="text-cyan-400 hover:underline font-medium">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  );
};

