"""
Step 4: On-Board Load & Crowdedness Estimation Engine
Computes segment-level on-board load using prefix-sum persistence, applies
alighting smoothing, incorporates Delhi Pink Pass uplift (+25%), performs
sensitivity analysis, computes load factors against bus capacities, and assigns
confidence tiers.
"""

import os
import sys
import time
import json
import yaml
import polars as pl
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_step4():
    print("=" * 80)
    print("STEP 4: ON-BOARD LOAD & CROWDEDNESS ESTIMATION ENGINE")
    print("=" * 80)

    config = load_config()
    outputs_dir = config["paths"]["outputs_dir"]
    plots_dir = config["paths"]["plots_dir"]
    gtfs_dir = config["paths"]["gtfs_dir"]
    input_parquet = os.path.join(outputs_dir, "matched_tickets_step2.parquet")

    # Load parameters from config
    pink_pass_factor = config["load_estimation"].get("pink_pass_uplift_factor", 1.25)
    expansion_factor = config["load_estimation"].get("daily_sampling_expansion_factor", 22.0)
    sensitivity_factors = config["load_estimation"].get("sensitivity_factors", [1.10, 1.20, 1.25, 1.35, 1.50])
    cap_non_ac = config["load_estimation"]["capacities"].get("standard_non_ac", 65)
    cap_ac = config["load_estimation"]["capacities"].get("standard_ac", 60)
    thresh_seated = config["load_estimation"]["crowding_thresholds"].get("seated", 0.65)
    thresh_standing = config["load_estimation"]["crowding_thresholds"].get("standing", 1.05)

    conf_tickets_high = config["load_estimation"]["confidence"].get("min_tickets_high", 50)
    conf_tickets_med = config["load_estimation"]["confidence"].get("min_tickets_med", 15)
    conf_days_high = config["load_estimation"]["confidence"].get("min_days_high", 7)
    conf_days_med = config["load_estimation"]["confidence"].get("min_days_med", 3)

    t0 = time.time()
    print(f"[*] Reading matched tickets from: {input_parquet}")
    df = pl.read_parquet(input_parquet)
    total_tickets = len(df)
    print(f"[+] Ingested {total_tickets:,} tickets in {time.time()-t0:.2f}s")

    # 1. Load Route Stop Sequences from GTFS
    seq_cache_path = os.path.join(gtfs_dir, "route_stop_sequences.json")
    with open(seq_cache_path, "r", encoding="utf-8") as f:
        route_stop_sequences = json.load(f)
    print(f"[+] Loaded route stop sequences for {len(route_stop_sequences):,} routes")

    # Overall missing vehicle scaling factor (from Step 3)
    # Total tickets / tickets with known vehicle
    n_known = len(df.filter(pl.col("vehicle_number").is_not_null()))
    scaling_factor_kappa = total_tickets / n_known
    print(f"[+] Scaling Factor kappa (Total / Known): {scaling_factor_kappa:.4f}")
    print(f"[+] Delhi Pink Pass Uplift Factor:        {pink_pass_factor:.2f} (+{(pink_pass_factor-1)*100:.0f}%)")

    # ---------------------------------------------------------
    # 2. SEGMENT LOAD COMPUTATION VIA DIFFERENCE ARRAY (PREFIX SUM)
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("2. COMPUTING SEGMENT-LEVEL LOAD VIA PREFIX-SUM INTERVAL PERSISTENCE")
    print("-" * 60)

    # We aggregate boardings (+p) at start_stop_idx and alightings (-p) at end_stop_idx
    # grouped by (route, direction, time_bin_15m, day_type, is_ac)
    print("[*] Aggregating boardings and alightings per cell...")

    boardings_agg = df.group_by([
        "route", "direction", "time_bin_15m", "day_type", "is_ac", "start_stop_idx"
    ]).agg([
        pl.col("passenger_count").sum().alias("boardings"),
        pl.len().alias("boarding_tickets"),
        pl.col("date").n_unique().alias("active_days")
    ]).rename({"start_stop_idx": "stop_idx"})

    alightings_agg = df.group_by([
        "route", "direction", "time_bin_15m", "day_type", "is_ac", "end_stop_idx"
    ]).agg([
        pl.col("passenger_count").sum().alias("alightings")
    ]).rename({"end_stop_idx": "stop_idx"})

    # Combine boardings and alightings
    flow_df = boardings_agg.join(
        alightings_agg,
        on=["route", "direction", "time_bin_15m", "day_type", "is_ac", "stop_idx"],
        how="full"
    ).fill_null(0)

    print(f"[+] Flow table compiled: {len(flow_df):,} stop-level flow records")

    # ---------------------------------------------------------
    # 3. APPLY SEGMENT CUMSUM, ALIGHTING SMOOTHING & UPLIFT
    # ---------------------------------------------------------
    print("\n[*] Applying interval persistence, smoothing, Pink Pass uplift, and capacity factors...")
    calc_t0 = time.time()

    # Process each unique cell (route, direction, time_bin_15m, day_type, is_ac)
    # Sort by stop_idx within each cell and compute cumulative on-board load
    cells_unique = flow_df.select(["route", "direction", "time_bin_15m", "day_type", "is_ac"]).unique()
    print(f"[+] Total route-time cells: {len(cells_unique):,}")

    # Sort flow_df by stop_idx
    flow_sorted = flow_df.sort(["route", "direction", "time_bin_15m", "day_type", "is_ac", "stop_idx"])

    # Compute net change and cumulative sum
    flow_sorted = flow_sorted.with_columns(
        (pl.col("boardings") - pl.col("alightings")).alias("net_change")
    )
    flow_sorted = flow_sorted.with_columns(
        pl.col("net_change").cum_sum().over(["route", "direction", "time_bin_15m", "day_type", "is_ac"]).alias("cum_passengers")
    )

    # Shift cum_passengers to represent segment k (from stop k to stop k+1)
    # The load on segment k is the cumulative load after boarding/alighting at stop k
    segment_records = []
    
    # We will build segment-level rows
    # Convert to segment table: segment from stop_idx k to k+1
    flow_sorted = flow_sorted.with_columns([
        pl.col("stop_idx").alias("from_stop_idx"),
        (pl.col("stop_idx") + 1).alias("to_stop_idx")
    ])

    # Convert to Python iteration for fast stop-sequence string mapping & smoothing
    # We can group by route
    segment_rows = []
    unique_routes_set = set(route_stop_sequences.keys())

    # We can compute segment statistics vectorized in Polars
    # Filter out terminal stop segments beyond route sequence length
    flow_agg_cell = flow_sorted.filter(pl.col("cum_passengers") > 0)

    # Map stop names and compute capacity, load factor, and confidence
    # Total tickets in cell = sum of boarding_tickets in that cell
    cell_totals = flow_sorted.group_by(["route", "direction", "time_bin_15m", "day_type", "is_ac"]).agg([
        pl.col("boarding_tickets").sum().alias("total_cell_tickets"),
        pl.col("active_days").max().alias("cell_days")
    ])

    flow_joined = flow_agg_cell.join(
        cell_totals,
        on=["route", "direction", "time_bin_15m", "day_type", "is_ac"],
        how="left"
    )

    # Apply 3-point alighting smoothing: 10% prev, 80% current, 10% next segment
    flow_joined = flow_joined.with_columns([
        pl.col("cum_passengers").shift(1).over(["route", "direction", "time_bin_15m", "day_type", "is_ac"]).fill_null(strategy="forward").alias("prev_cum"),
        pl.col("cum_passengers").shift(-1).over(["route", "direction", "time_bin_15m", "day_type", "is_ac"]).fill_null(strategy="backward").alias("next_cum")
    ])

    flow_joined = flow_joined.with_columns(
        (0.80 * pl.col("cum_passengers") + 0.10 * pl.col("prev_cum") + 0.10 * pl.col("next_cum")).alias("smoothed_passengers")
    )

    # Base load per bus:
    # (smoothed_passengers / cell_days) * (pink_pass_factor) * (1/2 trips per bin) * expansion_factor
    # Capacity lookup
    flow_joined = flow_joined.with_columns([
        pl.when(pl.col("is_ac")).then(cap_ac).otherwise(cap_non_ac).alias("bus_capacity"),
        (
            (pl.col("smoothed_passengers") / pl.col("cell_days").clip(1, 31)) *
            pink_pass_factor *
            (1.0 / 2.0) *
            expansion_factor
        ).alias("est_load_per_bus")
    ])

    # Compute Load Factor
    flow_joined = flow_joined.with_columns(
        (pl.col("est_load_per_bus") / pl.col("bus_capacity")).round(3).alias("load_factor")
    )

    # Assign 3-tier Crowding Level
    flow_joined = flow_joined.with_columns(
        pl.when(pl.col("load_factor") <= thresh_seated)
          .then(pl.lit("SEATS_AVAILABLE"))
          .when(pl.col("load_factor") <= thresh_standing)
          .then(pl.lit("STANDING_ROOM"))
          .otherwise(pl.lit("CROWDED"))
          .alias("crowding_level")
    )

    # Assign Confidence Tier
    flow_joined = flow_joined.with_columns(
        pl.when((pl.col("total_cell_tickets") >= conf_tickets_high) & (pl.col("cell_days") >= conf_days_high))
          .then(pl.lit("HIGH"))
          .when((pl.col("total_cell_tickets") >= conf_tickets_med) & (pl.col("cell_days") >= conf_days_med))
          .then(pl.lit("MEDIUM"))
          .otherwise(pl.lit("LOW"))
          .alias("confidence")
    )

    total_segments = len(flow_joined)
    print(f"[+] Computed {total_segments:,} segment load profiles in {time.time()-calc_t0:.2f}s")

    # Crowding tier distribution
    crowd_dist = flow_joined.group_by("crowding_level").len().with_columns(
        (pl.col("len") / total_segments * 100).round(2).alias("pct")
    ).sort("len", descending=True)
    print("\nCrowding Level Distribution Across All Segments:")
    print(crowd_dist)

    conf_dist = flow_joined.group_by("confidence").len().with_columns(
        (pl.col("len") / total_segments * 100).round(2).alias("pct")
    ).sort("len", descending=True)
    print("\nConfidence Tier Distribution:")
    print(conf_dist)

    # ---------------------------------------------------------
    # 4. SENSITIVITY ANALYSIS (PINK PASS UPLIFT)
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("4. SENSITIVITY ANALYSIS: DELPHI PINK PASS UPLIFT FACTORS")
    print("-" * 60)

    sens_results = []
    base_est = (flow_joined["smoothed_passengers"] / flow_joined["cell_days"].clip(1, 31) * 0.5) * expansion_factor
    capacities = flow_joined["bus_capacity"]

    for factor in sensitivity_factors:
        lf_sens = (base_est * factor) / capacities
        pct_seats = float((lf_sens <= thresh_seated).mean() * 100)
        pct_standing = float(((lf_sens > thresh_seated) & (lf_sens <= thresh_standing)).mean() * 100)
        pct_crowded = float((lf_sens > thresh_standing).mean() * 100)
        sens_results.append({
            "uplift_factor": factor,
            "mean_load_factor": round(float(lf_sens.mean()), 3),
            "pct_seats_available": round(pct_seats, 1),
            "pct_standing_room": round(pct_standing, 1),
            "pct_crowded": round(pct_crowded, 1)
        })
        print(f"Uplift {factor:.2f}x: Mean LF = {lf_sens.mean():.3f} | Seats: {pct_seats:>5.1f}% | Standing: {pct_standing:>5.1f}% | Crowded: {pct_crowded:>5.1f}%")

    # ---------------------------------------------------------
    # 5. GENERATE STEP 4 PLOTS
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("5. GENERATING STEP 4 VISUALIZATIONS")
    print("-" * 60)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Plot A: Sensitivity Analysis Plot
    sens_df = pl.DataFrame(sens_results).to_pandas()
    axes[0].plot(sens_df["uplift_factor"], sens_df["pct_seats_available"], marker="o", color="#10b981", label="Seats Available (%)", linewidth=2.5)
    axes[0].plot(sens_df["uplift_factor"], sens_df["pct_standing_room"], marker="s", color="#f59e0b", label="Standing Room (%)", linewidth=2.5)
    axes[0].plot(sens_df["uplift_factor"], sens_df["pct_crowded"], marker="^", color="#ef4444", label="Crowded / Packed (%)", linewidth=2.5)
    axes[0].axvline(pink_pass_factor, color="#6b7280", linestyle="--", label=f"Selected Baseline ({pink_pass_factor:.2f}x)")
    axes[0].set_title("Sensitivity of Crowding Tiers to Pink Pass Uplift Factor", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Pink Pass / Free Rider Uplift Factor")
    axes[0].set_ylabel("Share of Network Segments (%)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot B: Load Factor Distribution by Day Type (Weekday vs Weekend)
    sample_lf = flow_joined.sample(n=min(50000, len(flow_joined)), seed=42).to_pandas()
    sns.kdeplot(data=sample_lf, x="load_factor", hue="day_type", common_norm=False, ax=axes[1], palette={"weekday": "#2563eb", "weekend": "#f59e0b"}, linewidth=2.5)
    axes[1].axvline(thresh_seated, color="#10b981", linestyle="--", label="Seats / Standing Cutoff (0.65)")
    axes[1].axvline(thresh_standing, color="#ef4444", linestyle="--", label="Standing / Crowded Cutoff (1.05)")
    axes[1].set_title("Load Factor Density Distribution (Weekday vs Weekend)", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Segment Load Factor (Load / Capacity)")
    axes[1].set_ylabel("Density")
    axes[1].set_xlim(0, 2.5)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plot_path = os.path.join(plots_dir, "step4_load_sensitivity_profile.png")
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"[+] Saved sensitivity profile plot to: {plot_path}")

    # ---------------------------------------------------------
    # 6. EXPORT STEP 4 ESTIMATES PARQUET
    # ---------------------------------------------------------
    output_parquet = os.path.join(outputs_dir, "estimated_segment_load_step4.parquet")
    print(f"\n[*] Exporting segment load dataset ({len(flow_joined):,} rows) to: {output_parquet}")
    flow_joined.write_parquet(output_parquet)

    step4_report = {
        "total_segments_estimated": total_segments,
        "pink_pass_factor": pink_pass_factor,
        "capacities": {"ac": cap_ac, "non_ac": cap_non_ac},
        "crowding_distribution": crowd_dist.to_dicts(),
        "confidence_distribution": conf_dist.to_dicts(),
        "sensitivity_analysis": sens_results,
        "plot_saved": plot_path
    }
    with open(os.path.join(outputs_dir, "step4_report.json"), "w", encoding="utf-8") as f:
        json.dump(step4_report, f, indent=2)

    print("\n" + "=" * 80)
    print("STEP 4 COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    run_step4()
