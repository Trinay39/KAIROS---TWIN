import { useEffect, useRef, useState } from 'react';
import { ArrowRight, FlaskConical, Play, RotateCcw, TrendingDown, TrendingUp } from 'lucide-react';
import { messageForError } from '../api/client';
import { endpoints } from '../api/endpoints';
import { useDemo } from '../context/DemoContext';
import type { CounterfactualResult, RankedScenario, SimulationResponse } from '../types';
import {
  explorerScenarios,
  PARSE_HELP,
  parseNaturalLanguageScenario,
  scenarioFromPreset,
  type InterpretedScenario,
  type ScenarioIntent,
} from '../utils/scenarioIntent';

const INTENTS = [
  { value: 'sleep_more', label: 'Sleep more' },
  { value: 'sleep_less', label: 'Sleep less' },
  { value: 'study_more', label: 'Study more' },
  { value: 'study_less', label: 'Study less' },
  { value: 'reduce_workload', label: 'Reduce workload' },
  { value: 'increase_workload', label: 'Increase workload' },
  { value: 'reduce_stress', label: 'Reduce stress' },
  { value: 'improve_recovery', label: 'Improve recovery' },
  { value: 'improve_study_consistency', label: 'Improve study consistency' },
  { value: 'reduce_deadline_pressure', label: 'Reduce deadline pressure' },
] as const satisfies ReadonlyArray<{ value: ScenarioIntent; label: string }>;

type IntentValue = typeof INTENTS[number]['value'];

function pct(value: number | null | undefined) {
  return value == null ? 'Unavailable' : `${Math.round(value * 100)}%`;
}

function pp(delta: number) {
  const value = delta * 100;
  if (Math.abs(value) < 0.1) return '0.0 pp';
  return `${value > 0 ? '+' : ''}${value.toFixed(1)} pp`;
}

function modelInterpretation(delta: number) {
  if (Math.abs(delta) < 0.001) return 'No material change under the current model.';
  if (delta < 0) return 'Lower estimated risk under this simulated routine.';
  return 'Higher estimated risk under this simulated routine.';
}

function scenarioDetail(row: CounterfactualResult, plan?: InterpretedScenario) {
  const first = plan?.scenarios[0];
  const parameters = first?.parameters ?? {};
  if (first?.scenario_type === 'INCREASE_SLEEP') {
    return {
      current: 'Current sleep baseline',
      simulated: `${Number(parameters.hours_per_night ?? 0).toFixed(1)} h/night`,
      change: plan?.changes.join(' + ') ?? row.scenario_description,
    };
  }
  if (first?.scenario_type === 'INCREASE_STUDY_TIME') {
    const hours = Number(parameters.hours_per_day ?? 0);
    return {
      current: 'Current study baseline',
      simulated: `${hours > 0 ? '+' : ''}${hours.toFixed(1)} h/day for ${parameters.days ?? 7} days`,
      change: plan?.changes.join(' + ') ?? row.scenario_description,
    };
  }
  if (first?.scenario_type === 'REDUCE_WORKLOAD') {
    const reduction = Number(parameters.reduction_pct ?? 0);
    return {
      current: 'Current workload pressure',
      simulated: `${reduction > 0 ? '-' : '+'}${Math.abs(reduction).toFixed(0)}% workload pressure`,
      change: plan?.changes.join(' + ') ?? row.scenario_description,
    };
  }
  return {
    current: 'Current deadline density',
    simulated: 'Spread deadlines to reduce density peaks',
    change: plan?.changes.join(' + ') ?? row.scenario_description,
  };
}

