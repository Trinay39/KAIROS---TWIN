import { useCallback } from 'react';
import { presets, useDemo } from '../context/DemoContext';

const scenarios = [
  { key: 'BALANCED', label: 'Stable Student', description: 'Balanced workload, healthy recovery, low risk trajectory.' },
  { key: 'DEADLINE_CRUNCH', label: 'Deadline Overload', description: 'High deadline density, declining study consistency, rising stress.' },
  { key: 'RECOVERY', label: 'Recovery Collapse', description: 'Sleep deficit, low recovery score, high workload pressure.' },
  { key: 'ACADEMIC_PRESSURE', label: 'Emerging Overload', description: 'Early warning signals: workload uptick, academic decline, stress growth.' },
];

export function useDemoStudent() {
  const { activePreset, applyScenario } = useDemo();

  const load = useCallback((key: string) => {
    if (key in presets) applyScenario(key as keyof typeof presets);
  }, [applyScenario]);

  return { demo: activePreset, load, scenarios };
}
