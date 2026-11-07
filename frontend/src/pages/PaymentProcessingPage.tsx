import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { RotateCcw, ShieldCheck, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useConsultantStore } from '../store/consultantStore';

export const PaymentProcessingPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { token } = useAuthStore();

  const stateData = location.state || {};
  const amount = stateData.amount || 25000;
  const paymentMethod = stateData.paymentMethod || 'upi';
  const scenario = stateData.simScenario || 'success';

  const [step, setStep] = useState(1);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const processPayment = async () => {
      // Step 1: Initializing
      await new Promise((r) => setTimeout(r, 700));
      if (!isMounted) return;
      setStep(2);

      // Step 2: Contacting mock banking network
      await new Promise((r) => setTimeout(r, 900));
      if (!isMounted) return;
      setStep(3);

      try {
        const headers: Record<string, string> = {
          'Content-Type': 'application/json',
          'Idempotency-Key': `idemp_pay_${orderId}`
        };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch('/api/payments/mock/confirm', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            orderId: orderId,
            amount: amount,
            currency: 'INR',
            paymentMethod: paymentMethod,
            simScenario: scenario
          })
        });

        const data = await res.json();

        if (res.ok && data.status === 'SUCCESS') {
          // Real-time synchronization: notify Aura AI about the completed payment
          useConsultantStore.getState().acknowledgeManualTransaction({
            orderId: orderId || data.payment?.orderId || 'ORD-TXN',
            brand: stateData.vehicle?.brand || data.payment?.vehicleSnapshot?.brand,
            model: stateData.vehicle?.model || data.payment?.vehicleSnapshot?.model,
            amount,
            type: stateData.isRent ? 'RENT' : 'BUY',
          });

          await new Promise((r) => setTimeout(r, 600));
          if (!isMounted) return;
          navigate(`/payment/result/${orderId}`, {
            state: {
              status: 'SUCCESS',
              payment: data.payment,
              orderId,
              amount,
              vehicle: stateData.vehicle
            },
            replace: true
          });
        } else {
          const reason = data.payment?.errorMessage || data.detail || 'Payment was declined by the simulated card issuer.';
          setErrorMsg(reason);
          await new Promise((r) => setTimeout(r, 1000));
          if (!isMounted) return;
          navigate(`/payment/result/${orderId}`, {
            state: {
              status: 'FAILED',
              errorMessage: reason,
              orderId,
              amount,
              payment: data.payment
            },
            replace: true
          });
        }
      } catch (err: any) {
        setErrorMsg('Network timeout during payment gateway simulation.');
        setTimeout(() => {
          if (!isMounted) return;
          navigate(`/payment/result/${orderId}`, {
            state: {
              status: 'FAILED',
              errorMessage: 'Network timeout during payment gateway simulation.',
              orderId,
              amount
            },
            replace: true
          });
        }, 1200);
      }
    };

    if (orderId) {
      processPayment();
    }

    return () => {
      isMounted = false;
    };
  }, [orderId, amount, paymentMethod, scenario, navigate, token, stateData.vehicle]);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-3xl p-8 text-center shadow-2xl relative overflow-hidden">
        {/* Glow backdrop */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />

        <div className="w-16 h-16 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center mx-auto mb-6">
          <RotateCcw className="w-8 h-8 text-cyan-400 animate-spin" />
        </div>

        <span className="text-xs uppercase font-bold tracking-widest text-cyan-400">
          Mock Settlement Engine
        </span>
        <h2 className="text-2xl font-bold text-white mt-1">Processing Payment</h2>
        <p className="text-slate-400 text-xs mt-2">
          Securely negotiating with Amulate Hackathon simulated payment rail...
        </p>

        {/* Transaction Summary Card */}
        <div className="my-6 p-4 rounded-xl bg-slate-950 border border-slate-800 text-left text-xs space-y-2">
          <div className="flex justify-between text-slate-400">
            <span>Order Reference:</span>
            <span className="font-mono text-white font-semibold">{orderId}</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Payment Channel:</span>
            <span className="text-white capitalize">{paymentMethod} (Simulated)</span>
          </div>
          <div className="flex justify-between text-slate-400">
            <span>Amount:</span>
            <span className="font-bold text-emerald-400">₹{amount.toLocaleString()}</span>
          </div>
        </div>

        {/* Live Step Progress */}
        <div className="space-y-3 text-left text-xs mb-6">
          <div className="flex items-center gap-3">
            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
              step >= 1 ? 'bg-cyan-500 text-slate-950' : 'bg-slate-800 text-slate-400'
            }`}>
              1
            </div>
            <span className={step >= 1 ? 'text-white font-medium' : 'text-slate-500'}>
              Validating transaction payload &amp; idempotency key
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
              step >= 2 ? 'bg-cyan-500 text-slate-950' : 'bg-slate-800 text-slate-400'
            }`}>
              2
            </div>
            <span className={step >= 2 ? 'text-white font-medium' : 'text-slate-500'}>
              Transmitting token to simulated banking partner
            </span>
          </div>

          <div className="flex items-center gap-3">
            <div className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
              step >= 3 ? 'bg-cyan-500 text-slate-950' : 'bg-slate-800 text-slate-400'
            }`}>
              3
            </div>
            <span className={step >= 3 ? 'text-white font-medium' : 'text-slate-500'}>
              Awaiting authoritative ledger settlement confirmation
            </span>
          </div>
        </div>

        <div className="text-[11px] text-slate-500 flex items-center justify-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>Please do not refresh or close this window</span>
        </div>
      </div>
    </div>
  );
};

