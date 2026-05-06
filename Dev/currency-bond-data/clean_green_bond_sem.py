#!/usr/bin/env python3

from __future__ import annotations

import numpy as np
import pandas as pd


INPUT_FILE = "all_currencies_combined.csv"
OUTPUT_FILE = "green_bond_SEM_clean.csv"


def map_yes_no_to_binary(series: pd.Series) -> pd.Series:
    normalized = series.astype("string").str.strip().str.lower()
    out = pd.Series(np.nan, index=series.index, dtype="float64")
    out[normalized == "yes"] = 1.0
    out[normalized == "no"] = 0.0
    return out


def map_credit_rating(value: object) -> float:
    if pd.isna(value):
        return np.nan

    text = str(value).strip().lower()
    if text == "":
        return np.nan
    if "investment grade" in text:
        return 5.0
    if "baa" in text:
        return 2.0
    if "aa" in text:
        return 4.0
    if ("a1" in text or "a2" in text or "a3" in text) and "aa" not in text:
        return 3.0
    return 1.0


def main() -> None:
    # 1. Load file
    df = pd.read_csv(INPUT_FILE, low_memory=False)

    # 2. Convert 7. ESG to numeric
    df["ESG_num"] = pd.to_numeric(
        df["7. ESG"].replace("--", np.nan), errors="coerce"
    )

    # 3. Convert 6. Spread to numeric
    df["Spread_num"] = pd.to_numeric(df["6. Spread"], errors="coerce")

    # 4. Recode 8. Certification Status -> binary
    df["Cert_binary"] = map_yes_no_to_binary(df["8. Certification Status"])

    # 5. Recode Source Green Bond -> binary
    df["GreenBond_binary"] = map_yes_no_to_binary(df["Source Green Bond"])

    # 6. Recode 4. Credit Rating -> ordinal (1-5)
    df["CreditRating_ord"] = df["4. Credit Rating"].apply(map_credit_rating)

    # 7. Issuer Type dummies, with Corporate as reference (omitted)
    issuer = df["11. Issuer Type"].astype("string").str.strip()
    missing_issuer = df["11. Issuer Type"].isna()

    df["IssType_Govt"] = (issuer == "Govt/Treasury/Central Bank").astype("float64")
    df.loc[missing_issuer, "IssType_Govt"] = np.nan

    df["IssType_Agency"] = (issuer == "Agency").astype("float64")
    df.loc[missing_issuer, "IssType_Agency"] = np.nan

    df["IssType_Supra"] = (issuer == "Other Gov/Supra").astype("float64")
    df.loc[missing_issuer, "IssType_Supra"] = np.nan

    df["IssType_Munis"] = (issuer == "Non-US Munis").astype("float64")
    df.loc[missing_issuer, "IssType_Munis"] = np.nan

    # 8. Log-transform 1. Issue Size: log(x + 1)
    issue_size_numeric = pd.to_numeric(df["1. Issue Size"], errors="coerce")
    df["IssueSize_log"] = np.log1p(issue_size_numeric)

    # 9 + 10. Keep all original columns and save output
    df.to_csv(OUTPUT_FILE, index=False)

    # 11. Summary report for new columns
    new_columns = [
        "ESG_num",
        "Spread_num",
        "Cert_binary",
        "GreenBond_binary",
        "CreditRating_ord",
        "IssType_Govt",
        "IssType_Agency",
        "IssType_Supra",
        "IssType_Munis",
        "IssueSize_log",
    ]

    print(f"Saved cleaned file: {OUTPUT_FILE}")
    print(f"Output shape: {df.shape}")
    print("Summary of derived columns:")

    for col in new_columns:
        series = df[col]
        non_null = int(series.notna().sum())
        null_count = int(series.isna().sum())
        print(f"- {col}: non_null={non_null}, null={null_count}")

        if pd.api.types.is_numeric_dtype(series):
            mean_val = series.mean()
            std_val = series.std()
            print(f"  mean={mean_val:.6f}, std={std_val:.6f}")


if __name__ == "__main__":
    main()