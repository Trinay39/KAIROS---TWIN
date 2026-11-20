# Limitations And Future Work

## Genuine Limitations

- The training and evaluation data are synthetic. Real-world longitudinal student data is not included.
- Some session-level features are unavailable from the current simulator and are represented by defaults or compatibility constants to preserve the frozen 46-feature production contract.
- The model is not calibrated; production metadata reports `calibrated=false`.
- What-if scenarios are model-estimated projections, not causal intervention effects.
- The intervention registry and outcome tracker use prototype JSON persistence, not a production database.
- Outcome tracking compares predicted and follow-up risk estimates, but this prototype cannot prove that the intervention caused observed changes.
- The deterministic demo histories in `api/demo_data.py` are UI/demo histories and should not be confused with the original 200-student training simulation.
- Frontend tests pass but Recharts emits jsdom zero-size chart warnings.
- Production build passes but the main JS chunk is above Vite's default 500 kB warning threshold.

## Not Failures

These constraints are normal for an academic prototype:

- Synthetic data is appropriate for validating architecture, temporal leakage controls, and workflow integration.
- A frozen feature contract is useful for artifact integrity even when some fields are unavailable.
- Uncalibrated probabilities can still support relative prototype exploration when clearly labeled as estimates.

## Future Work

- Validate the full pipeline on consented real-world longitudinal student data.
- Add richer session-level data for break rate, distraction rate, focus quality, procrastination, confidence, and assignment effort.
- Calibrate production probabilities and document calibration curves.
- Add causal evaluation or randomized/pilot intervention study design before making causal claims.
- Move prototype JSON persistence to a database with audit trails and access control.
- Expand outcome tracking to compare specific observed state changes, not only follow-up risk.
- Add code splitting to reduce the frontend production chunk size.
- Add browser-level end-to-end tests for the full student/faculty workflow.
