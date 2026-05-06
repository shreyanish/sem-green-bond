# Indian Bond Pricing SEM Report

## 1) Executive Summary

This study tests what drives Indian bond pricing using Structural Equation Modeling (SEM), with models restricted to INR-denominated bonds to keep one macro-rate regime.

Core finding:
- The measurement side is strongest for `BondPricing` using `YTM_log` and `SourceCoupon`.
- `IssueSize_log` contributes to issuer quality, while `CreditRating_ord` is weaker.
- ESG behaves as a weak latent indicator and is more stable as a proxy predictor.
- Among competing models, **Model 2 (Quality Model)** is the most interpretable compromise with non-trivial explanatory gain (`R2_BondPricing = 0.314`) versus baseline (`0.082`), though global fit remains imperfect.

Practical implication:
- Pricing in this sample is best explained by a mixed mechanism where issuer strength and ESG signal both matter, but latent ESG structure is not robust enough to be treated as a fully validated latent construct.

---

## 2) Study Objective and Scope

### Objective
Assess whether Indian bond pricing is driven by:
- Market risk (`Spread_log`)
- Issuer quality (`CreditRating_ord`, `IssueSize_log`)
- ESG / greenium (`ESG_num`)

And whether these effects are independent or mediated.

### Why INR-only filtering
INR filtering is required for SEM comparability because covariance structure is not stable when combining currencies with different monetary regimes and spread/yield baselines.

---

## 3) Data and Preprocessing

### Data footprint
- Total observations before currency restriction: **139,067**
- INR observations: **25,095**
- Shared complete-case SEM sample: **565**

### Variables used
- Outcome-related indicators: `YTM_log`, `SourceCoupon`
- Market risk: `Spread_log`
- ESG signal: `ESG_num`
- Issuer quality proxies: `CreditRating_ord`, `IssueSize_log`

### Missing-data handling
- Strategy: shared complete-case sample across modeling variables for structural comparability.
- Trade-off:
  - Pros: same sample for all model comparisons; valid fit comparison.
  - Cons: reduced `n`, potential selection bias.

---

## 4) Exploratory Structure (Correlation + EFA)

### Correlation
See:
- `correlation_heatmap.png`

Interpretation highlights:
- A clear pricing block appears around yield/coupon behavior.
- ESG and rating are weaker/less stable contributors to common latent structure.
- Size has stronger shared variance with quality-related structure than rating.

### EFA evidence
See:
- `efa_loading_charts.png`

Decision rules used:
- Candidate indicator if loading >= 0.5
- Retain indicator if communality >= 0.3

Observed variable-level decisions:
- `YTM_log`: loading 0.990, communality 0.981 -> **retain as indicator**
- `SourceCoupon`: loading 0.978, communality 0.958 -> **retain as indicator**
- `IssueSize_log`: loading 0.802, communality 0.660 -> **retain (quality side)**
- `CreditRating_ord`: loading 0.495, communality 0.389 -> **borderline; keep cautiously / often predictor**
- `ESG_num`: loading 0.482, communality 0.249 -> **weak latent indicator; better as predictor/proxy**
- `Spread_log`: loading 0.332, communality 0.193 -> **predictor, not latent indicator**

Conclusion from EFA:
- Strong pricing measurement factor exists.
- Quality is partially supported, mostly through issue size.
- ESG does not meet strong latent measurement standards in this sample.

---

## 5) SEM Models and Results

## Model 1 - Baseline Pricing Model

Specification:
- `BondPricing =~ YTM_log + SourceCoupon`
- `BondPricing ~ Spread_log + ESG_num`

What it tests:
- Base pricing channel from market risk + ESG signal.

Key results:
- Fit: CFI 0.281, RMSEA 0.325, `R2_BondPricing = 0.082`
- Structural:
  - `Spread_log -> BondPricing`: -0.182 (p = 0.000015)
  - `ESG_num -> BondPricing`: +0.214 (p < 0.001)

Interpretation:
- Signals are statistically active, but model fit is poor.
- Baseline mechanism alone is insufficient.

## Model 2 - Quality Model

Specification:
- `BondPricing =~ YTM_log + SourceCoupon`
- `Quality =~ CreditRating_ord + IssueSize_log`
- `BondPricing ~ Spread_log + ESG_num + Quality`

What it tests:
- Whether issuer strength improves pricing explanation beyond baseline.

Key results:
- Fit: CFI 0.833, RMSEA 0.182, `R2_BondPricing = 0.314`
- Structural:
  - `Spread_log -> BondPricing`: +0.040 (p = 0.288)
  - `ESG_num -> BondPricing`: +0.527 (p < 0.001)
  - `Quality -> BondPricing`: +0.189 (p = 0.000292)

