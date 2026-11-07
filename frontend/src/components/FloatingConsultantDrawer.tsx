import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConsultantStore } from '../store/consultantStore';
import { AgentTimeline } from '../features/progress/AgentTimeline';
import { ChatContainer } from '../features/chat/ChatContainer';
import { MessageComposer } from '../features/chat/MessageComposer';
import { sendMessage, sendA2uiAction, createSession, deleteSession } from '../services/api';
import {
  Sparkles,
  X,
  RefreshCw,
  Minus,
  Maximize2,
  Minimize2,
  GripHorizontal,
} from 'lucide-react';

// --- Types ---
interface Position {
  x: number;
  y: number;
}

const STORAGE_KEY_POS = 'aura_consultant_position';
const STORAGE_KEY_MINIMIZED = 'aura_consultant_minimized';

const PANEL_WIDTH = 480;
const PANEL_HEIGHT_NORMAL = 680;
const PANEL_HEIGHT_EXPANDED = 780;

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

function getDefaultPosition(): Position {
  if (typeof window === 'undefined') return { x: 100, y: 80 };
  const x = window.innerWidth - PANEL_WIDTH - 24;
  const y = window.innerHeight - PANEL_HEIGHT_NORMAL - 24;
  return { x: clamp(x, 8, window.innerWidth - PANEL_WIDTH - 8), y: clamp(y, 8, window.innerHeight - PANEL_HEIGHT_NORMAL - 8) };
}

function loadPosition(): Position {
  try {
    const stored = localStorage.getItem(STORAGE_KEY_POS);
    if (stored) {
      const p = JSON.parse(stored) as Position;
      // Validate that saved position is still on-screen
      if (
        typeof p.x === 'number' && typeof p.y === 'number' &&
        p.x >= 0 && p.y >= 0 &&
        p.x < window.innerWidth && p.y < window.innerHeight
      ) {
        return p;
      }
    }
  } catch {}
  return getDefaultPosition();
}

