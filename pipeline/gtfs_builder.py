"""
GTFS Builder Module
Constructs standard, canonical GTFS tables for the Delhi DTC transit network
based on Delhi transport topology and ticket network consensus.
"""

import os
import json
import yaml
import polars as pl
from collections import defaultdict

def build_gtfs_tables(parquet_path: str = "outputs/cleaned_tickets_step1.parquet", gtfs_dir: str = "gtfs"):
    print("=" * 80)
    print("BUILDING CANONICAL GTFS TRANSIT TOPOLOGY")
    print("=" * 80)
    os.makedirs(gtfs_dir, exist_ok=True)

    print(f"[*] Reading cleaned tickets from: {parquet_path}")
    df = pl.read_parquet(parquet_path)

    # 1. Extract Unique Stops and build stops.txt
    print("[*] Compiling stops.txt...")
    start_counts = df.group_by("start_stop_name").len().rename({"start_stop_name": "stop_name", "len": "start_vol"})
    end_counts = df.group_by("end_stop_name").len().rename({"end_stop_name": "stop_name", "len": "end_vol"})
    all_stops = start_counts.join(end_counts, on="stop_name", how="full").fill_null(0)
    all_stops = all_stops.with_columns(
        (pl.col("start_vol") + pl.col("end_vol")).alias("total_vol")
    ).sort("total_vol", descending=True)

    # Assign stop IDs and synthetic baseline coordinates (Delhi central bounding box)
    # Delhi lat: 28.40 to 28.85, lon: 76.95 to 77.35
    stops_records = []
    stop_id_map = {}
    for idx, row in enumerate(all_stops.iter_rows(named=True)):
        s_id = f"DELHI_STOP_{idx+1:05d}"
        s_name = row["stop_name"]
        stop_id_map[s_name] = s_id
        # Coordinates deterministic hash within Delhi bounding box if not explicitly mapped
        h = abs(hash(s_name))
        lat = 28.50 + ((h % 350) / 1000.0)
        lon = 77.05 + (((h // 350) % 300) / 1000.0)
        stops_records.append({
            "stop_id": s_id,
            "stop_name": s_name,
            "stop_lat": round(lat, 5),
            "stop_lon": round(lon, 5),
            "zone_id": "DELHI_NCT"
        })

    stops_df = pl.DataFrame(stops_records)
    stops_df.write_csv(os.path.join(gtfs_dir, "stops.txt"))
    print(f"[+] Wrote {len(stops_df):,} stops to {os.path.join(gtfs_dir, 'stops.txt')}")

    # 2. Extract Routes and build routes.txt
    print("[*] Compiling routes.txt...")
    route_stats = df.group_by("route").agg([
        pl.len().alias("tickets"),
        pl.col("base_route").first().alias("base_route"),
        pl.col("direction").first().alias("direction"),
        pl.col("is_ac").mean().alias("ac_ratio")
    ]).sort("tickets", descending=True)

    routes_records = []
    for row in route_stats.iter_rows(named=True):
        r_id = row["route"]
        r_short = row["base_route"] or r_id
        r_type = 3 # Bus in GTFS
        r_desc = "AC Low Floor Bus" if row["ac_ratio"] > 0.5 else "Standard Non-AC Bus"
        routes_records.append({
            "route_id": r_id,
            "agency_id": "DTC",
            "route_short_name": r_short,
            "route_long_name": f"Route {r_id} ({r_desc})",
            "route_type": r_type
        })
    routes_df = pl.DataFrame(routes_records)
    routes_df.write_csv(os.path.join(gtfs_dir, "routes.txt"))
    print(f"[+] Wrote {len(routes_df):,} routes to {os.path.join(gtfs_dir, 'routes.txt')}")

    # 3. Build Ordered Stop Sequences per Route & Direction (trips.txt & stop_times.txt)
    print("[*] Reconstructing topological stop sequences per route...")
    # For each route, find pairwise frequencies (A precedes B)
    route_pairs = df.group_by(["route", "start_stop_name", "end_stop_name"]).len().sort("len", descending=True)

    trips_records = []
    stop_times_records = []
    route_stop_sequences = {}

    # Process each route's DAG of stops
    for r_entry in route_stats.iter_rows(named=True):
        r_id = r_entry["route"]
        direction_id = 0 if r_entry["direction"] == "UP" else 1

        # Get top OD pairs for this route
        pairs_subset = route_pairs.filter(pl.col("route") == r_id)
        if len(pairs_subset) == 0:
            continue

        # Build in-degree and out-degree adjacency graph
        in_deg = defaultdict(int)
        out_deg = defaultdict(int)
        adj = defaultdict(lambda: defaultdict(int))
        nodes = set()

        for p in pairs_subset.iter_rows(named=True):
            u = p["start_stop_name"]
            v = p["end_stop_name"]
            w = p["len"]
            nodes.add(u)
            nodes.add(v)
            adj[u][v] += w
            out_deg[u] += w
            in_deg[v] += w

        # Score nodes by net flow position (out_flow - in_flow)
        # Terminal stops where passengers mostly board have positive score
        # Terminus stops where passengers mostly alight have negative score
        node_scores = []
        for n in nodes:
            score = (out_deg[n] - in_deg[n]) / (out_deg[n] + in_deg[n] + 1e-5)
            node_scores.append((score, n))

        # Sort descending: origin terminal -> intermediate stops -> destination terminal
        node_scores.sort(key=lambda x: -x[0])
        ordered_stops = [x[1] for x in node_scores]
        route_stop_sequences[r_id] = ordered_stops

        # Create 1 representative scheduled trip for this route
        trip_id = f"TRIP_{r_id}_01"
        trips_records.append({
            "route_id": r_id,
            "service_id": "ALL_WEEK",
            "trip_id": trip_id,
            "direction_id": direction_id,
            "trip_headsign": ordered_stops[-1] if ordered_stops else "Terminal"
        })

        # Scheduled travel time: ~2 minutes per stop interval
        for seq_idx, s_name in enumerate(ordered_stops):
            s_id = stop_id_map.get(s_name, f"DELHI_STOP_{seq_idx}")
            arr_min = seq_idx * 2
            arr_time = f"{6 + arr_min//60:02d}:{arr_min%60:02d}:00"
            dep_time = f"{6 + arr_min//60:02d}:{arr_min%60:02d}:30"
            stop_times_records.append({
                "trip_id": trip_id,
                "arrival_time": arr_time,
                "departure_time": dep_time,
                "stop_id": s_id,
                "stop_sequence": seq_idx + 1
            })

    trips_df = pl.DataFrame(trips_records)
    trips_df.write_csv(os.path.join(gtfs_dir, "trips.txt"))
    print(f"[+] Wrote {len(trips_df):,} trips to {os.path.join(gtfs_dir, 'trips.txt')}")

    stop_times_df = pl.DataFrame(stop_times_records)
    stop_times_df.write_csv(os.path.join(gtfs_dir, "stop_times.txt"))
    print(f"[+] Wrote {len(stop_times_df):,} stop_times to {os.path.join(gtfs_dir, 'stop_times.txt')}")

    # Save compiled route stop sequences lookup for ultra-fast Step 2 matching
    seq_cache_path = os.path.join(gtfs_dir, "route_stop_sequences.json")
    with open(seq_cache_path, "w", encoding="utf-8") as f:
        json.dump(route_stop_sequences, f, indent=2)
    print(f"[+] Saved route sequences lookup to {seq_cache_path}")

    return route_stop_sequences

if __name__ == "__main__":
    build_gtfs_tables()
