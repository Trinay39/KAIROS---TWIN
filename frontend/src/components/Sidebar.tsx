import { NavLink } from 'react-router-dom';
import { Clock, Cpu, FlaskConical, Hexagon, LayoutDashboard, ShieldAlert, Users } from 'lucide-react';

const nav = [
  { to: '/', icon: LayoutDashboard, label: 'Command Center', exact: true },
  { to: '/twin', icon: Hexagon, label: 'Digital Twin' },
  { to: '/risk', icon: ShieldAlert, label: 'Risk Intelligence' },
  { to: '/whatif', icon: FlaskConical, label: 'What-If Lab' },
  { to: '/agents', icon: Cpu, label: 'Agent Control' },
  { to: '/history', icon: Clock, label: 'Student History' },
  { to: '/faculty', icon: Users, label: 'Faculty View' },
];

export default function Sidebar() {
  return (
    <aside className="w-60 flex flex-col bg-[#0f1014] border-r border-white/[0.06] shrink-0 shadow-[4px_0_30px_rgba(0,0,0,0.3)]">
      {/* Logo */}
      <div className="px-5 pt-5 pb-4">
        <div className="flex items-center gap-2">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 2L2 7l10 5 10-5-10-5z" fill="none" stroke="#00bfa5" strokeWidth="1.5"/>
            <path d="M2 17l10 5 10-5" fill="none" stroke="#00bfa5" strokeWidth="1.5"/>
            <path d="M2 12l10 5 10-5" fill="none" stroke="#00bfa5" strokeWidth="1.5"/>
          </svg>
          <span className="font-display text-sm font-semibold tracking-widest uppercase text-white">
            KAIROS-TWIN
          </span>
        </div>
        <p className="mt-1 text-[10px] text-white/30 tracking-wide uppercase">
          Closed-Loop Predictive Twin
        </p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-2 space-y-0.5" aria-label="Main navigation">
        {nav.map(({ to, icon: Icon, label, exact }) => (
          <NavLink
            key={to}
            to={to}
            end={exact}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors duration-150 ${
                isActive
                  ? 'bg-white/8 text-white'
                  : 'text-white/50 hover:text-white/75 hover:bg-white/4'
              }`
            }
          >
            <Icon size={16} strokeWidth={1.75} className="shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Status handoff */}
      <div className="px-4 py-4 border-t border-white/5 space-y-2">
        <p className="text-[10px] uppercase tracking-widest text-white/25 mb-3">
          Serving Status
        </p>
        <p className="text-[11px] leading-relaxed text-white/35">
          Live API and production model status are shown in the header when the backend is reachable.
        </p>
      </div>
    </aside>
  );
}
