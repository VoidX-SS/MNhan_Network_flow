"""Thử tăng số vòng trên case tải nhẹ bằng seed mới, giữ mọi thiết lập khác."""

import argparse
import json
from pathlib import Path

from experiments import write_csv
from research.measure import METHODS, OUT, med, run_trial, summary
from research.scenarios import screen_cases

UPDATES = (90, 180)
SEEDS = range(2000, 2012)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    case = next(case for case in screen_cases() if case["id"] == "light")
    catalog = json.loads((args.out / "catalog.json").read_text(encoding="utf-8"))
    ref = catalog["light"]["reference"]
    rows = []
    summaries = []
    comparisons = []
    for algorithm in METHODS:
        by_updates = {}
        for updates in UPDATES:
            group = []
            for seed in SEEDS:
                row, _ = run_trial(case, algorithm, seed, ref, updates)
                group.append(dict(row, updates=updates))
            by_updates[updates] = group
            rows.extend(group)
            summaries.append(dict(summary(group), updates=updates, calls=group[0]["calls"]))
        deltas = [b["cost"] - a["cost"] for a, b in zip(by_updates[90], by_updates[180]) if a["valid"] and b["valid"]]
        comparisons.append({"algorithm": algorithm, "paired_valid": len(deltas),
                            "lower_cost": sum(delta < -0.01 for delta in deltas),
                            "unchanged_cost": sum(abs(delta) <= 0.01 for delta in deltas),
                            "higher_cost": sum(delta > 0.01 for delta in deltas),
                            "median_cost_180_minus_90": med(deltas)})
    write_csv(args.out / "light_budget_runs.csv", rows)
    write_csv(args.out / "light_budget_summary.csv", summaries)
    write_csv(args.out / "light_budget_paired.csv", comparisons)
    for row in comparisons:
        print(row, flush=True)


if __name__ == "__main__":
    main()
