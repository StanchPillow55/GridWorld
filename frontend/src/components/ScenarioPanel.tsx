import React from 'react';
import { Play, Layers, Zap, Cpu, Award, Sparkles, Sliders } from 'lucide-react';
import { ScenarioConfig, ControllerType } from '../types/grid';

interface ScenarioPanelProps {
  scenarios: ScenarioConfig[];
  selectedScenarioId: string;
  onSelectScenario: (id: string) => void;
  selectedController: ControllerType;
  onSelectController: (c: ControllerType) => void;
  maxSteps: number;
  onChangeMaxSteps: (steps: number) => void;
  maxRounds: number;
  onChangeMaxRounds: (rounds: number) => void;
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
  maxRounds,
  onChangeMaxRounds,
  isRunning,
  onRunExperiment,
  onRunBenchmark,
}) => {
  const currentScenario = scenarios.find((s) => s.id === selectedScenarioId);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col gap-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-amber-400" />
          <h2 className="text-base font-bold text-slate-100">Experiment Control</h2>
        </div>
        {currentScenario && (
          <span
            className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded border ${
              currentScenario.split === 'dev'
                ? 'bg-blue-500/10 text-blue-400 border-blue-500/30'
                : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
            }`}
          >
            {currentScenario.split === 'dev' ? 'Development Split' : 'Held-Out Split'}
          </span>
        )}
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
          <optgroup label="Development Scenarios">
            {scenarios
              .filter((s) => s.split === 'dev')
              .map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.name}
                </option>
              ))}
          </optgroup>
          <optgroup label="Held-Out Evaluation Scenarios">
            {scenarios
              .filter((s) => s.split === 'held_out')
              .map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.name}
                </option>
              ))}
          </optgroup>
        </select>
        {currentScenario && (
          <p className="text-xs text-slate-400 leading-relaxed bg-slate-950/60 p-2.5 rounded border border-slate-800">
            {currentScenario.description}
            <span className="block mt-1 font-mono text-[10px] text-slate-500">
              Chronic: #{currentScenario.chronic_id} · Seed: {currentScenario.seed} · Horizon: {currentScenario.max_steps} steps
            </span>
          </p>
        )}
      </div>

      {/* Controller Selector: 5 Distinct Types */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Controller Strategy
        </label>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
          {/* 1. Noop */}
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
              1. Do-Nothing
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Passive Baseline</div>
          </button>

          {/* 2. Simple Heuristic */}
          <button
            type="button"
            onClick={() => onSelectController('simple_heuristic')}
            disabled={isRunning}
            className={`p-2.5 rounded-lg border text-left transition-all ${
              selectedController === 'simple_heuristic'
                ? 'bg-blue-600/20 border-blue-500 text-blue-200'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-bold flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-amber-400" />
              2. Simple Heuristic
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Greedy (0 Forecast)</div>
          </button>

          {/* 3. Simulation Planner */}
          <button
            type="button"
            onClick={() => onSelectController('simulation_planner')}
            disabled={isRunning}
            className={`p-2.5 rounded-lg border text-left transition-all ${
              selectedController === 'simulation_planner'
                ? 'bg-blue-600/20 border-blue-500 text-blue-200'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-bold flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              3. Sim Planner
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Deterministic Look-Ahead</div>
          </button>

          {/* 4. Direct LLM */}
          <button
            type="button"
            onClick={() => onSelectController('direct_llm')}
            disabled={isRunning}
            className={`p-2.5 rounded-lg border text-left transition-all ${
              selectedController === 'direct_llm'
                ? 'bg-blue-600/20 border-blue-500 text-blue-200'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-bold flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-purple-400" />
              4. Direct LLM
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">Single-Shot Output</div>
          </button>

          {/* 5. Refinement LLM */}
          <button
            type="button"
            onClick={() => onSelectController('refinement_llm')}
            disabled={isRunning}
            className={`p-2.5 rounded-lg border text-left transition-all col-span-1 sm:col-span-2 ${
              selectedController === 'refinement_llm'
                ? 'bg-purple-600/25 border-purple-500 text-purple-200 ring-1 ring-purple-500/50'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
          >
            <div className="text-xs font-bold flex items-center gap-1.5 text-purple-300">
              <Sparkles className="w-3.5 h-3.5 text-purple-400" />
              5. Simulation-Guided Refinement LLM
            </div>
            <div className="text-[10px] text-slate-400 mt-0.5">
              Propose → Simulate → Evaluate → Revise Loop (Core Contribution)
            </div>
          </button>
        </div>
      </div>

      {/* Episode Horizon & Refinement Rounds */}
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="font-semibold text-slate-400 uppercase tracking-wider">Horizon</span>
            <span className="font-mono text-slate-200">{maxSteps} steps</span>
          </div>
          <input
            type="range"
            min="5"
            max="40"
            step="5"
            value={maxSteps}
            onChange={(e) => onChangeMaxSteps(Number(e.target.value))}
            disabled={isRunning}
            className="w-full accent-blue-500"
          />
        </div>

        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="font-semibold text-slate-400 uppercase tracking-wider">Max Refinements</span>
            <span className="font-mono text-slate-200">{maxRounds} rounds</span>
          </div>
          <input
            type="range"
            min="1"
            max="4"
            step="1"
            value={maxRounds}
            onChange={(e) => onChangeMaxRounds(Number(e.target.value))}
            disabled={isRunning}
            className="w-full accent-purple-500"
          />
        </div>
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
              <span>Running Experiment...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-white" />
              <span>Run Selected Controller</span>
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
          <span>Run 5-Way Head-to-Head Benchmark Suite</span>
        </button>
      </div>
    </div>
  );
};
