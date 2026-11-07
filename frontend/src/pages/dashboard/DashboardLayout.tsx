import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import {
  LayoutDashboard,
  ShoppingBag,
  Calendar,
  CreditCard,
  Car,
  PlusCircle,
  ListOrdered,
  Heart,
  User as UserIcon,
  LogOut,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Overview', path: '/dashboard', icon: LayoutDashboard },
  { label: 'My Purchases', path: '/dashboard/purchases', icon: ShoppingBag },
  { label: 'My Rentals', path: '/dashboard/rentals', icon: Calendar },
  { label: 'Transactions / Payments', path: '/dashboard/payments', icon: CreditCard },
  { label: 'My Vehicles', path: '/dashboard/vehicles', icon: Car },
  { label: 'Sell a Car', path: '/sell-car', icon: PlusCircle, badge: 'New' },
  { label: 'My Listings', path: '/dashboard/listings', icon: ListOrdered },
  { label: 'Saved Cars', path: '/dashboard/saved', icon: Heart },
  { label: 'Profile', path: '/dashboard/profile', icon: UserIcon },
];

export const DashboardLayout: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-24 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* User Identity Header Banner */}
        <div className="bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 border border-slate-800 rounded-3xl p-6 sm:p-8 mb-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-2xl">
          <div className="flex items-center space-x-5">
            <div className="w-16 h-16 rounded-2xl bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-300 font-bold text-2xl shadow-inner">
              {user?.name ? user.name.charAt(0) : 'A'}
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h1 className="text-2xl font-bold text-white tracking-tight">{user?.name || 'Alex Vance'}</h1>
                <span className="inline-flex items-center gap-1 text-[10px] uppercase font-bold tracking-widest text-cyan-400 bg-cyan-950/80 px-2.5 py-0.5 rounded-full border border-cyan-800/40">
                  <ShieldCheck className="w-3 h-3 text-cyan-400" /> Verified Member
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                {user?.email || 'demo@auramotors.com'} • {user?.phone || '+91 98765 43210'} • ID: <span className="font-mono text-slate-300">{user?.id || 'usr_demo_01'}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/consultant')}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 text-xs font-bold hover:bg-cyan-500/20 transition-all"
            >
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>Aura AI Concierge</span>
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800/80 hover:bg-red-500/20 border border-slate-700 hover:border-red-500/40 text-slate-300 hover:text-red-300 text-xs font-bold transition-all"
            >
              <LogOut className="w-4 h-4" />
              <span>Logout</span>
            </button>
          </div>
        </div>

        {/* Dashboard Grid: Sidebar Navigation + Sub-page Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar Menu */}
          <aside className="lg:col-span-1">
            <nav className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-2.5 space-y-1 backdrop-blur-xl">
              {NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.path === '/dashboard'}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-4 py-3 rounded-xl text-xs font-semibold transition-all ${
                        isActive
                          ? 'bg-gradient-to-r from-cyan-600 to-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/20'
                          : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`
                    }
                  >
                    <div className="flex items-center space-x-3">
                      <Icon className="w-4 h-4" />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-800/50">
                        {item.badge}
                      </span>
                    )}
                  </NavLink>
                );
              })}
            </nav>
          </aside>

          {/* Main Content Area */}
          <section className="lg:col-span-3">
            <Outlet />
          </section>
        </div>
      </div>
    </div>
  );
};

