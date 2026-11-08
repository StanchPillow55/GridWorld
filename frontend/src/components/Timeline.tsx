import React, { useEffect, useState } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  Activity,
  AlertTriangle,
  Info,
  GitBranch,
  Target,
  CheckCircle2
} from 'lucide-react';
import { StepObservation } from '../types/grid';

interface TimelineProps {
  steps: StepObservation[];
  currentStepIndex: number;
  onSelectStep: (index: number) => void;
  controllerName: string;
}

export const Timeline: React.FC<TimelineProps> = ({
  steps,
  currentStepIndex,
  onSelectStep,
  controllerName,
}) => {
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    let timer: any = null;
    if (isPlaying) {
      timer = setInterval(() => {
        if (currentStepIndex >= steps.length - 1) {
          setIsPlaying(false);
        } else {
          onSelectStep(currentStepIndex + 1);
        }
      }, 700);
    }
    return () => clearInterval(timer);
  }, [isPlaying, currentStepIndex, steps.length, onSelectStep]);

  if (!steps.length) return null;

  const currentStep = steps[currentStepIndex] || steps[0];
  const maxRho = currentStep.max_rho;
  const isOverloaded = maxRho >= 1.0;
  const isCongested = maxRho >= 0.90;
  const forecast = currentStep.forecast_verification;
  const proposals = currentStep.proposals_history || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col gap-4">
      {/* Top Header & Controls */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => onSelectStep(0)}
              title="Reset to Start"
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
            <button
              onClick={() => onSelectStep(Math.max(0, currentStepIndex - 1))}
              disabled={currentStepIndex === 0}
              title="Previous Step"
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30"
            >
              <SkipBack className="w-4 h-4" />
            </button>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              title={isPlaying ? 'Pause' : 'Play Replay'}
              className="p-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white"
            >
              {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 fill-white" />}
            </button>
            <button
              onClick={() => onSelectStep(Math.min(steps.length - 1, currentStepIndex + 1))}
              disabled={currentStepIndex >= steps.length - 1}
              title="Next Step"
              className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white disabled:opacity-30"
            >
              <SkipForward className="w-4 h-4" />
            </button>
          </div>

          <div className="text-sm font-bold text-slate-200">
            Step <span className="font-mono text-blue-400 text-base">{currentStepIndex}</span> /{' '}
            <span className="font-mono text-slate-500">{steps.length - 1}</span>
          </div>
        </div>

        {/* Telemetry Stats */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Peak ρ:</span>
            <span
              className={`font-bold px-2 py-0.5 rounded ${
                isOverloaded
                  ? 'bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse'
                  : isCongested
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                  : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
              }`}
            >
              {(maxRho * 100).toFixed(1)}%
            </span>
          </div>

          {/* Forecast vs Actual Verification Pill */}
          {forecast && (
            <div className="hidden sm:flex items-center gap-1.5 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-[11px]">
              <Target className="w-3 h-3 text-purple-400" />
              <span className="text-slate-400">Forecast:</span>
              <span className="text-purple-300">{(forecast.forecasted_max_rho * 100).toFixed(1)}%</span>
              <span className="text-slate-500">|</span>
              <span className="text-slate-400">Err:</span>
              <span className={forecast.forecast_error > 0.05 ? 'text-amber-400' : 'text-emerald-400'}>
                {(forecast.forecast_error * 100).toFixed(1)}%
              </span>
            </div>
          )}

          <div>
            <span className="text-slate-400">Mean ρ: </span>
            <span className="text-slate-200">{(currentStep.mean_rho * 100).toFixed(1)}%</span>
          </div>

          {currentStep.fallback_used && (
            <span className="bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded text-[10px] font-bold border border-amber-500/30">
              FALLBACK USED
            </span>
          )}
        </div>
      </div>

      {/* Scrub Slider */}
      <div className="relative w-full">
        <input
          type="range"
          min="0"
          max={steps.length - 1}
          value={currentStepIndex}
          onChange={(e) => onSelectStep(Number(e.target.value))}
          className="w-full h-2 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-blue-500"
        />
        <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
          <span>T=0 (Initial State)</span>
          <span>T={steps.length - 1}</span>
        </div>
      </div>

      {/* Action & Reasoning Callout */}
      <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3 text-xs flex items-start gap-3">
        {currentStep.action_taken.action_type === 'noop' ? (
          <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
        ) : (
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        )}
        <div className="flex-1 space-y-1">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-slate-300">
              Executed Action ({controllerName}):{' '}
              <span className="text-blue-400 font-mono uppercase">
                {currentStep.action_taken.action_id || ''} {currentStep.action_taken.action_type}
                {currentStep.action_taken.target_id !== null && currentStep.action_taken.target_id !== undefined
                  ? ` [Line ${currentStep.action_taken.target_id}]`
                  : ''}
              </span>
            </span>
            {currentStep.done && (
              <span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded text-[10px] font-bold border border-red-500/30">
                TERMINATED: {currentStep.done_reason || 'Grid divergence / blackout'}
              </span>
            )}
          </div>
          <p className="text-slate-400 text-xs italic">
            "{currentStep.action_taken.rationale || 'No intervention recorded'}"
          </p>
        </div>
      </div>

      {/* Inspectable Proposal & Refinement History (Phase 3 Loop) */}
      {proposals.length > 0 && (
        <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 flex flex-col gap-2">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-purple-300">
            <GitBranch className="w-3.5 h-3.5" />
            <span>Online Refinement Trace ({proposals.length} proposal rounds evaluated before execution)</span>
          </div>
          <div className="space-y-1.5">
            {proposals.map((pr) => (
              <div
                key={pr.round_index}
                className={`p-2 rounded border text-xs flex items-start justify-between gap-3 ${
                  pr.selected
                    ? 'bg-purple-950/40 border-purple-500/50 text-purple-200'
                    : 'bg-slate-900/60 border-slate-800/80 text-slate-400'
                }`}
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-[11px] bg-slate-800 px-1.5 py-0.2 rounded text-slate-300">
                      Round {pr.round_index}
                    </span>
                    <span className="font-bold text-slate-200">{pr.action_id}</span>
                    <span className="text-[11px] text-slate-400">{pr.rationale}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 italic">
                    {pr.feedback}
                  </div>
                </div>

                <div className="text-right shrink-0 flex flex-col items-end gap-1">
                  <span className="font-mono text-[11px]">
                    Simulated ρ:{' '}
                    <span className={pr.simulated_max_rho >= 1.0 ? 'text-red-400 font-bold' : 'text-emerald-400 font-bold'}>
                      {(pr.simulated_max_rho * 100).toFixed(1)}%
                    </span>
                  </span>
                  {pr.selected && (
                    <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/30">
                      <CheckCircle2 className="w-3 h-3" /> Selected
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
