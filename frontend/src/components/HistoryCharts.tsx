import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { StudentHistoryObservation } from '../types';

interface ChartLine {
  key: keyof StudentHistoryObservation;
  label: string;
  color: string;
}

interface HistoryChartProps {
  title: string;
  subtitle: string;
  observations: StudentHistoryObservation[];
  lines: ChartLine[];
  domain?: [number, number];
}

function hasValue(observation: StudentHistoryObservation, key: keyof StudentHistoryObservation) {
  return typeof observation[key] === 'number';
}

export function HistoryChart({ title, subtitle, observations, lines, domain }: HistoryChartProps) {
  const visibleLines = lines.filter((line) => observations.some((observation) => hasValue(observation, line.key)));

  return (
    <section className="rounded-xl p-4 bg-[#181921] border border-white/10">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h3 className="text-[11px] uppercase tracking-widest text-white/50">{title}</h3>
          <p className="text-[10px] text-white/30 mt-1">{subtitle}</p>
        </div>
        <span className="text-[10px] text-white/25">Days {observations[0]?.day ?? '-'}-{observations[observations.length - 1]?.day ?? '-'}</span>
      </div>

      {observations.length < 2 || visibleLines.length === 0 ? (
        <div className="h-[220px] flex items-center justify-center rounded-lg bg-[#0f1020] border border-white/5 text-xs text-white/30">
          Insufficient historical observations
        </div>
      ) : (
        <div className="h-[220px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={observations} margin={{ top: 10, right: 18, bottom: 8, left: 0 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
              <XAxis dataKey="day" tick={{ fill: '#7b8191', fontSize: 10 }} axisLine={{ stroke: 'rgba(255,255,255,0.12)' }} tickLine={false} label={{ value: 'Day', fill: '#7b8191', fontSize: 10, position: 'insideBottom', offset: -4 }} />
              <YAxis domain={domain ?? ['auto', 'auto']} tick={{ fill: '#7b8191', fontSize: 10 }} axisLine={false} tickLine={false} width={34} />
              <Tooltip
                formatter={(value, name) => [typeof value === 'number' ? value.toFixed(2) : value, name]}
                labelFormatter={(label) => `Day ${label}`}
                contentStyle={{ background: '#111217', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 8, color: '#f8fafc', fontSize: 12 }}
                labelStyle={{ color: '#a0a3b0' }}
              />
              <Legend wrapperStyle={{ color: '#a0a3b0', fontSize: 11 }} />
              {visibleLines.map((line) => (
                <Line
                  key={String(line.key)}
                  type="monotone"
                  dataKey={line.key}
                  name={line.label}
                  stroke={line.color}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  connectNulls
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}

export function HistoryCharts({ observations }: { observations: StudentHistoryObservation[] }) {
  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <HistoryChart
        title="Behavioral Trajectory"
        subtitle="Observed study hours/day and sleep hours/night"
        observations={observations}
        domain={[0, 12]}
        lines={[
          { key: 'study_hours', label: 'Study Hours', color: '#7c6cf5' },
          { key: 'sleep_hours', label: 'Sleep Hours', color: '#00bfa5' },
        ]}
      />
      <HistoryChart
        title="Recovery & Stress"
        subtitle="Observed stress level and sleep recovery proxy"
        observations={observations}
        domain={[0, 10]}
        lines={[
          { key: 'stress_level', label: 'Stress', color: '#e0606e' },
          { key: 'sleep_hours', label: 'Sleep', color: '#4ade80' },
        ]}
      />
      <HistoryChart
        title="Academic Pressure"
        subtitle="Observed workload pressure and upcoming deadline density"
        observations={observations}
        domain={[0, 10]}
        lines={[
          { key: 'workload_pressure', label: 'Workload Pressure', color: '#f0a500' },
          { key: 'upcoming_deadlines_7d', label: 'Deadline Pressure', color: '#7c6cf5' },
        ]}
      />
      <HistoryChart
        title="Engagement & Attendance"
        subtitle="Observed engagement score and attendance rate"
        observations={observations}
        domain={[0, 1]}
        lines={[
          { key: 'engagement_score', label: 'Engagement', color: '#00bfa5' },
          { key: 'attendance_rate', label: 'Attendance', color: '#4ade80' },
        ]}
      />
    </div>
  );
}