Interpretation:
- Best practical model in this set.
- Meaningful explanatory gain vs Model 1.
- Quality contributes, though rating component remains weak.

## Model 3 - Greenium Model

Specification:
- `BondPricing =~ YTM_log + SourceCoupon`
- `Greenium =~ ESG_num`
- `BondPricing ~ Spread_log + Greenium`

What it tests:
- ESG-centric pricing channel.

Key results:
- Fit: CFI 0.865, RMSEA 0.199, `R2` not identified
- Structural:
  - `Spread_log -> BondPricing`: -0.003 (p = 0.944)
  - `Greenium -> BondPricing`: 1.000 (p = 1.0, unstable)

Interpretation:
- Numerical CFI is high relative to others, but identification is fragile due to single-indicator latent structure.
- Not preferred for substantive inference.

## Model 4 - Full Model

Specification:
- `BondPricing =~ YTM_log + SourceCoupon`
- `Quality =~ CreditRating_ord + IssueSize_log`
- `Greenium =~ ESG_num`
- `BondPricing ~ Spread_log + Quality + Greenium`

What it tests:
- Joint simultaneous mechanism.

Key results:
- Fit: CFI 0.383, RMSEA 0.298, `R2` not identified
- Structural effects are unstable / non-informative.

Interpretation:
- Over-parameterized relative to measurement quality in this sample.
- Joint latent setup not empirically supported.

## Model 5 - Mediation Model

Specification:
- `Quality -> Greenium -> BondPricing`
- `Spread_log -> BondPricing`
- With the same measurement blocks as full model.

What it tests:
- Whether ESG mediates quality effect.

Key results:
- Fit: CFI 0.696, RMSEA 0.210, `R2` not identified
- `Quality -> Greenium`: +0.438 (p = 0.000022)
- `Greenium -> BondPricing`: +1.064 (p = 0.000008)
- `Quality -> BondPricing`: -0.180 (p = 0.111)

Interpretation:
- Mediation path appears statistically active but model fit/identification remain weak.
- Treat as exploratory, not confirmatory evidence.

---

## 6) Model Comparison Table

| Model | CFI | RMSEA | R2 (BondPricing) | Decision |
|---|---:|---:|---:|---|
| Model 1 - Baseline Pricing | 0.281 | 0.325 | 0.082 | Weak baseline fit |
| Model 2 - Quality | 0.833 | 0.182 | 0.314 | Best compromise model |
| Model 3 - Greenium | 0.865 | 0.199 | not identified | Identification caution |
| Model 4 - Full | 0.383 | 0.298 | not identified | Not supported |
| Model 5 - Mediation | 0.696 | 0.210 | not identified | Exploratory only |

Ranking principle used:
- Prefer models with interpretable structure + identified variance + better fit.
- Under this criterion, **Model 2** is preferred.

---

## 7) Final Interpretation (Plain Language)

### What drives pricing?
- Pricing is primarily anchored by the yield-coupon measurement block.
- Quality adds explanatory value when represented with size and (weakly) rating.

### Does issuer quality matter?
- Yes, in Model 2 quality has a positive and significant relation with pricing.
- But the quality latent is only partially robust because rating is weak.

### Does ESG create pricing advantage (greenium)?
- ESG shows positive association in several models.
- However, ESG does not form a strong latent measurement construct by itself in this dataset.

### Which model best explains pricing?
- **Model 2 (Quality Model)**, because it improves explained variance and remains interpretable without the strongest identification issues.

### Confidence level
- Conclusions are **exploratory** due to persistent global misfit and weak latent support for some constructs.

---

## 8) Matching / Causal Next Step

Matching-ready dataset:
- `sem_matching_ready.csv`

Recommended causal setup for PSM/CEM:
- Treatment: `Green` (ESG threshold rule)
- Outcome: `BondPricing_score` (or `YTM_log` for sensitivity)
- Matching covariates: `Spread_log`, `CreditRating_ord`, `IssueSize_log`, `SourceCoupon`

Checks before causal claims:
- Common support diagnostics
- Balance diagnostics (SMD before/after)
- Sensitivity analysis to unobserved confounding

---

## 9) Visual Index

- Correlation: `correlation_heatmap.png`
- EFA loadings: `efa_loading_charts.png`
- Path diagrams:
  - `model_1_baseline_path_diagram.png`
  - `model_2_quality_path_diagram.png`
  - `model_3_greenium_path_diagram.png`
  - `model_4_full_path_diagram.png`
  - `model_5_mediation_path_diagram.png`

