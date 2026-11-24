"""
Step 1: Data Cleaning & Exploratory Data Analysis (EDA)
Profiles missing vehicle_numbers, parses timestamps and routes, audits anomalies,
and produces EDA visualizations and summary statistics.
"""

import os
import re
import sys
import time
import json
import yaml
import polars as pl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def run_step1():
    print("=" * 80)
    print("STEP 1: DATA CLEANING & EXPLORATORY DATA ANALYSIS (EDA)")
    print("=" * 80)

    config = load_config()
    csv_path = config["paths"]["ticket_csv"]
    plots_dir = config["paths"]["plots_dir"]
    outputs_dir = config["paths"]["outputs_dir"]
    os.makedirs(plots_dir, exist_ok=True)
    os.makedirs(outputs_dir, exist_ok=True)

    t0 = time.time()
    print(f"[*] Ingesting raw ticket dataset from: {csv_path}")
    # Note: Ticket dataset uses literal string 'NULL' for missing values
    raw_df = pl.read_csv(
        csv_path,
        null_values=["NULL", "null", "None", "NaN", ""]
    )
    total_raw_rows = len(raw_df)
    print(f"[+] Loaded {total_raw_rows:,} rows across {len(raw_df.columns)} columns in {time.time()-t0:.2f}s")

    # ---------------------------------------------------------
    # 1. PROFILE MISSING vehicle_number
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("1. PROFILING MISSING vehicle_number")
    print("-" * 60)

    nan_vehicle_count = raw_df["vehicle_number"].is_null().sum()
    nan_vehicle_pct = (nan_vehicle_count / total_raw_rows) * 100
    print(f"Total Rows:                   {total_raw_rows:,}")
    print(f"Rows with vehicle_number:     {total_raw_rows - nan_vehicle_count:,} ({100 - nan_vehicle_pct:.2f}%)")
    print(f"Rows with NaN/NULL vehicle_id:{nan_vehicle_count:,} ({nan_vehicle_pct:.2f}%)")

    # ---------------------------------------------------------
    # 2. TIMESTAMP PARSING & TEMPORAL ATTRIBUTES
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("2. PARSING TIMESTAMPS (Asia/Kolkata)")
    print("-" * 60)

    # created_at format: "2026-10-28 10:19:18.780611+05:30"
    df = raw_df.with_columns(
        pl.col("created_at").str.slice(0, 19).str.to_datetime("%Y-%m-%d %H:%M:%S").alias("dt")
    )
    df = df.with_columns([
        pl.col("dt").dt.date().alias("date"),
        pl.col("dt").dt.hour().alias("hour"),
        pl.col("dt").dt.weekday().alias("weekday"), # 1=Mon, 7=Sun in Polars
        pl.col("dt").dt.minute().alias("minute"),
        pl.col("dt").dt.day().alias("day_of_month")
    ])

    # Add 15-minute time bin and weekend flag
    df = df.with_columns([
        ((pl.col("hour") * 4) + (pl.col("minute") // 15)).alias("time_bin_15m_idx"),
        (pl.col("hour").cast(pl.String).str.zfill(2) + ":" + ((pl.col("minute") // 15) * 15).cast(pl.String).str.zfill(2)).alias("time_bin_15m"),
        (pl.col("weekday") >= 6).alias("is_weekend"),
        pl.when(pl.col("weekday") >= 6).then(pl.lit("weekend")).otherwise(pl.lit("weekday")).alias("day_type")
    ])

    # NaN Vehicle breakdown by Hour
    nan_by_hour = df.group_by("hour").agg([
        pl.len().alias("total_tickets"),
        pl.col("vehicle_number").is_null().sum().alias("nan_vehicles")
    ]).with_columns(
        (pl.col("nan_vehicles") / pl.col("total_tickets") * 100).round(2).alias("nan_pct")
    ).sort("hour")

    # NaN Vehicle breakdown by Day of Month
    nan_by_day = df.group_by("day_of_month").agg([
        pl.len().alias("total_tickets"),
        pl.col("vehicle_number").is_null().sum().alias("nan_vehicles")
    ]).with_columns(
        (pl.col("nan_vehicles") / pl.col("total_tickets") * 100).round(2).alias("nan_pct")
    ).sort("day_of_month")

    # NaN Vehicle breakdown by Top 20 Routes
    nan_by_route = df.group_by("route").agg([
        pl.len().alias("total_tickets"),
        pl.col("vehicle_number").is_null().sum().alias("nan_vehicles")
    ]).with_columns(
        (pl.col("nan_vehicles") / pl.col("total_tickets") * 100).round(2).alias("nan_pct")
    ).sort("total_tickets", descending=True).head(20)

    print(f"[+] Timestamp parsing completed. Date span: {df['date'].min()} to {df['date'].max()} ({df['date'].n_unique()} days)")
    print(f"NaN % across 24 Hours: Min = {nan_by_hour['nan_pct'].min():.1f}%, Max = {nan_by_hour['nan_pct'].max():.1f}%")
    print(f"NaN % across 31 Days:  Min = {nan_by_day['nan_pct'].min():.1f}%, Max = {nan_by_day['nan_pct'].max():.1f}%")

    print("\nTop 10 Routes Missing Vehicle Breakdown:")
    for row in nan_by_route.head(10).iter_rows(named=True):
        print(f"   Route {row['route']:<12}: Total {row['total_tickets']:>7,}, NaN Vehicles: {row['nan_vehicles']:>7,} ({row['nan_pct']:>5.1f}%)")

    # ---------------------------------------------------------
    # 3. ROUTE REGEX PARSING & ANOMALY DETECTION
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("3. ROUTE REGEX PARSING & ANOMALY DETECTION")
    print("-" * 60)

    unique_routes = df["route"].unique().to_list()
    print(f"Total Unique Raw Route Strings: {len(unique_routes)}")

    # Extended regex: extracts base route, UP/DOWN direction, and optional sub-trip/variant suffix (e.g. '863DOWN2', '8UP')
    route_regex = re.compile(r"^(.*?)(UP|DOWN)(\d*)$", re.IGNORECASE)

    standard_parsed = 0
    anomalous_routes = []

    for r in unique_routes:
        if not r or not isinstance(r, str):
            anomalous_routes.append((r, "Null or Non-string"))
            continue
        m = route_regex.match(r.strip())
        if m:
            standard_parsed += 1
        else:
            anomalous_routes.append((r, "Missing UP/DOWN suffix (e.g. Circular / Special)"))

    print(f"Standard Routes (matched '^(.*?)(UP|DOWN)(\\d*)$'): {standard_parsed} ({standard_parsed/len(unique_routes)*100:.1f}%)")
    print(f"Special / Circular Routes (without UP/DOWN): {len(anomalous_routes)}")
    if anomalous_routes:
        print("Sample Special Routes:")
        for r_str, reason in anomalous_routes[:10]:
            print(f"   '{r_str}': {reason}")

    # Extract base_route and direction
    df = df.with_columns([
        pl.col("route").str.extract(r"^(.*?)(?:UP|DOWN)(?:\d*)$", 1).alias("base_route"),
        pl.col("route").str.extract(r"(UP|DOWN)", 1).alias("direction")
    ])

    # For routes without UP/DOWN (e.g. 'DS CIRCULAR'), set base_route = route, direction = 'LOOP'
    df = df.with_columns([
        pl.when(pl.col("direction").is_null())
          .then(pl.col("route"))
          .otherwise(pl.col("base_route"))
          .alias("base_route"),
        pl.when(pl.col("direction").is_null())
          .then(pl.lit("LOOP"))
          .otherwise(pl.col("direction"))
          .alias("direction")
    ])

    # ---------------------------------------------------------
    # 4. DATA VALIDATION & AUDITED FILTERING
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("4. AUDITED FILTERING & OUTLIER DETECTION (NO SILENT DROPS)")
    print("-" * 60)

    audit_log = []

    # A. Check Duplicates
    dup_mask = df.is_duplicated()
    dup_count = int(dup_mask.sum())
    print(f"[Audit] Exact duplicate rows: {dup_count:,}")
    audit_log.append({"filter": "Exact duplicates", "removed": dup_count, "reason": "Identical ticket logs recorded concurrently"})

    # B. Passenger count <= 0 or extreme outliers
    zero_pax_mask = df["passenger_count"] <= 0
    zero_pax_count = int(zero_pax_mask.sum())
    pax_outlier_mask = df["passenger_count"] > 10
    pax_outlier_count = int(pax_outlier_mask.sum())
    print(f"[Audit] Tickets with passenger_count <= 0: {zero_pax_count}")
    print(f"[Audit] Tickets with passenger_count > 10:  {pax_outlier_count}")
    audit_log.append({"filter": "passenger_count <= 0", "removed": zero_pax_count, "reason": "Zero or negative passengers"})

    # C. Start stop == End stop
    same_stop_mask = df["start_stop_name"] == df["end_stop_name"]
    same_stop_count = int(same_stop_mask.sum())
    print(f"[Audit] Start stop equals End stop (zero-distance): {same_stop_count:,}")
    audit_log.append({"filter": "start_stop == end_stop", "removed": same_stop_count, "reason": "Zero-distance trip transaction"})

    # D. Fare / Amount anomalies
    zero_fare_mask = df["amount"] <= 0
    zero_fare_count = int(zero_fare_mask.sum())
    high_fare_mask = df["amount"] > 100
    high_fare_count = int(high_fare_mask.sum())
    print(f"[Audit] Tickets with amount <= 0: {zero_fare_count}")
    print(f"[Audit] Tickets with amount > ₹100: {high_fare_count}")
    audit_log.append({"filter": "amount <= 0", "removed": zero_fare_count, "reason": "Zero or negative ticket fare"})

    # Execute Audited Filtering
    clean_condition = (
        (df["passenger_count"] > 0) &
        (df["amount"] > 0) &
        (df["start_stop_name"] != df["end_stop_name"])
    )
    cleaned_df = df.filter(clean_condition)
    total_removed = len(df) - len(cleaned_df)
    retention_pct = (len(cleaned_df) / len(df)) * 100

    print(f"\n[+] Total rows BEFORE cleaning: {len(df):,}")
    print(f"[-] Total rows REMOVED:          {total_removed:,} ({100 - retention_pct:.4f}%)")
    print(f"[=] Total rows AFTER cleaning:   {len(cleaned_df):,} ({retention_pct:.4f}% retained)")

    # ---------------------------------------------------------
    # 5. TICKET_TYPE_ID ANALYSIS & FARE STRUCTURE
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("5. TICKET_TYPE_ID PROFILE & FARE PATTERNS")
    print("-" * 60)

    ticket_profile = cleaned_df.group_by("ticket_type_id").agg([
        pl.len().alias("count"),
        pl.col("amount").mean().round(2).alias("mean_fare"),
        pl.col("amount").median().alias("median_fare"),
        pl.col("amount").min().alias("min_fare"),
        pl.col("amount").max().alias("max_fare"),
        (pl.col("is_ac") == True).sum().alias("ac_tickets"),
        pl.col("passenger_count").mean().round(2).alias("avg_passengers")
    ]).with_columns([
        (pl.col("count") / len(cleaned_df) * 100).round(2).alias("share_pct"),
        (pl.col("ac_tickets") / pl.col("count") * 100).round(2).alias("ac_pct")
    ]).sort("count", descending=True)

    print(ticket_profile)

    # ---------------------------------------------------------
    # 6. GENERATE EDA PLOTS
    # ---------------------------------------------------------
    print("\n" + "-" * 60)
    print("6. GENERATING EDA VISUALIZATIONS")
    print("-" * 60)

    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Plot A: Hourly Ticket Distribution
    hourly_df = cleaned_df.group_by("hour").agg(pl.len().alias("tickets")).sort("hour").to_pandas()
    sns.barplot(data=hourly_df, x="hour", y="tickets", ax=axes[0, 0], color="#2563eb")
    axes[0, 0].set_title("Delhi Bus Ticket Volume by Hour of Day (Peak Commute Analysis)", fontsize=13, fontweight="bold")
    axes[0, 0].set_xlabel("Hour of Day (IST)")
    axes[0, 0].set_ylabel("Ticket Count")

    # Highlight morning (8-10) and evening (17-20) peaks
    for patch, h in zip(axes[0, 0].patches, hourly_df["hour"]):
        if h in [8, 9, 17, 18, 19]:
            patch.set_facecolor("#dc2626")

    # Plot B: Weekday vs Weekend Volume
    day_df = cleaned_df.group_by("weekday").agg(pl.len().alias("tickets")).sort("weekday").to_pandas()
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    day_df["day_name"] = [day_names[w - 1] for w in day_df["weekday"]]
    sns.barplot(data=day_df, x="day_name", y="tickets", ax=axes[0, 1], hue="day_name", palette=["#2563eb"]*5 + ["#f59e0b"]*2, legend=False)
    axes[0, 1].set_title("Ticket Volume by Day of Week (Weekday vs Weekend)", fontsize=13, fontweight="bold")
    axes[0, 1].set_xlabel("Day of Week")
    axes[0, 1].set_ylabel("Ticket Count")

    # Plot C: Top 15 DTC Routes by Volume
    top_routes_df = cleaned_df.group_by("route").agg(pl.len().alias("tickets")).sort("tickets", descending=True).head(15).to_pandas()
    sns.barplot(data=top_routes_df, y="route", x="tickets", ax=axes[1, 0], color="#059669")
    axes[1, 0].set_title("Top 15 Delhi Bus Routes by Ticket Volume", fontsize=13, fontweight="bold")
    axes[1, 0].set_xlabel("Total Tickets")
    axes[1, 0].set_ylabel("Route")

    # Plot D: AC vs Non-AC Share
    ac_counts = cleaned_df.group_by("is_ac").agg(pl.len().alias("count")).to_pandas()
    ac_labels = ["AC Bus" if x else "Non-AC Bus" for x in ac_counts["is_ac"]]
    axes[1, 1].pie(ac_counts["count"], labels=ac_labels, autopct="%1.1f%%", colors=["#10b981", "#3b82f6"], startangle=140, explode=[0.05, 0])
    axes[1, 1].set_title("Bus Fleet Share (AC vs Non-AC)", fontsize=13, fontweight="bold")

    plt.tight_layout()
    eda_plot_path = os.path.join(plots_dir, "step1_eda_distributions.png")
    plt.savefig(eda_plot_path, dpi=200)
    plt.close()
    print(f"[+] Saved comprehensive EDA plot to: {eda_plot_path}")

    # Plot 2: Missing Vehicle Distribution by Hour & Route
    fig2, (ax_h, ax_d) = plt.subplots(1, 2, figsize=(15, 5))
    h_nan_pd = nan_by_hour.to_pandas()
    sns.lineplot(data=h_nan_pd, x="hour", y="nan_pct", ax=ax_h, marker="o", color="#dc2626", linewidth=2.5)
    ax_h.set_title("Missing vehicle_number % Across 24 Hours", fontsize=12, fontweight="bold")
    ax_h.set_xlabel("Hour of Day (IST)")
    ax_h.set_ylabel("NaN Vehicle %")
    ax_h.set_ylim(0, 100)

    d_nan_pd = nan_by_day.to_pandas()
    sns.lineplot(data=d_nan_pd, x="day_of_month", y="nan_pct", ax=ax_d, marker="s", color="#7c3aed", linewidth=2.5)
    ax_d.set_title("Missing vehicle_number % Across 31 Days of October 2026", fontsize=12, fontweight="bold")
    ax_d.set_xlabel("Day of Month")
    ax_d.set_ylabel("NaN Vehicle %")
    ax_d.set_ylim(0, 100)

    plt.tight_layout()
    nan_plot_path = os.path.join(plots_dir, "step1_nan_vehicle_profiles.png")
    plt.savefig(nan_plot_path, dpi=200)
    plt.close()
    print(f"[+] Saved NaN vehicle profile plot to: {nan_plot_path}")

    # ---------------------------------------------------------
    # 7. SAVE CLEANED STEP 1 DATASET
    # ---------------------------------------------------------
    cleaned_parquet_path = os.path.join(outputs_dir, "cleaned_tickets_step1.parquet")
    print(f"\n[*] Exporting cleaned dataset ({len(cleaned_df):,} rows) to: {cleaned_parquet_path}")
    cleaned_df.write_parquet(cleaned_parquet_path)
    print(f"[+] Export complete: {os.path.getsize(cleaned_parquet_path) / (1024*1024):.2f} MB")

    # Save summary metadata
    step1_report = {
        "total_raw_rows": total_raw_rows,
        "nan_vehicle_count": int(nan_vehicle_count),
        "nan_vehicle_pct": float(nan_vehicle_pct),
        "cleaned_rows": len(cleaned_df),
        "retention_pct": float(retention_pct),
        "audit_filters": audit_log,
        "date_min": str(df["date"].min()),
        "date_max": str(df["date"].max()),
        "unique_routes": len(unique_routes),
        "plots_saved": [eda_plot_path, nan_plot_path],
        "ticket_profile": ticket_profile.to_dicts()
    }
    with open(os.path.join(outputs_dir, "step1_report.json"), "w", encoding="utf-8") as f:
        json.dump(step1_report, f, indent=2)

    print("\n" + "=" * 80)
    print("STEP 1 COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    run_step1()
