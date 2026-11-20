import type { ScenarioPayload, StudentTwinState } from '../types';

export interface InterpretedScenario {
  label: string;
  changes: string[];
  scenarios: ScenarioPayload[];
}

export const PARSE_HELP = 'Please clarify the routine change. Try: sleep 1 hour more and study 30 minutes less.';

export const EXPLORER_INTENTS = [
  'sleep_more',
  'study_less',
  'reduce_stress',
  'improve_recovery',
  'improve_study_consistency',
  'reduce_deadline_pressure',
  'reduce_workload',
] as const;

export type ScenarioIntent =
  | 'sleep_more'
  | 'sleep_less'
  | 'study_more'
  | 'study_less'
  | 'reduce_workload'
  | 'increase_workload'
  | 'reduce_stress'
  | 'improve_recovery'
  | 'improve_study_consistency'
  | 'reduce_deadline_pressure';

function clauseFor(text: string, word: string): string {
  const clauses = text.split(/\b(?:and|then|plus|also)\b|[,;]/).map((clause) => clause.trim());
  return clauses.find((clause) => clause.includes(word)) ?? text;
}

function hoursFromPhrase(text: string, word: string): number | null {
  const phrase = clauseFor(text, word);
  const hourMatch = phrase.match(new RegExp(`${word}[^.]*?(\\d+(?:\\.\\d+)?)\\s*(?:hour|hours|hr|hrs)`))
    ?? phrase.match(/(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs)/);
  if (hourMatch) return Number(hourMatch[1]);
  const minuteMatch = phrase.match(new RegExp(`${word}[^.]*?(\\d+(?:\\.\\d+)?)\\s*(?:minute|minutes|min|mins)`))
    ?? phrase.match(/(\d+(?:\.\d+)?)\s*(?:minute|minutes|min|mins)/);
  if (minuteMatch) return Number(minuteMatch[1]) / 60;
  return null;
}

function hasMoreIntent(text: string, word: string): boolean {
  const phrase = clauseFor(text, word);
  return new RegExp(`${word}[^.]*?(more|increase|extra|better)|(?:more|increase|extra|better)[^.]*?${word}`).test(phrase);
}

function hasLessIntent(text: string, word: string): boolean {
  const phrase = clauseFor(text, word);
  return new RegExp(`${word}[^.]*?(less|reduce|decrease|lower)|(?:less|reduce|decrease|lower)[^.]*?${word}`).test(phrase);
}

function currentSleep(twin: StudentTwinState): number {
  return twin.recovery.avg_sleep_hours_7d ?? 7;
}

