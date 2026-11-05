import React, { useEffect, useRef, useState } from 'react';
import { calculateBookingTotal, createBooking, createOrder } from '../services/api';
import { ShieldCheck, X } from 'lucide-react';

interface MCPAppHostProps {
  appName: 'booking' | 'checkout';
  contextData: any;
  onFinish: (result: any) => void;
  onCancel: () => void;
}

export const MCPAppHost: React.FC<MCPAppHostProps> = ({
  appName,
  contextData,
  onFinish,
  onCancel,
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [isReady, setIsReady] = useState(false);

  const iframeSrc = appName === 'booking' ? '/mcp-apps/booking/index.html' : '/mcp-apps/checkout/index.html';
  const uri = appName === 'booking' ? 'ui://booking-form' : 'ui://checkout-modal';

  useEffect(() => {
    const handleMessage = async (event: MessageEvent) => {
      const msg = event.data;
      if (!msg || typeof msg !== 'object') return;

      if (msg.type === 'mcp-app:ready') {
        setIsReady(true);
        // Send handshake initialization
        if (iframeRef.current && iframeRef.current.contentWindow) {
          iframeRef.current.contentWindow.postMessage(
            {
              type: 'mcp-app:init',
              protocolVersion: '1.0',
              context: contextData,
            },
            '*'
          );
        }
      } else if (msg.type === 'mcp-app:action') {
        if (msg.action === 'recalculate' && msg.payload) {
          try {
            const pricing = await calculateBookingTotal(
              msg.payload.vehicleId,
              msg.payload.durationDays,
              msg.payload.addonIds || []
            );
            // Post back authoritative calculation
            if (iframeRef.current && iframeRef.current.contentWindow) {
              iframeRef.current.contentWindow.postMessage(
                {
                  type: 'mcp-app:update',
                  pricing: pricing,
                },
                '*'
              );
            }
          } catch (err) {
            console.error('Failed to recalculate backend price:', err);
          }
        }
      } else if (msg.type === 'mcp-app:finish') {
        if (msg.status === 'cancelled' || msg.action === 'cancel') {
          onCancel();
        } else if (msg.action === 'proceed_checkout' && msg.data) {
          // Booking form completed -> Create booking or order on backend
          try {
            if (msg.data.intent === 'buy') {
              const res = await createOrder({
                session_id: msg.data.sessionId,
                vehicle_id: msg.data.vehicleId,
                customer_name: msg.data.customerName,
                customer_email: msg.data.customerEmail,
                customer_phone: msg.data.customerPhone,
                pan_or_id: msg.data.idNumber,
                delivery_city: msg.data.location || 'Delhi',
                financing_selected: false,
                deposit_amount: 25000.0,
              });
              onFinish({
                nextApp: 'checkout',
                orderId: res.order_id,
                totalAmount: 25000.0,
                vehicle: contextData.vehicle,
                intent: 'buy',
              });
            } else {
              const res = await createBooking({
                session_id: msg.data.sessionId,
                vehicle_id: msg.data.vehicleId,
                customer_name: msg.data.customerName,
                customer_email: msg.data.customerEmail,
                customer_phone: msg.data.customerPhone,
                driver_license_number: msg.data.idNumber,
                pickup_date: msg.data.pickupDate,
                return_date: msg.data.pickupDate, // calculated by backend
                duration_days: msg.data.durationDays,
                pickup_location: msg.data.location,
                return_location: msg.data.location,
                addon_ids: msg.data.addonIds,
              });
              onFinish({
                nextApp: 'checkout',
                bookingId: res.booking_id,
                totalAmount: res.booking.total_amount,
                vehicle: contextData.vehicle,
                durationDays: msg.data.durationDays,
                intent: 'rent',
              });
            }
          } catch (e) {
            console.error('Failed to save booking:', e);
          }
        } else if (msg.status === 'paid') {
          onFinish({
            status: 'CONFIRMED',
            payment: msg.payment,
            bookingId: msg.bookingId,
          });
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [contextData, onFinish, onCancel]);

  return (
    <div className="my-4 overflow-hidden rounded-xl border border-primary/40 bg-surface shadow-2xl transition-all">
      {/* MCP Frame Header */}
      <div className="flex items-center justify-between border-b border-surface-border bg-surface-muted/80 px-4 py-2.5 text-xs">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-mono text-cyan-400 font-semibold">{uri}</span>
          <span className="text-gray-500">•</span>
          <span className="text-gray-400">Sandboxed MCP App Container</span>
        </div>
        <button
          onClick={onCancel}
          className="text-gray-400 hover:text-white transition-colors p-1"
          title="Close MCP App"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Embedded Iframe */}
      <iframe
        ref={iframeRef}
        src={iframeSrc}
        title={`MCP App: ${uri}`}
        className="h-[520px] w-full border-0 bg-background"
        sandbox="allow-scripts allow-forms allow-same-origin"
      />
    </div>
  );
};

