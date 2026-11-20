import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useDemo } from '../context/DemoContext';

export default function DemoBanner() {
  const { state } = useDemo();
  const { input } = state;
  const [visible, setVisible] = useState(true);
  if (!visible) return null;
  return (
    <div className="sticky top-0 z-50 bg-[#181921]/95 backdrop-blur border-b border-white/10 px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-4 text-xs">
        <span className="font-bold text-[#00bfa5]">DEMO MODE</span>
        <span className="text-white/60">{input.student_id} · Day {input.day}</span>
        <span className="text-white/30">study={input.study_hours} · sleep={input.sleep_hours} · stress={input.stress_level} · grade={input.grade} · attend={input.attendance_rate} · missed={input.missed_deadline_observed}</span>
      </div>
      <div className="flex items-center gap-3 text-[10px] text-white/40">
        <Link to="/" className="hover:text-white">1. Input</Link>
        <span>→</span><Link to="/twin" className="hover:text-white">2. Twin</Link>
        <span>→</span><Link to="/risk" className="hover:text-white">3. Risk</Link>
        <span>→</span><Link to="/agents" className="hover:text-white">4. Diagnose</Link>
        <span>→</span><Link to="/whatif" className="hover:text-white">5. What-If</Link>
        <span>→</span><Link to="/recommend" className="hover:text-white">6. Recommend</Link>
        <span>→</span><Link to="/faculty" className="hover:text-white">7. Faculty</Link>
      </div>
      <button onClick={() => setVisible(false)} className="text-[10px] text-white/30 hover:text-white">Hide</button>
    </div>
  );
}
