
import { useDemo } from '../context/DemoContext';
import type { Diagnosis } from '../types';
import { isFailureStatus } from '../types';

export default function AgentControl() {
  const { state, runDiagnostics } = useDemo();
  const { input, twin, diagnostics, status, error } = state;
  const diagS = status.diag;

  return (
    <div className="max-w-5xl mx-auto space-y-5 animate-fade-up">
      <div className="rounded-2xl p-8 bg-gradient-to-br from-[#181921] to-[#121317] border border-white/10">
        <div className="flex items-center gap-2 mb-1"><span className="text-[10px] uppercase tracking-widest text-[#7c6cf5] font-medium">KAIROS-TWIN</span><span className="text-white/20">·</span><span className="text-[10px] uppercase tracking-widest text-white/30">Agent Control</span></div>
        <h1 className="text-3xl font-display font-bold tracking-tight text-white">Agent Control</h1>
        <p className="text-sm text-white/40 mt-1">Multi-agent diagnostic control · /diagnostics · 5 agents</p>
      </div>

      {/* INPUT USED */}
      <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5">
        <h3 className="text-[10px] font-bold text-[#00bfa5] mb-2">CURRENT STUDENT STATE</h3>
        <div className="grid grid-cols-4 gap-2 text-[10px] text-white/60">
          <span>Student: <b className="text-white">{input.student_id}</b></span>
          <span>Day: <b className="text-white">{input.day}</b></span>
          <span>Study: <b className="text-white">{input.study_hours} hrs/day</b></span>
          <span>Sleep: <b className="text-white">{input.sleep_hours} hrs/night</b></span>
          <span>Stress: <b className="text-white">{input.stress_level}/10</b></span>
          <span>Grade: <b className="text-white">{input.grade}/100</b></span>
          <span>Attendance: <b className="text-white">{Math.round(input.attendance_rate*100)}%</b></span>
          <span>Twin computed: <b className="text-white">{twin ? 'Yes' : 'No'}</b></span>
        </div>
      </div>

      <div className="rounded-xl p-5 bg-[#181921] border border-white/10 flex items-center justify-between">
        <div><h2 className="text-xs font-medium text-white/50 uppercase tracking-wider">5-Agent Diagnostic Panel</h2><p className="text-[10px] text-white/30">Current student: {input.student_id} · Day {input.day} · Calls /diagnostics</p></div>
        <button onClick={runDiagnostics} disabled={!twin || diagS === 'loading'} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[#7c6cf5]/10 text-[#7c6cf5] text-xs font-medium border border-[#7c6cf5]/20 hover:bg-[#7c6cf5]/20 disabled:opacity-40 transition-colors">
          {diagS === 'loading' ? '⏳ Running…' : diagnostics ? 'RERUN ALL AGENTS' : '[ RUN ALL AGENTS ]'}
        </button>
      </div>

      {isFailureStatus(diagS) && (
        <div className="rounded-xl p-3 bg-[#e0606e]/10 border border-[#e0606e]/30 text-xs text-[#e0606e]">
          {error || 'Agent diagnostics failed. Check that twin has been computed.'}
        </div>
      )}

      {diagS !== 'done' && !diagnostics && (
        <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-xs text-white/30">
          Compute twin first, then click [ RUN ALL AGENTS ].
        </div>
      )}

      {diagnostics && (
        <div className="rounded-2xl p-6 bg-[#181921] border border-white/10">
          {/* Agent summary cards */}
          <div className="grid grid-cols-5 gap-3 mb-6">
            {Object.entries(diagnostics.diagnoses || {}).map(([agent, issues]) => {
              const arr: Diagnosis[] = Array.isArray(issues) ? issues : [];
              return (
                <div key={agent} className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-center">
                  <p className="text-[10px] text-[#7c6cf5] font-bold mb-2">{agent}</p>
                  <p className="text-3xl font-display font-bold text-white">{arr.length}</p>
                  <p className="text-[10px] text-white/40">issues detected</p>
                </div>
              );
            })}
          </div>

          {/* Statistics */}
          {diagnostics.statistics && (
            <div className="mb-6 p-4 bg-[#0f1020] border border-white/5 rounded-xl">
              <h3 className="text-[11px] uppercase tracking-widest text-white/40 mb-3">Diagnostic Statistics</h3>
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div><p className="text-[10px] text-white/40">Total Diagnoses</p><p className="text-lg font-bold text-white">{diagnostics.statistics.total_diagnoses ?? '—'}</p></div>
                <div><p className="text-[10px] text-white/40">By Severity</p>
                  <div className="space-y-0.5 mt-1">
                    {Object.entries(diagnostics.statistics.by_severity || {}).map(([sev, cnt]) => (
                      <p key={sev} className="text-white/70">{sev}: <b className="text-white">{cnt as number}</b></p>
                    ))}
                  </div>
                </div>
                <div><p className="text-[10px] text-white/40">By Agent</p>
                  <div className="space-y-0.5 mt-1">
                    {Object.entries(diagnostics.statistics.by_agent || {}).map(([ag, cnt]) => (
                      <p key={ag} className="text-white/70">{ag}: <b className="text-white">{cnt as number}</b></p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* WHY THIS OUTPUT? */}
          <h3 className="text-[11px] uppercase tracking-widest text-white/40 mb-4">WHY THIS OUTPUT? (actual agent diagnoses)</h3>
          <div className="space-y-3">
            {Object.entries(diagnostics.diagnoses || {}).map(([agent, issues]) => {
              const arr: Diagnosis[] = Array.isArray(issues) ? issues : [];
              return (
                <div key={agent} className="rounded-xl bg-[#0f1020] border border-white/5 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <b className="text-[11px] text-[#7c6cf5]">{agent}</b>
                    <span className="text-[10px] text-white/40">{arr.length} issue(s)</span>
                  </div>
                  {arr.length === 0 ? (
                    <p className="text-xs text-[#4ade80]">No issue detected by this agent.</p>
                  ) : arr.map((issue, idx) => (
                    <div key={idx} className="mt-2 p-3 rounded bg-[#121317] border border-white/5">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded" style={{
                          color: issue.severity === 'critical' ? '#e0606e' : issue.severity === 'high' ? '#f0a500' : issue.severity === 'medium' ? '#7c6cf5' : '#4ade80',
                          background: issue.severity === 'critical' ? '#e0606e18' : issue.severity === 'high' ? '#f0a50018' : issue.severity === 'medium' ? '#7c6cf518' : '#4ade8018',
                          border: issue.severity === 'critical' ? '1px solid #e0606e40' : issue.severity === 'high' ? '1px solid #f0a50040' : issue.severity === 'medium' ? '1px solid #7c6cf540' : '1px solid #4ade8040',
                        }}>{issue.severity?.toUpperCase() || '?'}</span>
                        <b className="text-xs text-white">{issue.issue_name || '—'}</b>
                      </div>
                      <p className="text-[11px] text-white/60 mb-1">{issue.description || 'No description returned by backend.'}</p>
                      <div className="flex gap-4 text-[10px] text-white/40">
                        <span>Fields: {(issue.affected_fields || []).join(', ') || '—'}</span>
                        <span>Confidence: {issue.confidence != null ? `${(issue.confidence * 100).toFixed(1)}%` : '—'}</span>
                        <span>Suggested: {(issue.suggested_scenario_types || []).join(', ') || '—'}</span>
                      </div>
                    </div>
                  ))}
                </div>
              );
            })}
          </div>
          <p className="text-[9px] text-white/20 text-center mt-4">Source: /diagnostics · 5 agents · Model-estimated from synthetic data</p>
        </div>
      )}
    </div>
  );
}
