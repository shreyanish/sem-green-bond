#!/usr/bin/env python3

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from factor_analyzer import FactorAnalyzer
import factor_analyzer.factor_analyzer as fa_module
from semopy import Model, calc_stats


ROOT = Path(__file__).resolve().parent
INPUT_FILE = ROOT / "all_currencies_combined.csv"
OUTPUT_DIR = ROOT / "sem_outputs"

ALL_SELECTED_VARS = [
    "YTM_log",
    "SourceCoupon",
    "Spread_log",
    "ESG_num",
    "CreditRating_ord",
    "IssueSize_log",
]

MODEL_SPECS = {
    "model_1_baseline": {
        "title": "Model 1 - Baseline Pricing Model",
        "description": "BondPricing =~ YTM_log + SourceCoupon\nBondPricing ~ Spread_log + ESG_num",
        "purpose": "Establish the base market-risk and ESG mechanism.",
    },
    "model_2_quality": {
        "title": "Model 2 - Quality Model",
        "description": "BondPricing =~ YTM_log + SourceCoupon\nQuality =~ CreditRating_ord + IssueSize_log\nBondPricing ~ Spread_log + ESG_num + Quality",
        "purpose": "Test whether issuer strength adds explanatory power.",
    },
    "model_3_greenium": {
        "title": "Model 3 - Greenium Model",
        "description": "BondPricing =~ YTM_log + SourceCoupon\nGreenium =~ 1*ESG_num\nBondPricing ~ Spread_log + Greenium",
        "purpose": "Test a proxy greenium channel.",
    },
    "model_4_full": {
        "title": "Model 4 - Full Model",
        "description": "BondPricing =~ YTM_log + SourceCoupon\nQuality =~ CreditRating_ord + IssueSize_log\nGreenium =~ 1*ESG_num\nBondPricing ~ Spread_log + Quality + Greenium",
        "purpose": "Jointly test market risk, quality, and ESG.",
    },
    "model_5_mediation": {
        "title": "Model 5 - Mediation Model",
        "description": "BondPricing =~ YTM_log + SourceCoupon\nQuality =~ CreditRating_ord + IssueSize_log\nGreenium =~ 1*ESG_num\nGreenium ~ Quality\nBondPricing ~ Spread_log + Greenium + Quality",
        "purpose": "Test whether issuer quality feeds into pricing through ESG.",
    },
}


@dataclass
class EFAResult:
    n_factors: int
    loadings: pd.DataFrame
    communalities: pd.Series
    variance: pd.DataFrame


def ensure_efa_compatibility() -> None:
    """Patch factor_analyzer for the newer sklearn validation API."""

    try:
        from sklearn.utils.validation import check_array as sklearn_check_array
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("scikit-learn is required for EFA support.") from exc

    def patched_check_array(*args: Any, **kwargs: Any) -> Any:
        if "force_all_finite" in kwargs and "ensure_all_finite" not in kwargs:
            kwargs["ensure_all_finite"] = kwargs.pop("force_all_finite")
        return sklearn_check_array(*args, **kwargs)

    fa_module.check_array = patched_check_array


def signed_log1p(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series.replace("--", np.nan), errors="coerce")
    return np.sign(numeric) * np.log1p(np.abs(numeric))


def map_credit_rating(value: object) -> float:
    if pd.isna(value):
        return np.nan

    text = str(value).strip().lower()
    if not text:
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


def prepare_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print("Step 1 - Load CSV")
    print(f"Loaded rows: {df.shape[0]}, columns: {df.shape[1]}")
    print("Column names:")
    for column in df.columns:
        print(f"- {column}")
    print("\nBasic summary:")
    print(df.describe(include="all").transpose().head(12).to_string())

    print("\nStep 2 - Filter INR")
    inr = df[df["5. Currency"].astype(str).str.strip().eq("Indian Rupee")].copy()
    print(f"INR rows retained: {inr.shape[0]} of {df.shape[0]}")
    print(
        "Why this filter matters: different currencies sit in different rate regimes, "
        "so mixing them would break the covariance structure that SEM relies on."
    )

    print("\nStep 3 - Select variables")
    inr["YTM_log"] = signed_log1p(inr["Source Yield to Maturity"])
    inr["SourceCoupon"] = pd.to_numeric(inr["Source Coupon"], errors="coerce")
    inr["Spread_log"] = signed_log1p(inr["6. Spread"])
    inr["ESG_num"] = pd.to_numeric(inr["7. ESG"].replace("--", np.nan), errors="coerce")
    inr["CreditRating_ord"] = inr["4. Credit Rating"].apply(map_credit_rating)
    inr["IssueSize_log"] = np.log1p(pd.to_numeric(inr["1. Issue Size"], errors="coerce"))

    selected = inr[ALL_SELECTED_VARS].copy()
    print(selected.head(8).to_string())

    print("\nStep 4 - Handle missing data")
    missing_report = selected.isna().agg(["sum", "mean"]).T
    missing_report.columns = ["missing_count", "missing_share"]
    print(missing_report.to_string(float_format=lambda x: f"{x:.4f}"))

    complete_cases = selected.dropna().copy()
    print(
        f"\nComplete-case sample for comparable SEM models: {complete_cases.shape[0]} rows "
        f"({complete_cases.shape[0] / selected.shape[0]:.2%} of INR rows)."
    )
    print(
        "Decision: listwise deletion on the selected variables is used for the main models so "
        "all five SEMs compare the same covariance matrix. The tradeoff is a much smaller sample, "
        "but it avoids conflating model differences with different missing-data patterns."
    )

    return inr, complete_cases


