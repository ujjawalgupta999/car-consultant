import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useConsultantStore } from '../store/consultantStore';
import { AgentTimeline } from '../features/progress/AgentTimeline';
import { ChatContainer } from '../features/chat/ChatContainer';
import { MessageComposer } from '../features/chat/MessageComposer';
import { sendMessage, sendA2uiAction, createSession, deleteSession } from '../services/api';
import { Sparkles, RefreshCw, Cpu, Layers, ArrowLeft } from 'lucide-react';

export const ConsultantPage: React.FC = () => {
  const navigate = useNavigate();
  const {
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

  // Initialize session on mount if needed
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

      // Execute website actions
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
    <div className="min-h-screen bg-slate-950 text-slate-100 pt-24 pb-12 flex flex-col">
      <div className="max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 flex-1 flex flex-col">
        {/* Full Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 mb-4 border-b border-slate-800 gap-4">
          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate(-1)}
              className="p-2 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white rounded-xl transition"
              title="Go Back"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold text-white tracking-tight">Aura AI Consultant</h1>
                <span className="text-[10px] font-semibold text-cyan-400 bg-cyan-950/80 border border-cyan-800/40 px-2 py-0.5 rounded-full">
                  Website Controller
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Session: <span className="font-mono text-slate-300">{sessionId}</span> • Stage: <span className="font-semibold text-cyan-300">{workflowState}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleResetSession}
              className="px-3.5 py-1.5 border border-slate-800 hover:border-slate-700 text-slate-300 hover:text-white rounded-xl text-xs font-medium transition flex items-center space-x-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Reset State</span>
            </button>
          </div>
        </div>

        {/* State Machine Agent Timeline */}
        <div className="mb-4 bg-slate-900/60 border border-slate-800 rounded-2xl p-4 shadow-lg">
          <AgentTimeline currentEvent={currentEvent} workflowState={workflowState} />
        </div>

        {/* Main Conversation Container */}
        <div className="flex-1 bg-slate-900/40 border border-slate-800 rounded-2xl flex flex-col overflow-hidden min-h-[500px]">
          <ChatContainer
            messages={messages}
            a2uiSurfaces={a2uiSurfaces}
            activeMcpApp={activeMcpApp}
            onA2uiAction={handleA2uiAction}
            onMcpAppFinish={handleMcpAppFinish}
            onMcpAppCancel={() => setActiveMcpApp(null)}
            confirmedBooking={confirmedBooking}
          />

          <MessageComposer
            onSendMessage={handleSendMessage}
            disabled={isLoading || workflowState === 'CONFIRMED'}
          />
        </div>
      </div>
    </div>
  );
};