// ============================================================
export const FloatingConsultantDrawer: React.FC = () => {
  const navigate = useNavigate();
  const {
    isOpen,
    setIsOpen,
    toggleOpen,
    sessionId,
    setSessionId,
    workflowState,
    setWorkflowState,
    messages,
    addMessage,
    a2uiSurfaces,
    setA2uiSurfaces,
    activeMcpApp,
    setActiveMcpApp,
    confirmedBooking,
    setConfirmedBooking,
    currentEvent,
    setCurrentEvent,
    activeContext,
    executeWebsiteAction,
    resetConversation,
  } = useConsultantStore();

  const [isLoading, setIsLoading] = useState(false);
  const [isMinimized, setIsMinimized] = useState(() => {
    try { return localStorage.getItem(STORAGE_KEY_MINIMIZED) === '1'; } catch { return false; }
  });
  const [isExpanded, setIsExpanded] = useState(false);
  const [position, setPosition] = useState<Position>(loadPosition);
  const [isDragging, setIsDragging] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const panelRef = useRef<HTMLDivElement>(null);
  const dragOrigin = useRef<{ pointerX: number; pointerY: number; panelX: number; panelY: number } | null>(null);

  // ── Persist position ──────────────────────────────────────
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_POS, JSON.stringify(position));
    } catch {}
  }, [position]);

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_MINIMIZED, isMinimized ? '1' : '0');
    } catch {}
  }, [isMinimized]);

  // ── Unread badge ──────────────────────────────────────────
  useEffect(() => {
    if (!isOpen && messages.length > 1) {
      setUnreadCount((n) => n + 1);
    }
  }, [messages.length]);

  useEffect(() => {
    if (isOpen) setUnreadCount(0);
  }, [isOpen]);

  // ── Session init ──────────────────────────────────────────
  useEffect(() => {
    const init = async () => {
      if (sessionId === 'sess_init') {
        try {
          const res = await createSession();
          setSessionId(res.session_id);
        } catch (e) {
          console.error('Session init error:', e);
        }
      }
    };
    init();
  }, [sessionId, setSessionId]);

  // ── SSE subscription ──────────────────────────────────────
  useEffect(() => {
    if (!sessionId || sessionId === 'sess_init') return;
    const es = new EventSource(`/api/sessions/${sessionId}/events`);

    es.addEventListener('progress', (e) => {
      try {
        const data = JSON.parse(e.data);
        setCurrentEvent(data);
        if (data.stage) setWorkflowState(data.stage);
      } catch {}
    });

    es.addEventListener('a2ui', (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'createSurface' && msg.surfaceId && msg.components) {
          setA2uiSurfaces({ ...a2uiSurfaces, [msg.surfaceId]: msg.components });
        }
      } catch {}
    });

    es.addEventListener('website_action', (e) => {
      try {
        const act = JSON.parse(e.data);
        executeWebsiteAction(act, navigate);
      } catch {}
    });

    es.addEventListener('payment_status_updated', (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.status === 'SUCCESS') {
          setWorkflowState('CONFIRMED');
          setActiveMcpApp(null);
          const isBuy = data.transactionType === 'BUY';
          const title = isBuy ? 'Vehicle Purchase Confirmed' : 'Rental Reservation Confirmed';
          const targetDashboard = isBuy ? '/dashboard/purchases' : '/dashboard/rentals';

          addMessage({
            id: `msg_sync_confirm_${data.orderId || Date.now()}`,
            role: 'assistant',
            content: `### 🎉 ${title}!\n\n**Order Reference:** \`${data.orderId}\`\n**Transaction Reference:** \`${data.transactionReference}\`\n**Amount Settled:** ₹${(data.amount || 25000).toLocaleString()} *(Simulated Mock Rail)*\n**Status:** Authoritative Ledger Confirmed\n\nYour transaction has been recorded in our database and synchronized with your account dashboard.`,
            timestamp: new Date().toISOString(),
            data: {
              messageType: 'PAYMENT_SUCCESS',
              transaction: data,
              actions: [
                { label: isBuy ? 'View Purchase Details' : 'View Rental Details', path: targetDashboard },
                { label: 'Payment History', path: '/dashboard/payments' },
                { label: 'Explore More Cars', path: '/explore' }
              ]
            }
          });
        } else if (data.status === 'FAILED') {
          setWorkflowState('PAYMENT_FAILED');
          addMessage({
            id: `msg_sync_fail_${data.orderId || Date.now()}`,
            role: 'assistant',
            content: `### ❌ Payment Declined\n\n**Order ID:** \`${data.orderId}\`\n**Reason:** ${data.errorMessage || 'Simulated bank decline'}\n\nPlease retry checkout using another payment method or switch to Instant Success scenario.`,
            timestamp: new Date().toISOString(),
            data: {
              messageType: 'PAYMENT_FAILED',
              transaction: data
            }
          });
        }
      } catch (err) {
        console.error('Error in payment_status_updated SSE:', err);
      }
    });

    return () => es.close();
  }, [sessionId, navigate, executeWebsiteAction, setCurrentEvent, setWorkflowState, setA2uiSurfaces, a2uiSurfaces]);

  // ── Drag via Pointer Events API ───────────────────────────
  const onPointerDown = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      // Only drag on left-button, only on the handle (not buttons inside header)
      if (e.button !== 0) return;
      const target = e.target as HTMLElement;
      if (target.closest('button')) return;

      e.currentTarget.setPointerCapture(e.pointerId);
      setIsDragging(true);
      dragOrigin.current = {
        pointerX: e.clientX,
        pointerY: e.clientY,
        panelX: position.x,
        panelY: position.y,
      };
    },
    [position]
  );

  const onPointerMove = useCallback(
    (e: React.PointerEvent<HTMLDivElement>) => {
      if (!dragOrigin.current) return;
      const dx = e.clientX - dragOrigin.current.pointerX;
      const dy = e.clientY - dragOrigin.current.pointerY;
      const panelW = isExpanded ? Math.min(680, window.innerWidth - 16) : PANEL_WIDTH;
      const panelH = isExpanded ? PANEL_HEIGHT_EXPANDED : (isMinimized ? 60 : PANEL_HEIGHT_NORMAL);

      setPosition({
        x: clamp(dragOrigin.current.panelX + dx, 0, window.innerWidth - panelW),
        y: clamp(dragOrigin.current.panelY + dy, 0, window.innerHeight - panelH),
      });
    },
    [isExpanded, isMinimized]
  );

  const onPointerUp = useCallback(() => {
    dragOrigin.current = null;
    setIsDragging(false);
  }, []);

  // ── Message handlers ──────────────────────────────────────
  const handleSendMessage = async (text: string) => {
    setIsLoading(true);
    addMessage({
      id: `msg_user_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    });

    try {
      const res = await sendMessage(sessionId, text);
      if (res.workflow_state) setWorkflowState(res.workflow_state);
      if (res.message) addMessage(res.message);

      if (res.website_actions && Array.isArray(res.website_actions)) {
        res.website_actions.forEach((act: any) => {
          executeWebsiteAction(act, navigate);
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleA2uiAction = async (surfaceId: string, actionId: string, data: any) => {
    setIsLoading(true);
    try {
      const res = await sendA2uiAction(sessionId, surfaceId, actionId, data);
      if (res.workflow_state) setWorkflowState(res.workflow_state);
      if (res.message) addMessage(res.message);

      // Execute any website actions from A2UI response
      if (res.website_actions && Array.isArray(res.website_actions)) {
        res.website_actions.forEach((act: any) => executeWebsiteAction(act, navigate));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMcpAppFinish = (result: any) => {
    if (result.nextApp === 'checkout') {
      setActiveMcpApp({ name: 'checkout', context: result });
      setWorkflowState('CHECKOUT_READY');
    } else if (result.status === 'CONFIRMED') {
      setActiveMcpApp(null);
      setConfirmedBooking(result);
      setWorkflowState('CONFIRMED');
      addMessage({
        id: `msg_confirm_${Date.now()}`,
        role: 'assistant',
        content: `🎉 **Booking Confirmed!** Reference: **${result.bookingId || result.orderId}**. Payment receipt: **${result.payment?.transaction_reference || 'TXN-OK'}**. Voucher generated below.`,
        timestamp: new Date().toISOString(),
      });
    }
  };

  const handleResetSession = async () => {
    try {
      await deleteSession(sessionId);
      const newSess = await createSession();
      setSessionId(newSess.session_id);
      resetConversation();
    } catch (e) {
      console.error(e);
    }
  };

  // ── Panel dimensions ──────────────────────────────────────
  const panelW = isExpanded ? Math.min(680, window.innerWidth - 16) : PANEL_WIDTH;
  const panelH = isMinimized ? 56 : (isExpanded ? PANEL_HEIGHT_EXPANDED : PANEL_HEIGHT_NORMAL);

  // ── Render ────────────────────────────────────────────────
  return (
    <>
      {/* ── Floating Action Button (when closed) ── */}
      {!isOpen && (
        <button
          type="button"
          onClick={() => { toggleOpen(); setUnreadCount(0); }}
          className="fixed bottom-6 right-6 z-[9998] flex items-center gap-3 rounded-full bg-gradient-to-r from-primary to-cyan-500 p-4 text-white shadow-2xl transition-all hover:scale-105 active:scale-95 group"
          title="Open Aura AI Consultant"
        >
          <div className="relative">
            <Sparkles className="w-6 h-6 animate-pulse" />
            {unreadCount > 0 && (
              <span className="absolute -top-2 -right-2 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-[9px] font-black text-white shadow-md">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </div>
          <span className="hidden md:inline font-bold text-sm tracking-wide pr-1">
            Aura AI
          </span>
        </button>
      )}

      {/* ── Floating Draggable Panel (when open) ── */}
      {isOpen && (
        <div
          ref={panelRef}
          style={{
            position: 'fixed',
            left: position.x,
            top: position.y,
            width: panelW,
            height: panelH,
            zIndex: 9999,
            transition: isDragging ? 'none' : 'width 0.2s ease, height 0.2s ease',
          }}
          className="flex flex-col rounded-2xl border border-surface-border bg-background/97 backdrop-blur-2xl shadow-[0_8px_60px_rgba(0,0,0,0.6)] overflow-hidden"
        >
          {/* ── HEADER / DRAG HANDLE ── */}
          <div
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onPointerCancel={onPointerUp}
            className={`flex items-center justify-between border-b border-surface-border bg-surface px-4 py-3 select-none shrink-0 ${
              isDragging ? 'cursor-grabbing' : 'cursor-grab'
            }`}
          >
            {/* Left: Brand + Status */}
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-cyan-500 shadow-md">
                <Sparkles className="w-4 h-4 text-white" />
              </div>
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white tracking-wide whitespace-nowrap">
                    Aura AI
                  </span>
                  <span className="hidden sm:inline rounded-full bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 text-[10px] font-semibold text-cyan-400 whitespace-nowrap">
                    Website Controller
                  </span>
                  <span className="flex h-2 w-2 rounded-full bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.9)]" title="Online" />
                </div>
                {!isMinimized && (
                  <p className="text-[11px] text-gray-400 truncate">
                    {activeContext.vehicleName
                      ? <>Inspecting: <span className="text-white font-medium">{activeContext.vehicleName}</span></>
                      : <>Route: <span className="font-mono text-gray-300">{activeContext.currentRoute}</span></>
                    }
                  </p>
                )}
              </div>
            </div>

            {/* Center: Drag grip visual */}
            <div className="flex-1 flex justify-center pointer-events-none">
              <GripHorizontal className="w-5 h-5 text-gray-600" />
            </div>

            {/* Right: Controls */}
            <div className="flex items-center gap-1 shrink-0">
              <button
                type="button"
                onClick={handleResetSession}
                title="Reset Conversation"
                className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-surface-muted transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsMinimized((v) => !v)}
                title={isMinimized ? 'Restore' : 'Minimize'}
                className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-surface-muted transition-colors"
              >
                <Minus className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setIsExpanded((v) => !v)}
                title={isExpanded ? 'Shrink' : 'Expand'}
                className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-surface-muted transition-colors"
              >
                {isExpanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
              </button>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                title="Close"
                className="p-1.5 text-gray-400 hover:text-red-400 rounded-lg hover:bg-surface-muted transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* ── BODY (hidden when minimized) ── */}
          {!isMinimized && (
            <>
              {/* Progress Timeline */}
              <AgentTimeline currentEvent={currentEvent} workflowState={workflowState} />

              {/* Chat Stream */}
              <ChatContainer
                messages={messages}
                a2uiSurfaces={a2uiSurfaces}
                activeMcpApp={activeMcpApp}
                onA2uiAction={handleA2uiAction}
                onMcpAppFinish={handleMcpAppFinish}
                onMcpAppCancel={() => setActiveMcpApp(null)}
                confirmedBooking={confirmedBooking}
              />

              {/* Message Composer */}
              <MessageComposer onSendMessage={handleSendMessage} disabled={isLoading} />
            </>
          )}
        </div>
      )}
    </>
  );
};
