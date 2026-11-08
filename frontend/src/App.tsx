import React, { useEffect, useState, useCallback } from 'react';
import {
  GridTopology,
  ScenarioConfig,
  ControllerType,
  ExperimentRecord,
  ReplayData,
  StepObservation
} from './types/grid';
import { GridView } from './components/GridView';
import { ScenarioPanel } from './components/ScenarioPanel';
import { Timeline } from './components/Timeline';
import { AgentComparison } from './components/AgentComparison';
import { Zap, ShieldCheck, Activity, Terminal, RefreshCw, X } from 'lucide-react';

const App: React.FC = () => {
  const [topology, setTopology] = useState<GridTopology | null>(null);
  const [scenarios, setScenarios] = useState<ScenarioConfig[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('case14_corridor_congest');
  const [selectedController, setSelectedController] = useState<ControllerType>('heuristic');
  const [maxSteps, setMaxSteps] = useState<number>(30);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string>('Ready');

  const [currentRecord, setCurrentRecord] = useState<ExperimentRecord | null>(null);
  const [replayData, setReplayData] = useState<ReplayData | null>(null);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [benchmarkRecords, setBenchmarkRecords] = useState<ExperimentRecord[]>([]);

  const [selectedSubId, setSelectedSubId] = useState<number | null>(null);

  // Initial load: Fetch Grid Topology and Available Scenarios
  const fetchInitialData = useCallback(async () => {
    try {
      setStatusMessage('Loading grid topology...');
      const topoRes = await fetch('/api/environment');
      if (topoRes.ok) {
        const topoData = await topoRes.json();
        setTopology(topoData);
      }

      const scenRes = await fetch('/api/scenarios');
      if (scenRes.ok) {
        const scenData = await scenRes.json();
        setScenarios(scenData);
        if (scenData.length > 0 && !selectedScenarioId) {
          setSelectedScenarioId(scenData[0].id);
        }
      }
      setStatusMessage('Environment initialized.');
    } catch (err) {
      console.error('Failed to load initial data from backend:', err);
      setStatusMessage('Backend offline — please ensure FastAPI server is running on port 8000.');
    }
  }, [selectedScenarioId]);

  useEffect(() => {
    fetchInitialData();
  }, [fetchInitialData]);

  // Run a single experiment
  const handleRunExperiment = async () => {
    setIsRunning(true);
    setStatusMessage(`Running ${selectedController} controller on ${selectedScenarioId}...`);
    try {
      const res = await fetch('/api/experiments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: selectedScenarioId,
          controller_type: selectedController,
          max_steps: maxSteps,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed to execute experiment');
      }

      const record: ExperimentRecord = await res.json();
      setCurrentRecord(record);

      // Fetch replay data
      const repRes = await fetch(`/api/experiments/${record.id}/replay`);
      if (repRes.ok) {
        const replay: ReplayData = await repRes.json();
        setReplayData(replay);
        setCurrentStepIndex(0);
      }
      setStatusMessage(`Completed: survived ${record.metrics.survival_steps}/${record.metrics.max_steps} steps.`);
    } catch (err: any) {
      console.error(err);
      setStatusMessage(`Error: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  // Run full benchmark suite
  const handleRunBenchmark = async () => {
    setIsRunning(true);
    setStatusMessage(`Running Head-to-Head benchmark suite on ${selectedScenarioId}...`);
    try {
      const res = await fetch(`/api/benchmark?scenario_id=${selectedScenarioId}&max_steps=${maxSteps}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to run benchmark suite');

      const records: ExperimentRecord[] = await res.json();
      setBenchmarkRecords(records);

      // Default current view to the heuristic or AI result
      const topRecord = records.find((r) => r.controller_type === 'heuristic') || records[0];
      if (topRecord) {
        setCurrentRecord(topRecord);
        const repRes = await fetch(`/api/experiments/${topRecord.id}/replay`);
        if (repRes.ok) {
          const replay = await repRes.json();
          setReplayData(replay);
          setCurrentStepIndex(0);
        }
      }
      setStatusMessage(`Benchmark complete: evaluated ${records.length} controllers.`);
    } catch (err: any) {
      console.error(err);
      setStatusMessage(`Benchmark Error: ${err.message}`);
    } finally {
      setIsRunning(false);
    }
  };

  const currentSteps: StepObservation[] = replayData?.steps || [];
  const currentStep: StepObservation | null = currentSteps[currentStepIndex] || null;

  const selectedSubstation = topology?.substations.find((s) => s.id === selectedSubId);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md px-6 py-3.5 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-amber-500 to-yellow-300 flex items-center justify-center shadow-lg shadow-amber-500/20">
            <Zap className="w-5 h-5 text-slate-950 fill-slate-950" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
              GridWorld
              <span className="text-[10px] uppercase font-mono font-bold tracking-wider px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/30">
                v0.1 · IEEE-14
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">Autonomous Power Grid Resilience & Control Experimentation</p>
          </div>
        </div>

        {/* Center Status Pill */}
        <div className="hidden md:flex items-center gap-2 text-xs bg-slate-950 px-3.5 py-1.5 rounded-full border border-slate-800">
          <Activity className="w-3.5 h-3.5 text-blue-400 animate-pulse" />
          <span className="text-slate-400">Status:</span>
          <span className="font-mono text-slate-200">{statusMessage}</span>
        </div>

        {/* Right Tools */}
        <div className="flex items-center gap-3">
          <button
            onClick={fetchInitialData}
            title="Reload Environment"
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <div className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1.5 rounded-lg font-medium">
            <ShieldCheck className="w-4 h-4" />
            <span>Grid2Op + PandaPower Engine</span>
          </div>
        </div>
      </header>

      {/* Main Workspace Layout */}
      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-[1720px] w-full mx-auto">
        {/* Left Column: Visualizer & Timeline Scrubber (7 cols) */}
        <div className="lg:col-span-7 flex flex-col gap-4 min-h-[580px]">
          <div className="flex-1 min-h-[460px] relative">
            <GridView
              topology={topology}
              currentStep={currentStep}
              selectedSubId={selectedSubId}
              onSelectSubstation={setSelectedSubId}
            />

            {/* Substation Inspector Drawer */}
            {selectedSubstation && (
              <div className="absolute top-4 right-4 bg-slate-900/95 backdrop-blur-md border border-slate-700 p-4 rounded-xl shadow-2xl text-xs w-72 space-y-2 z-20">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="font-bold text-slate-100 flex items-center gap-1.5">
                    <Terminal className="w-3.5 h-3.5 text-blue-400" />
                    Substation #{selectedSubstation.id}: {selectedSubstation.name}
                  </div>
                  <button
                    onClick={() => setSelectedSubId(null)}
                    className="text-slate-400 hover:text-white p-0.5 rounded"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
                <div className="space-y-1 text-slate-300">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Connected Lines:</span>
                    <span className="font-mono">{selectedSubstation.connected_lines.join(', ') || 'None'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Generators:</span>
                    <span className="font-mono text-emerald-400">
                      {selectedSubstation.generators.length > 0
                        ? selectedSubstation.generators.map((g) => `#${g}`).join(', ')
                        : 'None'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Loads:</span>
                    <span className="font-mono text-amber-400">
                      {selectedSubstation.loads.length > 0
                        ? selectedSubstation.loads.map((l) => `#${l}`).join(', ')
                        : 'None'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Replay Timeline Scrubber */}
          <Timeline
            steps={currentSteps}
            currentStepIndex={currentStepIndex}
            onSelectStep={setCurrentStepIndex}
            controllerName={currentRecord?.controller_type || selectedController}
          />
        </div>

        {/* Right Column: Experiment Controls & Scientific Comparison (5 cols) */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          <ScenarioPanel
            scenarios={scenarios}
            selectedScenarioId={selectedScenarioId}
            onSelectScenario={setSelectedScenarioId}
            selectedController={selectedController}
            onSelectController={setSelectedController}
            maxSteps={maxSteps}
            onChangeMaxSteps={setMaxSteps}
            isRunning={isRunning}
            onRunExperiment={handleRunExperiment}
            onRunBenchmark={handleRunBenchmark}
          />

          <AgentComparison
            currentRecord={currentRecord}
            benchmarkRecords={benchmarkRecords}
            steps={currentSteps}
          />
        </div>
      </main>
    </div>
  );
};

export default App;
