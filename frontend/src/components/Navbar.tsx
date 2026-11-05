import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useComparisonStore } from '../store/comparisonStore';
import { useConsultantStore } from '../store/consultantStore';
import { useAuthStore } from '../store/authStore';
import { Car, Sparkles, Scale, User, Heart, Menu, X } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { comparedVehicles } = useComparisonStore();
  const { toggleOpen, isOpen } = useConsultantStore();
  const { user, isAuthenticated } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Explore Cars', path: '/explore' },
    { name: 'Rent a Car', path: '/rent' },
    { name: 'Buy a Car', path: '/buy' },
    { name: 'Compare', path: '/compare', badge: comparedVehicles.length },
    { name: 'About', path: '/about' },
    { name: 'Contact', path: '/contact' },
  ];

  return (
    <header className="sticky top-0 z-40 w-full border-b border-surface-border/80 bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-white to-gray-400 p-0.5 shadow-xl transition-transform group-hover:scale-105">
            <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-background">
              <Car className="w-5 h-5 text-white" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xl font-black tracking-widest text-white uppercase font-sans">
                AURA
              </span>
              <span className="text-xs font-semibold tracking-wider text-primary-accent uppercase">
                MOTORS
              </span>
            </div>
            <p className="text-[10px] tracking-wider text-gray-400 uppercase font-mono">
              The Intelligent Drive
            </p>
          </div>
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden lg:flex items-center gap-1">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`relative px-3.5 py-2 text-xs font-medium uppercase tracking-wider transition-colors rounded-lg ${
                  isActive
                    ? 'text-white bg-surface-muted/60 font-semibold'
                    : 'text-gray-400 hover:text-white hover:bg-surface-muted/30'
                }`}
              >
                {link.name}
                {link.badge !== undefined && link.badge > 0 && (
                  <span className="ml-1.5 inline-flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white">
                    {link.badge}
                  </span>
                )}
                {isActive && (
                  <span className="absolute bottom-0 left-3.5 right-3.5 h-[2px] bg-primary rounded-full" />
                )}
              </Link>
            );
          })}
        </nav>

        {/* Right Actions: AI Consultant Button + User Profile */}
        <div className="flex items-center gap-3">
          {/* AI Consultant Trigger */}
          <button
            type="button"
            onClick={toggleOpen}
            className={`relative flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-all shadow-lg active:scale-95 ${
              isOpen
                ? 'bg-cyan-500 text-black shadow-cyan-500/25'
                : 'bg-gradient-to-r from-primary to-cyan-500 text-white hover:opacity-95 shadow-primary/25 animate-pulse'
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span className="hidden sm:inline">AI Consultant</span>
            <span className="absolute -top-1 -right-1 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
            </span>
          </button>

          {/* User Account / Dashboard */}
          {isAuthenticated ? (
            <Link
              to="/dashboard"
              className="flex items-center gap-2 rounded-xl border border-surface-border bg-surface px-3 py-2 text-xs font-medium text-gray-200 hover:border-primary hover:text-white transition-all"
            >
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-primary-accent font-bold text-[10px]">
                {user?.name.charAt(0) || 'U'}
              </div>
              <span className="hidden md:inline">{user?.name.split(' ')[0]}</span>
            </Link>
          ) : (
            <Link
              to="/login"
              className="rounded-xl border border-surface-border bg-surface px-4 py-2 text-xs font-semibold text-gray-300 hover:border-primary hover:text-white transition-all"
            >
              Sign In
            </Link>
          )}

          {/* Mobile Menu Toggle */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-2 text-gray-400 hover:text-white"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="lg:hidden border-t border-surface-border bg-background px-4 pt-3 pb-6 space-y-2">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setMobileMenuOpen(false)}
              className="flex items-center justify-between px-3 py-2.5 text-sm font-medium text-gray-300 hover:bg-surface-muted rounded-lg"
            >
              <span>{link.name}</span>
              {link.badge !== undefined && link.badge > 0 && (
                <span className="h-5 w-5 rounded-full bg-primary text-center text-xs font-bold text-white">
                  {link.badge}
                </span>
              )}
            </Link>
          ))}
          <Link
            to="/consultant"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 px-3 py-2.5 text-sm font-bold text-cyan-400 bg-cyan-500/10 rounded-lg"
          >
            <Sparkles className="w-4 h-4" />
            Full-Screen AI Consultant
          </Link>
        </div>
      )}
    </header>
  );
};
