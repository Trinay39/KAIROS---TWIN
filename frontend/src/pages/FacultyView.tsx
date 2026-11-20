import { useEffect, useState } from 'react';
import { messageForError } from '../api/client';
import { endpoints } from '../api/endpoints';
import { HistoryCharts } from '../components/HistoryCharts';
import { presets, useDemo } from '../context/DemoContext';
import type { RequestStatus, StudentHistory, SystemAnalytics } from '../types';
import { getRiskLevel, isFailureStatus } from '../types';

function pct(value: number | null | undefined) {
  return value == null ? 'Unavailable' : `${Math.round(value * 100)}%`;
}

function score(value: number | null | undefined) {
  return value == null ? 'Unavailable' : value.toFixed(2);
}

function riskLanguage(probability: number | null | undefined) {
  if (probability == null) return 'Risk not predicted';
  const level = getRiskLevel(probability);
  if (level === 'critical' || level === 'high') return 'Higher estimated risk';
  if (level === 'moderate') return 'Moderate estimated risk';
  return 'Lower estimated risk';
}

export default function FacultyView() {
  const { state, applyScenario } = useDemo();
  const { input, twin, prediction, followup } = state;
  const [history, setHistory] = useState<StudentHistory | null>(null);
  const [analytics, setAnalytics] = useState<SystemAnalytics | null>(null);
  const [status, setStatus] = useState<RequestStatus>('pending');
  const [error, setError] = useState<string | null>(null);
  const [loadedKey, setLoadedKey] = useState<string | null>(null);
  const selectionKey = `${input.student_id}:${input.day}`;
  const historyForCurrentStudent = history?.student_id === input.student_id ? history : null;
  const observations = historyForCurrentStudent?.observations ?? [];
  const facultyLoading = loadedKey !== selectionKey;

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      endpoints.history(input.student_id, input.day),
      endpoints.analytics(),
    ]).then(([studentHistory, systemAnalytics]) => {
      if (cancelled) return;
      setHistory(studentHistory);
      setAnalytics(systemAnalytics);
      setStatus('done');
      setError(null);
      setLoadedKey(selectionKey);
    }).catch((caught) => {
      if (cancelled) return;
      setError(messageForError(caught, 'Faculty history is unavailable.'));
      setStatus('error');
      setLoadedKey(selectionKey);
    });

    return () => {
      cancelled = true;
    };
  }, [input.day, input.student_id, selectionKey]);

  return (
    <div className="max-w-6xl mx-auto space-y-5 animate-fade-up">
      <div className="rounded-2xl p-8 bg-gradient-to-br from-[#181921] to-[#121317] border border-white/10">
        <div className="flex items-center gap-2 mb-1"><span className="text-[10px] uppercase tracking-widest text-[#7c6cf5] font-medium">KAIROS-TWIN</span><span className="text-white/20">/</span><span className="text-[10px] uppercase tracking-widest text-white/30">Faculty View</span></div>
        <h1 className="text-3xl font-display font-bold tracking-tight text-white">Faculty Monitoring View</h1>
        <p className="text-sm text-white/40 mt-1">Neutral monitoring for attention signals, history, interventions, and follow-ups.</p>
      </div>

      <section className="rounded-2xl p-5 bg-[#181921] border border-white/10">
        <h2 className="text-[11px] uppercase tracking-widest text-white/40 mb-4">Student Overview</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-xs">
            <thead className="text-white/35">
              <tr className="border-b border-white/10">
                <th className="py-2 text-left font-medium">Student ID</th>
                <th className="py-2 text-left font-medium">Current Overload Risk</th>
                <th className="py-2 text-left font-medium">Academic Load</th>
                <th className="py-2 text-left font-medium">Recovery</th>
                <th className="py-2 text-left font-medium">Stress</th>
                <th className="py-2 text-left font-medium">Engagement</th>
                <th className="py-2 text-left font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {(Object.keys(presets) as Array<keyof typeof presets>).map((key) => {
                const preset = presets[key];
                const selected = preset.student_id === input.student_id;
                return (
                  <tr key={preset.student_id} className={`border-b border-white/5 ${selected ? 'bg-[#7c6cf5]/8' : ''}`}>
                    <td className="py-3 font-mono text-white">{preset.student_id}</td>
                    <td className="py-3 text-white/65">{selected ? riskLanguage(prediction?.overload_probability) : 'Select to compute'}</td>
                    <td className="py-3 text-white/65">{selected ? score(twin?.academic.academic_load_score) : 'Unavailable'}</td>
                    <td className="py-3 text-white/65">{selected ? score(twin?.recovery.recovery_score_7d) : 'Unavailable'}</td>
                    <td className="py-3 text-white/65">{selected ? score(twin?.engagement.avg_stress_7d) : `${preset.stress_level}/10 observed`}</td>
                    <td className="py-3 text-white/65">{selected ? score(twin?.engagement.engagement_composite_score) : 'Unavailable'}</td>
                    <td className="py-3">
                      <button onClick={() => applyScenario(key)} className="px-3 py-1.5 rounded-lg bg-white/5 text-white/65 text-[11px] border border-white/10 hover:bg-white/10">
                        Select
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-3 text-[10px] text-white/25">This table is a monitoring overview, not a leaderboard. Compute each selected twin for full current-state values.</p>
      </section>

      <section className="rounded-2xl p-5 bg-[#181921] border border-white/10">
        <h2 className="text-[11px] uppercase tracking-widest text-white/40 mb-4">Faculty System Summary</h2>
        {analytics ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
            <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Interventions Logged</p><p className="text-lg font-bold text-white">{analytics.registry.total_interventions}</p></div>
            <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Acceptance Rate</p><p className="text-lg font-bold text-white">{pct(analytics.registry.acceptance_rate)}</p></div>
            <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Follow-ups Recorded</p><p className="text-lg font-bold text-white">{analytics.outcomes.total_tracked}</p></div>
            <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Outcome Success Rate</p><p className="text-lg font-bold text-white">{pct(analytics.outcomes.success_rate)}</p></div>
          </div>
        ) : (
          <p className="text-xs text-white/35">System analytics will appear when /analytics/system responds.</p>
        )}
      </section>

      <section className="rounded-2xl p-6 bg-[#181921] border border-white/10">
        <h2 className="text-[11px] uppercase tracking-widest text-white/40 mb-4">Faculty Student Detail</h2>
        {facultyLoading && <p className="text-xs text-[#f0a500]">Loading student history and system analytics...</p>}
        {loadedKey === selectionKey && isFailureStatus(status) && <p className="text-xs text-[#e0606e]">{error || 'Faculty history is unavailable.'}</p>}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs mb-5">
          <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Current Estimated Risk</p><p className="text-lg font-bold text-white">{pct(prediction?.overload_probability)}</p><p className="text-[10px] text-white/35">{riskLanguage(prediction?.overload_probability)}</p></div>
          <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Academic Load</p><p className="text-lg font-bold text-white">{score(twin?.academic.academic_load_score)}</p></div>
          <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Recovery</p><p className="text-lg font-bold text-white">{score(twin?.recovery.recovery_score_7d)}</p></div>
          <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Engagement</p><p className="text-lg font-bold text-white">{score(twin?.engagement.engagement_composite_score)}</p></div>
          <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Stress</p><p className="text-lg font-bold text-white">{score(twin?.engagement.avg_stress_7d)}</p></div>
          <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Attendance</p><p className="text-lg font-bold text-white">{pct(twin?.academic.attendance_rate_7d)}</p></div>
          <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Study Behavior</p><p className="text-lg font-bold text-white">{score(twin?.behavioral.avg_study_hours_7d)}</p></div>
          <div className="rounded bg-[#0f1020] border border-white/5 p-3"><p className="text-[10px] text-white/40">Interventions</p><p className="text-lg font-bold text-white">{historyForCurrentStudent?.total_interventions ?? 0}</p></div>
        </div>

        {loadedKey === selectionKey && observations.length > 0 ? (
          <HistoryCharts observations={observations} />
        ) : loadedKey === selectionKey && status === 'done' ? (
          <p className="rounded bg-[#0f1020] border border-white/5 p-3 text-xs text-white/35">No historical observations available for this student.</p>
        ) : null}
      </section>

      <section className="rounded-2xl p-6 bg-[#181921] border border-white/10">
        <h2 className="text-[11px] uppercase tracking-widest text-white/40 mb-4">Intervention History</h2>
        {historyForCurrentStudent?.interventions?.length ? (
          <div className="space-y-2">
            {historyForCurrentStudent.interventions.slice(0, 6).map((item) => (
              <div key={item.intervention_id} className="rounded bg-[#0f1020] border border-white/5 p-3 text-xs text-white/65">
                <div className="flex items-center justify-between gap-3">
                  <b className="text-white">{item.scenario_description || item.scenario_type}</b>
                  <span className="text-[#00bfa5]">{item.status}</span>
                </div>
                <p className="mt-1 text-[10px] text-white/35">Decision: {item.student_response || 'Unavailable'} / Follow-up: {item.outcome_report_id || 'No follow-up recorded'} / Offered day {item.offered_at_day}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="rounded bg-[#0f1020] border border-white/5 p-3 text-xs text-white/35">No intervention history is available for this student yet.</p>
        )}
        {followup && (
          <p className="mt-3 text-[10px] text-white/45">Latest session follow-up: {followup.outcome_id} / day {followup.report.followup_day} / estimated risk {pct(followup.report.actual_risk_at_day7)}</p>
        )}
      </section>
    </div>
  );
}
