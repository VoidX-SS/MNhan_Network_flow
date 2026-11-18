"""Đối chứng có gợi ý khả thi trên lát cắt vừa đủ sức chứa."""

import argparse
import json
import random
from pathlib import Path

from algorithms.common import initial_population
from experiments import write_csv
from model import evaluate
from research.scenarios import screen_cases
from solver import ALGORITHMS, DEFAULT_POPULATION, DEFAULT_STEPS

WITNESS = [[88, 0, 2, 0, 0], [0, 92, 1, 3, 0], [0, 0, 105, 0, 0],
           [0, 0, 0, 84, 0], [0, 0, 0, 0, 85]]
SEEDS = range(3000, 3008)
ROOT = Path(__file__).resolve().parents[1]


def witness_genes(problem):
    # Chia mỗi dòng theo nhu cầu để ra trọng số trong [0,1].
    genes = []
    for pair, flows in zip(problem["pairs"], WITNESS):
        if sum(flows) != pair["demand"]:
            raise RuntimeError("Cách chia minh họa cần chở đủ nhu cầu từng cặp.")
        genes.extend(flow / pair["demand"] for flow in flows)
    if not evaluate(problem, genes)["valid"]:
        raise RuntimeError("Cách chia minh họa cần nằm trong sức chứa.")
    return genes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "Extras" / "tight_cut_witness.csv")
    args = parser.parse_args()
    problem = next(case["problem"] for case in screen_cases() if case["id"] == "tight_cut_100")
    genes = witness_genes(problem)
    catalog = json.loads((ROOT / "research" / "results" / "catalog.json").read_text(encoding="utf-8"))
    lower = catalog["tight_cut_100"]["reference"]["lower_bound"]
    rows = []

    def score(candidate):
        return evaluate(problem, candidate)

    for seed in SEEDS:
        for mode in ("random", "one_known_feasible"):
            for name, engine in ALGORITHMS.items():
                population = initial_population(problem["dimension"], DEFAULT_POPULATION, seed)
                if mode == "one_known_feasible":
                    population[0] = genes.copy()
                run = engine(population, score, DEFAULT_STEPS, random.Random(seed + 1))
                result = run["evaluation"]
                valid = result["valid"]
                cost = result["total_minutes"] if valid else None
                rows.append({"mode": mode, "algorithm": name, "seed": seed, "calls": run["calls"],
                             "valid": int(valid), "cost": cost, "violation": result["violation"],
                             "hit_1pct": int(valid and cost <= 1.01 * lower)})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.out, rows)
    for mode in ("random", "one_known_feasible"):
        for name in ALGORITHMS:
            group = [row for row in rows if row["mode"] == mode and row["algorithm"] == name]
            print(mode, name, sum(row["valid"] for row in group), sum(row["hit_1pct"] for row in group), flush=True)


if __name__ == "__main__":
    main()
