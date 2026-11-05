import React, { useState } from 'react';
import { Calculator, ArrowRight, Check } from 'lucide-react';

interface EMICalculatorProps {
  vehiclePrice: number;
}

export const EMICalculator: React.FC<EMICalculatorProps> = ({ vehiclePrice }) => {
  const [downPaymentPct, setDownPaymentPct] = useState(20);
  const [tenureYears, setTenureYears] = useState(5);
  const [interestRate, setInterestRate] = useState(9.5);

  const downPayment = Math.round((vehiclePrice * downPaymentPct) / 100);
  const loanAmount = vehiclePrice - downPayment;

  // Monthly EMI Calculation: [P x R x (1+R)^N]/[(1+R)^N-1]
  const monthlyRate = interestRate / (12 * 100);
  const totalMonths = tenureYears * 12;
  const emi =
    loanAmount > 0
      ? Math.round(
          (loanAmount * monthlyRate * Math.pow(1 + monthlyRate, totalMonths)) /
            (Math.pow(1 + monthlyRate, totalMonths) - 1)
        )
      : 0;

  const totalPayable = emi * totalMonths;
  const totalInterest = totalPayable - loanAmount;

  return (
    <div className="rounded-2xl border border-surface-border bg-surface p-6 shadow-xl">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 rounded-xl bg-primary/20 text-primary-accent">
          <Calculator className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white">Interactive EMI Loan Estimator</h3>
          <p className="text-xs text-gray-400">Customize down payment and loan tenure</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 my-4">
        {/* Down Payment Slider */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-gray-400">Down Payment ({downPaymentPct}%)</span>
            <span className="text-white font-bold">₹{downPayment.toLocaleString('en-IN')}</span>
          </div>
          <input
            type="range"
            min="10"
            max="60"
            step="5"
            value={downPaymentPct}
            onChange={(e) => setDownPaymentPct(Number(e.target.value))}
            className="w-full accent-primary h-1.5 bg-background rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Loan Tenure Slider */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-gray-400">Tenure</span>
            <span className="text-white font-bold">{tenureYears} Years ({totalMonths} Mos)</span>
          </div>
          <input
            type="range"
            min="1"
            max="7"
            step="1"
            value={tenureYears}
            onChange={(e) => setTenureYears(Number(e.target.value))}
            className="w-full accent-primary h-1.5 bg-background rounded-lg appearance-none cursor-pointer"
          />
        </div>

        {/* Interest Rate */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-gray-400">Interest Rate</span>
            <span className="text-white font-bold">{interestRate}% p.a.</span>
          </div>
          <input
            type="range"
            min="8.0"
            max="14.0"
            step="0.25"
            value={interestRate}
            onChange={(e) => setInterestRate(Number(e.target.value))}
            className="w-full accent-primary h-1.5 bg-background rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>

      {/* Output summary */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-surface-border/60 bg-background/50 rounded-xl p-4">
        <div>
          <div className="text-[11px] text-gray-400 uppercase tracking-wider">Estimated Monthly EMI</div>
          <div className="text-2xl font-black text-cyan-400 mt-0.5">
            ₹{emi.toLocaleString('en-IN')}<span className="text-xs font-normal text-gray-400">/mo</span>
          </div>
        </div>
        <div>
          <div className="text-[11px] text-gray-400 uppercase tracking-wider">Principal Loan</div>
          <div className="text-base font-bold text-white mt-1">
            ₹{loanAmount.toLocaleString('en-IN')}
          </div>
        </div>
        <div>
          <div className="text-[11px] text-gray-400 uppercase tracking-wider">Total Interest</div>
          <div className="text-base font-bold text-amber-400 mt-1">
            ₹{totalInterest.toLocaleString('en-IN')}
          </div>
        </div>
      </div>
    </div>
  );
};

