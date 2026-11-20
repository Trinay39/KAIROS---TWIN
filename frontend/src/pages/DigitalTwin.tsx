import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

import { useDemo } from '../context/DemoContext';
import type { FieldProvenance, StudentTwinState } from '../types';

interface TwinDimension {
  name: string;
  value: number;
  note: string;
  provenance?: FieldProvenance;
}

type RawTwinDimension = Omit<TwinDimension, 'value'> & { value: number | null };

function isVisibleDimension(d: RawTwinDimension): d is TwinDimension {
  return d.value !== null && d.provenance?.type !== 'imputed_default';
}

function dimsFromTwin(twin: StudentTwinState | null): TwinDimension[] {
  if (!twin) return [];
  const p = twin.provenance ?? {};
  const dims: RawTwinDimension[] = [
    { name: 'Academic', value: twin.academic?.academic_load_score ?? null, note: 'AcademicState.academic_load_score', provenance: p['academic.academic_load_score'] },
    { name: 'Behavioral', value: twin.behavioral?.study_consistency_score ?? null, note: 'BehavioralState.study_consistency_score', provenance: p['behavioral.study_consistency_score'] },
    { name: 'Recovery', value: twin.recovery?.recovery_score_7d ?? null, note: 'RecoveryState.recovery_score_7d', provenance: p['recovery.recovery_score_7d'] },
    { name: 'Workload', value: twin.workload?.workload_pressure_score_7d ?? null, note: 'WorkloadState.workload_pressure_score_7d', provenance: p['workload.workload_pressure_score_7d'] },
    { name: 'Engagement', value: twin.engagement?.engagement_composite_score ?? null, note: 'EngagementState.engagement_composite_score', provenance: p['engagement.engagement_composite_score'] },
    { name: 'Stress', value: twin.engagement?.avg_stress_7d ?? null, note: 'EngagementState.avg_stress_7d', provenance: p['engagement.avg_stress_7d'] },
  ];
  return dims.filter(isVisibleDimension);
}

