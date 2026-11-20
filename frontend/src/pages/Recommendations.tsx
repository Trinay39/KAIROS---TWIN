import { Link } from 'react-router-dom';
import { useDemo } from '../context/DemoContext';
import { isFailureStatus } from '../types';

export default function Recommendations() {
  const { state, generateRec, generateMoreRec, recordDecision, recordFollowup } = useDemo();
  const {
    input,
    twin,
    rec,
    recommendations,
    recommendationMessage,
    status,
    error,
    interventionId,
    followup,
    decision: studentDecision,
  } = state;
  const displayedRecommendations = recommendations.length ? recommendations : (rec ? [rec] : []);

  return (
    <div className="max-w-5xl mx-auto space-y-5 animate-fade-up">
      <div className="rounded-2xl p-8 bg-gradient-to-br from-[#181921] to-[#121317] border border-white/10">
        <div className="flex items-center gap-2 mb-1"><span className="text-[10px] uppercase tracking-widest text-[#7c6cf5] font-medium">KAIROS-TWIN</span><span className="text-white/20">/</span><span className="text-[10px] uppercase tracking-widest text-white/30">Recommendations</span></div>
        <h1 className="text-3xl font-display font-bold tracking-tight text-white">Recommendations</h1>
        <p className="text-sm text-white/40 mt-1">Recommendations connect current Twin signals to model-tested scenarios and intervention decisions.</p>
      </div>

      <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5">
        <h3 className="text-[10px] font-bold text-[#00bfa5] mb-2">INPUT USED</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-[10px] text-white/60">
          <span>Student: <b className="text-white">{input.student_id}</b></span>
          <span>Day: <b className="text-white">{input.day}</b></span>
          <span>Study: <b className="text-white">{input.study_hours} hrs/day</b></span>
          <span>Sleep: <b className="text-white">{input.sleep_hours} hrs/night</b></span>
          <span>Stress: <b className="text-white">{input.stress_level}/10</b></span>
          <span>Grade: <b className="text-white">{input.grade}/100</b></span>
          <span>Attend: <b className="text-white">{Math.round(input.attendance_rate * 100)}%</b></span>
          <span>Missed: <b className="text-white">{input.missed_deadline_observed ? 'Yes' : 'No'}</b></span>
        </div>
      </div>

      <div className="rounded-xl p-5 bg-[#181921] border border-white/10 flex items-center justify-between gap-4">
        <div><h2 className="text-xs font-medium text-white/50 uppercase tracking-wider">Recommendation Engine</h2><p className="text-[10px] text-white/30">Calls /recommendations/generate with the current twin state</p></div>
        <button onClick={generateRec} disabled={!twin || status.rec === 'loading'} className="px-4 py-2 rounded-lg bg-[#7c6cf5]/10 text-[#7c6cf5] text-xs font-medium border border-[#7c6cf5]/20 hover:bg-[#7c6cf5]/20 disabled:opacity-40 disabled:cursor-not-allowed">
          {status.rec === 'loading' ? 'Generating...' : rec ? 'Re-generate' : 'Generate recommendations'}
        </button>
      </div>

      {isFailureStatus(status.rec) && (
        <div className="rounded-xl p-3 bg-[#e0606e]/10 border border-[#e0606e]/30 text-xs text-[#e0606e]">{error || 'Recommendation failed. Make sure twin has been computed.'}</div>
      )}

      {!twin && (
        <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-xs text-white/30">Compute twin first on the Digital Twin or Command Center page.</div>
      )}

      {rec && (
        <div className="rounded-2xl p-6 bg-[#181921] border border-white/10">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h3 className="text-[11px] uppercase tracking-widest text-white/40">Recommendations From Backend</h3>
            <button onClick={generateMoreRec} disabled={!twin || status.rec === 'loading'} className="px-3 py-1.5 rounded-lg bg-white/5 text-white/70 text-xs border border-white/10 hover:bg-white/10 disabled:opacity-40">
              {status.rec === 'loading' ? 'Loading...' : 'More'}
            </button>
          </div>

          {recommendationMessage && <p className="mb-3 text-[10px] text-[#f0a500]">{recommendationMessage}</p>}

          <div className="space-y-3 mb-4">
            {displayedRecommendations.map((item) => (
              <div key={item.scenario_id} className="rounded-xl bg-[#0f1020] border border-white/5 p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-white/70">
                  <div><b className="text-white">Current issue/signal</b><br />{item.primary_diagnoses?.join(', ') || 'No primary diagnosis returned'}</div>
                  <div><b className="text-white">Suggested action</b><br />{item.scenario_description || item.scenario_type}</div>
                  <div><b className="text-white">Scenario projection</b><br />{item.risk_reduction_percentage != null ? `Estimated relative reduction ${Math.round(item.risk_reduction_percentage)}%` : 'Unavailable'}</div>
                </div>
                <p className="mt-3 text-xs leading-relaxed text-white/55">{item.explanation || 'No rationale returned by backend.'}</p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <Link to="/whatif" className="px-3 py-1.5 rounded-lg bg-[#7c6cf5]/10 text-[#7c6cf5] text-[11px] border border-[#7c6cf5]/20 hover:bg-[#7c6cf5]/20">
                    Explore related scenario
                  </Link>
                  <span className="text-[10px] text-white/35">Scenario ID: {item.scenario_id} / Student: {item.student_id} / Day {item.day}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-xl bg-[#0f1020] border border-white/5 p-4">
            <p className="text-[10px] text-white/40 mb-2">CURRENT SELECTION RATIONALE</p>
            <p className="text-xs leading-relaxed text-white/70">{rec.explanation || 'No rationale returned by backend.'}</p>
            <div className="mt-3 flex flex-wrap gap-3 text-[11px] text-white/45">
              <span>Confidence: <b className="text-white/75">{rec.confidence}</b></span>
              <span>Baseline risk: <b className="text-white/75">{Math.round(rec.baseline_risk * 100)}%</b></span>
              <span>Scenario projection: <b className="text-[#4ade80]">{Math.round(rec.counterfactual_risk * 100)}%</b></span>
            </div>
            {rec.caveats?.length ? <p className="mt-2 text-[10px] text-[#f0a500]">Caveats: {rec.caveats.join(' / ')}</p> : null}
          </div>

          <div className="mt-4 rounded-xl bg-[#0f1020] border border-white/5 p-4">
            <p className="text-[10px] text-white/40 mb-2">INTERVENTION DECISION</p>
            <div className="flex flex-wrap gap-2">
              {(['accepted', 'rejected', 'deferred', 'ask_more'] as const).map((decision) => (
                <button key={decision} onClick={() => recordDecision(decision)} disabled={status.decision === 'loading' || status.decision === 'done'} className="px-3 py-1.5 rounded-lg bg-white/5 text-white/70 text-xs border border-white/10 hover:bg-white/10 disabled:opacity-40">
                  {decision}
                </button>
              ))}
            </div>
            {status.decision === 'done' && studentDecision !== 'accepted' && (
              <p className="mt-2 text-[10px] text-white/35">Decision logged: {interventionId}. Follow-up outcome recording is available after an accepted intervention.</p>
            )}
            {status.decision === 'done' && studentDecision === 'accepted' && (
              <div className="mt-3 flex items-center justify-between gap-3 rounded-lg border border-[#00bfa5]/20 bg-[#00bfa5]/8 p-3">
                <p className="text-[10px] text-[#00bfa5]">Decision logged: {interventionId}</p>
                <button onClick={recordFollowup} disabled={status.followup === 'loading' || status.followup === 'done'} className="px-3 py-1.5 rounded-lg bg-[#00bfa5]/10 text-[#00bfa5] text-xs border border-[#00bfa5]/20 hover:bg-[#00bfa5]/20 disabled:opacity-40">
                  {status.followup === 'loading' ? 'Recording...' : 'Record follow-up'}
                </button>
              </div>
            )}
            {isFailureStatus(status.decision) && <p className="mt-2 text-[10px] text-[#e0606e]">{error || 'Decision could not be recorded.'}</p>}
            {status.followup === 'done' && followup && (
              <p className="mt-2 text-[10px] text-white/50">Follow-up outcome recorded: <b className="text-white">{followup.outcome_id}</b> / estimated risk {Math.round(followup.report.actual_risk_at_day7 * 100)}%</p>
            )}
            {isFailureStatus(status.followup) && <p className="mt-2 text-[10px] text-[#e0606e]">{error || 'Follow-up could not be recorded.'}</p>}
          </div>

          <div className="mt-4 p-3 rounded bg-[#f0a500]/8 border border-[#f0a500]/20 text-xs text-white/60">
            Additional recommendations are requested from the backend for the same student and current twin state, then deduplicated by scenario ID.
          </div>
        </div>
      )}

      {!rec && twin && status.rec !== 'loading' && (
        <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5 text-xs text-white/30">Twin is ready. Generate recommendations above.</div>
      )}
    </div>
  );
}