export function scenarioFromPreset(intent: ScenarioIntent, twin: StudentTwinState, day: number): InterpretedScenario {
  const sleep = currentSleep(twin);
  const currentStudy = twin.behavioral.avg_study_hours_7d ?? 4;
  switch (intent) {
    case 'sleep_more':
      return {
        label: 'Sleep more',
        changes: [`Sleep target ${Math.min(12, sleep + 1).toFixed(1)} hours/night`],
        scenarios: [{ scenario_id: `intent_sleep_more_${day}`, scenario_type: 'INCREASE_SLEEP', description: 'Sleep more', parameters: { hours_per_night: Math.min(12, sleep + 1) } }],
      };
    case 'sleep_less':
      return {
        label: 'Sleep less',
        changes: [`Sleep target ${Math.max(0, sleep - 1).toFixed(1)} hours/night`],
        scenarios: [{ scenario_id: `intent_sleep_less_${day}`, scenario_type: 'INCREASE_SLEEP', description: 'Sleep less', parameters: { hours_per_night: Math.max(0, sleep - 1) } }],
      };
    case 'study_more':
      return {
        label: 'Study more',
        changes: ['Study +1.0 hour/day for 7 days'],
        scenarios: [{ scenario_id: `intent_study_more_${day}`, scenario_type: 'INCREASE_STUDY_TIME', description: 'Study more', parameters: { hours_per_day: 1, days: 7 } }],
      };
    case 'study_less':
      return {
        label: 'Study less',
        changes: ['Study -1.0 hour/day for 7 days'],
        scenarios: [{ scenario_id: `intent_study_less_${day}`, scenario_type: 'INCREASE_STUDY_TIME', description: 'Study less', parameters: { hours_per_day: -1, days: 7 } }],
      };
    case 'reduce_workload':
      return {
        label: 'Reduce workload',
        changes: ['Workload pressure -20%'],
        scenarios: [{ scenario_id: `intent_reduce_workload_${day}`, scenario_type: 'REDUCE_WORKLOAD', description: 'Reduce workload', parameters: { reduction_pct: 20 } }],
      };
    case 'increase_workload':
      return {
        label: 'Increase workload',
        changes: ['Workload pressure +20%'],
        scenarios: [{ scenario_id: `intent_increase_workload_${day}`, scenario_type: 'REDUCE_WORKLOAD', description: 'Increase workload', parameters: { reduction_pct: -20 } }],
      };
    case 'reduce_stress':
      return {
        label: 'Reduce stress',
        changes: ['Workload pressure -15% (existing counterfactual proxy)'],
        scenarios: [{ scenario_id: `intent_reduce_stress_${day}`, scenario_type: 'REDUCE_WORKLOAD', description: 'Reduce stress via lower workload pressure', parameters: { reduction_pct: 15 } }],
      };
    case 'improve_recovery':
      return {
        label: 'Improve recovery',
        changes: [`Sleep target ${Math.min(12, sleep + 1).toFixed(1)} hours/night`],
        scenarios: [{ scenario_id: `intent_improve_recovery_${day}`, scenario_type: 'INCREASE_SLEEP', description: 'Improve recovery', parameters: { hours_per_night: Math.min(12, sleep + 1) } }],
      };
    case 'improve_study_consistency':
      return {
        label: 'Improve study consistency',
        changes: [`Study +0.5 hour/day from current ${currentStudy.toFixed(1)} hours/day`],
        scenarios: [{ scenario_id: `intent_improve_consistency_${day}`, scenario_type: 'INCREASE_STUDY_TIME', description: 'Improve study consistency', parameters: { hours_per_day: 0.5, days: 7 } }],
      };
    case 'reduce_deadline_pressure':
      return {
        label: 'Reduce deadline pressure',
        changes: ['Spread deadlines to reduce density peaks'],
        scenarios: [{ scenario_id: `intent_reduce_deadlines_${day}`, scenario_type: 'REDUCE_DEADLINE_DENSITY', description: 'Reduce deadline pressure', parameters: {} }],
      };
  }
}

export function explorerScenarios(twin: StudentTwinState, day: number): InterpretedScenario[] {
  return EXPLORER_INTENTS.map((intent) => scenarioFromPreset(intent, twin, day));
}

