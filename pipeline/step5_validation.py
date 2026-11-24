"""
Step 5: Validation & Domain Sanity Checks
Validates week-to-week stability across October 2026 weeks, executes holdout
testing on Week 4, verifies peak-hour and weekday dominance sanity checks,
evaluates route continuity, detects holiday anomalies, and generates plots.
"""

import os
import sys
import time
import json
import yaml
import polars as pl
import numpy as np
import scipy.stats as stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_step5():
    print("=" * 80)
    print("STEP 5: VALIDATION & SANITY CHECKS")
    print("=" * 80)

    config = load_config()
    outputs_dir = config["paths"]["outputs_dir"]
    plots_dir = config["paths"]["plots_dir"]
    matched_parquet = os.path.join(outputs_dir, "matched_tickets_step2.parquet")
    estimated_parquet = os.path.join(outputs_dir, "estimated_segment_load_step4.parquet")

    t0 = time.time()
    print(f"[*] Ingesting matched tickets from: {matched_parquet}")
    df = pl.read_parquet(matched_parquet)
    print(f"[+] Loaded {len(df):,} tickets in {time.time()-t0:.2f}s")

    # Add Week Identifier (1 to 5)
    # Week 1: Oct 1-7, Week 2: Oct 8-14, Week 3: Oct 15-21, Week 4: Oct 22-28, Week 5: Oct 29-31
    df = df.with_columns(
        pl.when(pl.col("day_of_month") <= 7).then(1)
          .when(pl.col("day_of_month") <= 14).then(2)
          .when(pl.col("day_of_month") <= 21).then(3)
          .when(pl.col("day_of_month") <= 28).then(4)
          .otherwise(5)
          .alias("week_num")
    )

    # ---------------------------------------------------------
    # 1. WEEK-TO-WEEK STABILITY & HOLDOUT VALIDATION
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("1. WEEK-TO-WEEK STABILITY & HOLDOUT TESTING")
    print("-" * 60)

    # Aggregate weekly ticket volume per (route, direction, hour)
    weekly_agg = df.group_by(["route", "direction", "hour", "week_num"]).agg([
        pl.len().alias("tickets"),
        pl.col("passenger_count").sum().alias("passengers")
    ])

    # Select only relevant columns for clean pairwise join
    w1 = weekly_agg.filter(pl.col("week_num") == 1).select(["route", "direction", "hour", pl.col("tickets").alias("w1_tickets")])
    w2 = weekly_agg.filter(pl.col("week_num") == 2).select(["route", "direction", "hour", pl.col("tickets").alias("w2_tickets")])
    w3 = weekly_agg.filter(pl.col("week_num") == 3).select(["route", "direction", "hour", pl.col("tickets").alias("w3_tickets")])
    w4 = weekly_agg.filter(pl.col("week_num") == 4).select(["route", "direction", "hour", pl.col("tickets").alias("w4_tickets")])

    pivoted = w1.join(w2, on=["route", "direction", "hour"], how="inner") \
                .join(w3, on=["route", "direction", "hour"], how="inner") \
                .join(w4, on=["route", "direction", "hour"], how="inner")

    r_w1_w2, _ = stats.pearsonr(pivoted["w1_tickets"].to_numpy(), pivoted["w2_tickets"].to_numpy())
    r_w2_w3, _ = stats.pearsonr(pivoted["w2_tickets"].to_numpy(), pivoted["w3_tickets"].to_numpy())
    r_w3_w4, _ = stats.pearsonr(pivoted["w3_tickets"].to_numpy(), pivoted["w4_tickets"].to_numpy())

    print(f"Weekly Stability Correlations (Pearson r across matching cells):")
    print(f"   - Week 1 vs Week 2: r = {r_w1_w2:.4f}")
    print(f"   - Week 2 vs Week 3: r = {r_w2_w3:.4f}")
    print(f"   - Week 3 vs Week 4: r = {r_w3_w4:.4f}")

    # Holdout Test: Baseline (Weeks 1-3) vs Held-out Week 4
    baseline_agg = df.filter(pl.col("week_num") <= 3).group_by(["route", "direction", "hour"]).agg([
        (pl.len() / 3.0).alias("baseline_weekly_tickets"),
        (pl.col("passenger_count").sum() / 3.0).alias("baseline_weekly_passengers")
    ])

    holdout_comp = baseline_agg.join(
        weekly_agg.filter(pl.col("week_num") == 4).rename({"tickets": "holdout_tickets"}),
        on=["route", "direction", "hour"],
        how="inner"
    )

    y_true = holdout_comp["holdout_tickets"].to_numpy()
    y_pred = holdout_comp["baseline_weekly_tickets"].to_numpy()

    mae = np.mean(np.abs(y_true - y_pred))
    rmse = np.sqrt(np.mean((y_true - y_pred)**2))
    # Relative MAPE for cells with >= 10 tickets
    mask_dense = y_true >= 10
    mape = np.mean(np.abs(y_true[mask_dense] - y_pred[mask_dense]) / y_true[mask_dense]) * 100
    r2_score = 1.0 - (np.sum((y_true - y_pred)**2) / np.sum((y_true - np.mean(y_true))**2))
    corr_holdout, _ = stats.pearsonr(y_pred, y_true)

    print(f"\nHoldout Test (Weeks 1-3 Baseline -> Held-Out Week 4):")
    print(f"   - Evaluation Cells:  {len(holdout_comp):,} (route, direction, hour) triplets")
    print(f"   - Correlation (r):   {corr_holdout:.4f}")
    print(f"   - R2 Score:          {r2_score:.4f}")
    print(f"   - MAE:               {mae:.2f} tickets")
    print(f"   - MAPE:              {mape:.2f}%")

    # ---------------------------------------------------------
    # 2. DOMAIN SANITY CHECKS
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("2. DOMAIN SANITY CHECKS")
    print("-" * 60)

    # Sanity Check 1: Morning & Evening Peak vs Midday Trough
    hourly_loads = df.group_by("hour").agg([
        pl.len().alias("tickets"),
        pl.col("passenger_count").sum().alias("passengers")
    ]).sort("hour")

    morning_peak = hourly_loads.filter(pl.col("hour").is_in([8, 9]))["tickets"].sum() / 2.0
    evening_peak = hourly_loads.filter(pl.col("hour").is_in([17, 18, 19]))["tickets"].sum() / 3.0
    midday_trough = hourly_loads.filter(pl.col("hour").is_in([12, 13, 14]))["tickets"].sum() / 3.0
    night_trough = hourly_loads.filter(pl.col("hour").is_in([1, 2, 3]))["tickets"].sum() / 3.0

    am_ratio = morning_peak / midday_trough
    pm_ratio = evening_peak / midday_trough

    print("A. Dual Peak Verification:")
    print(f"   - Morning Peak (8-10 AM) Avg Tickets/hr:  {morning_peak:,.0f}")
    print(f"   - Evening Peak (5-8 PM) Avg Tickets/hr:   {evening_peak:,.0f}")
    print(f"   - Midday Trough (12-3 PM) Avg Tickets/hr: {midday_trough:,.0f}")
    print(f"   - Morning-to-Midday Ratio:               {am_ratio:.2f}x (Peak Verified: {am_ratio > 1.2})")
    print(f"   - Evening-to-Midday Ratio:               {pm_ratio:.2f}x (Peak Verified: {pm_ratio > 1.2})")

    # Sanity Check 2: Weekday vs Weekend Volume
    day_loads = df.group_by("day_type").agg([
        pl.len().alias("tickets"),
        pl.col("date").n_unique().alias("num_days")
    ]).with_columns(
        (pl.col("tickets") / pl.col("num_days")).alias("avg_daily_tickets")
    )

    weekday_avg = day_loads.filter(pl.col("day_type") == "weekday")["avg_daily_tickets"][0]
    weekend_avg = day_loads.filter(pl.col("day_type") == "weekend")["avg_daily_tickets"][0]
    wd_ratio = weekday_avg / weekend_avg

    print("\nB. Weekday vs Weekend Dominance:")
    print(f"   - Average Weekday Tickets/day: {weekday_avg:,.0f}")
    print(f"   - Average Weekend Tickets/day: {weekend_avg:,.0f}")
    print(f"   - Weekday-to-Weekend Ratio:    {wd_ratio:.2f}x (Weekday Dominance: {wd_ratio > 1.0})")

    # Sanity Check 3: Non-Negative Loads
    est_df = pl.read_parquet(estimated_parquet)
    negative_loads = int((est_df["est_load_per_bus"] < 0).sum())
    print(f"\nC. Non-Negative Load Check:")
    print(f"   - Negative Load Count: {negative_loads} (100% Non-Negative: {negative_loads == 0})")

    # Sanity Check 4: Route Load Profile Continuity
    # Route 717AUP (Top route in Delhi)
    r717_segments = est_df.filter(
        (pl.col("route") == "717AUP") &
        (pl.col("time_bin_15m") == "09:00") &
        (pl.col("day_type") == "weekday")
    ).sort("from_stop_idx")

    print(f"\nD. Route Load Profile Check (Route 717AUP at 9:00 AM Weekday):")
    if len(r717_segments) > 0:
        p_start = r717_segments["est_load_per_bus"][0]
        p_max = r717_segments["est_load_per_bus"].max()
        p_end = r717_segments["est_load_per_bus"][-1]
        print(f"   - Terminal Start Load:   {p_start:.1f} pax")
        print(f"   - Mid-Corridor Peak Load:{p_max:.1f} pax")
        print(f"   - Terminus End Load:     {p_end:.1f} pax")
        is_concave = bool(p_max > p_start and p_max > p_end)
        print(f"   - Concave Profile (Rises from start, peaks in middle, drops at end): {is_concave}")

    # ---------------------------------------------------------
    # 3. KNOWN CALENDAR ANOMALIES (OCTOBER 2026 HOLIDAYS)
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("3. KNOWN EVENT / FESTIVAL ANOMALIES CHECK")
    print("-" * 60)

    daily_totals = df.group_by("date").agg([
        pl.len().alias("tickets"),
        pl.col("is_weekend").first().alias("is_weekend"),
        pl.col("day_of_month").first().alias("day")
    ]).sort("date")

    # Oct 02: Gandhi Jayanti (Friday)
    gandhi_jayanti_tickets = daily_totals.filter(pl.col("day") == 2)["tickets"][0]
    regular_fridays = daily_totals.filter((pl.col("day").is_in([9, 16, 23])) & (~pl.col("is_weekend")))["tickets"].mean()
    gandhi_drop_pct = (1.0 - (gandhi_jayanti_tickets / regular_fridays)) * 100

    # Oct 20: Dussehra (Tuesday)
    dussehra_tickets = daily_totals.filter(pl.col("day") == 20)["tickets"][0]
    regular_tuesdays = daily_totals.filter(pl.col("day").is_in([6, 13, 27]))["tickets"].mean()
    dussehra_drop_pct = (1.0 - (dussehra_tickets / regular_tuesdays)) * 100

    print("Holiday Ridership Impact Analysis:")
    print(f"   - Oct 02 (Gandhi Jayanti, Fri): {gandhi_jayanti_tickets:,} tickets (vs regular Fri avg {regular_fridays:,.0f}, drop = -{gandhi_drop_pct:.1f}%)")
    print(f"   - Oct 20 (Dussehra, Tue):       {dussehra_tickets:,} tickets (vs regular Tue avg {regular_tuesdays:,.0f}, drop = -{dussehra_drop_pct:.1f}%)")

    # ---------------------------------------------------------
    # 4. GENERATE STEP 5 VALIDATION PLOTS
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("4. GENERATING VALIDATION VISUALIZATIONS")
    print("-" * 60)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot 1: Holdout Validation Scatter (Weeks 1-3 Baseline vs Week 4 Actual)
    sample_h = holdout_comp.filter(pl.col("holdout_tickets") >= 5).sample(n=min(3000, len(holdout_comp)), seed=42).to_pandas()
    axes[0, 0].scatter(sample_h["baseline_weekly_tickets"], sample_h["holdout_tickets"], alpha=0.4, color="#2563eb", s=25)
    max_val = max(sample_h["baseline_weekly_tickets"].max(), sample_h["holdout_tickets"].max())
    axes[0, 0].plot([0, max_val], [0, max_val], color="#ef4444", linestyle="--", linewidth=2, label="Perfect Agreement (1:1)")
    axes[0, 0].set_title(f"Holdout Test: Baseline vs Week 4 (r = {corr_holdout:.3f}, R² = {r2_score:.3f})", fontsize=12, fontweight="bold")
    axes[0, 0].set_xlabel("Predicted Baseline Tickets (Weeks 1-3)")
    axes[0, 0].set_ylabel("Observed Tickets (Held-Out Week 4)")
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)

    # Plot 2: 24-Hour Diurnal Load Curve (Dual Peak Sanity Check)
    hourly_df = hourly_loads.to_pandas()
    axes[0, 1].plot(hourly_df["hour"], hourly_df["tickets"], marker="o", color="#059669", linewidth=2.5)
    axes[0, 1].axvspan(8, 10, color="#ef4444", alpha=0.15, label="Morning Peak (8-10 AM)")
    axes[0, 1].axvspan(17, 20, color="#f59e0b", alpha=0.15, label="Evening Peak (5-8 PM)")
    axes[0, 1].set_title("Network Diurnal Curve: Dual Peak Commute Verification", fontsize=12, fontweight="bold")
    axes[0, 1].set_xlabel("Hour of Day (IST)")
    axes[0, 1].set_ylabel("Ticket Volume")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)

    # Plot 3: Route Profile Along Stop Sequence (Concavity Check)
    if len(r717_segments) > 0:
        r717_pd = r717_segments.to_pandas()
        axes[1, 0].plot(r717_pd["from_stop_idx"], r717_pd["est_load_per_bus"], marker="o", color="#7c3aed", linewidth=2.5)
        axes[1, 0].set_title("Route 717A Concave Load Profile (Morning Peak 9:00 AM)", fontsize=12, fontweight="bold")
        axes[1, 0].set_xlabel("Stop Sequence Progression (Badarpur -> Kapashera)")
        axes[1, 0].set_ylabel("Estimated On-Board Passengers")
        axes[1, 0].grid(True, alpha=0.3)

    # Plot 4: Daily October Timeline (Holiday Drops)
    d_df = daily_totals.to_pandas()
    axes[1, 1].plot(d_df["day"], d_df["tickets"], marker="s", color="#3b82f6", linewidth=2)
    # Highlight holidays
    axes[1, 1].scatter([2], [gandhi_jayanti_tickets], color="#dc2626", s=100, zorder=5, label=f"Gandhi Jayanti (-{gandhi_drop_pct:.0f}%)")
    axes[1, 1].scatter([20], [dussehra_tickets], color="#ea580c", s=100, zorder=5, label=f"Dussehra (-{dussehra_drop_pct:.0f}%)")
    axes[1, 1].set_title("October 2026 Daily Timeline: Public Holiday Dips", fontsize=12, fontweight="bold")
    axes[1, 1].set_xlabel("Day of Month (October 2026)")
    axes[1, 1].set_ylabel("Daily Tickets")
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    val_plot_path = os.path.join(plots_dir, "step5_validation_sanity_checks.png")
    plt.savefig(val_plot_path, dpi=200)
    plt.close()
    print(f"[+] Saved validation plot to: {val_plot_path}")

    # Summary Report
    step5_report = {
        "weekly_correlations": {
            "w1_w2": round(float(r_w1_w2), 4),
            "w2_w3": round(float(r_w2_w3), 4),
            "w3_w4": round(float(r_w3_w4), 4)
        },
        "holdout_week4_validation": {
            "r2_score": round(float(r2_score), 4),
            "pearson_r": round(float(corr_holdout), 4),
            "mae_tickets": round(float(mae), 2),
            "mape_pct": round(float(mape), 2)
        },
        "sanity_checks": {
            "morning_to_midday_ratio": round(float(am_ratio), 2),
            "evening_to_midday_ratio": round(float(pm_ratio), 2),
            "weekday_to_weekend_ratio": round(float(wd_ratio), 2),
            "negative_loads_count": negative_loads,
            "route_continuity_concave": is_concave
        },
        "holiday_anomalies": {
            "gandhi_jayanti_drop_pct": round(float(gandhi_drop_pct), 1),
            "dussehra_drop_pct": round(float(dussehra_drop_pct), 1)
        },
        "plot_saved": val_plot_path
    }
    with open(os.path.join(outputs_dir, "step5_validation_report.json"), "w", encoding="utf-8") as f:
        json.dump(step5_report, f, indent=2)

    print("\n" + "=" * 80)
    print("STEP 5 COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    run_step5()