export default function WhatIfLab() {
  const { state } = useDemo();
  const { input, twin } = state;
  const [selectedIntent, setSelectedIntent] = useState<IntentValue>('sleep_more');
  const [naturalText, setNaturalText] = useState('');
  const [interpreted, setInterpreted] = useState<InterpretedScenario | null>(null);
  const [resultState, setResultState] = useState<{ key: string; response: SimulationResponse } | null>(null);
  const [explorerState, setExplorerState] = useState<{ key: string; plans: InterpretedScenario[]; response: SimulationResponse } | null>(null);
  const [explorerStatus, setExplorerStatus] = useState<'pending' | 'loading' | 'done' | 'error'>('pending');
  const [runningKey, setRunningKey] = useState<string | null>(null);
  const [errorState, setErrorState] = useState<{ key: string; message: string } | null>(null);
  const [explorerError, setExplorerError] = useState<{ key: string; message: string } | null>(null);
  const selectionKey = `${input.student_id}:${input.day}:${twin?.computed_at ?? 'no-twin'}`;
  const latestSelectionKey = useRef(selectionKey);
  const twinRef = useRef(twin);
  const requestSeq = useRef(0);
  const explorerSeq = useRef(0);

  useEffect(() => {
    twinRef.current = twin;
  }, [twin]);

  useEffect(() => {
    latestSelectionKey.current = selectionKey;
  }, [selectionKey]);

  useEffect(() => {
    const currentTwin = twinRef.current;
    if (!currentTwin) {
      setExplorerState(null);
      setExplorerStatus('pending');
      setExplorerError(null);
      return;
    }

    explorerSeq.current += 1;
    const requestId = explorerSeq.current;
    const requestKey = selectionKey;
    const plans = explorerScenarios(currentTwin, input.day);

    setExplorerStatus('loading');
    setExplorerError(null);
    endpoints.simulate({ twin_state: currentTwin, day: input.day, scenarios: plans.flatMap((plan) => plan.scenarios) })
      .then((response) => {
        if (latestSelectionKey.current !== requestKey || explorerSeq.current !== requestId) return;
        setExplorerState({ key: requestKey, plans, response });
        setExplorerStatus('done');
      })
      .catch((e: unknown) => {
        if (latestSelectionKey.current !== requestKey || explorerSeq.current !== requestId) return;
        setExplorerState(null);
        setExplorerError({ key: requestKey, message: messageForError(e, 'Unable to generate scenario explorer. Please try again.') });
        setExplorerStatus('error');
      });
  }, [input.day, selectionKey]);

  const results = resultState?.key === selectionKey ? resultState.response : null;
  const explorer = explorerState?.key === selectionKey ? explorerState : null;
  const error = errorState?.key === selectionKey ? errorState.message : null;
  const explorerFailure = explorerError?.key === selectionKey ? explorerError.message : null;
  const running = runningKey === selectionKey;
  const resultRows = results?.results ?? [];

  async function runInterpreted(next: InterpretedScenario) {
    if (!twin) {
      setErrorState({ key: selectionKey, message: 'Compute twin first on the Digital Twin page before running simulation.' });
      return;
    }
    requestSeq.current += 1;
    const requestId = requestSeq.current;
    const requestKey = selectionKey;
    setInterpreted(next);
    setRunningKey(requestKey);
    setErrorState(null);
    setResultState(null);
    try {
      const res = await endpoints.simulate({ twin_state: twin, day: input.day, scenarios: next.scenarios });
      if (latestSelectionKey.current !== requestKey || requestSeq.current !== requestId) return;
      setResultState({ key: requestKey, response: res });
    } catch (e: unknown) {
      if (latestSelectionKey.current !== requestKey || requestSeq.current !== requestId) return;
      setErrorState({ key: requestKey, message: messageForError(e, 'Unable to generate scenario. Please try again.') });
    } finally {
      if (latestSelectionKey.current === requestKey && requestSeq.current === requestId) {
        setRunningKey(null);
      }
    }
  }

  function handlePresetRun() {
    if (!twin) {
      setErrorState({ key: selectionKey, message: 'Compute twin first on the Digital Twin page before running simulation.' });
      return;
    }
    void runInterpreted(scenarioFromPreset(selectedIntent, twin, input.day));
  }

  function handleNaturalRun() {
    if (!twin) {
      setErrorState({ key: selectionKey, message: 'Compute twin first on the Digital Twin page before running simulation.' });
      return;
    }
    const parsed = parseNaturalLanguageScenario(naturalText, twin, input.day);
    if (!parsed) {
      setInterpreted(null);
      setResultState(null);
      setErrorState({ key: selectionKey, message: PARSE_HELP });
      return;
    }
    void runInterpreted(parsed);
  }

  function handleReset() {
    setNaturalText('');
    setInterpreted(null);
    setResultState(null);
    setErrorState(null);
  }

  function riskLabel(row: CounterfactualResult) {
    const delta = row.counterfactual_probability - row.baseline_probability;
    if (Math.abs(delta) < 0.001) return 'No material change under the current model.';
    const direction = delta < 0 ? 'lower' : 'higher';
    return `Estimated relative change: ${Math.abs(delta * 100).toFixed(1)} percentage points ${direction}.`;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-5 animate-fade-up">
      <header className="rounded-2xl p-8 bg-gradient-to-br from-[#181921] to-[#121317] border border-white/10">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] uppercase tracking-widest text-[#7c6cf5] font-medium">KAIROS-TWIN</span>
          <span className="text-white/20">/</span>
          <span className="text-[10px] uppercase tracking-widest text-white/30">Scenario Explorer</span>
        </div>
        <h1 className="text-3xl font-display font-bold tracking-tight text-white">What-If Scenario Lab</h1>
        <p className="text-sm text-white/40 mt-2">Estimated 7-day overload risk under model-based scenario projections from /simulations/run.</p>
      </header>

      <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5">
        <h3 className="text-[10px] font-bold text-[#00bfa5] mb-2">INPUT USED FOR SIMULATION</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] text-white/60">
          <span>Student: <b className="text-white">{input.student_id}</b></span>
          <span>Day: <b className="text-white">{input.day}</b></span>
          <span>Study: <b className="text-white">{input.study_hours} hrs/day</b></span>
          <span>Sleep: <b className="text-white">{input.sleep_hours} hrs/night</b></span>
          <span>Stress: <b className="text-white">{input.stress_level}/10</b></span>
          <span>Grade: <b className="text-white">{input.grade}/100</b></span>
          <span>Attend: <b className="text-white">{Math.round(input.attendance_rate * 100)}%</b></span>
          <span>Twin: <b className="text-white">{twin ? 'Computed baseline' : 'Not computed'}</b></span>
        </div>
      </div>

      <section className="rounded-2xl p-6 bg-[#181921] border border-white/10">
        <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3 mb-5">
          <div>
            <h2 className="text-[11px] uppercase tracking-widest text-white/60">Scenario Explorer</h2>
            <p className="text-xs text-white/35 mt-1">Ranked by estimated model risk change. This is not a causal or lifestyle ranking.</p>
          </div>
          <div className="rounded-lg bg-[#0f1020] border border-white/5 px-4 py-2">
            <p className="text-[10px] text-white/30">Current estimated risk</p>
            <p className="text-lg font-display font-bold text-white">{pct(explorer?.response.results[0]?.baseline_probability ?? twin?.predictions?.overload_risk_probability)}</p>
          </div>
        </div>

        {!twin && <p className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-xs text-white/30">Compute twin first to evaluate predefined scenarios.</p>}
        {twin && explorerStatus === 'loading' && <p className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-xs text-[#f0a500]">Loading scenario explorer...</p>}
        {explorerFailure && <p className="rounded-xl p-4 bg-[#e0606e]/10 border border-[#e0606e]/30 text-xs text-[#e0606e]">{explorerFailure}</p>}
        {explorer && explorer.response.results.length === 0 && <p className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-xs text-white/30">No supported scenario projections are available for this state.</p>}

        {explorer && explorer.response.results.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {[...explorer.response.results]
              .sort((a, b) => a.risk_delta - b.risk_delta)
              .map((row, idx) => {
                const plan = explorer.plans.find((item) => item.scenarios.some((s) => s.scenario_id === row.scenario_id));
                const delta = row.counterfactual_probability - row.baseline_probability;
                const detail = scenarioDetail(row, plan);
                return (
                  <article key={row.scenario_id} className="rounded-xl p-4 bg-[#0f1020] border border-white/5">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] text-[#00bfa5] font-bold">#{idx + 1}</p>
                        <h3 className="text-sm font-semibold text-white">{plan?.label ?? row.scenario_description}</h3>
                      </div>
                      <span className={`text-[10px] px-2 py-1 rounded border ${delta < -0.001 ? 'text-[#4ade80] border-[#4ade80]/25 bg-[#4ade80]/10' : delta > 0.001 ? 'text-[#e0606e] border-[#e0606e]/25 bg-[#e0606e]/10' : 'text-white/50 border-white/10 bg-white/5'}`}>
                        {pp(delta)}
                      </span>
                    </div>
                    <div className="mt-3 grid grid-cols-2 gap-2 text-[11px]">
                      <div><p className="text-white/30">Current</p><p className="text-white/70">{detail.current}</p></div>
                      <div><p className="text-white/30">Simulated</p><p className="text-white/70">{detail.simulated}</p></div>
                      <div><p className="text-white/30">Baseline</p><p className="text-white/80">{pct(row.baseline_probability)}</p></div>
                      <div><p className="text-white/30">Projected</p><p className="text-white/80">{pct(row.counterfactual_probability)}</p></div>
                    </div>
                    <p className="mt-3 text-[11px] text-white/45">{detail.change}</p>
                    <p className="mt-1 text-[11px] text-white/55">{modelInterpretation(delta)}</p>
                    <button
                      onClick={() => {
                        if (plan) void runInterpreted(plan);
                      }}
                      disabled={running || !plan}
                      className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-medium text-white/70 border border-white/10 disabled:opacity-40"
                    >
                      Explore this scenario <ArrowRight size={12} />
                    </button>
                  </article>
                );
              })}
          </div>
        )}
      </section>

      <section className="rounded-2xl p-6 bg-[#181921] border border-white/10">
        <div className="flex items-center gap-2 mb-4">
          <FlaskConical size={14} className="text-[#7c6cf5]" />
          <h2 className="text-[11px] uppercase tracking-widest text-white/60">Describe Your Own Plan</h2>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-4">
          {INTENTS.map((intent) => (
            <button
              key={intent.value}
              onClick={() => { setSelectedIntent(intent.value); setErrorState(null); setResultState(null); }}
              className={`px-3 py-2 rounded-lg text-xs font-medium border transition-all ${selectedIntent === intent.value ? 'bg-[#7c6cf5]/15 border-[#7c6cf5]/40 text-[#7c6cf5]' : 'bg-white/5 border-white/10 text-white/50 hover:border-white/20'}`}
            >
              {intent.label}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-2 mb-5">
          <button onClick={handleReset} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-white/6 hover:bg-white/10 text-xs font-medium text-white/60 hover:text-white transition-colors">
            <RotateCcw size={13} /> Reset
          </button>
          <button onClick={handlePresetRun} disabled={running || !twin} className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-[#00bfa5]/10 hover:bg-[#00bfa5]/20 text-xs font-medium text-[#00bfa5] border border-[#00bfa5]/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
            <Play size={13} /> {running ? 'Simulating...' : 'Run Selected Scenario'}
          </button>
        </div>

        <div className="rounded-xl p-4 bg-[#0f1020] border border-white/8">
          <p className="text-[10px] text-white/30 mb-2">Natural-language what-if</p>
          <div className="flex flex-col md:flex-row gap-2">
            <input
              value={naturalText}
              onChange={(event) => setNaturalText(event.target.value)}
              placeholder="I need to sleep more and study less"
              className="flex-1 bg-[#181921] border border-white/10 rounded px-3 py-2 text-xs text-white"
            />
            <button onClick={handleNaturalRun} disabled={running || !twin} className="flex items-center justify-center gap-1.5 px-4 py-2 rounded-lg bg-[#7c6cf5]/10 hover:bg-[#7c6cf5]/20 text-xs font-medium text-[#7c6cf5] border border-[#7c6cf5]/20 transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
              <Play size={13} /> Interpret & Run
            </button>
          </div>
          <p className="text-[10px] text-white/25 mt-2">Ambiguous text asks for clarification instead of silently choosing another scenario.</p>
        </div>
      </section>

      {interpreted && (
        <div className="rounded-xl p-4 bg-[#00bfa5]/8 border border-[#00bfa5]/20">
          <h3 className="text-[10px] font-bold text-[#00bfa5] mb-2">INTERPRETED PLAN</h3>
          <p className="text-xs text-white/70">{interpreted.label}</p>
          <div className="flex flex-wrap gap-2 mt-2">
            {interpreted.changes.map((change) => (
              <span key={change} className="px-2 py-1 rounded bg-[#0f1020] border border-white/5 text-[10px] text-white/60">{change}</span>
            ))}
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-xl p-4 bg-[#e0606e]/10 border border-[#e0606e]/30 text-xs text-[#e0606e]">{error}</div>
      )}

      {!twin && !running && (
        <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-xs text-white/30">
          Compute twin first on the Digital Twin page. The twin state is used as the simulation baseline.
        </div>
      )}

      {results && (
        <div className="rounded-2xl p-6 bg-[#181921] border border-white/10">
          <div className="flex items-center gap-2 mb-4">
            <TrendingDown size={14} className="text-[#4ade80]" />
            <h2 className="text-[11px] uppercase tracking-widest text-white/60">Scenario Projection</h2>
          </div>

          <div className="space-y-3">
            {resultRows.map((row) => {
              const delta = row.counterfactual_probability - row.baseline_probability;
              return (
                <div key={row.scenario_id} className="rounded-xl p-4 bg-white/[0.02] border border-white/5">
                  <div className="flex flex-col md:flex-row md:items-end gap-4 md:gap-8">
                    <div>
                      <p className="text-[10px] text-white/30 mb-1">Baseline Estimated 7-Day Risk</p>
                      <p className="text-3xl font-display font-bold text-white/40">{pct(row.baseline_probability)}</p>
                    </div>
                    <TrendingUp size={18} className="text-white/20 hidden md:block mb-2" />
                    <div>
                      <p className="text-[10px] text-white/30 mb-1">Scenario Projection</p>
                      <p className="text-3xl font-display font-bold text-[#4ade80]">{pct(row.counterfactual_probability)}</p>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-white">{row.scenario_description || row.scenario_type}</p>
                      <p className="text-[11px] text-white/45 mt-1">{riskLabel(row)}</p>
                      <p className="text-[11px] text-white/35 mt-1">{modelInterpretation(delta)}</p>
                      <span className={`inline-flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded mt-2 ${delta < -0.001 ? 'text-[#0d0e12] bg-[#4ade80]' : delta > 0.001 ? 'text-white bg-[#e0606e]' : 'text-white/70 bg-white/10'}`}>
                        {delta < -0.001 ? 'Lower' : delta > 0.001 ? 'Higher' : 'No material change'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {results.ranked_scenarios?.length ? (
            <div className="mt-5 space-y-2">
              <h3 className="text-[10px] uppercase tracking-widest text-white/35">Backend Ranked Scenario Output</h3>
              {results.ranked_scenarios.map((scenario: RankedScenario, idx: number) => (
                <div key={scenario.scenario_id || idx} className="rounded-xl p-3 bg-[#0f1020] border border-white/5 text-xs text-white/60">
                  #{scenario.rank} {scenario.scenario_description} - Score {scenario.overall_score?.toFixed(3) ?? 'Unavailable'}
                </div>
              ))}
            </div>
          ) : null}

          <p className="text-[10px] text-white/20 text-center mt-4">Observed inputs create the Digital Twin. Derived state feeds the RF prediction. Scenario projections are simulated model outputs, not causal claims.</p>
        </div>
      )}
    </div>
  );
}
