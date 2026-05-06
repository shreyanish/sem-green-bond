import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'all_currencies_combined.csv'
OUT = ROOT / 'sem_outputs' / 'sem_matching_ready.csv'

df = pd.read_csv(DATA, low_memory=False)

# Identify reasonable column names by keyword because the CSV uses numbered headers
col_map = {}
cols = list(df.columns)
def find_col(keywords):
    # prefer exact match (case-insensitive), then substring
    lower_cols = {c.lower(): c for c in cols}
    for k in keywords:
        if k.lower() in lower_cols:
            return lower_cols[k.lower()]
    for c in cols:
        for k in keywords:
            if k.lower() in c.lower():
                return c
    return None

col_map['Currency'] = find_col(['currency'])
col_map['YTM'] = find_col(['yield to maturity','ytm'])
col_map['SourceCoupon'] = find_col(['source coupon','source_coupon','source coupon'])
col_map['Spread'] = find_col(['spread'])
col_map['ESG'] = find_col(['esg score','esg','source esg'])
col_map['CreditRating'] = find_col(['4. Credit Rating','credit rating','bond grade','source bond grade'])
# prefer the spreadsheet '1. Issue Size' field when present
if '1. Issue Size' in cols:
    col_map['IssueSize'] = '1. Issue Size'
else:
    col_map['IssueSize'] = find_col(['issue size','amount issued','source amount issued'])

# Filter to INR only (design principle: same interest-rate regime)
if col_map['Currency'] is None:
    raise KeyError('Could not find a currency column in CSV')
# match common labels: 'INR', 'Indian Rupee', 'Rupee'
df_inr = df[df[col_map['Currency']].astype(str).str.contains(r'INR|Indian|Rupee', case=False, na=False)].copy()

# Map to requested variable names
# For some semantic fields there are multiple candidate columns; pick the best (most non-null in INR)
def best_col(candidates):
    best = None
    best_count = -1
    for c in candidates:
        if c and c in df_inr.columns:
            cnt = df_inr[c].notna().sum()
            if cnt > best_count:
                best_count = cnt
                best = c
    return best

# YTM: prefer 'Source Yield to Maturity'
yc = best_col([col_map.get('YTM'), find_col(['Source Yield to Maturity','Source Yield'])])
sc = best_col([col_map.get('SourceCoupon'), find_col(['Source Coupon'])])
spc = best_col([col_map.get('Spread'), find_col(['6. Spread','Spread'])])
esgc = best_col([find_col(['Source ESG Score','Source ESG','7. ESG']), col_map.get('ESG')])
# credit: prefer Source Bond Grade if available else 4. Credit Rating
creditc = best_col([find_col(['Source Bond Grade','Source Bond Grade']), col_map.get('CreditRating')])
issc = best_col([col_map.get('IssueSize'), find_col(['1. Issue Size','Source Amount Issued'])])

print('Columns chosen for mapping:')
print('YTM col:', yc)
print('SourceCoupon col:', sc)
print('Spread col:', spc)
print('ESG col:', esgc)
print('Credit col:', creditc)
print('IssueSize col:', issc)

df_inr['YTM_log'] = pd.to_numeric(df_inr[yc], errors='coerce') if yc else np.nan
df_inr['SourceCoupon'] = pd.to_numeric(df_inr[sc], errors='coerce') if sc else np.nan
df_inr['Spread_log'] = pd.to_numeric(df_inr[spc], errors='coerce') if spc else np.nan
df_inr['ESG_num'] = pd.to_numeric(df_inr[esgc], errors='coerce') if esgc else np.nan
df_inr['CreditRating_ord'] = pd.to_numeric(df_inr[creditc], errors='coerce') if creditc else np.nan
df_inr['IssueSize_log'] = pd.to_numeric(df_inr[issc], errors='coerce') if issc else np.nan

vars_needed = ['YTM_log','SourceCoupon','Spread_log','ESG_num','CreditRating_ord','IssueSize_log']

# Quantify missingness
missing = df_inr[vars_needed].isna().mean()

# Debug: report counts before dropping
print('INR rows total:', len(df_inr))
for v in vars_needed:
    print(v, 'non-null count in INR:', df_inr[v].notna().sum())

# Use complete-case for matching-ready dataset (ensures covariance comparability)
df_cc = df_inr.dropna(subset=vars_needed).copy()
print('Complete-case rows after dropna:', len(df_cc))

# If log fields are not numeric, coerce (already handled above)
for v in ['YTM_log','Spread_log','IssueSize_log']:
    df_cc[v] = pd.to_numeric(df_cc[v], errors='coerce')

# Compute latent scores using empirically-backed weights from EFA/SEM
# BondPricing weights (EFA/Model evidence): YTM_log ~0.99, SourceCoupon ~0.98
bp_w = {'YTM_log':0.99,'SourceCoupon':0.98}
bp_sum = sum(bp_w.values())
df_cc['BondPricing_score'] = (df_cc['YTM_log']*bp_w['YTM_log'] + df_cc['SourceCoupon']*bp_w['SourceCoupon'])/bp_sum

# Quality weights: IssueSize dominant (1.0), CreditRating weaker (~0.32)
q_w = {'IssueSize_log':1.0,'CreditRating_ord':0.324}
q_sum = sum(q_w.values())
df_cc['Quality_score'] = (df_cc['IssueSize_log']*q_w['IssueSize_log'] + df_cc['CreditRating_ord']*q_w['CreditRating_ord'])/q_sum

# Greenium score: ESG_num loading ~0.48 from EFA/SEM
df_cc['Greenium_score'] = pd.to_numeric(df_cc['ESG_num'], errors='coerce')

# Treatment: Green = 1 if ESG_num >= 75th percentile (top quartile)
thresh = df_cc['ESG_num'].quantile(0.75)
df_cc['Green'] = (df_cc['ESG_num'] >= thresh).astype(int)

# Matching bins
df_cc['Rating_group'] = pd.cut(df_cc['CreditRating_ord'], bins=[-np.inf,2,4,6,np.inf], labels=['Low','Med','High','VeryHigh'])
try:
    if df_cc['IssueSize_log'].nunique(dropna=True) >= 4:
        df_cc['Size_bin'] = pd.qcut(df_cc['IssueSize_log'].rank(method='first'), q=4, labels=['S','M','L','XL'])
    else:
        df_cc['Size_bin'] = 'Unknown'
except Exception:
    df_cc['Size_bin'] = 'Unknown'
try:
    if df_cc['Quality_score'].nunique(dropna=True) >= 4:
        df_cc['Quality_bin'] = pd.qcut(df_cc['Quality_score'], q=4, labels=False)
    else:
        df_cc['Quality_bin'] = -1
except Exception:
    df_cc['Quality_bin'] = -1

# Save matching-ready CSV (row-level)
OUT.parent.mkdir(parents=True, exist_ok=True)
cols_out = vars_needed + ['BondPricing_score','Quality_score','Greenium_score','Green','Rating_group','Size_bin','Quality_bin']
df_cc.to_csv(OUT, columns=cols_out, index=False)

print(f"Wrote matching-ready CSV: {OUT} (n={len(df_cc)})")
