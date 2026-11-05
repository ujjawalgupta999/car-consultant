import React from 'react';
import { ProgressEvent } from '../../types';
import { Check, Circle, Loader2, Sparkles, ShieldCheck } from 'lucide-react';

interface AgentTimelineProps {
  currentEvent: ProgressEvent | null;
  workflowState: string;
}

const STAGES = [
  { id: 'INTERVIEW', label: '1. Interview' },
  { id: 'SEARCHING', label: '2. Search' },
  { id: 'RANKING', label: '3. Ranking' },
  { id: 'RECOMMENDATIONS_READY', label: '4. Selection' },
  { id: 'CHECKOUT_READY', label: '5. Checkout' },
  { id: 'CONFIRMED', label: '6. Confirmed' },
];

export const AgentTimeline: React.FC<AgentTimelineProps> = ({
  currentEvent,
  workflowState,
}) => {
  const getStageIndex = (state: string) => {
    switch (state) {
      case 'NEW':
      case 'INTERVIEWING':
        return 0;
      case 'READY_TO_SEARCH':
      case 'SEARCHING':
        return 1;
      case 'RANKING':
        return 2;
      case 'RECOMMENDATIONS_READY':
      case 'VEHICLE_SELECTED':
        return 3;
      case 'BOOKING_IN_PROGRESS':
      case 'CHECKOUT_READY':
      case 'PAYMENT_PROCESSING':
      case 'PAYMENT_FAILED':
        return 4;
      case 'CONFIRMED':
        return 5;
      default:
        return 0;
    }
  };

  const currentIndex = getStageIndex(workflowState);

  return (
    <div className="border-b border-surface-border bg-surface/80 backdrop-blur-md px-4 py-2.5">
      <div className="mx-auto max-w-5xl">
        {/* Stages steps */}
        <div className="flex items-center justify-between text-xs">
          {STAGES.map((s, idx) => {
            const isCompleted = idx < currentIndex || workflowState === 'CONFIRMED';
            const isCurrent = idx === currentIndex && workflowState !== 'CONFIRMED';

            return (
              <div key={s.id} className="flex items-center gap-1.5">
                <div
                  className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold transition-all ${
                    isCompleted
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                      : isCurrent
                      ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40 animate-pulse'
                      : 'bg-surface-muted text-gray-500 border border-surface-border'
                  }`}
                >
                  {isCompleted ? <Check className="w-3 h-3" /> : isCurrent ? <Loader2 className="w-3 h-3 animate-spin" /> : idx + 1}
                </div>
                <span
                  className={`hidden sm:inline font-medium ${
                    isCurrent ? 'text-cyan-400' : isCompleted ? 'text-gray-200' : 'text-gray-500'
                  }`}
                >
                  {s.label}
                </span>
                {idx < STAGES.length - 1 && (
                  <div className="hidden md:block h-[1px] w-6 lg:w-10 bg-surface-border mx-1" />
                )}
              </div>
            );
          })}
        </div>

        {/* Live Status ticker */}
        {currentEvent && (
          <div className="mt-2 flex items-center gap-2 text-[11px] text-cyan-300/90 font-mono">
            <span className="flex h-1.5 w-1.5 rounded-full bg-cyan-400 animate-ping" />
            <span className="truncate">{currentEvent.message}</span>
          </div>
        )}
      </div>
    </div>
  );
};

