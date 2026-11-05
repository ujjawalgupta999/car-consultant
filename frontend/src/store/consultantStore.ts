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

  executeWebsiteAction: (action: WebsiteAction, navigate?: (path: string) => void) => {
    console.log('[AI Consultant Controller Action]:', action);
    const { type, payload } = action;

    switch (type) {
      case 'NAVIGATE_TO_PAGE':
        if (navigate && payload.path) {
          navigate(payload.path);
        }
        break;

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

      case 'CLEAR_FILTERS':
        useVehicleStore.getState().resetFilters();
        break;

      case 'OPEN_VEHICLE_DETAILS':
        if (navigate && payload.vehicleId) {
          navigate(`/vehicles/${payload.vehicleId}`);
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
    });
  },
}));

