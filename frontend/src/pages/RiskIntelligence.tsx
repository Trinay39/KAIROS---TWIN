
import { useDemo } from '../context/DemoContext';
import { isFailureStatus } from '../types';

export default function RiskIntelligence() {
  const { state, predictRisk } = useDemo();
  const { input, twin, prediction, status, error } = state;

  const prob = prediction?.overload_probability ?? null;
  const probPct = prob != null ? `${(prob * 100).toFixed(2)}` : null;
  const level = prob != null ? (prob >= 0.75 ? 'CRITICAL' : prob >= 0.5 ? 'HIGH' : prob >= 0.3 ? 'MODERATE' : 'LOW') : null;
  const color = prob != null ? (prob >= 0.75 ? '#e0606e' : prob >= 0.5 ? '#f0a500' : prob >= 0.3 ? '#7c6cf5' : '#4ade80') : '#4ade80';

  return (
    <div className="max-w-5xl mx-auto space-y-5 animate-fade-up">
      <header>
        <h1 className="text-xl font-display font-semibold tracking-tight text-white">Risk Intelligence</h1>
        <p className="text-xs text-white/35 mt-0.5">RF PredictionService · /predictions · Synthetic data · Research prototype</p>
      </header>

      {/* INPUT USED */}
      <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5">
        <h3 className="text-[10px] font-bold text-[#00bfa5] mb-2">INPUT USED FOR PREDICTION</h3>
        <div className="grid grid-cols-4 gap-2 text-[10px] text-white/60">
          <span>Student: <b className="text-white">{input.student_id}</b></span>
          <span>Day: <b className="text-white">{input.day}</b></span>
          <span>Study: <b className="text-white">{input.study_hours} hrs/day</b></span>
          <span>Sleep: <b className="text-white">{input.sleep_hours} hrs/night</b></span>
          <span>Stress: <b className="text-white">{input.stress_level}/10</b></span>
          <span>Grade: <b className="text-white">{input.grade}/100</b></span>
          <span>Attendance: <b className="text-white">{Math.round(input.attendance_rate*100)}%</b></span>
          <span>Missed: <b className="text-white">{input.missed_deadline_observed ? 'Yes' : 'No'}</b></span>
        </div>
      </div>

      {status.twin !== 'done' && (
        <div className="rounded-xl p-4 bg-[#7c6cf5]/10 border border-[#7c6cf5]/20 text-xs text-[#7c6cf5]">
          Compute a twin first on the Command Center page.
        </div>
      )}

      <button onClick={predictRisk} disabled={!twin || status.risk === 'loading'} className="px-4 py-2 rounded-lg bg-[#f0a500]/10 text-[#f0a500] text-sm border border-[#f0a500]/20 hover:bg-[#f0a500]/20 disabled:opacity-30">
        {status.risk === 'loading' ? 'Predicting…' : prediction ? 'RE-PREDICT RISK' : '[ PREDICT 7-DAY OVERLOAD RISK ]'}
      </button>

      {isFailureStatus(status.risk) && (
        <div className="rounded-xl p-3 bg-[#e0606e]/10 border border-[#e0606e]/30 text-xs text-[#e0606e]">
          {error || 'Prediction service is unavailable.'}
        </div>
      )}

      {prediction && (
        <div className="rounded-2xl p-8 bg-[#181921] border border-white/10">
          <div className="rounded-xl p-6 bg-gradient-to-r from-[#f0a500]/10 to-transparent border border-[#f0a500]/20 mb-6 text-center">
            <p className="text-[10px] text-white/40 uppercase tracking-wider mb-2">7-Day Overload Probability</p>
            <p className="text-6xl font-display font-bold" style={{ color }}>{probPct}%</p>
            <span className="inline-block text-xs font-bold px-3 py-1 rounded mt-2" style={{ color, background: `${color}18`, border: `1px solid ${color}30` }}>{level}</span>
          </div>
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="rounded bg-[#0f1020] border border-white/5 p-4">
              <p className="text-[10px] text-white/40 mb-2">MODEL OUTPUT</p>
              <div className="space-y-1 text-white/70">
                <p>overload_probability: <b className="text-white">{prob?.toFixed(6)}</b></p>
                <p>overload_prediction: <b className="text-white">{String(prediction.overload_prediction ?? '—')}</b></p>
                <p>strain_index: <b className="text-white">{prediction.strain_index ?? '—'}</b></p>
              </div>
            </div>
            <div className="rounded bg-[#0f1020] border border-white/5 p-4">
              <p className="text-[10px] text-white/40 mb-2">WHY THIS OUTPUT?</p>
              <div className="space-y-1 text-white/70">
                <p>Source: <b className="text-white">/predictions</b></p>
                <p>Model: <b className="text-white">Random Forest</b></p>
                <p>Based on: <b className="text-white">TwinEngine state</b></p>
              </div>
            </div>
          </div>
          <div className="mt-4 p-3 rounded-lg bg-[#f0a500]/8 border border-[#f0a500]/20">
            <p className="text-[11px] text-white/60">⚠ Model-estimated from synthetic observations via RF PredictionService. Not clinical. Based on current student twin state.</p>
          </div>
        </div>
      )}

      {!prediction && status.risk !== 'loading' && status.twin === 'done' && (
        <p className="text-xs text-white/30">Press [ PREDICT 7-DAY OVERLOAD RISK ] to call /predictions.</p>
      )}
    </div>
  );
}
