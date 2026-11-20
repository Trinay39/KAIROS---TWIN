# Frontend Modules

Source root: `frontend/src`.

## App And Layout

- `App.tsx`: route setup for the application pages.
- `layouts/Layout.tsx`: main shell.
- `components/Sidebar.tsx`: navigation.
- `components/TopBar.tsx`: page header/status area.
- `components/DemoBanner.tsx`: demo mode/status banner.
- `components/DemoModal.tsx`: demo selection/help modal.

## State And API

- `context/DemoContext.tsx`: central demo workflow state, selected student/day/input state, twin/prediction/diagnostic/scenario/recommendation/history loading.
- `api/client.ts`: API request client and error mapping.
- `api/endpoints.ts`: endpoint helper functions.
- `types/index.ts`: frontend TypeScript types matching backend payloads.
- `hooks/useDemoStudent.ts`: demo student helper.
- `hooks/useLiveIntegration.ts`: live backend integration status.

## Pages

- `pages/CommandCenter.tsx`: integrated command view for student input, risk, diagnostics, agent status, scenario/recommendation controls.
- `pages/DigitalTwin.tsx`: twin computation and display of state sections.
- `pages/RiskIntelligence.tsx`: overload probability and risk/diagnostic presentation.
- `pages/WhatIfLab.tsx`: scenario explorer, natural-language what-if input, simulation results.
- `pages/Recommendations.tsx`: recommendation generation, presentation, and intervention response workflow.
- `pages/AgentControl.tsx`: specialized agent status/diagnostic view.
- `pages/FacultyView.tsx`: faculty monitoring, analytics, current risk/state summary, history/intervention records.
- `pages/StudentHistory.tsx`: selected-day observation history and charts.

## Reusable Components

- `components/StudentInputPanel.tsx`: student/day/observation input controls.
- `components/HistoryCharts.tsx`: Recharts visualizations for study, sleep, stress, grades, and related history.

## Scenario Parser

- `utils/scenarioIntent.ts`: preset scenario explorer intents and natural-language parser for sleep, study, workload, deadline pressure, stress proxy, recovery, and study consistency.

## Frontend Tests

Frontend tests exist for API helpers, DemoContext, Faculty View, Student History, What-If Lab, and scenario intent parsing. Latest run: 7 test files, 30 tests passed.