def compute_correlation_matrix(data: pd.DataFrame) -> pd.DataFrame:
    corr = data.corr(numeric_only=True)
    print("\nStep 5 - Correlation matrix")
    print(corr.round(3).to_string())
    return corr


def run_efa(data: pd.DataFrame) -> dict[int, EFAResult]:
    ensure_efa_compatibility()
    results: dict[int, EFAResult] = {}

    print("\nStep 6 - Exploratory factor analysis")
    for n_factors in (2, 3):
        fa = FactorAnalyzer(n_factors=n_factors, rotation="oblimin", method="ml")
        fa.fit(data)
        loadings = pd.DataFrame(
            fa.loadings_, index=data.columns, columns=[f"F{i + 1}" for i in range(n_factors)]
        )
        communalities = pd.Series(fa.get_communalities(), index=data.columns, name="communality")
        variance = pd.DataFrame(
            fa.get_factor_variance(),
            index=["SS Loadings", "Proportion Var", "Cumulative Var"],
            columns=[f"F{i + 1}" for i in range(n_factors)],
        )
        results[n_factors] = EFAResult(
            n_factors=n_factors,
            loadings=loadings,
            communalities=communalities,
            variance=variance,
        )
        print(f"\nEFA with {n_factors} factors")
        print(loadings.round(3).to_string())
        print("Communalities:")
        print(communalities.round(3).to_string())
        print("Variance explained:")
        print(variance.round(3).to_string())

    return results


def classify_efa_variables(efa_result: EFAResult) -> pd.DataFrame:
    abs_loadings = efa_result.loadings.abs()
    best_factor = abs_loadings.idxmax(axis=1)
    best_loading = abs_loadings.max(axis=1)
    decision = pd.DataFrame(
        {
            "best_factor": best_factor,
            "loading": best_loading,
            "communality": efa_result.communalities,
        }
    )
    decision["retain_as_indicator"] = (
        (decision["loading"] >= 0.5) & (decision["communality"] >= 0.3)
    )
    decision["decision"] = np.where(
        decision["retain_as_indicator"],
        "retain as indicator",
        "drop from latent / treat as predictor",
    )
    return decision


def fit_sem_model(description: str, data: pd.DataFrame) -> tuple[Model, dict[str, float], pd.DataFrame]:
    model = Model(description)
    model.fit(data)
    fit_stats = calc_stats(model).iloc[0].to_dict()
    estimates = model.inspect(std_est=True)
    return model, fit_stats, estimates


def extract_r2(estimates: pd.DataFrame, endogenous: str) -> float:
    row = estimates[(estimates["lval"] == endogenous) & (estimates["op"] == "~~") & (estimates["rval"] == endogenous)]
    if row.empty:
        return float("nan")
    residual_std = float(row.iloc[0]["Est. Std"])
    if math.isnan(residual_std):
        return float("nan")
    if abs(residual_std) < 1e-8:
        return float("nan")
    return float(max(0.0, min(1.0, 1.0 - residual_std)))


def summarise_measurement(estimates: pd.DataFrame) -> pd.DataFrame:
    rows = estimates[estimates["op"] == "~"].copy()
    return rows[["lval", "rval", "Est. Std", "p-value"]].rename(
        columns={"lval": "indicator_or_endogenous", "rval": "latent_or_predictor"}
    )


def save_heatmap(corr: pd.DataFrame) -> None:
    plt.figure(figsize=(9, 7))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True)
    plt.title("INR Selected Variables Correlation Heatmap")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "correlation_heatmap.png", dpi=180)
    plt.close()


