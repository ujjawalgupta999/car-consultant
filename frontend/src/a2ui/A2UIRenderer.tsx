import React, { useState } from 'react';
import { A2UIComponent } from '../types';
import { CheckCircle2, AlertTriangle, Zap, Fuel, Gauge, Users } from 'lucide-react';

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

        return (
          <div
            key={comp.id}
            className="group relative my-3 overflow-hidden rounded-xl border border-surface-border bg-surface/90 backdrop-blur-md p-4 transition-all hover:border-primary/60 hover:shadow-2xl"
          >
            {/* Header */}
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between pb-3 border-b border-surface-border/60">
              <div className="flex items-center gap-3">
                {props.imageUrl && (
                  <img
                    src={props.imageUrl}
                    alt={`${props.brand} ${props.model}`}
                    className="h-14 w-20 rounded-lg object-cover border border-surface-border shadow-md"
                  />
                )}
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-semibold text-primary-accent tracking-wide uppercase">
                      {props.category}
                    </span>
                    <span className="text-xs text-gray-500">•</span>
                    <span className="text-xs text-gray-400">{props.year}</span>
                  </div>
                  <h3 className="text-base font-bold text-white group-hover:text-primary-accent transition-colors">
                    {props.brand} {props.model}
                  </h3>
                </div>
              </div>

              <div className="flex items-center gap-3 self-end sm:self-center">
                <div
                  className={`px-2.5 py-1 rounded-full border text-xs font-bold tracking-wide flex items-center gap-1 ${scoreColor}`}
                >
                  <Zap className="w-3.5 h-3.5" />
                  {score}% Match
                </div>
                <div className="text-right">
                  <div className="text-lg font-extrabold text-white">{props.priceDisplay}</div>
                  <div className="text-[10px] text-gray-400 uppercase tracking-wider">
                    Authoritative Rate
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Specs */}
            <div className="flex flex-wrap gap-2 my-3 text-xs text-gray-300">
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-muted border border-surface-border">
                <Gauge className="w-3.5 h-3.5 text-cyan-400" />
                {props.transmission}
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-muted border border-surface-border">
                <Fuel className="w-3.5 h-3.5 text-amber-400" />
                {props.fuelType}
              </span>
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded bg-surface-muted border border-surface-border">
                <Users className="w-3.5 h-3.5 text-blue-400" />
                {props.seats} Seats
              </span>
            </div>

            {/* Positive Matches */}
            {props.positiveMatches && props.positiveMatches.length > 0 && (
              <div className="mb-2 space-y-1">
                {props.positiveMatches.slice(0, 3).map((pos: string, idx: number) => (
                  <div key={idx} className="flex items-start gap-1.5 text-xs text-emerald-300/90">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{pos}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Trade-offs */}
            {props.tradeOffs && props.tradeOffs.length > 0 && (
              <div className="mb-3 space-y-1">
                {props.tradeOffs.slice(0, 2).map((trade: string, idx: number) => (
                  <div key={idx} className="flex items-start gap-1.5 text-xs text-amber-300/80">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0 mt-0.5" />
                    <span>{trade}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Explanation */}
            {props.explanation && (
              <p className="text-xs text-gray-400 italic mb-4 border-l-2 border-primary/40 pl-2.5">
                {props.explanation}
              </p>
            )}

            {/* Action button */}
            <div className="flex justify-end pt-2 border-t border-surface-border/40">
              <button
                type="button"
                onClick={() => onAction(props.actionId || 'select_vehicle', props.actionData || {})}
                className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white shadow-lg transition-all hover:bg-primary-hover active:scale-95"
              >
                <span>Select &amp; Book Vehicle</span>
                <span>→</span>
              </button>
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
