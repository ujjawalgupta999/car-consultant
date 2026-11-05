import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConsultantStore } from '../store/consultantStore';
import { AgentTimeline } from '../features/progress/AgentTimeline';
import { ChatContainer } from '../features/chat/ChatContainer';
import { MessageComposer } from '../features/chat/MessageComposer';
import { sendMessage, sendA2uiAction, createSession, deleteSession } from '../services/api';
import { Sparkles, X, RefreshCw, Cpu, ExternalLink } from 'lucide-react';

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

  // Initialize session on mount
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

  // Subscribe to SSE events
  useEffect(() => {
    if (!sessionId || sessionId === 'sess_init') return;
    const es = new EventSource(`/api/sessions/${sessionId}/events`);

    es.addEventListener('progress', (e) => {
      try {
        const data = JSON.parse(e.data);
        setCurrentEvent(data);
        if (data.stage) setWorkflowState(data.stage);
      } catch (err) {
        console.error(err);
      }
    });

    es.addEventListener('a2ui', (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'createSurface' && msg.surfaceId && msg.components) {
          setA2uiSurfaces({ ...a2uiSurfaces, [msg.surfaceId]: msg.components });
        }
      } catch (err) {
        console.error(err);
      }
    });

    es.addEventListener('website_action', (e) => {
      try {
        const act = JSON.parse(e.data);
        executeWebsiteAction(act, navigate);
      } catch (err) {
        console.error(err);
      }
    });

    return () => es.close();
  }, [sessionId, navigate, executeWebsiteAction, setCurrentEvent, setWorkflowState, setA2uiSurfaces, a2uiSurfaces]);

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

      // Execute any website controller actions
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

      if (actionId === 'select_vehicle' && res.selected_vehicle) {
        setActiveMcpApp({
          name: 'booking',
          context: {
            sessionId,
            vehicle: res.selected_vehicle,
            vehicleId: res.selected_vehicle.id,
            intent: 'rent',
          },
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMcpAppFinish = (result: any) => {
    if (result.nextApp === 'checkout') {
      setActiveMcpApp({
        name: 'checkout',
        context: result,
      });
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

  return (
    <>
      {/* Floating Action Button (FAB) when closed */}
      {!isOpen && (
        <button
          type="button"
          onClick={toggleOpen}
          className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-full bg-gradient-to-r from-primary to-cyan-500 p-4 text-white shadow-2xl transition-all hover:scale-105 active:scale-95 group"
          title="Open AI Automotive Consultant"
        >
          <div className="relative">
            <Sparkles className="w-6 h-6 animate-pulse" />
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-300"></span>
            </span>
          </div>
          <span className="hidden md:inline font-bold text-sm tracking-wide pr-1">
            AI Consultant
          </span>
        </button>
      )}

      {/* Floating Drawer Container when open */}
      {isOpen && (
        <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-2xl flex-col border-l border-surface-border bg-background/95 backdrop-blur-2xl shadow-2xl animate-in slide-in-from-right duration-300">
          {/* Drawer Header */}
          <div className="flex items-center justify-between border-b border-surface-border bg-surface px-5 py-3.5">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-cyan-500 shadow-md">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-bold text-white tracking-wide">
                    Aura AI Consultant
                  </h3>
                  <span className="rounded-full bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.5 text-[10px] font-semibold text-cyan-400">
                    Website Controller
                  </span>
                </div>
                {activeContext.vehicleName ? (
                  <p className="text-[11px] text-gray-400 truncate max-w-xs">
                    Inspecting: <span className="text-white font-medium">{activeContext.vehicleName}</span>
                  </p>
                ) : (
                  <p className="text-[11px] text-gray-400">
                    Active on: <span className="font-mono text-gray-300">{activeContext.currentRoute}</span>
                  </p>
                )}
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={handleResetSession}
                title="Reset Conversation"
                className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-surface-muted transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={() => navigate('/consultant')}
                title="Expand to Full Page"
                className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-surface-muted transition-colors"
              >
                <ExternalLink className="w-4 h-4" />
              </button>
              <button
                type="button"
                onClick={toggleOpen}
                title="Close Drawer"
                className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-surface-muted transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Live Progress Timeline */}
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
          <MessageComposer
            onSendMessage={handleSendMessage}
            disabled={isLoading}
          />
        </div>
      )}
    </>
  );
};
