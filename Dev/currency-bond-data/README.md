# Indian Bond SEM Study

This repository contains the data and analysis code for a structural equation modeling (SEM) study of bond pricing with a focus on the Indian market.

Purpose
- Investigate drivers of bond pricing in INR: market risk (spread), issuer quality (rating, size), and ESG (greenium).
- Produce reproducible SEM models, diagnostics, visualizations, and a matching-ready dataset for causal inference.

Key scripts
- `india_bond_sem_study.py` — full SEM analysis (EFA, 5 SEM models, figures, report). Outputs saved to `sem_outputs/`.
- `generate_matching_ready.py` — builds `sem_outputs/sem_matching_ready.csv` containing original variables, derived latent scores, treatment indicator (`Green`), and matching bins.

Primary outputs (folder: `sem_outputs/`)
- `report.md` — analysis narrative, EFA, and model-level summaries.
- `model_comparison.csv` — model fit table used for comparisons.
- `*.png` — figures (correlation heatmap, factor loadings, SEM path diagrams).
- `sem_matching_ready.csv` — matching-ready dataset (row-level) for PSM/CEM.

Quickstart
1. Activate the project's virtualenv (if present):

```bash
source .venv/bin/activate
```

2. Run the SEM analysis (produces `sem_outputs/` artifacts):

```bash
python india_bond_sem_study.py
```

3. Generate the matching-ready CSV (idempotent):

```bash
python generate_matching_ready.py
```

Design notes
- All SEM analyses are restricted to INR-only rows to ensure a single interest-rate regime and comparable covariance structure.
- Latent constructs are validated empirically (EFA loadings, communalities). Weak indicators are removed or treated as predictors — see `sem_outputs/report.md` for the decision log.
- The matching-ready dataset uses complete-case selection for the set of variables required by the SEM models to ensure comparability of factor scores. The treatment `Green` is defined in `generate_matching_ready.py` (default: top quartile of `ESG_num`) — adjust the threshold there if desired.

Extending
- To change model specifications, edit `india_bond_sem_study.py` (models are defined and labeled Model 1–5).
- To adjust matching variables, thresholds, or binning logic, edit `generate_matching_ready.py`.

Contact
- For questions about the analysis choices, model diagnostics, or reproducibility, open an issue or contact the repository owner.
