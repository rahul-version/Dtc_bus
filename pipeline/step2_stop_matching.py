"""
Step 2: Stop Name Matching & GTFS Sequence Alignment
Maps raw ticket stop names to GTFS stops via normalization and 2-tier rapidfuzz
(route-constrained first, global fallback), determines sequence indices, and
filters directional anomalies.
"""

import os
import re
import sys
import time
import json
import yaml
import polars as pl
from rapidfuzz import process, fuzz

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# Delhi transit abbreviations map
ABBREVIATIONS = {
    r"\bbdr\b": "border",
    r"\bmkt\b": "market",
    r"\bcr\b": "crossing",
    r"\b(t)\b|\bt\b": "terminal",
    r"\bsec\b|\bsector\b": "sector",
    r"\bblk\b|\bblock\b": "block",
    r"\bjj\b": "jj colony",
    r"\bfl\b|\bflyover\b": "flyover",
    r"\bstl\b": "shuttle",
    r"\bext\b|\bextn\b": "extension",
    r"\bisbt\b": "isbt",
    r"\bstn\b": "station",
    r"\brd\b": "road",
    r"\bpkt\b": "pocket",
    r"\bmore\b": "mor",
    r"\bvill\b": "village"
}

def normalize_stop_name(raw_name: str) -> str:
    """Normalize raw stop name by lowercasing, expanding abbreviations, and cleaning."""
    if not raw_name or not isinstance(raw_name, str):
        return ""
    text = raw_name.lower().strip()
    # Strip trailing punctuation, colons, slashes
    text = re.sub(r"[:\-_/\\,.]+", " ", text)
    # Expand abbreviations
    for pattern, replacement in ABBREVIATIONS.items():
        text = re.sub(pattern, replacement, text)
    # Clean whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

def load_manual_overrides(csv_path: str = "data/manual_stop_overrides.csv") -> dict:
    overrides = {}
    if os.path.exists(csv_path):
        import csv
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw = row["raw_stop_name"].strip()
                target = row["override_stop_name"].strip()
                overrides[raw] = target
                overrides[normalize_stop_name(raw)] = target
    return overrides

