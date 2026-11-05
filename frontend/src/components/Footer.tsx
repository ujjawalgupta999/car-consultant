import React from 'react';
import { Link } from 'react-router-dom';
import { Car, Shield, Sparkles, MapPin, Phone, Mail, ArrowUpRight } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-surface-border bg-surface text-gray-400">
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-10">
          {/* Brand Col */}
          <div className="lg:col-span-2 space-y-4">
            <Link to="/" className="flex items-center gap-2">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-white p-0.5">
                <Car className="w-5 h-5 text-black" />
              </div>
              <span className="text-xl font-black tracking-widest text-white uppercase">
                AURA MOTORS
              </span>
            </Link>
            <p className="text-xs text-gray-400 leading-relaxed max-w-sm">
              Amulate Summer Hackathon 2026. Setting the benchmark in autonomous automotive marketplace discovery, verified inventory matching, and generative AI consultation.
            </p>
            <div className="flex items-center gap-2 text-xs text-emerald-400">
              <Shield className="w-4 h-4" />
              <span>100% Verified Inventory & Zero Hallucination Guarantee</span>
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-white mb-4">
              Explore
            </h4>
            <ul className="space-y-2.5 text-xs">
              <li><Link to="/explore" className="hover:text-white transition-colors">Complete Catalogue</Link></li>
              <li><Link to="/rent" className="hover:text-white transition-colors">Self-Drive Rentals</Link></li>
              <li><Link to="/buy" className="hover:text-white transition-colors">Buy New & Used</Link></li>
              <li><Link to="/compare" className="hover:text-white transition-colors">Compare Vehicles</Link></li>
              <li><Link to="/consultant" className="text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1">AI Consultant <ArrowUpRight className="w-3 h-3" /></Link></li>
            </ul>
          </div>

          {/* Popular Categories */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-white mb-4">
              Categories
            </h4>
            <ul className="space-y-2.5 text-xs">
              <li><Link to="/explore?category=SUV" className="hover:text-white transition-colors">Luxury SUVs</Link></li>
              <li><Link to="/explore?category=Sedan" className="hover:text-white transition-colors">Executive Sedans</Link></li>
              <li><Link to="/explore?category=Electric+Vehicle" className="hover:text-white transition-colors">Electric Vehicles (EV)</Link></li>
              <li><Link to="/explore?category=Sports+Car" className="hover:text-white transition-colors">Sports Cars</Link></li>
              <li><Link to="/explore?category=Convertible" className="hover:text-white transition-colors">Convertibles</Link></li>
            </ul>
          </div>

          {/* Contact Details */}
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-white mb-4">
              Headquarters
            </h4>
            <ul className="space-y-3 text-xs">
              <li className="flex items-start gap-2">
                <MapPin className="w-4 h-4 text-primary-accent shrink-0 mt-0.5" />
                <span>Cyber City, Phase II, Gurugram, Delhi NCR 122002</span>
              </li>
              <li className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-primary-accent shrink-0" />
                <span>+91 (124) 490-AURA</span>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-primary-accent shrink-0" />
                <span>concierge@auramotors.com</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Strip */}
        <div className="mt-12 pt-8 border-t border-surface-border/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <p>© 2026 Aura Motors Technologies Pvt Ltd. Amulate Summer Hackathon 2026.</p>
          <div className="flex gap-6">
            <span className="text-gray-500">Privacy Policy</span>
            <span className="text-gray-500">Terms of Service</span>
            <span className="text-gray-500">MCP Protocol Compliance</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

