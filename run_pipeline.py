"""
Master Pipeline Runner: Crowdedness-Aware Delhi Bus Journey Planner
Executes the end-to-end pipeline reproducibly with a single command:
    python run_pipeline.py
"""

import sys
import time
import argparse

from pipeline.step1_cleaning_eda import run_step1
from pipeline.gtfs_builder import build_gtfs_tables
from pipeline.step2_stop_matching import run_step2
from pipeline.step3_hybrid_load import run_step3
from pipeline.step4_load_estimation import run_step4
from pipeline.step5_validation import run_step5
from pipeline.step6_outputs import run_step6

def main():
    parser = argparse.ArgumentParser(description="Reproducible Delhi Bus Crowdedness Pipeline")
    parser.add_argument("--step", type=int, choices=[1, 2, 3, 4, 5, 6], help="Run a specific step only")
    args = parser.parse_args()

    print("\n" + "=" * 80)
    print("STARTING CROWDEDNESS-AWARE DELHI BUS PIPELINE (REPRODUCIBLE)")
    print("=" * 80)
    start_total = time.time()

    steps = [
        (1, "Data Cleaning & EDA", run_step1),
        (2, "GTFS Building & Stop Name Matching", lambda: (build_gtfs_tables(), run_step2())),
        (3, "Hybrid Missing Vehicle Estimation", run_step3),
        (4, "On-Board Load & Crowdedness Calculation", run_step4),
        (5, "Model Validation & Sanity Checks", run_step5),
        (6, "Production Tidy Outputs & Diagnostics", run_step6)
    ]

    for step_num, step_name, step_fn in steps:
        if args.step is not None and args.step != step_num:
            continue
        print(f"\n>>> Running Step {step_num}: {step_name}...")
        t_step = time.time()
        step_fn()
        print(f">>> Step {step_num} finished in {time.time()-t_step:.2f}s\n")

    print("=" * 80)
    print(f"PIPELINE COMPLETED SUCCESSFULLY IN {time.time()-start_total:.2f} SECONDS")
    print("All artifacts generated in: outputs/")
    print("To launch the Journey Planner UI, run:")
    print("    streamlit run app_streamlit.py")
    print("=" * 80)

if __name__ == "__main__":
    main()
