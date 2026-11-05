import React from 'react';
import { Car, RefreshCw, Cpu, ShieldCheck } from 'lucide-react';

interface HeaderProps {
  sessionId: string;
  onResetSession: () => void;
  workflowState: string;
}

export const Header: React.FC<HeaderProps> = ({
  sessionId,
  onResetSession,
  workflowState,
}) => {
  return (
    <header className="border-b border-surface-border bg-surface/90 backdrop-blur-md px-4 py-3 sticky top-0 z-50">
      <div className="mx-auto flex max-w-5xl items-center justify-between">
        {/* Logo & title */}
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-cyan-500 shadow-lg text-white">
            <Car className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-extrabold tracking-tight text-white">
                Amulate AI
              </h1>
              <span className="rounded-full bg-primary/20 border border-primary/40 px-2 py-0.5 text-[10px] font-bold text-primary-accent uppercase tracking-wider">
                Hackathon 2026
              </span>
            </div>
            <p className="text-xs text-gray-400">
              Conversational Car Rental & Purchase Consultant
            </p>
          </div>
        </div>

        {/* Status badges & reset */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
            <Cpu className="w-3.5 h-3.5" />
            <span>Mock Engine Active</span>
          </div>

          <div className="hidden md:block font-mono text-[11px] text-gray-400 bg-surface-muted px-2.5 py-1 rounded-lg border border-surface-border">
            {sessionId}
          </div>

          <button
            type="button"
            onClick={onResetSession}
            title="Reset Conversation"
            className="flex items-center gap-1.5 rounded-lg border border-surface-border bg-surface-muted px-3 py-1.5 text-xs font-medium text-gray-300 hover:border-primary hover:text-white transition-all active:scale-95"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Reset</span>
          </button>
        </div>
      </div>
    </header>
  );
};