def save_loading_chart(efa_results: dict[int, EFAResult]) -> None:
    fig, axes = plt.subplots(1, len(efa_results), figsize=(14, 6), sharey=True)
    if len(efa_results) == 1:
        axes = [axes]
    for ax, (n_factors, result) in zip(axes, efa_results.items()):
        result.loadings.plot(kind="bar", ax=ax)
        ax.axhline(0.5, color="gray", linestyle="--", linewidth=1)
        ax.axhline(-0.5, color="gray", linestyle="--", linewidth=1)
        ax.set_title(f"{n_factors}-Factor Oblimin Solution")
        ax.set_xlabel("Variables")
        ax.set_ylabel("Loading")
        ax.legend(loc="best")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "efa_loading_charts.png", dpi=180)
    plt.close()


def _draw_node(ax: plt.Axes, xy: tuple[float, float], text: str, *, latent: bool) -> None:
    if latent:
        circle = plt.Circle(xy, 0.06, fill=False, linewidth=1.8)
        ax.add_patch(circle)
    else:
        rect = plt.Rectangle((xy[0] - 0.085, xy[1] - 0.04), 0.17, 0.08, fill=False, linewidth=1.4)
        ax.add_patch(rect)
    ax.text(xy[0], xy[1], text, ha="center", va="center", fontsize=9)


def _draw_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.annotate(
        "",
        xy=end,
        xytext=start,
        arrowprops=dict(arrowstyle="->", linewidth=1.2, color="black"),
    )


def save_path_diagram(model_key: str, title: str, description: str) -> None:
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    latent_positions = {
        "BondPricing": (0.5, 0.6),
        "Quality": (0.78, 0.6),
        "Greenium": (0.2, 0.6),
    }
    observed_positions = {
        "YTM_log": (0.42, 0.25),
        "SourceCoupon": (0.58, 0.25),
        "Spread_log": (0.18, 0.82),
        "ESG_num": (0.2, 0.25),
        "CreditRating_ord": (0.76, 0.25),
        "IssueSize_log": (0.9, 0.25),
    }

    _draw_node(ax, latent_positions["BondPricing"], "BondPricing", latent=True)
    _draw_node(ax, observed_positions["YTM_log"], "YTM_log", latent=False)
    _draw_node(ax, observed_positions["SourceCoupon"], "SourceCoupon", latent=False)
    _draw_arrow(ax, latent_positions["BondPricing"], (0.42, 0.31))
    _draw_arrow(ax, latent_positions["BondPricing"], (0.58, 0.31))

    if "Spread_log" in description:
        _draw_node(ax, observed_positions["Spread_log"], "Spread_log", latent=False)
        _draw_arrow(ax, observed_positions["Spread_log"], (0.46, 0.63))
    if "ESG_num" in description and "Greenium" not in description:
        _draw_node(ax, observed_positions["ESG_num"], "ESG_num", latent=False)
        _draw_arrow(ax, observed_positions["ESG_num"], (0.44, 0.57))
    if "Quality" in description:
        _draw_node(ax, latent_positions["Quality"], "Quality", latent=True)
        _draw_node(ax, observed_positions["CreditRating_ord"], "CreditRating_ord", latent=False)
        _draw_node(ax, observed_positions["IssueSize_log"], "IssueSize_log", latent=False)
        _draw_arrow(ax, latent_positions["Quality"], (0.76, 0.31))
        _draw_arrow(ax, latent_positions["Quality"], (0.9, 0.31))
        _draw_arrow(ax, latent_positions["Quality"], (0.57, 0.6))
    if "Greenium" in description:
        _draw_node(ax, latent_positions["Greenium"], "Greenium", latent=True)
        _draw_node(ax, observed_positions["ESG_num"], "ESG_num", latent=False)
        _draw_arrow(ax, latent_positions["Greenium"], (0.2, 0.31))
        if "Greenium ~ Quality" in description:
            _draw_arrow(ax, latent_positions["Quality"], latent_positions["Greenium"])
        _draw_arrow(ax, latent_positions["Greenium"], (0.49, 0.6))

    ax.text(0.5, 0.95, title, ha="center", va="top", fontsize=13, weight="bold")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"{model_key}_path_diagram.png", dpi=180)
    plt.close()


