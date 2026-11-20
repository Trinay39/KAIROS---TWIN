import { Link } from 'react-router-dom';
import { useDemo } from '../context/DemoContext';
import { isFailureStatus, type Diagnosis } from '../types';

export default function CommandCenter() {
  const { state, presets, activePreset, applyScenario, updateInput, resetToDefault, computeTwin, predictRisk, runDiagnostics, runWhatIf, generateRec, recordDecision, recordFollowup } = useDemo();
  const { input, twin, prediction, diagnostics, sim, rec, followup, status, error, interventionId, decision: studentDecision } = state;
  const { twin: twinS, risk: riskS, diag: diagS, whatif: whatifS, rec: recS, decision: decisionS, followup: followupS } = status;

  const prob = prediction?.overload_probability ?? null;
  const probPct = prob != null ? `${Math.round(prob * 100)}` : null;
  const level = prob != null ? (prob >= 0.75 ? 'CRITICAL' : prob >= 0.5 ? 'HIGH' : prob >= 0.3 ? 'MODERATE' : 'LOW') : null;
  const color = prob != null ? (prob >= 0.75 ? '#e0606e' : prob >= 0.5 ? '#f0a500' : prob >= 0.3 ? '#7c6cf5' : '#4ade80') : '#4ade80';
  const simResult = sim?.results?.[0];
  const provenance = twin?.provenance ?? {};

  return (
    <div className="max-w-7xl mx-auto space-y-6 animate-fade-up">

      {/* Header */}
      <div className="rounded-2xl p-6 bg-gradient-to-br from-[#181921] via-[#1c1d23] to-[#121317] border border-white/10">
        <p className="text-[10px] uppercase tracking-widest text-[#00bfa5] font-medium">KAIROS-TWIN — Command Center</p>
        <h1 className="text-2xl font-display font-bold text-white">Pipeline Demo</h1>
        <p className="text-xs text-white/40 mt-0.5">Single canonical state · All stages share the same input and twin</p>
      </div>

      {/* SCENARIO SELECTOR */}
      <section className="rounded-2xl p-4 bg-gradient-to-r from-[#181921] to-[#121317] border border-[#7c6cf5]/20">
        <div className="flex items-center gap-2 mb-2"><span className="text-[10px] uppercase tracking-widest text-[#7c6cf5] font-bold">DEMO MODE</span><span className="text-[10px] text-white/30">Synthetic data only — no live integration</span></div>
        <h2 className="text-lg font-display font-bold text-white mb-3">Scenario Selector</h2>
        <div className="flex flex-wrap gap-2 mb-3">
          {(Object.keys(presets) as Array<keyof typeof presets>).map((key) => (
            <button key={key} onClick={() => applyScenario(key)} className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${activePreset === key ? 'bg-[#7c6cf5]/20 border-[#7c6cf5]/50 text-[#7c6cf5]' : 'bg-[#0f1020] border-white/10 text-white/60 hover:text-white hover:border-white/30'}`}>
              {key.replace('_',' ')} {key === 'BALANCED' ? '★' : ''}
            </button>
          ))}
        </div>
        {activePreset && (
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#00bfa5]/10 border border-[#00bfa5]/30 text-xs text-[#00bfa5]">
            ACTIVE: {activePreset} · Apply to set inputs · All downstream stages will be cleared
          </div>
        )}
      </section>

      {/* 1. CURRENT STUDENT INPUT */}
      <section className="rounded-2xl p-6 bg-[#181921] border border-white/10">
        <h2 className="text-[11px] uppercase tracking-widest text-[#00bfa5] mb-4">1. CURRENT STUDENT INPUT</h2>
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Student ID</label>
            <input value={input.student_id} onChange={e => updateInput({ student_id: e.target.value })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white font-mono" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Current Day (of 90)</label>
            <input type="number" min="1" max="90" value={input.day} onChange={e => updateInput({ day: parseInt(e.target.value) || 50 })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white font-mono" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Study Hours / day (0–10)</label>
            <input type="number" step="0.1" min="0" max="10" value={input.study_hours} onChange={e => updateInput({ study_hours: parseFloat(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Sleep Hours / night (0–12)</label>
            <input type="number" step="0.1" min="0" max="12" value={input.sleep_hours} onChange={e => updateInput({ sleep_hours: parseFloat(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Stress Level (0–10)</label>
            <input type="number" step="0.5" min="0" max="10" value={input.stress_level} onChange={e => updateInput({ stress_level: parseFloat(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Grade (0–100)</label>
            <input type="number" min="0" max="100" value={input.grade} onChange={e => updateInput({ grade: parseInt(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Attendance Rate (0–1)</label>
            <input type="number" step="0.01" min="0" max="1" value={input.attendance_rate} onChange={e => updateInput({ attendance_rate: parseFloat(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Missed Deadline (0=No, 1=Yes)</label>
            <select value={input.missed_deadline_observed} onChange={e => updateInput({ missed_deadline_observed: parseInt(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white">
              <option value={0}>No (0)</option><option value={1}>Yes (1)</option>
            </select>
          </div>
        </div>

        {/* INPUT USED */}
        <div className="rounded-lg bg-[#0f1020] border border-white/5 p-3 mb-3">
          <h4 className="text-[10px] font-bold text-[#00bfa5] mb-2">CURRENT INPUT (sent to backend on each action)</h4>
          <div className="grid grid-cols-5 gap-2 text-[10px] text-white/60">
            <span>Student: <b className="text-white">{input.student_id}</b></span>
            <span>Day: <b className="text-white">Day {input.day}/90</b></span>
            <span>Study: <b className="text-white">{input.study_hours} hrs/day</b></span>
            <span>Sleep: <b className="text-white">{input.sleep_hours} hrs/night</b></span>
            <span>Stress: <b className="text-white">{input.stress_level}/10</b></span>
            <span>Grade: <b className="text-white">{input.grade}/100</b></span>
            <span>Attendance: <b className="text-white">{Math.round(input.attendance_rate * 100)}%</b></span>
            <span>Missed: <b className="text-white">{input.missed_deadline_observed ? 'Yes (1)' : 'No (0)'}</b></span>
          </div>
        </div>

        <div className="flex gap-2">
          <button onClick={resetToDefault} className="px-3 py-2 rounded-lg bg-white/5 text-white/60 text-xs border border-white/10 hover:bg-white/10">[ Reset Demo ]</button>
          <button onClick={computeTwin} disabled={twinS === 'loading'} className="px-3 py-2 rounded-lg bg-[#7c6cf5]/10 text-[#7c6cf5] text-xs border border-[#7c6cf5]/20 hover:bg-[#7c6cf5]/20 disabled:opacity-30">
            {twinS === 'loading' ? '⏳ Computing…' : '[ 2. COMPUTE TWIN ]'}
          </button>
        </div>
      </section>

      {/* Pipeline Status */}
      <section className="rounded-xl p-4 bg-[#181921] border border-white/10">
        <h3 className="text-[11px] uppercase tracking-widest text-white/40 mb-3">Pipeline Status</h3>
        <div className="grid grid-cols-4 md:grid-cols-8 gap-2 text-[11px]">
          {[
            { label: '1 Input', s: status.input },
            { label: '2 Twin', s: twinS },
            { label: '3 Risk', s: riskS },
            { label: '4 Agents', s: diagS },
            { label: '5 What-If', s: whatifS },
            { label: '6 Rec', s: recS },
            { label: '7 Decision', s: decisionS },
            { label: '8 Follow-up', s: followupS },
          ].map((st, i) => (
            <div key={i} className={`rounded p-2 text-center border ${st.s === 'done' ? 'border-[#00bfa5]/40 bg-[#00bfa5]/10 text-[#00bfa5]' : st.s === 'loading' ? 'border-[#f0a500]/40 bg-[#f0a500]/10 text-[#f0a500]' : isFailureStatus(st.s) ? 'border-[#e0606e]/40 bg-[#e0606e]/10 text-[#e0606e]' : 'border-white/10 bg-white/[0.03] text-white/30'}`}>
              <p className="text-[10px]">{st.label}</p>
              <p className="text-[11px] mt-0.5">{st.s === 'done' ? '✓' : st.s === 'loading' ? '⏳' : isFailureStatus(st.s) ? '✕' : '○'}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Error */}
      {error && <div className="rounded-xl p-3 bg-[#e0606e]/10 border border-[#e0606e]/30 text-xs text-[#e0606e]">{error}</div>}

      {/* Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

        {/* 2. Twin */}
        <section className="rounded-2xl p-5 bg-[#181921] border border-white/10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[11px] uppercase tracking-widest text-[#7c6cf5]">2. COMPUTED DIGITAL TWIN</h2>
            <button onClick={computeTwin} disabled={twinS === 'loading'} className="text-[10px] px-2 py-1 rounded bg-[#7c6cf5]/10 text-[#7c6cf5] border border-[#7c6cf5]/20">RECOMPUTE</button>
          </div>
          {twinS === 'loading' && <p className="text-xs text-[#f0a500]">Computing twin from observations via /states/compute…</p>}
          {twin && (
            <div>
              <div className="mb-2 text-[10px] text-white/40">INPUT: {input.student_id} · Day {input.day} · Study {input.study_hours}h · Sleep {input.sleep_hours}h · Stress {input.stress_level}</div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                {[
                  { label: 'Academic Load Score', v: twin.academic?.academic_load_score, note: provenance['academic.academic_load_score']?.type ?? 'TwinEngine' },
                  { label: 'Study Consistency', v: twin.behavioral?.study_consistency_score, note: provenance['behavioral.study_consistency_score']?.type ?? 'TwinEngine' },
                  { label: 'Recovery Score (7d)', v: twin.recovery?.recovery_score_7d, note: provenance['recovery.recovery_score_7d']?.type ?? 'TwinEngine' },
                  { label: 'Workload Pressure (7d)', v: twin.workload?.workload_pressure_score_7d, note: provenance['workload.workload_pressure_score_7d']?.type ?? 'TwinEngine' },
                  { label: 'Engagement Composite', v: twin.engagement?.engagement_composite_score, note: provenance['engagement.engagement_composite_score']?.type ?? 'TwinEngine' },
                  { label: 'State Version', v: twin.state_version, note: twin.state_version != null ? 'system' : null },
                ].map(d => (
                  <div key={d.label} className="rounded bg-[#0f1020] border border-white/5 p-2">
                    <p className="text-[9px] text-white/40">{d.label}</p>
                    <p className="text-sm font-mono text-white">{d.v != null ? (typeof d.v === 'number' ? d.v.toFixed(3) : d.v) : 'Unavailable'}</p>
                    {d.note ? <p className="text-[8px] text-white/20">Source: {d.note}</p> : null}
                  </div>
                ))}
              </div>
              <p className="text-[9px] text-white/20 mt-2">Source: TwinEngine (/states/compute) — null values indicate single-observation input cannot produce rolling averages</p>
            </div>
          )}
          {!twin && twinS !== 'loading' && <p className="text-xs text-white/30">Load input, then press [ COMPUTE TWIN ].</p>}
        </section>

        {/* 3. Risk */}
        <section className="rounded-2xl p-5 bg-[#181921] border border-white/10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[11px] uppercase tracking-widest text-[#f0a500]">3. PREDICT 7-DAY OVERLOAD RISK</h2>
            <button onClick={predictRisk} disabled={!twin || riskS === 'loading'} className="text-[10px] px-2 py-1 rounded bg-[#f0a500]/10 text-[#f0a500] border border-[#f0a500]/20 disabled:opacity-30">{riskS === 'loading' ? '⏳' : 'PREDICT'}</button>
          </div>
          {riskS === 'loading' && <p className="text-xs text-[#f0a500]">Calling /predictions (RF PredictionService)…</p>}
          {prediction && (
            <div>
              <div className="mb-2 text-[10px] text-white/40">INPUT: Twin state of {input.student_id} at Day {input.day}</div>
              <div className="rounded-xl p-4 bg-gradient-to-r from-[#f0a500]/10 to-transparent border border-[#f0a500]/20 mb-3">
                <p className="text-[10px] text-white/40">Overload Probability (from RF model)</p>
                <p className="text-5xl font-display font-bold" style={{ color }}>{probPct}%</p>
                <span className="inline-block text-[10px] font-bold px-2 py-0.5 rounded mt-1" style={{ color, background: `${color}18`, border: `1px solid ${color}30` }}>{level}</span>
              </div>
              <div className="text-[10px] text-white/50 space-y-1">
                <p><b className="text-white/70">MODEL OUTPUT:</b> overload_probability={prob?.toFixed(6)} · overload_prediction={String(prediction?.overload_prediction ?? '—')}</p>
                <p><b className="text-white/70">SOURCE:</b> /predictions · RF PredictionService</p>
                <p className="text-[#f0a500]">⚠ Model-estimated from synthetic observations. Not clinical.</p>
              </div>
            </div>
          )}
          {!prediction && riskS !== 'loading' && <p className="text-xs text-white/30">Requires computed twin (Step 2).</p>}
        </section>

        {/* 4. Diagnostics */}
        <section className="rounded-2xl p-5 bg-[#181921] border border-white/10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[11px] uppercase tracking-widest text-[#7c6cf5]">4. RUN 5-AGENT DIAGNOSIS</h2>
            <button onClick={runDiagnostics} disabled={!twin || diagS === 'loading'} className="text-[10px] px-2 py-1 rounded bg-[#7c6cf5]/10 text-[#7c6cf5] border border-[#7c6cf5]/20 disabled:opacity-30">{diagS === 'loading' ? '⏳' : 'RUN'}</button>
          </div>
          {diagS === 'loading' && <p className="text-xs text-[#7c6cf5]">Calling /diagnostics (5 agents)…</p>}
          {diagnostics && (
            <div>
              <div className="mb-2 text-[10px] text-white/40">INPUT: Twin state of {input.student_id} at Day {input.day}</div>
              <div className="grid grid-cols-5 gap-2 text-xs mb-3">
                {Object.entries(diagnostics.diagnoses || {}).map(([agent, issues]) => (
                  <div key={agent} className="rounded bg-[#0f1020] border border-white/5 p-2 text-center">
                    <p className="text-[9px] text-[#7c6cf5] font-bold">{agent}</p>
                    <p className="text-xl font-bold text-white">{Array.isArray(issues) ? issues.length : 0}</p>
                    <p className="text-[9px] text-white/40">issues</p>
                  </div>
                ))}
              </div>
              <h4 className="text-[10px] font-bold text-white/50 mb-2">WHY THIS OUTPUT? (actual agent diagnoses)</h4>
              <div className="space-y-2">
                {Object.entries(diagnostics.diagnoses || {}).map(([agent, issues]) => {
                  const arr: Diagnosis[] = Array.isArray(issues) ? issues : [];
                  return (
                    <div key={agent} className="rounded bg-[#0f1020] border border-white/5 p-2">
                      <b className="text-[10px] text-[#7c6cf5]">{agent}</b>
                      {arr.length === 0 ? <span className="text-[10px] text-[#4ade80] ml-2">No issue detected</span>
                        : arr.map((i, idx) => (
                          <div key={idx} className="mt-1 text-[10px] text-white/60">
                            <span className="text-[#e0606e]">[{i.severity || '?'}]</span> {i.issue_name || '—'}: {i.description || 'No explanation returned by backend.'}
                          </div>
                        ))}
                    </div>
                  );
                })}
              </div>
              <p className="text-[9px] text-white/20 mt-2">Source: /diagnostics · Academic, Behavioral, Recovery, Workload, Schedule agents</p>
            </div>
          )}
          {!diagnostics && diagS !== 'loading' && <p className="text-xs text-white/30">Requires computed twin (Step 2).</p>}
        </section>

        {/* 5. What-If */}
        <section className="rounded-2xl p-5 bg-[#181921] border border-white/10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[11px] uppercase tracking-widest text-[#4ade80]">5. WHAT-IF SIMULATION</h2>
            <button onClick={runWhatIf} disabled={!twin || whatifS === 'loading'} className="text-[10px] px-2 py-1 rounded bg-[#4ade80]/10 text-[#4ade80] border border-[#4ade80]/20 disabled:opacity-30">{whatifS === 'loading' ? '⏳' : 'RUN'}</button>
          </div>
          {whatifS === 'loading' && <p className="text-xs text-[#4ade80]">Calling Phase 5 CounterfactualEngine (/simulations/run)…</p>}
          {simResult && (
            <div>
              <div className="mb-2 text-[10px] text-white/40">INPUT: Twin state of {input.student_id} at Day {input.day}</div>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div className="rounded-lg bg-[#0f1020] border border-white/5 p-3 text-center">
                  <p className="text-[10px] text-white/30">BASELINE RISK</p>
                  <p className="text-2xl font-display font-bold text-white/50">{simResult.baseline_probability != null ? `${Math.round(simResult.baseline_probability * 100)}%` : '—'}</p>
                </div>
                <div className="rounded-lg bg-[#0f1020] border border-white/5 p-3 text-center">
                  <p className="text-[10px] text-white/30">COUNTERFACTUAL RISK</p>
                  <p className="text-2xl font-display font-bold text-[#4ade80]">{simResult.counterfactual_probability != null ? `${Math.round(simResult.counterfactual_probability * 100)}%` : '—'}</p>
                </div>
              </div>
              <div className="text-[10px] text-white/50 space-y-1">
                <p><b className="text-white/70">SCENARIO:</b> {simResult.scenario_description || simResult.scenario_type || '—'}</p>
                <p><b className="text-white/70">RISK DELTA:</b> {simResult.risk_delta != null ? `${simResult.risk_delta.toFixed(4)}` : '—'}</p>
                <p><b className="text-white/70">INTERPRETATION:</b> {simResult.interpretation || '—'}</p>
                <p><b className="text-white/70">SOURCE:</b> Phase 5 CounterfactualEngine (/simulations/run)</p>
              </div>
            </div>
          )}
          {!simResult && whatifS !== 'loading' && <p className="text-xs text-white/30">Requires computed twin (Step 2). Go to What-If Lab for full scenario control.</p>}
        </section>

        {/* 6+7. Recommend */}
        <section className="rounded-2xl p-5 bg-[#181921] border border-white/10">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-[11px] uppercase tracking-widest text-[#00bfa5]">6. GENERATE RECOMMENDATION</h2>
            <button onClick={generateRec} disabled={!twin || recS === 'loading'} className="text-[10px] px-2 py-1 rounded bg-[#00bfa5]/10 text-[#00bfa5] border border-[#00bfa5]/20 disabled:opacity-30">{recS === 'loading' ? '⏳' : 'GENERATE'}</button>
          </div>
          {recS === 'loading' && <p className="text-xs text-[#00bfa5]">Calling /recommendations/generate (Phase 6)…</p>}
          {rec && (
            <div>
              <div className="mb-2 text-[10px] text-white/40">INPUT: Twin state of {input.student_id} at Day {input.day}</div>
              <h4 className="text-sm font-semibold text-white mb-1">{rec.scenario_description || rec.scenario_id || 'Recommendation'}</h4>
              <p className="text-xs text-white/50 mb-2">Scenario: {rec.scenario_type} · Confidence: {rec.confidence}</p>
              <p className="text-xs text-white/70 leading-relaxed mb-2">{rec.explanation || 'No explanation returned.'}</p>
              <div className="flex gap-3 text-xs mb-2">
                <span>Baseline: <b className="text-white">{rec.baseline_risk != null ? `${Math.round(rec.baseline_risk * 100)}%` : '—'}</b></span>
                <span>Counterfactual: <b className="text-[#4ade80]">{rec.counterfactual_risk != null ? `${Math.round(rec.counterfactual_risk * 100)}%` : '—'}</b></span>
                <span>Est. reduction: <b className="text-[#f0a500]">{rec.risk_reduction_percentage != null ? `${Math.round(rec.risk_reduction_percentage)}%` : '—'}</b></span>
              </div>
              <p className="text-[10px] text-white/30 mb-2">Diagnoses: {rec.primary_diagnoses?.join(', ') || '—'}</p>
              <p className="text-[10px] text-white/30 mb-2">Caveats: {(rec.caveats || []).join(' · ') || 'None returned.'}</p>
              <p className="text-[10px] text-[#f0a500]">⚠ Synthetic data. Model-estimated. Not clinical.</p>

              {/* 7. Record Decision */}
              <div className="mt-3 pt-3 border-t border-white/10">
                <p className="text-[10px] text-white/50 mb-2">7. RECORD DECISION</p>
                <div className="flex flex-wrap gap-2">
                  <button onClick={() => recordDecision('accepted')} disabled={decisionS === 'loading' || decisionS === 'done'} className="px-3 py-1.5 rounded-lg bg-[#4ade80]/10 text-[#4ade80] text-xs border border-[#4ade80]/20 hover:bg-[#4ade80]/20 disabled:opacity-40">[ ACCEPT ]</button>
                  <button onClick={() => recordDecision('rejected')} disabled={decisionS === 'loading' || decisionS === 'done'} className="px-3 py-1.5 rounded-lg bg-[#e0606e]/10 text-[#e0606e] text-xs border border-[#e0606e]/20 hover:bg-[#e0606e]/20 disabled:opacity-40">[ REJECT ]</button>
                  <button onClick={() => recordDecision('deferred')} disabled={decisionS === 'loading' || decisionS === 'done'} className="px-3 py-1.5 rounded-lg bg-[#f0a500]/10 text-[#f0a500] text-xs border border-[#f0a500]/20 hover:bg-[#f0a500]/20 disabled:opacity-40">[ DEFER ]</button>
                  <button onClick={() => recordDecision('ask_more')} disabled={decisionS === 'loading' || decisionS === 'done'} className="px-3 py-1.5 rounded-lg bg-[#7c6cf5]/10 text-[#7c6cf5] text-xs border border-[#7c6cf5]/20 hover:bg-[#7c6cf5]/20 disabled:opacity-40">[ ASK MORE ]</button>
                </div>
                {decisionS === 'done' && <p className="text-[10px] text-[#00bfa5] mt-1">✓ Decision persisted · Intervention ID: {interventionId || rec.scenario_id}</p>}
                {isFailureStatus(decisionS) && <p className="text-[10px] text-[#e0606e] mt-1">✕ Decision log failed.</p>}
                {decisionS === 'done' && studentDecision !== 'accepted' && (
                  <p className="text-[10px] text-white/35 mt-2">Follow-up outcome recording is available after an accepted intervention.</p>
                )}
                {decisionS === 'done' && studentDecision === 'accepted' && (
                  <div className="mt-3 rounded-lg bg-[#0f1020] border border-white/5 p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="text-[10px] text-white/50">8. FOLLOW-UP / OUTCOME</p>
                        <p className="text-[10px] text-white/30">Records a day+7 demo follow-up through the existing backend outcome endpoint.</p>
                      </div>
                      <button onClick={recordFollowup} disabled={followupS === 'loading' || followupS === 'done' || !interventionId} className="px-3 py-1.5 rounded-lg bg-[#00bfa5]/10 text-[#00bfa5] text-xs border border-[#00bfa5]/20 hover:bg-[#00bfa5]/20 disabled:opacity-40">
                        {followupS === 'loading' ? 'Recording...' : 'RECORD FOLLOW-UP'}
                      </button>
                    </div>
                    {followupS === 'done' && followup && (
                      <div className="mt-2 grid grid-cols-3 gap-2 text-[10px] text-white/60">
                        <span>Outcome: <b className="text-white">{followup.outcome_id}</b></span>
                        <span>Follow-up day: <b className="text-white">{followup.report.followup_day}</b></span>
                        <span>Actual risk: <b className="text-white">{Math.round(followup.report.actual_risk_at_day7 * 100)}%</b></span>
                      </div>
                    )}
                    {isFailureStatus(followupS) && <p className="text-[10px] text-[#e0606e] mt-2">Follow-up could not be recorded.</p>}
                  </div>
                )}
              </div>
            </div>
          )}
          {!rec && recS !== 'loading' && <p className="text-xs text-white/30">Requires computed twin (Step 2).</p>}
        </section>
      </div>

      {/* Quick Nav */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { to: '/twin', label: '2. Digital Twin', sub: 'All 6 dimensions' },
          { to: '/risk', label: '3. Risk Intelligence', sub: 'RF PredictionService' },
          { to: '/agents', label: '4. Agent Control', sub: '5-agent panel' },
          { to: '/whatif', label: '5. What-If Lab', sub: 'Phase 5 engine' },
          { to: '/recommend', label: '6. Recommendations', sub: 'Phase 6 service' },
          { to: '/history', label: '8. Student History', sub: 'Observed trajectories' },
          { to: '/faculty', label: '9. Faculty View', sub: 'History & outcomes' },
        ].map(item => (
          <Link key={item.to} to={item.to} className="group p-3 rounded-xl bg-[#181921] border border-white/8 hover:border-white/15 text-xs text-white/70 hover:text-white transition-all">
            <b className="text-white">{item.label}</b><br /><span className="text-[10px] text-white/30">{item.sub}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
