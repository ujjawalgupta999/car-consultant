import React, { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChatMessage, A2UIComponent } from '../../types';
import { A2UIRenderer } from '../../a2ui/A2UIRenderer';
import { useConsultantStore } from '../../store/consultantStore';
import { Bot, User, CheckCircle2, Ticket, ArrowUpRight, Car, Calendar, CreditCard, Tag } from 'lucide-react';

/** Render a markdown string as JSX (supports **bold**, *italic*, ### headers, \n, `code`) */
function renderMarkdown(text: string): React.ReactNode {
  const lines = text.split('\n');
  return lines.map((line, lineIdx) => {
    // Heading levels ### and ##
    const h3Match = line.match(/^###\s+(.*)/);
    const h2Match = line.match(/^##\s+(.*)/);
    if (h3Match) return <p key={lineIdx} className="font-bold text-white text-sm mt-2">{inlineMarkdown(h3Match[1])}</p>;
    if (h2Match) return <p key={lineIdx} className="font-bold text-white text-base mt-2">{inlineMarkdown(h2Match[1])}</p>;
    // Bullet points
    const bulletMatch = line.match(/^[-•]\s+(.*)/);
    if (bulletMatch) return <div key={lineIdx} className="flex gap-2"><span className="text-primary-accent">•</span><span>{inlineMarkdown(bulletMatch[1])}</span></div>;
    // Numbered points
    const numMatch = line.match(/^(\d+)\.\s+(.*)/);
    if (numMatch) return <div key={lineIdx} className="flex gap-2"><span className="text-primary-accent font-bold">{numMatch[1]}.</span><span>{inlineMarkdown(numMatch[2])}</span></div>;
    // Empty line → spacing
    if (line.trim() === '') return <div key={lineIdx} className="h-1" />;
    return <p key={lineIdx}>{inlineMarkdown(line)}</p>;
  });
}

function inlineMarkdown(text: string): React.ReactNode {
  // Split on **bold**, *italic*, `code`
  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-bold text-white">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) {
      return <em key={i} className="italic text-gray-200">{part.slice(1, -1)}</em>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="bg-surface-muted px-1 py-0.5 rounded text-cyan-300 font-mono text-[11px]">{part.slice(1, -1)}</code>;
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

interface ChatContainerProps {
  messages: ChatMessage[];
  a2uiSurfaces: Record<string, A2UIComponent[]>;
  activeMcpApp: { name: 'booking' | 'checkout'; context: any } | null;
  onA2uiAction: (surfaceId: string, actionId: string, data: any) => void;
  onMcpAppFinish: (result: any) => void;
  onMcpAppCancel: () => void;
  confirmedBooking: any | null;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({
  messages,
  a2uiSurfaces,
  activeMcpApp,
  onA2uiAction,
  onMcpAppFinish,
  onMcpAppCancel,
  confirmedBooking,
}) => {
  const navigate = useNavigate();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, activeMcpApp, confirmedBooking]);

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6">
      {messages.map((msg) => {
        const isAssistant = msg.role === 'assistant';

        return (
          <div
            key={msg.id}
            className={`flex gap-3 sm:gap-4 ${isAssistant ? 'justify-start' : 'justify-end'}`}
          >
            {isAssistant && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/20 border border-primary/40 text-primary-accent shadow-md">
                <Bot className="w-5 h-5" />
              </div>
            )}

            <div
              className={`max-w-2xl rounded-2xl px-4 py-3 text-sm shadow-md ${
                isAssistant
                  ? 'bg-surface border border-surface-border text-gray-200'
                  : 'bg-primary text-white font-medium self-end rounded-br-sm'
              }`}
            >
              {/* Message text content */}
              <div className="leading-relaxed space-y-0.5 text-sm">
                {isAssistant ? renderMarkdown(msg.content) : msg.content}
              </div>

              {/* Render associated A2UI Surfaces */}
              {isAssistant && msg.a2ui_surfaces && msg.a2ui_surfaces.length > 0 && (
                <div className="mt-3 space-y-3">
                  {msg.a2ui_surfaces.map((surfId) => {
                    const comps = a2uiSurfaces[surfId];
                    if (!comps) return null;
                    return (
                      <A2UIRenderer
                        key={surfId}
                        surfaceId={surfId}
                        components={comps}
                        onAction={(actionId, data) => onA2uiAction(surfId, actionId, data)}
                      />
                    );
                  })}
                </div>
              )}

              {/* Render dynamic structured cards from assistant metadata if present */}
              {isAssistant && (msg as any).data?.cards && Array.isArray((msg as any).data.cards) && (msg as any).data.cards.length > 0 && (
                <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 border-t border-surface-border/40">
                  {(msg as any).data.cards.map((card: any, cIdx: number) => {
                    const isOwnedCard =
                      card.cardType === 'PURCHASED_SHOWCASE' ||
                      card.cardType === 'OWNED_VEHICLE' ||
                      card.status === 'OWNED' ||
                      card.status === 'PURCHASED';
                    const isRentedCard =
                      card.cardType === 'RENTAL' ||
                      card.status === 'RENTAL CONFIRMED' ||
                      card.status === 'ACTIVE RENTAL';

                    const priceStr = card.amount
                      ? `₹${card.amount.toLocaleString('en-IN')}`
                      : card.purchasePrice
                      ? `₹${card.purchasePrice.toLocaleString('en-IN')}`
                      : card.rentalPrice
                      ? `₹${card.rentalPrice.toLocaleString('en-IN')}/day`
                      : card.totalAmount
                      ? `₹${card.totalAmount.toLocaleString('en-IN')}`
                      : card.expectedPrice
                      ? `₹${card.expectedPrice.toLocaleString('en-IN')}`
                      : card.currentEstimatedValue
                      ? `₹${card.currentEstimatedValue.toLocaleString('en-IN')}`
                      : null;

                    const titleStr = card.brand
                      ? `${card.brand} ${card.model}`
                      : (card.vehicleName || `Ref: ${card.orderId || card.id}`);

                    return (
                      <div
                        key={card.id || cIdx}
                        className={`group relative overflow-hidden rounded-xl border bg-slate-900/90 shadow-md transition-all duration-300 hover:shadow-xl select-none ${
                          isOwnedCard
                            ? 'border-emerald-500/80 ring-1 ring-emerald-500/40'
                            : isRentedCard
                            ? 'border-cyan-500/80 ring-1 ring-cyan-500/40'
                            : 'border-surface-border hover:border-cyan-500/60'
                        }`}
                      >
                        {/* Minimal Default View */}
                        <div className="relative aspect-[16/10] w-full overflow-hidden bg-slate-950">
                          {card.image ? (
                            <img
                              src={card.image}
                              alt={titleStr}
                              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                            />
                          ) : (
                            <div className="h-full w-full bg-slate-900 flex items-center justify-center text-gray-500 text-xs">
                              Vehicle Details
                            </div>
                          )}
                          <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />

                          {/* Top Badges */}
                          <div className="absolute top-2 left-2 right-2 flex items-center justify-between gap-1.5">
                            <div className="flex items-center gap-1">
                              {isOwnedCard ? (
                                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500 text-slate-950 text-[9px] font-black px-2 py-0.5 shadow uppercase tracking-wider">
                                  ✓ OWNED
                                </span>
                              ) : isRentedCard ? (
                                <span className="inline-flex items-center gap-1 rounded-full bg-cyan-500 text-slate-950 text-[9px] font-black px-2 py-0.5 shadow uppercase tracking-wider">
                                  RENTED
                                </span>
                              ) : card.category ? (
                                <span className="rounded-full bg-slate-900/80 backdrop-blur-md px-2 py-0.5 text-[9px] font-bold text-gray-300 border border-white/10 uppercase tracking-wider">
                                  {card.category}
                                </span>
                              ) : null}
                            </div>
                            {card.status && (
                              <span className="rounded-full bg-slate-900/80 backdrop-blur-md px-2 py-0.5 text-[9px] font-semibold text-gray-300 border border-white/10 uppercase">
                                {card.status}
                              </span>
                            )}
                          </div>

                          {/* Bottom Default Info */}
                          <div className="absolute bottom-2 left-2.5 right-2.5 flex items-end justify-between">
                            <div className="min-w-0 pr-2">
                              <h4 className="text-xs font-bold text-white truncate drop-shadow-md">
                                {titleStr}
                              </h4>
                              {card.year && (
                                <span className="text-[10px] text-gray-400 font-mono">{card.year}</span>
                              )}
                            </div>
                            <div className="text-right shrink-0">
                              {priceStr && (
                                <div className="text-xs font-extrabold text-white drop-shadow-md">
                                  {priceStr}
                                </div>
                              )}
                              <span className="text-[8px] text-cyan-300 uppercase tracking-wider font-semibold">
                                Hover for specs
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Smooth Hover-Reveal Overlay */}
                        <div className="absolute inset-0 bg-slate-950/95 backdrop-blur-md p-3 flex flex-col justify-between opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none group-hover:pointer-events-auto">
                          <div>
                            <div className="flex items-center justify-between pb-1.5 border-b border-surface-border/60">
                              <div className="min-w-0 pr-2">
                                <h4 className="text-xs font-bold text-white truncate">
                                  {titleStr}
                                </h4>
                                {card.category && (
                                  <p className="text-[9px] text-primary-accent uppercase tracking-wider">{card.category}</p>
                                )}
                              </div>
                              {priceStr && (
                                <span className="text-xs font-black text-cyan-400 shrink-0">{priceStr}</span>
                              )}
                            </div>

                            <div className="space-y-1 my-2 text-[11px] text-gray-300">
                              {card.variant && (
                                <p><span className="text-gray-500">Variant:</span> {card.variant}</p>
                              )}
                              {card.currentEstimatedValue && (
                                <p><span className="text-gray-500">Est. Value:</span> <span className="text-emerald-400 font-semibold">₹{card.currentEstimatedValue.toLocaleString()}</span></p>
                              )}
                              {card.purchasePrice && (
                                <p><span className="text-gray-500">Paid:</span> <span className="text-emerald-400 font-semibold">₹{card.purchasePrice.toLocaleString()}</span></p>
                              )}
                              {card.totalAmount && (
                                <p><span className="text-gray-500">Rental Total:</span> <span className="text-cyan-300 font-semibold">₹{card.totalAmount.toLocaleString()}</span></p>
                              )}
                              {card.expectedPrice && (
                                <p><span className="text-gray-500">Asking Price:</span> <span className="text-emerald-400 font-semibold">₹{card.expectedPrice.toLocaleString()}</span></p>
                              )}
                              {card.paymentMethod && (
                                <p><span className="text-gray-500">Method:</span> {card.paymentMethod}</p>
                              )}
                              {card.orderId && (
                                <p><span className="text-gray-500">Ref:</span> <span className="font-mono text-cyan-300 text-[10px]">{card.orderId}</span></p>
                              )}
                            </div>
                          </div>

                          {card.actions && Array.isArray(card.actions) && card.actions.length > 0 && (
                            <div className="flex items-center gap-1.5 pt-1.5 border-t border-surface-border/60">
                              {card.actions.map((act: any, actIdx: number) => (
                                <button
                                  key={actIdx}
                                  type="button"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    if (act.path) navigate(act.path);
                                    else if (act.action === 'SELL_VEHICLE') navigate('/sell-car');
                                    else if (act.action === 'select_vehicle') {
                                      useConsultantStore.getState().executeWebsiteAction(
                                        { type: 'NAVIGATE_TO_PAGE', payload: { path: `/booking/${card.id || card.vehicleId}` } },
                                        navigate
                                      );
                                    }
                                  }}
                                  className="flex-1 text-center py-1 px-2 rounded-md bg-gradient-to-r from-primary to-cyan-600 text-[10px] font-bold text-white shadow hover:opacity-90 transition cursor-pointer"
                                >
                                  {act.label || 'View'}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Render quick navigation actions from metadata if present */}
              {isAssistant && (msg as any).data?.actions && Array.isArray((msg as any).data.actions) && (
                <div className="mt-3 flex flex-wrap gap-2 pt-2 border-t border-surface-border/40">
                  {(msg as any).data.actions
                    .filter((a: any) => a.type === 'NAVIGATE_TO_PAGE' && a.payload?.path)
                    .map((a: any, aIdx: number) => {
                      const path: string = a.payload.path;
                      let label = 'Open Page';
                      if (path.includes('/dashboard/purchases')) label = 'View My Purchases';
                      else if (path.includes('/dashboard/rentals')) label = 'View My Rentals';
                      else if (path.includes('/dashboard/payments')) label = 'Payment History';
                      else if (path.includes('/dashboard/listings')) label = 'My Listings';
                      else if (path.includes('/buy')) label = 'Explore Buy Cars';
                      else if (path.includes('/rent')) label = 'Explore Rental Fleet';
                      else if (path.includes('/compare')) label = 'View Comparison Matrix';
                      else if (path.includes('/sell')) label = 'Sell a Car Portal';

                      return (
                        <button
                          key={aIdx}
                          type="button"
                          onClick={() => navigate(path)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary/20 hover:bg-primary/30 text-cyan-300 hover:text-cyan-200 border border-cyan-500/30 text-xs font-medium transition cursor-pointer"
                        >
                          <span>{label}</span>
                          <ArrowUpRight className="w-3.5 h-3.5" />
                        </button>
                      );
                    })}
                </div>
              )}
            </div>

            {!isAssistant && (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-surface-muted border border-surface-border text-gray-400 shadow-md">
                <User className="w-5 h-5" />
              </div>
            )}
          </div>
        );
      })}


      {/* Confirmed Booking Voucher Card */}
      {confirmedBooking && (
        <div className="max-w-2xl ml-11 my-4 overflow-hidden rounded-2xl border border-emerald-500/50 bg-surface p-5 shadow-2xl relative">
          <div className="absolute top-0 right-0 bg-emerald-500/20 text-emerald-400 border-b border-l border-emerald-500/30 px-3 py-1 rounded-bl-xl text-xs font-bold uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" /> Confirmed
          </div>

          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
              <Ticket className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Booking Voucher Confirmed!</h3>
              <p className="text-xs text-gray-400">Reference: <span className="font-mono text-cyan-400 font-semibold">{confirmedBooking.bookingId || confirmedBooking.orderId}</span></p>
            </div>
          </div>

          <div className="rounded-xl bg-background/60 border border-surface-border p-3 text-xs space-y-2 mb-3">
            <div className="flex justify-between">
              <span className="text-gray-400">Transaction Authorization:</span>
              <span className="font-mono text-emerald-400 font-semibold">{confirmedBooking.payment?.transaction_reference || 'TXN-MOCK-OK'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Simulated Total Paid:</span>
              <span className="font-bold text-white">₹{(confirmedBooking.totalAmount || 18290).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Vehicle:</span>
              <span className="text-gray-200">{confirmedBooking.vehicle?.brand} {confirmedBooking.vehicle?.model}</span>
            </div>
          </div>

          <p className="text-[11px] text-gray-500 italic">
            🛡️ Simulated confirmation for Hackathon demonstration. No actual funds debited.
          </p>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

