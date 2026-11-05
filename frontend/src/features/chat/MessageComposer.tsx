import React, { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

interface MessageComposerProps {
  onSendMessage: (content: string) => void;
  disabled?: boolean;
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  onSendMessage,
  disabled = false,
}) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const setPreset = (presetText: string) => {
    setInput(presetText);
  };

  return (
    <div className="border-t border-surface-border bg-surface-muted/90 p-4">
      {/* Quick Scenario Pills */}
      <div className="mb-3 flex flex-wrap gap-2 text-xs">
        <span className="text-[11px] font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1 self-center">
          <Sparkles className="w-3 h-3 text-cyan-400" /> Demo Scenarios:
        </span>
        <button
          type="button"
          onClick={() => setPreset("I need an automatic SUV in Delhi for five days starting 15 December 2026. My budget is ₹3,000 per day.")}
          className="rounded-full border border-surface-border bg-surface px-3 py-1 text-gray-300 hover:border-cyan-500/60 hover:text-white transition-all"
        >
          🚗 Scenario A: Rental (Delhi SUV 5 Days)
        </button>
        <button
          type="button"
          onClick={() => setPreset("I want to buy a used automatic SUV in Delhi with a maximum budget of ₹15 lakh.")}
          className="rounded-full border border-surface-border bg-surface px-3 py-1 text-gray-300 hover:border-cyan-500/60 hover:text-white transition-all"
        >
          🏷️ Scenario B: Purchase (Used SUV ₹15L)
        </button>
        <button
          type="button"
          onClick={() => setPreset("I need an automatic convertible in Delhi for 5 days starting 15 December 2026 with a daily budget of ₹500.")}
          className="rounded-full border border-surface-border bg-surface px-3 py-1 text-gray-300 hover:border-amber-500/60 hover:text-white transition-all"
        >
          ⚠️ Scenario C: Zero Match Relaxation
        </button>
      </div>

      {/* Input composer */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask for car recommendations, specify preferences, or ask questions..."
          disabled={disabled}
          className="flex-1 rounded-xl border border-surface-border bg-background px-4 py-3 text-sm text-white placeholder-gray-500 outline-none transition-all focus:border-primary focus:ring-1 focus:ring-primary"
        />
        <button
          type="submit"
          disabled={disabled || !input.trim()}
          className="flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-bold text-white shadow-lg transition-all hover:bg-primary-hover disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
        >
          <span>Send</span>
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