export default function DigitalTwin() {
  const { state, computeTwin, updateInput } = useDemo();
  const { input, twin, status } = state;
  const dims = dimsFromTwin(twin);

  return (
    <div className="max-w-7xl mx-auto space-y-5 animate-fade-up">
      <div className="rounded-2xl p-8 bg-gradient-to-br from-[#181921] via-[#1c1d23] to-[#121317] border border-white/10">
        <div className="flex items-center gap-2 mb-1"><span className="text-[10px] uppercase tracking-widest text-[#00bfa5]">KAIROS-TWIN</span><span className="text-white/20">·</span><span className="text-[10px] uppercase tracking-widest text-white/30">Digital Twin</span></div>
        <h1 className="text-3xl font-display font-bold tracking-tight text-white">Student Digital Twin</h1>
        <p className="text-sm text-white/40 mt-1">Phase 3 TwinEngine · Input → Process → StudentTwinState</p>
      </div>

      {/* CURRENT OBSERVATIONS (editable, labeled) */}
      <section className="rounded-2xl p-6 bg-[#181921] border border-white/10">
        <h2 className="text-[11px] uppercase tracking-widest text-[#00bfa5] mb-4">CURRENT OBSERVATIONS (Phase 3 Schema)</h2>
        <div className="grid grid-cols-4 gap-3 mb-3">
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Student ID</label>
            <input value={input.student_id} onChange={e => updateInput({ student_id: e.target.value })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white font-mono" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Day</label>
            <input type="number" value={input.day} onChange={e => updateInput({ day: parseInt(e.target.value) || 50 })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white font-mono" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Study Hours / day (0–10)</label>
            <input type="number" step="0.1" value={input.study_hours} onChange={e => updateInput({ study_hours: parseFloat(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Sleep Hours / night (0–12)</label>
            <input type="number" step="0.1" value={input.sleep_hours} onChange={e => updateInput({ sleep_hours: parseFloat(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Stress Level (0–10)</label>
            <input type="number" step="0.5" value={input.stress_level} onChange={e => updateInput({ stress_level: parseFloat(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Grade (0–100)</label>
            <input type="number" value={input.grade} onChange={e => updateInput({ grade: parseInt(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Attendance Rate (0–1)</label>
            <input type="number" step="0.01" value={input.attendance_rate} onChange={e => updateInput({ attendance_rate: parseFloat(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white" />
          </div>
          <div>
            <label className="text-[10px] text-white/40 block mb-1">Missed Deadline (0=No, 1=Yes)</label>
            <select value={input.missed_deadline_observed} onChange={e => updateInput({ missed_deadline_observed: parseInt(e.target.value) })} className="w-full bg-[#0f1020] border border-white/10 rounded px-2 py-1.5 text-sm text-white">
              <option value={0}>No (0)</option><option value={1}>Yes (1)</option>
            </select>
          </div>
        </div>
        <div className="flex gap-2">
          <button onClick={computeTwin} disabled={status.twin === 'loading'} className="px-4 py-2 rounded-lg bg-[#00bfa5]/10 text-[#00bfa5] text-sm border border-[#00bfa5]/20 hover:bg-[#00bfa5]/20 disabled:opacity-40">[ COMPUTE TWIN ]</button>
        </div>
      </section>

      {/* INPUT USED */}
      <section className="rounded-xl p-3 bg-[#0f1020] border border-white/5">
        <h4 className="text-[10px] font-bold text-[#00bfa5] mb-2">INPUT USED: CURRENT OBSERVATIONS</h4>
        <div className="grid grid-cols-8 gap-2 text-[10px] text-white/60">
          <span>Student: <b className="text-white">{input.student_id}</b></span>
          <span>Day: <b className="text-white">{input.day}</b></span>
          <span>Study: <b className="text-white">{input.study_hours} hrs/day</b></span>
          <span>Sleep: <b className="text-white">{input.sleep_hours} hrs/night</b></span>
          <span>Stress: <b className="text-white">{input.stress_level}</b></span>
          <span>Grade: <b className="text-white">{input.grade}</b></span>
          <span>Attend: <b className="text-white">{Math.round(input.attendance_rate*100)}%</b></span>
          <span>Missed: <b className="text-white">{input.missed_deadline_observed ? 'Yes' : 'No'}</b></span>
        </div>
      </section>

      {/* COMPUTED DIGITAL TWIN */}
      <section className="rounded-2xl p-6 bg-[#181921] border border-white/10">
        <h2 className="text-[11px] uppercase tracking-widest text-white/40 mb-4">COMPUTED DIGITAL TWIN (from /states/compute)</h2>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="col-span-2 rounded-2xl p-6 bg-[#181921] border border-white/10">
            <h3 className="text-[11px] uppercase tracking-widest text-white/40 mb-4">State Profile — 6 Dimensions (from TwinEngine)</h3>
            {dims && dims.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={dims.map((d) => ({ name: d.name, value: d.value }))}>
                  <PolarGrid stroke="rgba(255,255,255,0.08)" />
                  <PolarAngleAxis dataKey="name" tick={{ fill: '#a0a3b0', fontSize: 11, fontFamily: 'Inter' }} />
                  <PolarRadiusAxis angle={90} domain={[0, 1]} tick={{ fill: '#6b7280', fontSize: 9 }} />
                  <Radar name="Twin" dataKey="value" stroke="#00bfa5" fill="#00bfa5" fillOpacity={0.18} strokeWidth={2} />
                  <Tooltip contentStyle={{ background: '#1a1b22', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 10, fontSize: 12, color: '#f3f4f6', fontFamily: 'Inter' }} labelStyle={{ color: '#a0a3b0' }} itemStyle={{ color: '#00bfa5' }} />
                </RadarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[300px] flex items-center justify-center text-white/30 text-sm">No dimension data available from backend (requires longer observation history for rolling averages)</div>
            )}
          </div>
          <div className="space-y-3">
            <div className="rounded-2xl p-5 bg-[#181921] border border-white/10">
              <h3 className="text-[11px] uppercase tracking-widest text-white/40 mb-4">Dimension Scores (actual backend)</h3>
              {dims.map((d) => (
                <div key={d.name} className="mb-2">
                  <div className="flex items-center justify-between mb-1"><span className="text-[11px] text-white/60">{d.name}</span><span className="text-[11px] font-mono text-white">{d.value != null ? d.value.toFixed(3) : '—'}</span></div>
                  <div className="h-1.5 rounded-full bg-white/5 overflow-hidden"><div className="h-full rounded-full bg-[#00bfa5] transition-all duration-700" style={{ width: d.value != null ? `${Math.min(100, d.value * 100)}%` : '0%' }} /></div>
                  <p className="text-[9px] text-white/30 mt-0.5">{d.note}</p>
                  <p className="text-[9px] text-[#00bfa5]/70 mt-0.5">{d.provenance?.type ?? 'unknown'}{d.provenance?.window ? ` · ${d.provenance.window}` : ''}</p>
                </div>
              ))}
              {dims.length === 0 && <p className="text-xs text-white/30">No dimension values returned by TwinEngine for this input. This is expected for single-observation inputs.</p>}
            </div>
            <div className="rounded-2xl p-5 bg-[#181921] border border-white/10">
              <h3 className="text-[11px] uppercase tracking-widest text-white/40 mb-4">Twin Metadata (actual returned)</h3>
              <div className="space-y-2 text-[11px]">
                <div className="flex justify-between"><span className="text-white/40">Student ID</span><span className="font-mono text-white">{twin?.student_id || '—'}</span></div>
                <div className="flex justify-between"><span className="text-white/40">Day</span><span className="font-mono text-white">{twin?.day ?? '—'}</span></div>
                <div className="flex justify-between"><span className="text-white/40">Data Source</span><span className="text-white">{twin?.data_source || '—'}</span></div>
                <div className="flex justify-between"><span className="text-white/40">State Version</span><span className="font-mono text-white">{twin?.state_version ?? '—'}</span></div>
                <div className="flex justify-between"><span className="text-white/40">Computed At</span><span className="font-mono text-white">{twin?.computed_at || '—'}</span></div>
                <div className="flex justify-between"><span className="text-white/40">Academic Load</span><span className="font-mono text-white">{twin?.academic?.academic_load_score != null ? twin.academic.academic_load_score.toFixed(3) : 'Unavailable'}</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <p className="text-[10px] text-white/20 text-center">Digital twin computed from Phase 3 observations via TwinEngine. Values are actual backend outputs — single observations may yield null rolling averages.</p>
    </div>
  );
}