def run_step2():
    print("=" * 80)
    print("STEP 2: STOP NAME MATCHING & GTFS SEQUENCE ALIGNMENT")
    print("=" * 80)

    config = load_config()
    gtfs_dir = config["paths"]["gtfs_dir"]
    outputs_dir = config["paths"]["outputs_dir"]
    matched_parquet_path = os.path.join(outputs_dir, "matched_tickets_step2.parquet")
    unmatched_csv_path = "data/unmatched_stops.csv"
    threshold = config["stop_matching"].get("rapidfuzz_threshold", 70.0)

    t0 = time.time()

    # 1. Load GTFS Stops and Route Sequences
    print(f"[*] Loading GTFS transit topology from: {gtfs_dir}")
    stops_file = os.path.join(gtfs_dir, "stops.txt")
    stops_df = pl.read_csv(stops_file)
    gtfs_stops_list = stops_df["stop_name"].to_list()
    gtfs_stops_set = set(gtfs_stops_list)
    gtfs_normalized_map = {normalize_stop_name(s): s for s in gtfs_stops_list}
    gtfs_normalized_list = list(gtfs_normalized_map.keys())

    seq_cache_path = os.path.join(gtfs_dir, "route_stop_sequences.json")
    with open(seq_cache_path, "r", encoding="utf-8") as f:
        route_stop_sequences = json.load(f)

    print(f"[+] Loaded {len(gtfs_stops_list):,} canonical GTFS stops and {len(route_stop_sequences):,} route topologies")

    # 2. Load Manual Overrides
    manual_overrides = load_manual_overrides()
    print(f"[+] Loaded {len(manual_overrides)} manual stop overrides from data/manual_stop_overrides.csv")

    # 3. Load Cleaned Tickets from Step 1
    input_parquet = os.path.join(outputs_dir, "cleaned_tickets_step1.parquet")
    print(f"[*] Ingesting cleaned tickets from: {input_parquet}")
    df = pl.read_parquet(input_parquet)
    total_tickets = len(df)
    print(f"[+] Ingested {total_tickets:,} tickets")

    # 4. Extract Unique (Route, Stop Name) Pairs for Route-Constrained Matching
    print("\n[*] Profiling unique route-stop combinations for two-tier matching...")
    start_pairs = df.select(["route", "start_stop_name"]).unique().rename({"start_stop_name": "raw_stop"})
    end_pairs = df.select(["route", "end_stop_name"]).unique().rename({"end_stop_name": "raw_stop"})
    unique_route_stops = pl.concat([start_pairs, end_pairs]).unique()
    total_unique_pairs = len(unique_route_stops)
    print(f"[+] Total unique (route, stop) pairs to match: {total_unique_pairs:,}")

    # Build lookup cache: (route, raw_stop) -> (matched_gtfs_stop, score, match_tier, stop_idx)
    match_cache = {}
    unmatched_counts = {}

    print(f"[*] Executing 2-Tier matching (Route-constrained -> Global fallback, threshold={threshold})...")
    match_t0 = time.time()

    tier1_hits = 0
    tier2_hits = 0
    exact_hits = 0
    unmatched_hits = 0

    for idx, row in enumerate(unique_route_stops.iter_rows(named=True)):
        route = row["route"]
        raw_stop = row["raw_stop"]
        cache_key = (route, raw_stop)

        # 0. Check Manual Overrides
        if raw_stop in manual_overrides:
            target = manual_overrides[raw_stop]
            match_cache[cache_key] = (target, 100.0, "MANUAL_OVERRIDE")
            exact_hits += 1
            continue

        # 1. Exact Match against GTFS
        if raw_stop in gtfs_stops_set:
            match_cache[cache_key] = (raw_stop, 100.0, "EXACT")
            exact_hits += 1
            continue

        norm_stop = normalize_stop_name(raw_stop)
        if norm_stop in gtfs_normalized_map:
            canonical = gtfs_normalized_map[norm_stop]
            match_cache[cache_key] = (canonical, 100.0, "EXACT_NORMALIZED")
            exact_hits += 1
            continue

        # 2. Tier 1: Route-Constrained Fuzzy Match
        route_stops = route_stop_sequences.get(route, [])
        matched = False

        if route_stops:
            best_match = process.extractOne(
                norm_stop,
                route_stops,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=threshold
            )
            if best_match:
                matched_stop, score, _ = best_match
                match_cache[cache_key] = (matched_stop, float(score), "TIER1_ROUTE")
                tier1_hits += 1
                matched = True

        # 3. Tier 2: Global Network Fallback Fuzzy Match
        if not matched:
            best_global = process.extractOne(
                norm_stop,
                gtfs_normalized_list,
                scorer=fuzz.token_sort_ratio,
                score_cutoff=threshold
            )
            if best_global:
                matched_norm, score, _ = best_global
                canonical = gtfs_normalized_map[matched_norm]
                match_cache[cache_key] = (canonical, float(score), "TIER2_GLOBAL")
                tier2_hits += 1
                matched = True

        # 4. Unmatched
        if not matched:
            match_cache[cache_key] = (raw_stop, 0.0, "UNMATCHED")
            unmatched_hits += 1
            unmatched_counts[raw_stop] = unmatched_counts.get(raw_stop, 0) + 1

    print(f"[+] Matching cache resolved in {time.time()-match_t0:.2f}s:")
    print(f"    - Exact / Overrides:   {exact_hits:,} ({exact_hits/total_unique_pairs*100:.1f}%)")
    print(f"    - Tier 1 (Route-level):{tier1_hits:,} ({tier1_hits/total_unique_pairs*100:.1f}%)")
    print(f"    - Tier 2 (Global):     {tier2_hits:,} ({tier2_hits/total_unique_pairs*100:.1f}%)")
    print(f"    - Unmatched:           {unmatched_hits:,} ({unmatched_hits/total_unique_pairs*100:.1f}%)")

    # 5. Export Top Unmatched Stops to CSV
    os.makedirs("data", exist_ok=True)
    unmatched_sorted = sorted(unmatched_counts.items(), key=lambda x: -x[1])
    with open(unmatched_csv_path, "w", encoding="utf-8") as f:
        f.write("unmatched_stop_name,frequency\n")
        for s_name, freq in unmatched_sorted:
            f.write(f'"{s_name}",{freq}\n')
    print(f"[+] Saved {len(unmatched_sorted)} unmatched stop names to: {unmatched_csv_path}")

    # 6. Map Matches Back to Ticket DataFrame and Compute Sequence Indices
    print("\n[*] Applying matched stops and directional sequence indices to ticket transactions...")

    # Build route stop index map for fast index retrieval: route -> {stop_name: index}
    route_stop_idx_map = {}
    for r_id, seq in route_stop_sequences.items():
        route_stop_idx_map[r_id] = {s: i for i, s in enumerate(seq)}

    # Map matched names and indices using Polars dictionary / struct mapping
    # Prepare mapping tables for Polars join
    pairs_list = []
    for (r, s), (matched_stop, score, tier) in match_cache.items():
        s_idx = route_stop_idx_map.get(r, {}).get(matched_stop, -1)
        pairs_list.append({
            "route": r,
            "raw_stop": s,
            "matched_stop": matched_stop,
            "match_score": score,
            "match_tier": tier,
            "stop_sequence_idx": s_idx
        })
    mapping_df = pl.DataFrame(pairs_list)

    # Join start stop matches
    df = df.join(
        mapping_df.select([
            pl.col("route"),
            pl.col("raw_stop").alias("start_stop_name"),
            pl.col("matched_stop").alias("matched_start_stop"),
            pl.col("match_score").alias("start_match_score"),
            pl.col("match_tier").alias("start_match_tier"),
            pl.col("stop_sequence_idx").alias("start_stop_idx")
        ]),
        on=["route", "start_stop_name"],
        how="left"
    )

    # Join end stop matches
    df = df.join(
        mapping_df.select([
            pl.col("route"),
            pl.col("raw_stop").alias("end_stop_name"),
            pl.col("matched_stop").alias("matched_end_stop"),
            pl.col("match_score").alias("end_match_score"),
            pl.col("match_tier").alias("end_match_tier"),
            pl.col("stop_sequence_idx").alias("end_stop_idx")
        ]),
        on=["route", "end_stop_name"],
        how="left"
    )

    # 7. Directional Monotonicity Audit & Filtering
    print("\n" + "-" * 60)
    print("AUDITING DIRECTIONAL MONOTONICITY (start_idx < end_idx)")
    print("-" * 60)

    # Valid if:
    # 1. Both stops matched (match_tier != 'UNMATCHED')
    # 2. Both stops have valid sequence index (>= 0)
    # 3. start_stop_idx < end_stop_idx (monotonic forward progression)
    unmatched_tickets_mask = (df["start_match_tier"] == "UNMATCHED") | (df["end_match_tier"] == "UNMATCHED")
    unmatched_tickets_count = int(unmatched_tickets_mask.sum())

    missing_idx_mask = (df["start_stop_idx"] < 0) | (df["end_stop_idx"] < 0)
    missing_idx_count = int(missing_idx_mask.sum())

    reverse_order_mask = (df["start_stop_idx"] >= 0) & (df["end_stop_idx"] >= 0) & (df["end_stop_idx"] <= df["start_stop_idx"])
    reverse_order_count = int(reverse_order_mask.sum())

    valid_mask = (
        (df["start_match_tier"] != "UNMATCHED") &
        (df["end_match_tier"] != "UNMATCHED") &
        (df["start_stop_idx"] >= 0) &
        (df["end_stop_idx"] >= 0) &
        (df["start_stop_idx"] < df["end_stop_idx"])
    )
    aligned_df = df.filter(valid_mask)

    total_valid = len(aligned_df)
    match_rate = (total_valid / total_tickets) * 100

    print(f"Total Input Tickets:                  {total_tickets:,}")
    print(f"Tickets with Unmatched Stop Names:    {unmatched_tickets_count:,} ({unmatched_tickets_count/total_tickets*100:.2f}%)")
    print(f"Tickets with Reverse Sequence Order:  {reverse_order_count:,} ({reverse_order_count/total_tickets*100:.2f}%)")
    print(f"Tickets Aligned with GTFS Forward Seq:{total_valid:,} ({match_rate:.2f}% Match Rate)")

    # 8. Export Matched & Aligned Parquet Dataset
    print(f"\n[*] Exporting aligned dataset ({total_valid:,} rows) to: {matched_parquet_path}")
    aligned_df.write_parquet(matched_parquet_path)
    file_size_mb = os.path.getsize(matched_parquet_path) / (1024 * 1024)
    print(f"[+] Export complete: {file_size_mb:.2f} MB in {time.time()-t0:.2f}s")

    # Save summary report
    step2_report = {
        "total_tickets_input": total_tickets,
        "total_unique_route_stops": total_unique_pairs,
        "exact_matches": exact_hits,
        "tier1_route_fuzzy": tier1_hits,
        "tier2_global_fuzzy": tier2_hits,
        "unmatched_stops_count": len(unmatched_sorted),
        "reverse_sequence_tickets_dropped": reverse_order_count,
        "aligned_tickets_retained": total_valid,
        "match_rate_pct": round(match_rate, 2),
        "output_file": matched_parquet_path,
        "output_size_mb": round(file_size_mb, 2)
    }
    with open(os.path.join(outputs_dir, "step2_report.json"), "w", encoding="utf-8") as f:
        json.dump(step2_report, f, indent=2)

    print("\n" + "=" * 80)
    print("STEP 2 COMPLETED SUCCESSFULLY")
    print("=" * 80)

if __name__ == "__main__":
    run_step2()
