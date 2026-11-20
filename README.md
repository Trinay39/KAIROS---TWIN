# KAIROS-TWIN

**An academic overload early-warning and intervention research prototype.**

KAIROS-TWIN combines a longitudinal student digital twin, a frozen machine-learning model, scenario simulation, and intervention follow-up in one workflow. It estimates short-term academic overload risk from observations available up to the selected day, explains relevant student-state signals, and lets users compare hypothetical changes against a baseline.

> **Research prototype:** The included student records are synthetic. Model outputs and recommendations are for research and demonstration; they are not a clinical assessment, a disciplinary tool, or a substitute for human judgment.

## What it does

- Builds a time-aware `StudentTwinState` from a student's history through day *t*.
- Estimates overload probability for the following seven-day outcome window using a frozen production model.
- Runs focused diagnostics across academic, behavioral, recovery, workload, and schedule signals.
- Simulates and ranks what-if scenarios, then generates recommendations.
- Records intervention responses and follow-up outcomes for student history and faculty analytics.
- Provides a React dashboard for the command center, digital twin, risk view, what-if lab, recommendations, student history, and faculty view.

## How the system is organized

```text
React + Vite dashboard
        │ /api (development proxy)
        ▼
FastAPI service (api/)
        ├── Twin and temporal feature engines (core/)
        ├── Frozen prediction and scenario engines (simulation/, ml/)
        ├── Agent and intervention workflow (agents/, intervention/)
        └── Prototype JSON persistence (data/phase7/)
```

The API is an orchestration layer over the existing Phase 2–6 components. The model is loaded from `experiments/results/model_pipeline.pkl`; this checked-in artifact lets the prototype serve predictions without retraining. The source dataset and phase 3 splits are under `data/`.

## Quick start

### Requirements

- Python 3.10 or newer
- Node.js 18 or newer and npm

### 1. Install dependencies

From the repository root:

```bash
python -m venv .venv
```

Activate the environment, then install the Python packages:

```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

python -m pip install -r requirements.txt
```

Install the dashboard dependencies:

```bash
cd frontend
npm ci
cd ..
```

### 2. Configure a local API key

Create a local `.env` file from the example and set a private development key:

```bash
cp .env.example .env
```

On Windows PowerShell, use `Copy-Item .env.example .env`. Set `KAIROS_TWIN_API_KEY` in `.env` and in `frontend/.env.local` to the same value. These local files are ignored by Git. Never commit real API keys.

### 3. Start the API and dashboard

In one terminal, from the repository root:

```bash
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm run dev
```

Open the local URL printed by Vite (normally `http://localhost:5173`). The Vite development server forwards `/api` requests to the API at `http://127.0.0.1:8000`. The API's interactive documentation is available at `http://127.0.0.1:8000/docs`.

The public `GET /health` endpoint reports whether the model artifact loaded. Authenticated API routes require `Authorization: Bearer <KAIROS_TWIN_API_KEY>`.

## API overview

The service includes endpoints for:

| Capability | Routes |
| --- | --- |
| Health and model metadata | `GET /health`, `GET /metadata/model` |
| Student state and risk | `POST /states/compute`, `POST /predictions` |
| Diagnostics and what-if analysis | `POST /diagnostics`, `POST /scenarios/generate`, `POST /simulations/run` |
| Recommendations and follow-up | `POST /recommendations/generate`, `/interventions/*`, `/outcomes/*` |
| History and aggregate analytics | `GET /students/{student_id}/history`, `GET /analytics/system` |

See [PHASE7_API.md](PHASE7_API.md) for request behavior, authentication, temporal validation, persistence, and the full route table.

## Data and temporal safeguards

The label engine defines overload using outcomes in the future window `[t+1, t+7]`. Features and twin state at day *t* are built only from observations at or before *t*. The API rejects future observations and future-label fields at its boundary. Synthetic data is intended for reproducible development and evaluation; it does not establish real-world predictive validity or represent any specific student population.

## Development

Python dependencies are listed in `requirements.txt`. Frontend commands are defined in `frontend/package.json`:

```bash
cd frontend
npm run typecheck
npm run lint
npm test
npm run build
```

The Python test suite is run from the repository root with:

```bash
python -m pytest
```

## Project map

| Path | Purpose |
| --- | --- |
| `api/` | FastAPI routes, schemas, service, security, and persistence |
| `core/` | Twin state, temporal sampling, features, and outcome labels |
| `simulation/` | Prediction, scenario generation, counterfactuals, and ranking |
| `ml/` | Training, evaluation, calibration, and interpretability utilities |
| `agents/`, `intervention/` | Diagnostics, orchestration, recommendations, and follow-up |
| `frontend/` | React, TypeScript, and Vite dashboard |
| `data/` | Synthetic observations, derived phase 3 data, and prototype state |
| `experiments/` | Model artifacts, experiment outputs, and validation reports |
| `REPORT_EVIDENCE/` | Architecture, methods, results, and limitations documentation |
| `tests/` | Python and frontend test suites |

## Limitations

- The included dataset is synthetic and does not demonstrate generalization to real students.
- A model probability is an estimate from the included frozen artifact, not a diagnosis or a guaranteed outcome.
- Prototype intervention persistence uses local JSON files and is designed for a single-process research setup, not production deployment.
- Recommendations and scenario projections support exploration; human review remains essential.

## License

No license has been specified yet. Contact the project owner before reusing or redistributing this project.
