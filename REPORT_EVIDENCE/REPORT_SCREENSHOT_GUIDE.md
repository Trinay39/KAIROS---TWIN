# Report Screenshot Guide

Capture screenshots from the actual running application after starting the backend and frontend.

## Suggested Screenshots

1. Command Center
   - Demonstrates the integrated workflow: selected student/day, input state, risk, diagnostics, scenario and recommendation actions.

2. Student Input
   - Demonstrates the observation fields used to compute a twin state: study, sleep, stress, grade, attendance, and deadline status.

3. Digital Twin
   - Demonstrates structured `StudentTwinState` sections: academic, behavioral, recovery, workload, engagement, temporal, history, and provenance/state metadata.

4. Risk Prediction
   - Demonstrates model-estimated overload probability, threshold interpretation, and risk language.

5. Diagnostics
   - Demonstrates specialized agent output and the bridge from twin state to intervention reasoning.

6. Scenario Explorer
   - Demonstrates preset what-if options such as sleep, study, workload, deadline pressure, recovery, and consistency.

7. Natural-Language What-If
   - Demonstrates the parser with text such as "sleep 1 hour more and study 30 minutes less."

8. Counterfactual Result
   - Demonstrates baseline risk, counterfactual risk, risk delta, risk reduction percentage, and changed features.

9. Recommendations
   - Demonstrates model-estimated recommendation text, confidence, caveats, and scenario details.

10. Intervention
   - Demonstrates response logging with canonical choices: accepted, rejected, deferred, ask_more.

11. Student History Charts
   - Demonstrates longitudinal history for study, sleep, stress, grades, attendance, and related observations.

12. Faculty View
   - Demonstrates aggregate analytics, current student risk/state summary, intervention records, and follow-up monitoring.

13. API/Model Status
   - Optional screenshot of `/health` or model metadata in a browser/API client showing model loaded and production model available. Do not expose API keys or `.env` values.

## Capture Notes

- Use demo students with deterministic histories so screenshots are repeatable.
- Avoid showing secrets, terminal history with tokens, or `.env` files.
- Include at least one screenshot where baseline and counterfactual risk are both visible.
- Include at least one screenshot showing the synthetic-data/model-estimate caveat.
