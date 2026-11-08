import React, { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  MarkerType,
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { GridTopology, StepObservation } from '../types/grid';

interface GridViewProps {
  topology: GridTopology | null;
  currentStep: StepObservation | null;
  selectedSubId: number | null;
  onSelectSubstation: (subId: number | null) => void;
}

export const GridView: React.FC<GridViewProps> = ({
  topology,
  currentStep,
  selectedSubId,
  onSelectSubstation,
}) => {
  const nodes: Node[] = useMemo(() => {
    if (!topology) return [];

    return topology.substations.map((sub) => {
      const isSelected = selectedSubId === sub.id;
      const genCount = sub.generators.length;
      const loadCount = sub.loads.length;

      return {
        id: `sub-${sub.id}`,
        position: { x: sub.pos_x * 1.6, y: sub.pos_y * 1.5 },
        data: {
          label: (
            <div
              onClick={() => onSelectSubstation(sub.id)}
              className={`p-2 rounded-lg border text-xs cursor-pointer transition-all duration-200 select-none ${
                isSelected
                  ? 'bg-blue-600 border-blue-300 text-white shadow-lg shadow-blue-500/50 scale-105'
                  : 'bg-slate-900 border-slate-700 hover:border-slate-500 text-slate-200'
              }`}
            >
              <div className="font-bold flex items-center justify-between gap-2">
                <span>{sub.name}</span>
                <span className="text-[10px] text-slate-400">#{sub.id}</span>
              </div>
              <div className="flex gap-2 mt-1 text-[10px] text-slate-400">
                {genCount > 0 && <span className="text-emerald-400 font-medium">{genCount} Gen</span>}
                {loadCount > 0 && <span className="text-amber-400 font-medium">{loadCount} Load</span>}
              </div>
            </div>
          ),
        },
        type: 'default',
        style: {
          background: 'transparent',
          border: 'none',
          padding: 0,
          width: 110,
        },
      };
    });
  }, [topology, selectedSubId, onSelectSubstation]);

  const edges: Edge[] = useMemo(() => {
    if (!topology) return [];

    return topology.lines.map((line) => {
      const rho = currentStep?.line_rhos?.[line.id] ?? line.rho;
      const isConnected = currentStep?.line_status?.[line.id] ?? line.status;

      let stroke = '#10b981'; // Green: Safe (< 70%)
      let strokeWidth = 2;
      let animated = false;

      if (!isConnected) {
        stroke = '#475569'; // Disconnected / Tripped: Slate
        strokeWidth = 1.5;
      } else if (rho >= 1.0) {
        stroke = '#ef4444'; // Red: Critical Overload (>= 100%)
        strokeWidth = 4;
        animated = true;
      } else if (rho >= 0.90) {
        stroke = '#f97316'; // Orange: High Congestion (>= 90%)
        strokeWidth = 3;
        animated = true;
      } else if (rho >= 0.70) {
        stroke = '#eab308'; // Yellow: Moderate Loading (>= 70%)
        strokeWidth = 2.5;
      }

      return {
        id: `line-${line.id}`,
        source: `sub-${line.from_sub}`,
        target: `sub-${line.to_sub}`,
        animated: isConnected && animated,
        style: {
          stroke,
          strokeWidth,
          strokeDasharray: isConnected ? undefined : '5,5',
        },
        label: isConnected ? `${(rho * 100).toFixed(0)}%` : 'OFFLINE',
        labelStyle: {
          fill: isConnected ? (rho >= 0.9 ? '#ef4444' : '#94a3b8') : '#64748b',
          fontWeight: 600,
          fontSize: 10,
        },
        labelBgStyle: {
          fill: '#0f172a',
          fillOpacity: 0.85,
        },
        labelBgPadding: [4, 2] as [number, number],
        labelBgBorderRadius: 4,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: stroke,
          width: 10,
          height: 10,
        },
      };
    });
  }, [topology, currentStep]);

  return (
    <div className="w-full h-full relative bg-slate-950 rounded-xl border border-slate-800 overflow-hidden shadow-2xl">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        minZoom={0.4}
        maxZoom={2.0}
        attributionPosition="bottom-right"
      >
        <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#334155" />
        <Controls className="!bg-slate-900 !border-slate-800 !fill-slate-300" />
      </ReactFlow>

      {/* Modeling & Busbar Note Banner */}
      <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur-md border border-slate-800 px-3 py-1.5 rounded-lg text-[10px] text-slate-400 max-w-sm pointer-events-none shadow-md">
        <span className="font-semibold text-slate-300">Modeling Scope:</span> Substation-level topology view. Dual-busbar splitting actions are resolved by the underlying Grid2Op solver.
      </div>

      {/* Legend Overlay */}
      <div className="absolute bottom-4 left-4 bg-slate-900/90 backdrop-blur-md border border-slate-800 p-3 rounded-lg text-xs space-y-1.5 shadow-lg pointer-events-none">
        <div className="font-semibold text-slate-300 text-[11px] mb-1">Thermal Loading (ρ)</div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-1 bg-emerald-500 rounded"></span>
          <span className="text-slate-400">&lt; 70% (Nominal)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-1 bg-yellow-500 rounded"></span>
          <span className="text-slate-400">70% – 90% (Moderate)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-1 bg-orange-500 rounded"></span>
          <span className="text-slate-400">90% – 100% (Congestion)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-1 bg-red-500 rounded"></span>
          <span className="text-slate-400">&ge; 100% (Critical Overload)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-1 border-t border-dashed border-slate-500"></span>
          <span className="text-slate-400">Tripped / Offline</span>
        </div>
      </div>
    </div>
  );
};
