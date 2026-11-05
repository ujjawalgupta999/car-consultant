import React, { useState } from 'react';
import { Mail, Phone, MapPin, Send, CheckCircle2, MessageSquare, Sparkles } from 'lucide-react';
import { useConsultantStore } from '../store/consultantStore';

export const Contact: React.FC = () => {
  const { setIsOpen } = useConsultantStore();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('General Fleet Inquiry');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-28 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <span className="text-xs font-semibold tracking-widest uppercase text-cyan-400">
            Aura Concierge Desk
          </span>
          <h1 className="text-3xl md:text-5xl font-light tracking-tight text-white mt-2">
            Get in <span className="font-semibold">Touch</span>
          </h1>
          <p className="text-slate-400 text-sm mt-3">
            Speak with our automotive advisors or experience our AI Consultant for instant answers.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          {/* Contact Details (5 cols) */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6">
              <h3 className="text-base font-semibold text-white mb-4">Direct Concierge Channels</h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3 text-xs">
                  <Phone className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-slate-400 block">Fleet Concierge Hotline (24/7)</span>
                    <span className="text-white font-mono text-sm font-medium">+91 (800) 287-2466</span>
                  </div>
                </div>

                <div className="flex items-start space-x-3 text-xs">
                  <Mail className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-slate-400 block">Client Relations Email</span>
                    <span className="text-white font-medium">concierge@auramotors.com</span>
                  </div>
                </div>

                <div className="flex items-start space-x-3 text-xs">
                  <MapPin className="w-4 h-4 text-cyan-400 mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-slate-400 block">Headquarters</span>
                    <span className="text-white">Aura Tower, Cyber City, Phase II, Gurugram, India</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Instant AI Assistance Card */}
            <div className="bg-gradient-to-br from-cyan-950/40 to-slate-900 border border-cyan-800/40 rounded-2xl p-6">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">Prefer Zero-Wait Answers?</h4>
                  <p className="text-[11px] text-slate-400">Our AI Consultant is online right now</p>
                </div>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed mb-4">
                Ask about availability, live rates, trade-in valuations, or compare models with zero waiting times.
              </p>
              <button
                onClick={() => setIsOpen(true)}
                className="w-full py-2.5 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs rounded-xl transition flex items-center justify-center space-x-2"
              >
                <MessageSquare className="w-4 h-4" />
                <span>Open AI Consultant</span>
              </button>
            </div>
          </div>

          {/* Form (7 cols) */}
          <div className="lg:col-span-7">
            <div className="bg-slate-900/50 border border-slate-800 rounded-3xl p-8">
              {submitted ? (
                <div className="text-center py-12">
                  <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center mx-auto mb-4">
                    <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                  </div>
                  <h3 className="text-xl font-semibold text-white">Message Dispatched</h3>
                  <p className="text-slate-400 text-xs max-w-md mx-auto mt-2 leading-relaxed">
                    Thank you, {name}. An Aura Senior Concierge will contact you at {email} within 2 hours.
                  </p>
                  <button
                    onClick={() => {
                      setSubmitted(false);
                      setName('');
                      setEmail('');
                      setMessage('');
                    }}
                    className="mt-6 px-6 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl transition"
                  >
                    Send Another Inquiry
                  </button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-5">
                  <h3 className="text-lg font-semibold text-white mb-2">Send a Message</h3>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1.5">Full Name</label>
                      <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="John Doe"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                        required
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-slate-400 mb-1.5">Email Address</label>
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="john@example.com"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                        required
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1.5">Subject</label>
                    <select
                      value={subject}
                      onChange={(e) => setSubject(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                    >
                      <option value="General Fleet Inquiry">General Fleet Inquiry</option>
                      <option value="Long-term Luxury Rental">Long-term Luxury Rental</option>
                      <option value="Pre-owned Vehicle Purchase">Pre-owned Vehicle Purchase</option>
                      <option value="Corporate Fleet Solutions">Corporate Fleet Solutions</option>
                      <option value="Press & Media">Press & Media</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1.5">Your Message</label>
                    <textarea
                      rows={5}
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      placeholder="Please specify your preferred vehicle, dates, or purchase timeline..."
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500"
                      required
                    />
                  </div>

                  <button
                    type="submit"
                    className="w-full py-3 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold rounded-xl transition shadow-lg shadow-cyan-950/40 flex items-center justify-center space-x-2 text-sm"
                  >
                    <Send className="w-4 h-4 text-slate-950" />
                    <span>Dispatch Inquiry</span>
                  </button>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

