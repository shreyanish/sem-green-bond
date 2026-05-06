# Executive Summary - Indian Bond SEM

## Research Question
What drives bond pricing in the Indian market: market risk, issuer quality, ESG, or a combination of these channels?

## Data and Method
- Currency restricted to INR to keep one interest-rate regime.
- Final comparable SEM sample: 565 complete cases.
- Five competing SEM models estimated and compared.

## What the data supports
- Strong measurement for pricing with `YTM_log` and `SourceCoupon`.
- Partial support for issuer quality (size stronger than rating).
- ESG is useful as a signal, but weak as a standalone latent construct.

## Best model for interpretation
**Model 2 (Quality Model)**
- CFI: 0.833
- RMSEA: 0.182
- R2 (BondPricing): 0.314

Why this model:
- Largest usable explained variance among identified models.
- Clearer economic interpretation than models with unstable latent ESG structure.

## Bottom line
- Bond pricing in this sample reflects a combined mechanism where quality and ESG signal matter, but full latent-factor confirmation is limited by measurement weakness and global misfit.
- Results are suitable for exploratory evidence and for building the next causal stage (PSM/CEM), not yet for strict confirmatory claims.

## Next analytical step
Use `sem_matching_ready.csv` to estimate treatment effects of green status with balance diagnostics and sensitivity checks.
