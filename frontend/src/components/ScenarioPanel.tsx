import React from 'react';
import { Play, Layers, Zap, Cpu, Award } from 'lucide-react';
import { ScenarioConfig, ControllerType } from '../types/grid';

interface ScenarioPanelProps {
  scenarios: ScenarioConfig[];
  selectedScenarioId: string;
  onSelectScenario: (id: string) => void;
  selectedController: ControllerType;
  onSelectController: (c: ControllerType) => void;
  maxSteps: number;
  onChangeMaxSteps: (steps: number) => void;
  isRunning: boolean;
  onRunExperiment: () => void;
  onRunBenchmark: () => void;
}

export const ScenarioPanel: React.FC<ScenarioPanelProps> = ({
  scenarios,
  selectedScenarioId,
  onSelectScenario,
  selectedController,
  onSelectController,
  maxSteps,
  onChangeMaxSteps,
  isRunning,
  onRunExperiment,
  onRunBenchmark,
}) => {
  const currentScenario = scenarios.find((s) => s.id === selectedScenarioId);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-5">
      <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
        <Zap className="w-5 h-5 text-amber-400" />
        <h2 className="text-base font-bold text-slate-100">Experiment Control</h2>
      </div>

      {/* Scenario Selector */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Select Scenario
        </label>
        <select
          value={selectedScenarioId}
          onChange={(e) => onSelectScenario(e.target.value)}
          disabled={isRunning}
          className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-500 disabled:opacity-50"
        >
          {scenarios.map((sc) => (
            <option key={sc.id} value={sc.id}>
              {sc.name}
            </option>
          ))}
        </select>
        {currentScenario && (
          <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-2.5 rounded border border-slate-800">
            {currentScenario.description}
            {currentScenario.disturbances.length > 0 && (
              <span className="block mt-1 text-amber-400/90 font-mono text-[11px]">
                Disturbance: Line {currentScenario.disturbances.map((d) => d.line_id).join(', ')} disconnects at step {currentScenario.disturbances.map((d) => d.step).join(', ')}.
              </span>
            )}
          </p>
        )}
      </div>

      {/* Controller Selector */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Control Strategy
        </label>
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => onSelectController('noop')}
            disabled={isRunning}
            className={`p-2.5 rounded-lg border text-left transition-all ${
              selectedController === 'noop'
                ? 'bg-blue-600/20 border-blue-500 text-blue-200'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-bold flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Do-Nothing
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Passive Baseline</div>
          </button>

          <button
            type="button"
            onClick={() => onSelectController('heuristic')}
            disabled={isRunning}
            className={`p-2.5 rounded-lg border text-left transition-all ${
              selectedController === 'heuristic'
                ? 'bg-blue-600/20 border-blue-500 text-blue-200'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-bold flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              Heuristic
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Simulation Search</div>
          </button>

          <button
            type="button"
            onClick={() => onSelectController('ai')}
            disabled={isRunning}
            className={`p-2.5 rounded-lg border text-left transition-all ${
              selectedController === 'ai'
                ? 'bg-blue-600/20 border-blue-500 text-blue-200'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-bold flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-purple-400" />
              AI Agent
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Autonomous Policy</div>
          </button>
        </div>
      </div>

      {/* Episode Length */}
      <div className="space-y-1.5">
        <div className="flex justify-between text-xs">
          <span className="font-semibold text-slate-400 uppercase tracking-wider">Episode Horizon</span>
          <span className="font-mono text-slate-200">{maxSteps} steps</span>
        </div>
        <input
          type="range"
          min="10"
          max="50"
          step="5"
          value={maxSteps}
          onChange={(e) => onChangeMaxSteps(Number(e.target.value))}
          disabled={isRunning}
          className="w-full accent-blue-500"
        />
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col gap-2 pt-2">
        <button
          type="button"
          onClick={onRunExperiment}
          disabled={isRunning}
          className="w-full bg-blue-600 hover:bg-blue-500 active:bg-blue-700 disabled:opacity-50 text-white font-semibold py-2.5 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors shadow-lg shadow-blue-600/30 text-sm"
        >
          {isRunning ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Simulating...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Run Experiment</span>
            </>
          )}
        </button>

        <button
          type="button"
          onClick={onRunBenchmark}
          disabled={isRunning}
          className="w-full bg-slate-800 hover:bg-slate-700 active:bg-slate-850 disabled:opacity-50 text-slate-200 font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors text-xs border border-slate-700"
        >
          <Award className="w-3.5 h-3.5 text-amber-400" />
          <span>Run Head-to-Head Benchmark Suite</span>
        </button>
      </div>
    </div>
  );
};
