import { create } from 'zustand';
import { ChatMessage, A2UIComponent, ProgressEvent, Vehicle } from '../types';
import { useVehicleStore } from './vehicleStore';
import { useComparisonStore } from './comparisonStore';

export interface WebsiteAction {
  type: string;
  payload: Record<string, any>;
}

interface ConsultantStore {
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
  toggleOpen: () => void;
  sessionId: string;
  setSessionId: (id: string) => void;
  workflowState: string;
  setWorkflowState: (state: string) => void;
  messages: ChatMessage[];
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (msg: ChatMessage) => void;
  a2uiSurfaces: Record<string, A2UIComponent[]>;
  setA2uiSurfaces: (surfaces: Record<string, A2UIComponent[]>) => void;
  addA2uiSurface: (surfaceId: string, components: A2UIComponent[]) => void;
  activeMcpApp: { name: 'booking' | 'checkout'; context: any } | null;
  setActiveMcpApp: (app: { name: 'booking' | 'checkout'; context: any } | null) => void;
  confirmedBooking: any | null;
  setConfirmedBooking: (booking: any | null) => void;
  currentEvent: ProgressEvent | null;
  setCurrentEvent: (event: ProgressEvent | null) => void;
  activeContext: { currentRoute: string; vehicleId?: string; vehicleName?: string };
  setActiveContext: (ctx: { currentRoute: string; vehicleId?: string; vehicleName?: string }) => void;
  sellDraft: any | null;
  setSellDraft: (draft: any) => void;
  checkoutDraft: Record<string, any> | null;
  setCheckoutDraft: (draft: Record<string, any> | null) => void;
  acknowledgeManualTransaction: (transaction: { orderId: string; brand?: string; model?: string; amount?: number; type?: 'RENT' | 'BUY' }) => void;
  executeWebsiteAction: (action: WebsiteAction, navigate?: (path: string) => void) => void;
  resetConversation: () => void;
}