def main() -> None:
    warnings.filterwarnings("default")
    OUTPUT_DIR.mkdir(exist_ok=True)

    inr_data, complete_cases = prepare_data()
    corr = compute_correlation_matrix(complete_cases)
    efa_results = run_efa(complete_cases)
    efa_decision = classify_efa_variables(efa_results[3])

    print("\nEFA decision log using the 3-factor solution")
    print(efa_decision.round(3).to_string())
    for variable, row in efa_decision.iterrows():
        print(
            f"- {variable}: loading={row['loading']:.3f}, communality={row['communality']:.3f}, "
            f"{row['decision']}"
        )

    save_heatmap(corr)
    save_loading_chart(efa_results)

    model_results: list[dict[str, Any]] = []
    report_lines: list[str] = []

    for model_key, spec in MODEL_SPECS.items():
        print(f"\nFitting {spec['title']}")
        print(spec["purpose"])
        try:
            _, fit_stats, estimates = fit_sem_model(spec["description"], complete_cases)
            measurement = summarise_measurement(estimates)
            r2 = extract_r2(estimates, "BondPricing")
            model_results.append(
                {
                    "model": spec["title"],
                    "sample_n": int(complete_cases.shape[0]),
                    "CFI": float(fit_stats["CFI"]),
                    "RMSEA": float(fit_stats["RMSEA"]),
                    "Chi2": float(fit_stats["chi2"]),
                    "DoF": float(fit_stats["DoF"]),
                    "AIC": float(fit_stats["AIC"]),
                    "BIC": float(fit_stats["BIC"]),
                    "R2_BondPricing": float(r2),
                }
            )
            print("Measurement model")
            print(measurement.round(4).to_string(index=False))
            print("Fit statistics")
            print({k: round(float(fit_stats[k]), 4) for k in ["CFI", "RMSEA", "chi2", "DoF", "AIC", "BIC"]})
            if math.isnan(r2):
                print("R^2(BondPricing) = not identified / not meaningful for this specification")
            else:
                print(f"R^2(BondPricing) = {r2:.4f}")
            print("Structural coefficients")
            structural = estimates[(estimates["op"] == "~") & (estimates["lval"] == "BondPricing")]
            if "Greenium ~ Quality" in spec["description"]:
                structural = estimates[estimates["op"] == "~"]
            print(structural[["lval", "rval", "Est. Std", "p-value"]].to_string(index=False))
            save_path_diagram(model_key, spec["title"], spec["description"])

            report_lines.append(f"## {spec['title']}")
            report_lines.append(spec["purpose"])
            r2_text = "not identified" if math.isnan(r2) else f"{r2:.3f}"
            report_lines.append(f"CFI: {fit_stats['CFI']:.3f}, RMSEA: {fit_stats['RMSEA']:.3f}, R2(BondPricing): {r2_text}")
            report_lines.append(measurement.round(3).to_string(index=False))
            report_lines.append(structural[["lval", "rval", "Est. Std", "p-value"]].round(3).to_string(index=False))
        except Exception as exc:  # noqa: BLE001
            print(f"Model failed: {type(exc).__name__}: {exc}")
            model_results.append(
                {
                    "model": spec["title"],
                    "sample_n": int(complete_cases.shape[0]),
                    "CFI": np.nan,
                    "RMSEA": np.nan,
                    "Chi2": np.nan,
                    "DoF": np.nan,
                    "AIC": np.nan,
                    "BIC": np.nan,
                    "R2_BondPricing": np.nan,
                }
            )
            report_lines.append(f"## {spec['title']}")
            report_lines.append(f"Model failed: {exc}")

    comparison = pd.DataFrame(model_results)
    comparison = comparison.sort_values(by=["CFI", "RMSEA"], ascending=[False, True])
    comparison.to_csv(OUTPUT_DIR / "model_comparison.csv", index=False)
    print("\nModel comparison table")
    print(comparison.round(4).to_string(index=False))

    report = []
    report.append("# Indian Bond SEM Study")
    report.append("\n## Data preprocessing summary")
    report.append(f"INR rows: {inr_data.shape[0]} of {pd.read_csv(INPUT_FILE, low_memory=False).shape[0]}")
    report.append(f"Shared complete-case sample: {complete_cases.shape[0]} rows")
    report.append(efa_decision.round(3).to_string())
    report.append("\n## EFA findings")
    for n_factors, result in efa_results.items():
        report.append(f"### {n_factors} factors")
        report.append(result.loadings.round(3).to_string())
        report.append(result.communalities.round(3).to_string())
    report.append("\n## Model comparison")
    report.append(comparison.round(4).to_string(index=False))
    report.append("\n## Final interpretation")
    report.append(
        "The data support a strong pricing block around yield and coupon, but not a fully clean latent structure. "
        "Issuer quality is only partly supported: issue size behaves like the dominant indicator, while rating is weak. "
        "ESG is the weakest element in the measurement system and works better as a proxy predictor than a robust latent. "
        "Among the competing SEMs, the quality model is the least implausible compromise, but all models show non-trivial misfit, "
        "so the conclusions should be treated as exploratory rather than confirmatory."
    )
    report.append("\n## Decision logging")
    report.extend(report_lines)

    (OUTPUT_DIR / "report.md").write_text("\n\n".join(report), encoding="utf-8")
    print(f"\nWrote report and figures to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()