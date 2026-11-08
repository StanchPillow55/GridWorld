import React, { useEffect, useState } from 'react';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  RotateCcw,
  Activity,
  AlertTriangle,
  Info
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

          <div>
            <span className="text-slate-400">Mean ρ: </span>
            <span className="text-slate-200">{(currentStep.mean_rho * 100).toFixed(1)}%</span>
          </div>

          <div>
            <span className="text-slate-400">Load: </span>
            <span className="text-slate-200">{currentStep.total_load_mw.toFixed(1)} MW</span>
          </div>

          <div>
            <span className="text-slate-400">Gen: </span>
            <span className="text-slate-200">{currentStep.total_gen_mw.toFixed(1)} MW</span>
          </div>
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
              Agent Action ({controllerName}):{' '}
              <span className="text-blue-400 font-mono uppercase">
                {currentStep.action_taken.action_type}
                {currentStep.action_taken.target_id !== null && currentStep.action_taken.target_id !== undefined
                  ? ` [Line ${currentStep.action_taken.target_id}]`
                  : ''}
              </span>
            </span>
            {currentStep.done && (
              <span className="bg-red-500/20 text-red-400 px-2 py-0.5 rounded text-[10px] font-bold border border-red-500/30">
                TERMINATED: {currentStep.done_reason || 'Outage / Blackout'}
              </span>
            )}
          </div>
          <p className="text-slate-400 text-xs italic">
            "{currentStep.action_taken.rationale || 'No intervention recorded'}"
          </p>
        </div>
      </div>
    </div>
  );
};
