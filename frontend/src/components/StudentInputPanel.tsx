import { useDemo } from '../context/DemoContext';

interface Props {
  /** Show twin computation status */
  showTwinStatus?: boolean;
  /** Extra column count for custom fields */
  cols?: number;
}

export default function StudentInputPanel({ showTwinStatus = false, cols = 4 }: Props) {
  const { state } = useDemo();
  const { input, twin } = state;

  const gridClass = {
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
    5: 'grid-cols-5',
    8: 'grid-cols-8',
  }[cols] ?? 'grid-cols-4';

  return (
    <div className="rounded-xl p-4 bg-[#0f1020] border border-white/5">
      <h3 className="text-[10px] font-bold text-[#00bfa5] mb-2">CURRENT INPUT USED</h3>
      <div className={`grid ${gridClass} gap-2 text-[10px] text-white/60`}>
        <span>Student: <b className="text-white">{input.student_id}</b></span>
        <span>Day: <b className="text-white">{input.day}/90</b></span>
        <span>Study: <b className="text-white">{input.study_hours} hrs/day</b></span>
        <span>Sleep: <b className="text-white">{input.sleep_hours} hrs/night</b></span>
        <span>Stress: <b className="text-white">{input.stress_level}/10</b></span>
        <span>Grade: <b className="text-white">{input.grade}/100</b></span>
        <span>Attend: <b className="text-white">{Math.round(input.attendance_rate * 100)}%</b></span>
        <span>Missed: <b className="text-white">{input.missed_deadline_observed ? 'Yes' : 'No'}</b></span>
        {showTwinStatus && (
          <span>Twin: <b className="text-white">{twin ? 'Computed' : 'Not yet'}</b></span>
        )}
      </div>
    </div>
  );
}
