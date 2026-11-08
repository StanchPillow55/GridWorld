import React from 'react';
import { Award, CheckCircle2, XCircle, TrendingUp, ShieldAlert, Clock } from 'lucide-react';
import { ExperimentRecord, StepObservation } from '../types/grid';

interface AgentComparisonProps {
  currentRecord: ExperimentRecord | null;
  benchmarkRecords: ExperimentRecord[];
  steps: StepObservation[];
}

export const AgentComparison: React.FC<AgentComparisonProps> = ({
  currentRecord,
  benchmarkRecords,
  steps,
}) => {
  const metrics = currentRecord?.metrics;

  // Compute SVG polyline for max_rho trajectory
  const points = steps
    .map((s, idx) => {
      const x = steps.length > 1 ? (idx / (steps.length - 1)) * 360 + 20 : 200;
      // map rho 0.0 -> y=120, rho 1.2 -> y=10
      const y = Math.max(10, Math.min(130, 130 - (s.max_rho / 1.2) * 110));
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Award className="w-5 h-5 text-blue-400" />
          <h2 className="text-base font-bold text-slate-100">Scientific Evaluation Metrics</h2>
        </div>
        {metrics && (
          <div className="flex items-center gap-1.5 text-xs">
            {metrics.survived ? (
              <span className="flex items-center gap-1 text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/30">
                <CheckCircle2 className="w-3.5 h-3.5" /> Grid Survived
              </span>
            ) : (
              <span className="flex items-center gap-1 text-red-400 font-semibold bg-red-500/10 px-2 py-0.5 rounded border border-red-500/30">
                <XCircle className="w-3.5 h-3.5" /> Blackout / Failure
              </span>
            )}
          </div>
        )}
      </div>

      {/* KPI Cards */}
      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold flex items-center gap-1">
              <Clock className="w-3 h-3 text-blue-400" />
              Survival Steps
            </div>
            <div className="text-xl font-bold font-mono text-slate-100 mt-1">
              {metrics.survival_steps}{' '}
              <span className="text-xs text-slate-500 font-normal">/ {metrics.max_steps}</span>
            </div>
          </div>

          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-amber-400" />
              Peak Thermal Loading
            </div>
            <div
              className={`text-xl font-bold font-mono mt-1 ${
                metrics.peak_line_utilization >= 1.0 ? 'text-red-400' : 'text-slate-100'
              }`}
            >
              {(metrics.peak_line_utilization * 100).toFixed(1)}%
            </div>
          </div>

          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold flex items-center gap-1">
              <ShieldAlert className="w-3 h-3 text-red-400" />
              Overload Violations
            </div>
            <div className="text-xl font-bold font-mono text-slate-100 mt-1">
              {metrics.overload_violations}
            </div>
          </div>

          <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
            <div className="text-[11px] text-slate-400 uppercase font-semibold flex items-center gap-1">
              <Award className="w-3 h-3 text-purple-400" />
              Control Actions
            </div>
            <div className="text-xl font-bold font-mono text-slate-100 mt-1">
              {metrics.actions_taken}{' '}
              <span className="text-xs text-slate-500 font-normal">({metrics.execution_time_ms.toFixed(0)} ms)</span>
            </div>
          </div>
        </div>
      )}

      {/* Trajectory Sparkline / Line Loading Plot */}
      {steps.length > 1 && (
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex flex-col gap-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-semibold text-slate-300">Peak Thermal Loading Trajectory (Max ρ)</span>
            <span className="text-[11px] text-red-400 font-mono">100% Emergency Limit (Red Line)</span>
          </div>
          <div className="relative w-full h-32">
            <svg viewBox="0 0 400 140" className="w-full h-full overflow-visible">
              {/* 100% Threshold line */}
              <line x1="20" y1="38" x2="380" y2="38" stroke="#ef4444" strokeDasharray="4,4" strokeWidth="1" />
              {/* 90% Congestion line */}
              <line x1="20" y1="48" x2="380" y2="48" stroke="#f59e0b" strokeDasharray="2,2" strokeWidth="0.8" opacity="0.6" />
              {/* Trajectory Polyline */}
              <polyline
                fill="none"
                stroke="#38bdf8"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={points}
              />
              {/* Axis labels */}
              <text x="20" y="34" fill="#ef4444" fontSize="9" fontFamily="monospace">1.0 (Limit)</text>
              <text x="20" y="136" fill="#64748b" fontSize="9" fontFamily="monospace">T=0</text>
              <text x="365" y="136" fill="#64748b" fontSize="9" fontFamily="monospace">T={steps.length - 1}</text>
            </svg>
          </div>
        </div>
      )}

      {/* Head-to-Head Comparison Table */}
      {benchmarkRecords.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
            Head-to-Head Benchmark Suite ({benchmarkRecords[0].scenario_id})
          </h3>
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Agent</th>
                  <th className="py-2.5 px-3">Survived</th>
                  <th className="py-2.5 px-3">Steps</th>
                  <th className="py-2.5 px-3">Peak ρ</th>
                  <th className="py-2.5 px-3">Mean ρ</th>
                  <th className="py-2.5 px-3">Overloads</th>
                  <th className="py-2.5 px-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850 bg-slate-900/60 font-mono">
                {benchmarkRecords.map((rec) => (
                  <tr key={rec.id} className="hover:bg-slate-800/50">
                    <td className="py-2 px-3 font-sans font-bold capitalize text-slate-100 flex items-center gap-1.5">
                      {rec.controller_type === 'noop' && <span className="w-2 h-2 rounded-full bg-slate-400" />}
                      {rec.controller_type === 'heuristic' && <span className="w-2 h-2 rounded-full bg-emerald-400" />}
                      {rec.controller_type === 'ai' && <span className="w-2 h-2 rounded-full bg-purple-400" />}
                      {rec.controller_type}
                    </td>
                    <td className="py-2 px-3">
                      {rec.metrics.survived ? (
                        <span className="text-emerald-400 font-bold">YES</span>
                      ) : (
                        <span className="text-red-400 font-bold">NO</span>
                      )}
                    </td>
                    <td className="py-2 px-3">{rec.metrics.survival_steps} / {rec.metrics.max_steps}</td>
                    <td className="py-2 px-3">{(rec.metrics.peak_line_utilization * 100).toFixed(1)}%</td>
                    <td className="py-2 px-3">{(rec.metrics.mean_line_utilization * 100).toFixed(1)}%</td>
                    <td className="py-2 px-3">{rec.metrics.overload_violations}</td>
                    <td className="py-2 px-3">{rec.metrics.actions_taken}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
