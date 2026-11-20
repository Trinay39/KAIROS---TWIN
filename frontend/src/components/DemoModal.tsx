import { X } from 'lucide-react';
import { useDemo, presets } from '../context/DemoContext';

const DEMOS = [
  {
    key: 'BALANCED',
    label: 'Stable Student',
    description: 'Balanced workload, healthy recovery, consistent study patterns. Baseline demonstration of a thriving student.',
    tags: ['low-risk', 'reference'],
    color: '#4ade80',
  },
  {
    key: 'DEADLINE_CRUNCH',
    label: 'Deadline Overload',
    description: 'High deadline density in the next 7 days, declining study consistency, rising stress indicators.',
    tags: ['high-risk', 'workload'],
    color: '#f0a500',
  },
  {
    key: 'RECOVERY',
    label: 'Recovery Collapse',
    description: 'Severe sleep deficit, low recovery score, high workload pressure. Multiple compounding stressors.',
    tags: ['critical-risk', 'recovery'],
    color: '#e0606e',
  },
  {
    key: 'ACADEMIC_PRESSURE',
    label: 'Emerging Overload',
    description: 'Early warning signals emerging: workload uptick, academic decline beginning, stress growth trend.',
    tags: ['moderate-risk', 'early-warning'],
    color: '#00bfa5',
  },
];

export default function DemoModal({ onClose }: { onClose: () => void }) {
  const { activePreset, applyScenario } = useDemo();

  function handleSelect(key: string) {
    applyScenario(key as keyof typeof presets);
    onClose();
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.75)', backdropFilter: 'blur(4px)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="w-[560px] bg-[#181921] rounded-xl border border-white/10 overflow-hidden"
        style={{ boxShadow: '0 24px 80px rgba(0,0,0,0.6)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/5">
          <div>
            <h2 className="text-sm font-semibold text-white">Select Demo Scenario</h2>
            <p className="text-[11px] text-white/40 mt-0.5">All data is synthetic — research prototype only</p>
          </div>
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white/70 transition-colors p-1"
            aria-label="Close"
          >
            <X size={18} />
          </button>
        </div>

        {/* Options */}
        <div className="p-4 space-y-2 max-h-[360px] overflow-auto">
          {DEMOS.map((d) => (
            <button
              key={d.key}
              onClick={() => handleSelect(d.key)}
              className={`w-full text-left p-4 rounded-lg border transition-all duration-150 ${
                activePreset === d.key
                  ? 'border-[#00bfa5]/50 bg-[#00bfa5]/5'
                  : 'border-white/8 hover:border-white/15 bg-white/[0.03]'
              }`}
            >
              <div className="flex items-start gap-3">
                <span
                  className="inline-block w-2 h-2 rounded-full mt-1.5 shrink-0"
                  style={{ background: d.color }}
                />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white">{d.label}</span>
                    {activePreset === d.key && (
                      <span className="text-[10px] font-medium text-[#00bfa5] bg-[#00bfa5]/15 px-1.5 py-0.5 rounded">
                        ACTIVE
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-white/45 mt-1 leading-relaxed">{d.description}</p>
                  <div className="flex gap-1.5 mt-2">
                    {d.tags.map((tag) => (
                      <span key={tag} className="text-[10px] text-white/30 bg-white/5 px-1.5 py-0.5 rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="px-6 py-3 border-t border-white/5 bg-[#0f1115]">
          <p className="text-[10px] text-white/25 text-center">
            This is a research prototype using synthetic data. Results are model-estimated, not real-world predictions.
          </p>
        </div>
      </div>
    </div>
  );
}