export function parseNaturalLanguageScenario(text: string, twin: StudentTwinState, day: number): InterpretedScenario | null {
  const normalized = text.trim().toLowerCase();
  if (!normalized) return null;

  const scenarios: ScenarioPayload[] = [];
  const changes: string[] = [];
  const sleepTargetMatch = normalized.match(/sleep\s+(?:to|until)\s+(\d+(?:\.\d+)?)\s*(?:hour|hours|hr|hrs)?/);

  if (normalized.includes('sleep')) {
    if (sleepTargetMatch) {
      const target = Number(sleepTargetMatch[1]);
      if (Number.isFinite(target) && target >= 0 && target <= 12) {
        changes.push(`Sleep target ${target.toFixed(1)} hours/night`);
        scenarios.push({ scenario_id: `nl_sleep_target_${day}`, scenario_type: 'INCREASE_SLEEP', description: 'Natural-language sleep target', parameters: { hours_per_night: target } });
      }
    } else if (hasMoreIntent(normalized, 'sleep')) {
      const delta = hoursFromPhrase(normalized, 'sleep') ?? 1;
      const target = Math.min(12, currentSleep(twin) + delta);
      changes.push(`Sleep +${delta.toFixed(1)} hour/night`);
      scenarios.push({ scenario_id: `nl_sleep_more_${day}`, scenario_type: 'INCREASE_SLEEP', description: 'Natural-language sleep increase', parameters: { hours_per_night: target } });
    } else if (hasLessIntent(normalized, 'sleep')) {
      const delta = hoursFromPhrase(normalized, 'sleep') ?? 1;
      const target = Math.max(0, currentSleep(twin) - delta);
      changes.push(`Sleep -${delta.toFixed(1)} hour/night`);
      scenarios.push({ scenario_id: `nl_sleep_less_${day}`, scenario_type: 'INCREASE_SLEEP', description: 'Natural-language sleep decrease', parameters: { hours_per_night: target } });
    }
  }

  if (normalized.includes('study')) {
    if (hasMoreIntent(normalized, 'study')) {
      const delta = hoursFromPhrase(normalized, 'study') ?? 1;
      changes.push(`Study +${delta.toFixed(1)} hour/day`);
      scenarios.push({ scenario_id: `nl_study_more_${day}`, scenario_type: 'INCREASE_STUDY_TIME', description: 'Natural-language study increase', parameters: { hours_per_day: delta, days: 7 } });
    } else if (hasLessIntent(normalized, 'study')) {
      const delta = hoursFromPhrase(normalized, 'study') ?? 1;
      changes.push(`Study -${delta.toFixed(1)} hour/day`);
      scenarios.push({ scenario_id: `nl_study_less_${day}`, scenario_type: 'INCREASE_STUDY_TIME', description: 'Natural-language study decrease', parameters: { hours_per_day: -delta, days: 7 } });
    }
  }

  if (/(reduce|lower|less).*(deadline pressure|deadlines?)/.test(normalized)) {
    changes.push('Spread deadlines to reduce density peaks');
    scenarios.push({ scenario_id: `nl_reduce_deadlines_${day}`, scenario_type: 'REDUCE_DEADLINE_DENSITY', description: 'Natural-language deadline pressure reduction', parameters: {} });
  } else if (/(reduce|lower|less).*(workload|work load)/.test(normalized)) {
    changes.push('Workload pressure -20%');
    scenarios.push({ scenario_id: `nl_reduce_workload_${day}`, scenario_type: 'REDUCE_WORKLOAD', description: 'Natural-language workload reduction', parameters: { reduction_pct: 20 } });
  } else if (/(increase|more).*(workload|work load)/.test(normalized)) {
    changes.push('Workload pressure +20%');
    scenarios.push({ scenario_id: `nl_increase_workload_${day}`, scenario_type: 'REDUCE_WORKLOAD', description: 'Natural-language workload increase', parameters: { reduction_pct: -20 } });
  }

  if (/(reduce|lower).*(stress)/.test(normalized)) {
    changes.push('Workload pressure -15% (existing counterfactual proxy)');
    scenarios.push({ scenario_id: `nl_reduce_stress_${day}`, scenario_type: 'REDUCE_WORKLOAD', description: 'Natural-language stress reduction proxy', parameters: { reduction_pct: 15 } });
  }

  if (/(better|improve|increase).*(recovery|recover)/.test(normalized)) {
    const target = Math.min(12, currentSleep(twin) + 1);
    changes.push(`Sleep target ${target.toFixed(1)} hours/night`);
    scenarios.push({ scenario_id: `nl_improve_recovery_${day}`, scenario_type: 'INCREASE_SLEEP', description: 'Natural-language recovery improvement', parameters: { hours_per_night: target } });
  }

  if (/(improve|better|increase).*(study consistency|consistency)/.test(normalized)) {
    changes.push('Study +0.5 hour/day for consistency');
    scenarios.push({ scenario_id: `nl_improve_consistency_${day}`, scenario_type: 'INCREASE_STUDY_TIME', description: 'Natural-language study consistency improvement', parameters: { hours_per_day: 0.5, days: 7 } });
  }

  if (scenarios.length === 0) return null;
  return {
    label: 'Natural-language scenario',
    changes,
    scenarios,
  };
}
