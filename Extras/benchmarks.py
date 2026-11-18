"""Đo GA và WOA trên ba hàm có nghiệm toàn cục biết trước."""

import argparse
import csv
import json
import math
from pathlib import Path
import platform
import random
from statistics import median, quantiles

from algorithms.common import initial_population
from solver import ALGORITHMS, check_settings


DIMENSIONS = (4, 10)
INSTANCE_COUNT = 3
TARGET = 0.01
PROBE = 1.0
CENTERS_SEED = 20261108


def sphere(values):
    return sum(value * value for value in values)


def rastrigin(values):
    return sum(value * value + 10 * (1 - math.cos(math.tau * value)) for value in values)


def ackley(values):
    mean_square = sum(value * value for value in values) / len(values)
    mean_cosine = sum(math.cos(math.tau * value) for value in values) / len(values)
    # expm1(z) là exp(z) - 1, giúp giữ độ chính xác khi z rất gần 0.
    return -20 * math.expm1(-0.2 * math.sqrt(mean_square)) - math.e * math.expm1(mean_cosine - 1)


FUNCTIONS = {
    "Sphere": (sphere, 10.24),
    "Rastrigin": (rastrigin, 10.24),
    "Ackley": (ackley, 65.536),
}


def optimum(dimension, instance):
    # Tâm khác nhau giữa các ô. Seed tâm tách riêng với seed của GA và WOA.
    rng = random.Random(CENTERS_SEED + 1000 * dimension + instance)
    return [rng.uniform(0.20, 0.80) for _ in range(dimension)]


def run_one(function, width, center, population, algorithm, steps, seed):
    calls = 0
    hit = None
    probe_hit = None

    def evaluate(candidate):
        nonlocal calls, hit, probe_hit
        values = [width * (value - target) for value, target in zip(candidate, center)]
        error = function(values)
        calls += 1
        if hit is None and error <= TARGET:
            hit = calls
        if probe_hit is None and error <= PROBE:
            probe_hit = calls
        return {"rank": (error,), "error": error}

    initial = [candidate.copy() for candidate in population]
    result = ALGORITHMS[algorithm](initial, evaluate, steps, random.Random(seed + 1))
    budget = len(population) * (steps + 1)
    if result["calls"] != calls or calls != budget:
        raise RuntimeError("Số lượt chấm không khớp ngân sách.")
    return {
        "algorithm": algorithm,
        "budget_calls": calls,
        "start_error": result["history"][0]["evaluation"]["error"],
        "final_error": result["evaluation"]["error"],
        "target_error": TARGET,
        "hit_call": hit,
        "probe_error": PROBE,
        "probe_hit_call": probe_hit,
        "seconds": result["seconds"],
    }


def run_suite(seeds, population_size, steps):
    rows = []
    for name, (function, width) in FUNCTIONS.items():
        for dimension in DIMENSIONS:
            for seed in range(seeds):
                instance = seed % INSTANCE_COUNT
                center = optimum(dimension, instance)
                population = initial_population(dimension, population_size, seed)
                order = ("GA", "WOA") if seed % 2 == 0 else ("WOA", "GA")
                paired = []
                for algorithm in order:
                    result = run_one(function, width, center, population, algorithm, steps, seed)
                    paired.append(result)
                    rows.append({
                        "function": name,
                        "dimension": dimension,
                        "instance": instance + 1,
                        "seed": seed,
                        **result,
                    })
                if paired[0]["start_error"] != paired[1]["start_error"]:
                    raise RuntimeError("Hai thuật toán phải bắt đầu từ cùng quần thể.")
    return rows


def make_summary(rows):
    summary = []
    for name in FUNCTIONS:
        for dimension in DIMENSIONS:
            for algorithm in ("GA", "WOA"):
                runs = [
                    row for row in rows
                    if row["function"] == name and row["dimension"] == dimension and row["algorithm"] == algorithm
                ]
                errors = [row["final_error"] for row in runs]
                quartiles = quantiles(errors, n=4, method="inclusive") if len(errors) > 1 else errors * 3
                hits = [row["hit_call"] for row in runs if row["hit_call"] is not None]
                budget_censored_calls = sum(
                    row["hit_call"] if row["hit_call"] is not None else row["budget_calls"]
                    for row in runs
                )
                summary.append({
                    "function": name,
                    "dimension": dimension,
                    "algorithm": algorithm,
                    "runs": len(runs),
                    "near_optimal_hits": len(hits),
                    "probe_hits": sum(row["probe_hit_call"] is not None for row in runs),
                    "median_final_error": median(errors),
                    "q1_final_error": quartiles[0],
                    "q3_final_error": quartiles[2],
                    "median_hit_call_if_success": median(hits) if hits else None,
                    "ert_calls": budget_censored_calls / len(hits) if hits else None,
                    "median_seconds": median(row["seconds"] for row in runs),
                })
    return summary


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_results(output, rows, seeds, population, steps):
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "runs.csv", rows)
    write_csv(output / "summary.csv", make_summary(rows))
    centers = []
    for dimension in DIMENSIONS:
        for instance in range(INSTANCE_COUNT):
            for index, coordinate in enumerate(optimum(dimension, instance), start=1):
                centers.append({
                    "dimension": dimension, "instance": instance + 1,
                    "coordinate": index, "optimum": coordinate,
                })
    write_csv(output / "instances.csv", centers)
    metadata = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dimensions": DIMENSIONS,
        "functions_and_widths": {name: width for name, (_, width) in FUNCTIONS.items()},
        "population": population,
        "steps": steps,
        "budget_calls": population * (steps + 1),
        "paired_seeds": list(range(seeds)),
        "center_seed": CENTERS_SEED,
        "target_error": TARGET,
        "probe_error": PROBE,
        "global_minimum_value": 0,
    }
    (output / "metadata.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=30)
    parser.add_argument("--population", type=int, default=32)
    parser.add_argument("--steps", type=int, default=90)
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("benchmarks_results"))
    args = parser.parse_args()
    if not 1 <= args.seeds <= 500:
        parser.error("--seeds cần nằm trong [1, 500].")
    try:
        check_settings(args.population, args.steps, args.seeds - 1)
    except ValueError as error:
        parser.error(str(error))
    rows = run_suite(args.seeds, args.population, args.steps)
    write_results(args.out, rows, args.seeds, args.population, args.steps)
    print(f"Đã ghi {len(rows)} lượt chạy vào {args.out}")


if __name__ == "__main__":
    main()
