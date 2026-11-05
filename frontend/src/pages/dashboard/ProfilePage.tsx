import React from 'react';
import { useAuthStore } from '../../store/authStore';
import { User, ShieldCheck, Mail, Phone, MapPin, Award, CheckCircle2, Lock } from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const { user } = useAuthStore();

  return (
    <div className="space-y-6">
      <div>
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 text-[11px] font-bold uppercase tracking-wider mb-1">
          <User className="w-3.5 h-3.5" /> Account Details
        </div>
        <h2 className="text-2xl font-bold text-white tracking-tight">Member Profile</h2>
        <p className="text-xs text-slate-400">
          Personal identification, verified KYC credentials, and membership tier benefits.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Personal Details */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2">
            Personal Information
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <span className="text-slate-500 block mb-1">Full Legal Name</span>
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white font-medium">
                <User className="w-4 h-4 text-cyan-400" />
                <span>{user?.name || 'Alex Vance'}</span>
              </div>
            </div>

            <div>
              <span className="text-slate-500 block mb-1">Registered Email</span>
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white font-medium">
                <Mail className="w-4 h-4 text-cyan-400" />
                <span>{user?.email || 'demo@auramotors.com'}</span>
              </div>
            </div>

            <div>
              <span className="text-slate-500 block mb-1">Phone Number</span>
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white font-medium">
                <Phone className="w-4 h-4 text-cyan-400" />
                <span>{user?.phone || '+91 98765 43210'}</span>
              </div>
            </div>

            <div>
              <span className="text-slate-500 block mb-1">Primary Residence / Delivery City</span>
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white font-medium">
                <MapPin className="w-4 h-4 text-cyan-400" />
                <span>Delhi NCR (Vasant Kunj)</span>
              </div>
            </div>
          </div>
        </div>

        {/* KYC & Membership Tier */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl space-y-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2 flex items-center justify-between">
            <span>KYC & Verification Status</span>
            <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
              100% Complete
            </span>
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block">Government Driving License</span>
                <span className="text-[11px] text-slate-400">DL-1420110012345 • Verified</span>
              </div>
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block">Identity Verification (Aadhaar / Passport)</span>
                <span className="text-[11px] text-slate-400">Biometric Authenticated</span>
              </div>
              <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            </div>

            <div className="p-3.5 rounded-xl bg-gradient-to-r from-cyan-950/40 to-slate-950 border border-cyan-800/40 flex items-center justify-between">
              <div>
                <span className="font-bold text-cyan-300 block">Aura Black Tier Member</span>
                <span className="text-[11px] text-slate-400">Zero-deposit car rentals & VIP priority dispatch</span>
              </div>
              <Award className="w-6 h-6 text-cyan-400" />
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block">Security & Two-Factor Authentication</span>
                <span className="text-[11px] text-slate-400">Active via Registered Mobile Device</span>
              </div>
              <Lock className="w-4 h-4 text-slate-400" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
