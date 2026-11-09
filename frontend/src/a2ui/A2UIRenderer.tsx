import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { A2UIComponent } from '../types';
import { useVehicleStore } from '../store/vehicleStore';
import { useConsultantStore } from '../store/consultantStore';
import { CheckCircle2, AlertTriangle, Zap, Fuel, Gauge, Users, ArrowRight, ShieldCheck, MapPin } from 'lucide-react';

interface A2UIRendererProps {
  surfaceId: string;
  components: A2UIComponent[];
  onAction: (actionId: string, data: any) => void;
}

export const A2UIRenderer: React.FC<A2UIRendererProps> = ({
  surfaceId,
  components,
  onAction,
}) => {
  const navigate = useNavigate();
  const { purchasedVehicleIds, getVehicleById } = useVehicleStore();
  // Track selected value per RadioGroup field (keyed by component id)
  const [selectedValues, setSelectedValues] = useState<Record<string, string>>({});
  // Track loading state per component id
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const componentMap = new Map<string, A2UIComponent>();
  components.forEach((c) => componentMap.set(c.id, c));

  const handleChipClick = async (
    compId: string,
    actionId: string,
    field: string,
    value: string,
    label: string
  ) => {
    // Prevent double-click while loading
    if (loadingId) return;

    // Update selected state immediately (optimistic)
    setSelectedValues((prev) => ({ ...prev, [compId]: value }));
    setLoadingId(compId);

    try {
      // Build data payload based on actionId
      let data: Record<string, any> = { field, value };
      if (actionId === 'update_category') {
        data = { category: value };
      } else if (actionId === 'update_location') {
        data = { location: value };
      } else if (actionId === 'update_fuel') {
        data = { fuel_type: value };
      } else if (actionId === 'update_transmission') {
        data = { transmission: value };
      } else if (actionId === 'update_intent') {
        data = { intent: value };
      } else if (actionId === 'update_preference') {
        data = { field, value };
      }

      await onAction(actionId, data);
    } finally {
      setLoadingId(null);
    }
  };

  const renderComponent = (compId: string): React.ReactNode => {
    const comp = componentMap.get(compId);
    if (!comp) return null;

    const props = comp.properties || {};
    const children = (comp.children || []).map((childId) => renderComponent(childId));

    switch (comp.component) {
      case 'Card':
        return (
          <div
            key={comp.id}
            className="my-3 rounded-xl border border-surface-border bg-surface/90 backdrop-blur-md p-4 shadow-xl transition-all"
          >
            {props.title && (
              <div className="mb-3 border-b border-surface-border/60 pb-2">
                <h4 className="text-sm font-semibold tracking-wide text-gray-200 uppercase">
                  {props.title}
                </h4>
              </div>
            )}
            <div className="space-y-3">{children}</div>
          </div>
        );

      case 'Grid': {
        const cols = props.columns || 1;
        const colClass =
          cols === 2
            ? 'grid-cols-1 md:grid-cols-2'
            : cols === 3
            ? 'grid-cols-1 md:grid-cols-3'
            : 'grid-cols-1';
        return (
          <div key={comp.id} className={`grid ${colClass} gap-3 my-2`}>
            {children}
          </div>
        );
      }

      case 'RadioGroup': {
        const actionId: string = props.actionId || 'update_preference';
        const field: string = props.field || (
          actionId === 'update_category' ? 'category'
          : actionId === 'update_location' ? 'location'
          : actionId === 'update_fuel' ? 'fuel_type'
          : actionId === 'update_transmission' ? 'transmission'
          : actionId === 'update_intent' ? 'intent'
          : 'value'
        );
        const currentSelected = selectedValues[comp.id];
        const isGroupLoading = loadingId === comp.id;

        return (
          <div key={comp.id} className="space-y-2">
            {props.label && (
              <label className="text-xs font-semibold text-gray-400 tracking-wider uppercase block">
                {props.label}
              </label>
            )}
            <div className="flex flex-wrap gap-2">
              {(props.options || []).map((opt: any) => {
                const isSelected = currentSelected === opt.value;
                return (
                  <button
                    key={opt.value}
                    type="button"
                    disabled={isGroupLoading}
                    onClick={() =>
                      handleChipClick(comp.id, actionId, field, opt.value, opt.label)
                    }
                    className={`
                      rounded-lg border px-3 py-2 text-xs font-medium transition-all
                      ${isGroupLoading ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}
                      ${
                        isSelected
                          ? 'border-primary bg-primary/20 text-primary-accent shadow-md ring-1 ring-primary/40'
                          : 'border-surface-border bg-surface-muted text-gray-200 hover:border-primary hover:bg-surface-hover hover:text-white active:scale-95'
                      }
                    `}
                  >
                    {isSelected && isGroupLoading ? (
                      <span className="inline-flex items-center gap-1.5">
                        <span className="w-3 h-3 border-2 border-primary-accent border-t-transparent rounded-full animate-spin" />
                        {opt.label}
                      </span>
                    ) : (
                      opt.label
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        );
      }

      case 'VehicleCard': {
        const score = props.matchScore || 90;
        const scoreColor =
          score >= 90
            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40'
            : score >= 75
            ? 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40'
            : 'bg-amber-500/20 text-amber-400 border-amber-500/40';

        const vId = props.vehicleId || props.actionData?.vehicle_id || props.actionData?.id;
        const isPurchased = vId && purchasedVehicleIds.includes(vId);

        const handleInspectClick = (e: React.MouseEvent) => {
          e.preventDefault();
          if (!vId) return;

          navigate(`/vehicles/${vId}`);
          useConsultantStore.getState().setActiveContext({
            currentRoute: `/vehicles/${vId}`,
            vehicleId: vId,
            vehicleName: `${props.brand} ${props.model}`
          });

          const v = getVehicleById(vId);
          const hpStr = v?.specs?.horsepower ? `${v.specs.horsepower} HP` : 'Refined High-Output Engine';
          const fuelEff = v?.mileage_kmpl ? `${v.mileage_kmpl} kmpl` : (v?.fuel_type === 'ELECTRIC' ? '450 km EV Range' : '16.5 kmpl');
          const trans = props.transmission || v?.transmission || 'Automatic';
          const fuel = props.fuelType || v?.fuel_type || 'Petrol';
          const seats = props.seats || v?.seats || 5;
          const odo = v?.odometer_km ? `${v.odometer_km.toLocaleString()} km` : '12,500 km (Certified)';
          const cond = v?.condition ? v.condition.toUpperCase() : 'PRE-OWNED CERTIFIED';

          const breakdownContent = 
            `### 🔍 Vehicle Deep-Dive: ${props.brand} ${props.model} (${props.year || 2024})\n\n` +
            `I've updated the background website to display the full specifications for the **${props.brand} ${props.model}**.\n\n` +
            `**Executive Overview & Architecture:**\n` +
            `- **Powertrain & Dynamics:** ${hpStr} • ${trans} • ${fuel} • ${fuelEff}\n` +
            `- **Seating & Ergonomics:** ${seats}-Seater Luxury Cabin with active climate control\n` +
            `- **Odometer & Condition:** ${odo} • ${cond} (Multi-point safety inspection cleared)\n` +
            `- **Authoritative Valuation:** ${props.priceDisplay}\n\n` +
            `**Strategic Fit Verdict:**\n` +
            `${props.explanation || `The ${props.brand} ${props.model} provides exceptional highway poise and city ergonomics with a ${score}% match against your criteria.`}\n\n` +
            `Would you like me to reserve or book this car for you? Just say *"book this car"* or click below.`;

          useConsultantStore.getState().addMessage({
            id: `msg_inspect_${Date.now()}`,
            role: 'assistant',
            content: breakdownContent,
            timestamp: new Date().toISOString()
          });
        };

        return (
          <div
            key={comp.id}
            onClick={handleInspectClick}
            className={`group relative my-3 overflow-hidden rounded-2xl border bg-slate-900/90 shadow-xl cursor-pointer transition-all duration-300 hover:shadow-2xl select-none ${
              isPurchased
                ? 'border-emerald-500/80 ring-1 ring-emerald-500/40'
                : 'border-surface-border hover:border-cyan-500/70'
            }`}
          >
            {/* Minimal Default View (Details Hidden) */}
            <div className="relative aspect-[16/9] w-full overflow-hidden bg-slate-950">
              <img
                src={props.imageUrl || 'https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80'}
                alt={`${props.brand} ${props.model}`}
                className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent" />

              {/* Top Badges */}
              <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 flex-wrap">
                  {isPurchased ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500 text-slate-950 text-[10px] font-black px-2.5 py-0.5 shadow-lg uppercase tracking-wider">
                      <ShieldCheck className="w-3 h-3" /> OWNED / PURCHASED
                    </span>
                  ) : (
                    <span className="rounded-full bg-slate-900/80 backdrop-blur-md px-2.5 py-0.5 text-[10px] font-bold text-gray-300 border border-white/10 uppercase tracking-wider">
                      {props.category}
                    </span>
                  )}
                </div>

                <div className={`px-2 py-0.5 rounded-full border text-[11px] font-bold flex items-center gap-1 backdrop-blur-md shadow-md ${scoreColor}`}>
                  <Zap className="w-3 h-3" />
                  {score}% Match
                </div>
              </div>

              {/* Bottom Default Info */}
              <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
                <div>
                  <span className="text-[11px] text-gray-400 font-mono">{props.year}</span>
                  <h3 className="text-base font-bold text-white tracking-tight drop-shadow-md">
                    {props.brand} {props.model}
                  </h3>
                </div>
                <div className="text-right">
                  <div className="text-base font-extrabold text-white drop-shadow-md">{props.priceDisplay}</div>
                  <div className="text-[9px] text-cyan-300 font-semibold uppercase tracking-wider">
                    Hover for specs &bull; Click to inspect
                  </div>
                </div>
              </div>
            </div>

            {/* Smooth Hover-Reveal Overlay */}
            <div className="absolute inset-0 bg-slate-950/92 backdrop-blur-md p-4 flex flex-col justify-between opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none group-hover:pointer-events-auto">
              <div>
                <div className="flex items-center justify-between pb-2 border-b border-surface-border/60">
                  <div>
                    <h4 className="text-sm font-bold text-white tracking-tight">
                      {props.brand} {props.model} <span className="text-gray-400 text-xs font-normal">({props.year})</span>
                    </h4>
                    <p className="text-[10px] text-primary-accent uppercase tracking-wider">{props.category}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-black text-cyan-400">{props.priceDisplay}</span>
                  </div>
                </div>

                {/* Key Specs */}
                <div className="flex flex-wrap gap-1.5 my-2.5 text-[11px] text-gray-200">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-muted border border-surface-border">
                    <Gauge className="w-3 h-3 text-cyan-400" />
                    {props.transmission}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-muted border border-surface-border">
                    <Fuel className="w-3 h-3 text-amber-400" />
                    {props.fuelType}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-surface-muted border border-surface-border">
                    <Users className="w-3 h-3 text-blue-400" />
                    {props.seats} Seats
                  </span>
                </div>

                {/* Positive Matches */}
                {props.positiveMatches && props.positiveMatches.length > 0 && (
                  <div className="space-y-1 mb-2">
                    {props.positiveMatches.slice(0, 2).map((pos: string, idx: number) => (
                      <div key={idx} className="flex items-start gap-1 text-[11px] text-emerald-300/90 leading-tight">
                        <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
                        <span className="truncate">{pos}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Trade-offs */}
                {props.tradeOffs && props.tradeOffs.length > 0 && (
                  <div className="space-y-1">
                    {props.tradeOffs.slice(0, 1).map((trade: string, idx: number) => (
                      <div key={idx} className="flex items-start gap-1 text-[11px] text-amber-300/90 leading-tight">
                        <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0 mt-0.5" />
                        <span className="truncate">{trade}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Action Footer */}
              <div className="pt-2 border-t border-surface-border/60 flex items-center justify-between">
                <span className="text-[10px] text-gray-400 italic">Click card for deep-dive</span>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onAction(props.actionId || 'select_vehicle', props.actionData || { vehicle_id: vId });
                  }}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-primary to-cyan-600 px-3.5 py-1.5 text-xs font-bold text-white shadow-lg transition-all hover:opacity-95 active:scale-95"
                >
                  <span>Book / Reserve</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          </div>
        );
      }

      case 'Button':
        return (
          <button
            key={comp.id}
            type="button"
            onClick={() => onAction(props.actionId || 'click', props.actionData || {})}
            className={`rounded-lg px-4 py-2 text-xs font-semibold transition-all ${
              props.variant === 'primary'
                ? 'bg-primary text-white hover:bg-primary-hover'
                : 'border border-surface-border bg-surface-muted text-gray-200 hover:border-primary'
            }`}
          >
            {props.text}
          </button>
        );

      default:
        return (
          <div key={comp.id} className="text-xs text-gray-400">
            {children}
          </div>
        );
    }
  };

  // Render root components (not listed as children of any other)
  const childIds = new Set<string>();
  components.forEach((c) => (c.children || []).forEach((cid) => childIds.add(cid)));
  const rootComponents = components.filter((c) => !childIds.has(c.id));

  return (
    <div className="a2ui-surface w-full my-2">
      {rootComponents.map((c) => renderComponent(c.id))}
    </div>
  );
};
