# Indian Bond SEM Study


## Data preprocessing summary

INR rows: 25095 of 139067

Shared complete-case sample: 565 rows

                 best_factor  loading  communality  retain_as_indicator                               decision
YTM_log                   F2    0.990        0.981                 True                    retain as indicator
SourceCoupon              F1    0.978        0.958                 True                    retain as indicator
Spread_log                F3    0.332        0.193                False  drop from latent / treat as predictor
ESG_num                   F1    0.482        0.249                False  drop from latent / treat as predictor
CreditRating_ord          F3    0.495        0.389                False  drop from latent / treat as predictor
IssueSize_log             F3    0.802        0.660                 True                    retain as indicator


## EFA findings

### 2 factors

                     F1     F2
YTM_log           0.424  0.137
SourceCoupon      0.999 -0.022
Spread_log       -0.003 -0.388
ESG_num           0.524  0.124
CreditRating_ord -0.259  0.602
IssueSize_log     0.239  0.625

YTM_log             0.198
SourceCoupon        0.998
Spread_log          0.150
ESG_num             0.290
CreditRating_ord    0.430
IssueSize_log       0.448

### 3 factors

                     F1     F2     F3
YTM_log           0.024  0.990 -0.014
SourceCoupon      0.978  0.037  0.027
Spread_log        0.148 -0.246 -0.332
ESG_num           0.482  0.061  0.115
CreditRating_ord -0.369  0.093  0.495
IssueSize_log     0.124 -0.042  0.802

YTM_log             0.981
SourceCoupon        0.958
Spread_log          0.193
ESG_num             0.249
CreditRating_ord    0.389
IssueSize_log       0.660


## Model comparison

                           model  sample_n    CFI  RMSEA     Chi2  DoF     AIC     BIC  R2_BondPricing
        Model 3 - Greenium Model       565 0.8654 0.1989  46.6368  2.0 15.8349 50.5295             NaN
         Model 2 - Quality Model       565 0.8333 0.1824 197.5854 10.0 21.3006 69.0057          0.3138
       Model 5 - Mediation Model       565 0.6955 0.2096 180.4697  7.0 27.3612 88.0767             NaN
            Model 4 - Full Model       565 0.3826 0.2985 358.7754  7.0 26.7300 87.4456             NaN
Model 1 - Baseline Pricing Model       565 0.2808 0.3247 241.7926  4.0 11.1441 37.1651          0.0822


## Final interpretation

The data support a strong pricing block around yield and coupon, but not a fully clean latent structure. Issuer quality is only partly supported: issue size behaves like the dominant indicator, while rating is weak. ESG is the weakest element in the measurement system and works better as a proxy predictor than a robust latent. Among the competing SEMs, the quality model is the least implausible compromise, but all models show non-trivial misfit, so the conclusions should be treated as exploratory rather than confirmatory.


## Decision logging

## Model 1 - Baseline Pricing Model

Establish the base market-risk and ESG mechanism.

CFI: 0.281, RMSEA: 0.325, R2(BondPricing): 0.082

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
            BondPricing          Spread_log    -0.182  0.000015
            BondPricing             ESG_num     0.214       0.0
                YTM_log         BondPricing     0.963         -
           SourceCoupon         BondPricing     0.544  0.000014

       lval       rval  Est. Std   p-value
BondPricing Spread_log    -0.182  0.000015
BondPricing    ESG_num     0.214       0.0

## Model 2 - Quality Model

Test whether issuer strength adds explanatory power.

CFI: 0.833, RMSEA: 0.182, R2(BondPricing): 0.314

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
            BondPricing          Spread_log     0.040  0.288247
            BondPricing             ESG_num     0.527       0.0
            BondPricing             Quality     0.189  0.000292
                YTM_log         BondPricing     0.443         -
           SourceCoupon         BondPricing     0.954       0.0
       CreditRating_ord             Quality     0.324         -
          IssueSize_log             Quality     1.000  0.088148

       lval       rval  Est. Std   p-value
BondPricing Spread_log     0.040  0.288247
BondPricing    ESG_num     0.527       0.0
BondPricing    Quality     0.189  0.000292

## Model 3 - Greenium Model

Test a proxy greenium channel.

CFI: 0.865, RMSEA: 0.199, R2(BondPricing): not identified

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
            BondPricing          Spread_log    -0.003  0.944359
            BondPricing            Greenium     1.000       1.0
                YTM_log         BondPricing     0.422         -
           SourceCoupon         BondPricing     1.000  0.000001
                ESG_num            Greenium     0.441         -

       lval       rval  Est. Std   p-value
BondPricing Spread_log    -0.003  0.944359
BondPricing   Greenium     1.000       1.0

## Model 4 - Full Model

Jointly test market risk, quality, and ESG.

CFI: 0.383, RMSEA: 0.298, R2(BondPricing): not identified

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
            BondPricing          Spread_log     0.055  0.210557
            BondPricing             Quality    -0.221  0.906158
            BondPricing            Greenium     1.080  0.782479
                YTM_log         BondPricing     0.427         -
           SourceCoupon         BondPricing     1.000  0.001178
       CreditRating_ord             Quality     0.032         -
          IssueSize_log             Quality     1.000  0.835831
                ESG_num            Greenium     0.101         -

       lval       rval  Est. Std   p-value
BondPricing Spread_log     0.055  0.210557
BondPricing    Quality    -0.221  0.906158
BondPricing   Greenium     1.080  0.782479

## Model 5 - Mediation Model

Test whether issuer quality feeds into pricing through ESG.

CFI: 0.696, RMSEA: 0.210, R2(BondPricing): not identified

indicator_or_endogenous latent_or_predictor  Est. Std   p-value
               Greenium             Quality     0.438  0.000022
            BondPricing          Spread_log     0.051  0.172256
            BondPricing            Greenium     1.064  0.000008
            BondPricing             Quality    -0.180  0.110525
                YTM_log         BondPricing     0.426         -
           SourceCoupon         BondPricing     1.000       0.0
       CreditRating_ord             Quality     0.325         -
          IssueSize_log             Quality     1.000  0.014955
                ESG_num            Greenium     0.467         -

            lval        rval  Est. Std   p-value
        Greenium     Quality     0.438  0.000022
     BondPricing  Spread_log     0.051  0.172256
     BondPricing    Greenium     1.064  0.000008
     BondPricing     Quality    -0.180  0.110525
         YTM_log BondPricing     0.426         -
    SourceCoupon BondPricing     1.000       0.0
CreditRating_ord     Quality     0.325         -
   IssueSize_log     Quality     1.000  0.014955
         ESG_num    Greenium     0.467         -