export const useConsultantStore = create<ConsultantStore>((set, get) => ({
  isOpen: false,
  setIsOpen: (open) => set({ isOpen: open }),
  toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
  sessionId: 'sess_init',
  setSessionId: (id) => set({ sessionId: id }),
  workflowState: 'NEW',
  setWorkflowState: (state) => set({ workflowState: state }),
  messages: [
    {
      id: 'msg_welcome',
      role: 'assistant',
      content:
        "Welcome to **Aura Motors**. I am your personal automotive strategist.\n\n" +
        "I can directly control the website for you — filter cars, open vehicle details, compare specs, or guide you through seamless booking. " +
        "What are you looking for today? (e.g. *'Show me automatic SUVs under ₹15 Lakh'* or *'Compare the two best luxury sedans'*).",
      timestamp: new Date().toISOString(),
    },
  ],
  setMessages: (messages) => set({ messages }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  a2uiSurfaces: {},
  setA2uiSurfaces: (surfaces) => set({ a2uiSurfaces: surfaces }),
  addA2uiSurface: (surfaceId, components) =>
    set((state) => ({
      a2uiSurfaces: { ...state.a2uiSurfaces, [surfaceId]: components },
    })),
  activeMcpApp: null,
  setActiveMcpApp: (app) => set({ activeMcpApp: app }),
  confirmedBooking: null,
  setConfirmedBooking: (booking) => set({ confirmedBooking: booking }),
  currentEvent: null,
  setCurrentEvent: (event) => set({ currentEvent: event }),
  activeContext: { currentRoute: '/' },
  setActiveContext: (ctx) => set({ activeContext: ctx }),
  sellDraft: null,
  setSellDraft: (draft) => set({ sellDraft: draft }),
  checkoutDraft: null,
  setCheckoutDraft: (draft) => set({ checkoutDraft: draft }),

  acknowledgeManualTransaction: (txn) => {
    const carTitle = txn.brand && txn.model ? `${txn.brand} ${txn.model}` : 'your selected vehicle';
    const txnType = txn.type === 'RENT' ? 'rental booking' : 'purchase reservation';
    const amountStr = txn.amount ? ` (Total: ₹${txn.amount.toLocaleString()})` : '';

    const ackMessage: ChatMessage = {
      id: `msg_txn_ack_${Date.now()}`,
      role: 'assistant',
      content:
        `🎉 **Transaction Confirmed on Website!**\n\n` +
        `Your ${txnType} for **${carTitle}**${amountStr} has been successfully recorded (Reference: \`${txn.orderId}\`).\n\n` +
        `I have updated your digital garage, transaction records, and payment history in real time.`,
      timestamp: new Date().toISOString(),
    };
    set((state) => ({ messages: [...state.messages, ackMessage] }));
    try {
      window.dispatchEvent(new CustomEvent('aura_data_refresh', { detail: txn }));
    } catch (e) {
      console.warn('Could not dispatch aura_data_refresh', e);
    }
  },

  executeWebsiteAction: (action: WebsiteAction, navigate?: (path: string) => void) => {
    console.log('[AI Consultant Controller Action]:', action);
    const { type, payload } = action;

    switch (type) {
      case 'PREFILL_SELL_FORM':
      case 'START_WORKFLOW':
      case 'UPDATE_FORM':
        set({ sellDraft: payload });
        break;

      case 'NAVIGATE_TO_PAGE':
      case 'NAVIGATE':
        if (navigate && payload.path) {
          navigate(payload.path);
        }
        break;

      case 'FILTER_VEHICLES':
      case 'APPLY_FILTERS':
        const vehicleStore = useVehicleStore.getState();
        const filterUpdates: Record<string, any> = {};
        if (payload.category !== undefined) filterUpdates.category = payload.category;
        if (payload.transmission !== undefined) filterUpdates.transmission = payload.transmission;
        if (payload.fuelType !== undefined) filterUpdates.fuelType = payload.fuelType;
        if (payload.location !== undefined) filterUpdates.location = payload.location;
        if (payload.brand !== undefined) filterUpdates.brand = payload.brand;
        if (payload.intent !== undefined) filterUpdates.intent = payload.intent;
        if (payload.maxPrice !== undefined && payload.maxPrice > 0) filterUpdates.maxPrice = payload.maxPrice;
        if (payload.minPrice !== undefined && payload.minPrice > 0) filterUpdates.minPrice = payload.minPrice;
        if (payload.seats !== undefined) filterUpdates.seats = payload.seats;
        if (payload.seatsMatchType !== undefined) filterUpdates.seatsMatchType = payload.seatsMatchType;
        vehicleStore.setFilters(filterUpdates);
        break;

      case 'REFRESH_DATA':
        try {
          window.dispatchEvent(new CustomEvent('aura_data_refresh', { detail: payload }));
        } catch (e) {
          console.warn('Could not dispatch aura_data_refresh event', e);
        }
        break;

      case 'SHOW_NOTIFICATION':
        try {
          window.dispatchEvent(new CustomEvent('aura_notification', { detail: payload }));
        } catch (e) {
          console.warn('Could not dispatch aura_notification event', e);
        }
        break;

      case 'CLEAR_FILTERS':
        useVehicleStore.getState().resetFilters();
        break;

      case 'SELECT_VEHICLE':
      case 'OPEN_VEHICLE_DETAILS':
        if (navigate && (payload.vehicleId || payload.id)) {
          navigate(`/vehicles/${payload.vehicleId || payload.id}`);
        }
        break;

      case 'ADD_TO_COMPARISON':
        const compStore = useComparisonStore.getState();
        const vStore = useVehicleStore.getState();
        if (payload.vehicleIds && Array.isArray(payload.vehicleIds)) {
          compStore.clearComparison();
          payload.vehicleIds.forEach((vid: string) => {
            const vehicle = vStore.getVehicleById(vid);
            if (vehicle) compStore.addVehicle(vehicle);
          });
        }
        break;

      case 'OPEN_BOOKING_APP':
        set({
          activeMcpApp: {
            name: 'booking',
            context: payload,
          },
        });
        break;

      case 'OPEN_CHECKOUT_APP':
        set({
          activeMcpApp: {
            name: 'checkout',
            context: payload,
          },
        });
        break;

      case 'PREFILL_CHECKOUT_FORM':
        const currentDraft = get().checkoutDraft || {};
        const mergedDraft = { ...currentDraft, ...payload };
        set({ checkoutDraft: mergedDraft });
        try {
          window.dispatchEvent(new CustomEvent('aura_prefill_checkout', { detail: mergedDraft }));
        } catch (e) {
          console.warn('Could not dispatch aura_prefill_checkout', e);
        }
        break;

      case 'AUTO_CLICK_BOOK':
        try {
          const btn = document.querySelector('[data-action="book-button"]') || document.getElementById('book-button');
          if (btn) {
            btn.classList.add('ring-4', 'ring-cyan-400', 'animate-pulse');
            setTimeout(() => {
              btn.classList.remove('ring-4', 'ring-cyan-400', 'animate-pulse');
              (btn as HTMLElement).click();
            }, 400);
          } else if (navigate && (payload.path || payload.vehicleId)) {
            const targetPath = payload.path || (payload.intent === 'buy' ? `/checkout/${payload.vehicleId}` : `/booking/${payload.vehicleId}`);
            navigate(targetPath);
          }
          window.dispatchEvent(new CustomEvent('aura_auto_click_book', { detail: payload }));
        } catch (e) {
          console.warn('Could not execute auto click book', e);
        }
        break;

      case 'EXECUTE_CHECKOUT_SUBMIT':
        try {
          window.dispatchEvent(new CustomEvent('aura_execute_checkout_submit', { detail: payload }));
        } catch (e) {
          console.warn('Could not dispatch aura_execute_checkout_submit', e);
        }
        break;

      default:
        console.warn('Unhandled Website Action:', type);
    }
  },

  resetConversation: () => {
    set({
      messages: [
        {
          id: 'msg_welcome_reset',
          role: 'assistant',
          content: 'Session reset! How can I assist you with vehicle discovery, rental, purchase, or comparisons today?',
          timestamp: new Date().toISOString(),
        },
      ],
      workflowState: 'NEW',
      a2uiSurfaces: {},
      activeMcpApp: null,
      confirmedBooking: null,
      currentEvent: null,
      sellDraft: null,
      checkoutDraft: null,
    });
  },
}));

