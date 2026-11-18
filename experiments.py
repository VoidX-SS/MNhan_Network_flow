"""Đo nhiều seed, ghi số liệu CSV và lưu một lượt đại diện cho demo."""

import argparse
import csv
import json
import platform
import statistics
from pathlib import Path

from model import NETWORK_FILES, cut_proof, load_network, make_problem
from solver import ALGORITHMS, DEFAULT_POPULATION, DEFAULT_SEED, DEFAULT_STEPS, solve

TIE_MINUTES = 0.01


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, data):
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def row_for(problem, result):
    evaluation = result["evaluation"]
    first_valid = None
    for record in result["history"]:
        if record["evaluation"]["valid"]:
            first_valid = record["calls"]
            break
    demand = sum(pair["demand"] for pair in problem["pairs"])
    minutes = evaluation["total_minutes"] if evaluation["valid"] else None
    average = None
    if minutes is not None and demand > 0:
        average = minutes / demand
    return {"case": problem["id"], "algorithm": result["algorithm"], "seed": result["seed"],
            "demand": demand, "calls": result["calls"], "valid": int(evaluation["valid"]),
            "total_vehicle_minutes": minutes, "mean_minutes_per_vehicle": average,
            "violation": evaluation["violation"], "overflow_edge_vehicles": evaluation["overflow"],
            "unassigned_vehicles": evaluation["unassigned"],
            "first_valid_checkpoint_calls": first_valid, "seconds": result["seconds"]}


def median_or_blank(numbers):
    if numbers:
        return statistics.median(numbers)
    return None


def summarize(rows):
    feasible = [row for row in rows if row["valid"]]
    costs = [row["total_vehicle_minutes"] for row in feasible]
    best = min(feasible, key=lambda row: row["total_vehicle_minutes"]) if feasible else None
    q1 = q3 = median_or_blank(costs)
    if len(costs) > 1:
        q1, _, q3 = statistics.quantiles(costs, n=4, method="inclusive")
    first = [row["first_valid_checkpoint_calls"] for row in feasible]
    return {"case": rows[0]["case"], "algorithm": rows[0]["algorithm"], "runs": len(rows),
            "valid_runs": len(feasible), "median_valid_cost": median_or_blank(costs),
            "q1_valid_cost": q1, "q3_valid_cost": q3,
            "best_valid_cost": best["total_vehicle_minutes"] if best else None,
            "best_valid_seed": best["seed"] if best else None,
            "median_first_valid_checkpoint_calls": median_or_blank(first),
            "median_invalid_violation": median_or_blank([row["violation"] for row in rows if not row["valid"]]),
            "median_seconds": statistics.median(row["seconds"] for row in rows)}


def compare_paired(ga_rows, woa_rows):
    differences = []
    for ga, woa in zip(ga_rows, woa_rows):
        if ga["valid"] and woa["valid"]:
            differences.append(ga["total_vehicle_minutes"] - woa["total_vehicle_minutes"])
    return {"case": ga_rows[0]["case"], "paired_valid": len(differences),
            "GA_lower": sum(value < -TIE_MINUTES for value in differences),
            "WOA_lower": sum(value > TIE_MINUTES for value in differences),
            "ties": sum(abs(value) <= TIE_MINUTES for value in differences),
            "tie_tolerance_vehicle_minutes": TIE_MINUTES,
            "median_GA_minus_WOA": median_or_blank(differences)}


def run_cases(network, seeds, sample_seed, population, steps):
    rows = []
    summary = []
    paired = []
    samples = {}
    normal = {}
    for case in network["cases"]:
        problem = make_problem(network, case)
        samples[case] = {"proof": cut_proof(problem), "runs": {}}
        by_algorithm = {}
        for algorithm in ALGORITHMS:
            group = []
            for seed in seeds:
                result = solve(problem, algorithm, population, steps, seed)
                row = row_for(problem, result)
                group.append(row)
                if seed == sample_seed:
                    samples[case]["runs"][algorithm] = result
                if case == "normal":
                    normal[(algorithm, seed)] = row
            summary.append(summarize(group))
            rows.extend(group)
            by_algorithm[algorithm] = group
        paired.append(compare_paired(by_algorithm["GA"], by_algorithm["WOA"]))
        valid_counts = [sum(row["valid"] for row in group) for group in by_algorithm.values()]
        print(f"{case:8s}  hợp lệ GA {valid_counts[0]}/{len(seeds)}, WOA {valid_counts[1]}/{len(seeds)}", flush=True)
    return rows, summary, paired, samples, normal


def scan_roads(network, normal, seeds, population, steps):
    summary = []
    raw = []
    study_roads = network.get("study_roads")
    for road in network["roads"]:
        road_id = road["id"]
        if study_roads is not None and road_id not in study_roads:
            continue
        reduced = road["capacity"] * 0.5
        problem = make_problem(network, "normal", overrides={road_id: reduced})
        for algorithm in ALGORITHMS:
            differences = []
            valid_count = 0
            for seed in seeds:
                row = row_for(problem, solve(problem, algorithm, population, steps, seed))
                reference = normal[(algorithm, seed)]
                delta = None
                if row["valid"]:
                    valid_count += 1
                    if reference["valid"] and reference["total_vehicle_minutes"] > 0:
                        delta = 100 * (row["total_vehicle_minutes"] / reference["total_vehicle_minutes"] - 1)
                        differences.append(delta)
                row["road"] = road_id
                row["new_capacity"] = reduced
                row["normal_valid_cost"] = reference["total_vehicle_minutes"]
                row["change_percent"] = delta
                raw.append(row)
            summary.append({"road": road_id, "new_capacity": reduced, "algorithm": algorithm,
                            "runs": len(seeds), "valid_runs": valid_count, "paired_valid": len(differences),
                            "median_change_percent": median_or_blank(differences)})
    return summary, raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", choices=NETWORK_FILES, default="main", help="main là mạng 50 nút, small là mạng 8 nút.")
    parser.add_argument("--seeds", type=int, default=30, help="Số seed liên tiếp bắt đầu từ 0.")
    parser.add_argument("--sensitivity-seeds", type=int, help="Số seed đầu dùng cho lượt giảm 50%% từng đường. Mặc định tối đa 8. Dùng 0 để bỏ qua.")
    parser.add_argument("--sample-seed", type=int, help="Seed lưu chi tiết. Mặc định 7 nếu đã chạy tới seed này.")
    parser.add_argument("--population", type=int, default=DEFAULT_POPULATION)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--out", type=Path, default=Path("ket_qua_moi"))
    args = parser.parse_args()
    if not 1 <= args.seeds <= 100:
        parser.error("--seeds phải từ 1 đến 100.")
    if args.sensitivity_seeds is None:
        args.sensitivity_seeds = min(8, args.seeds)
    if args.sample_seed is None:
        args.sample_seed = min(DEFAULT_SEED, args.seeds - 1)
    if not 0 <= args.sensitivity_seeds <= args.seeds or not 0 <= args.sample_seed < args.seeds:
        parser.error("Dùng --sensitivity-seeds không quá số seed và --sample-seed thuộc dãy seed đã chạy.")
    network = load_network(NETWORK_FILES[args.network])
    if args.sensitivity_seeds and "normal" not in network["cases"]:
        parser.error("Cần kịch bản normal để quét từng cạnh. Dùng --sensitivity-seeds 0 để bỏ qua phép quét.")
    args.out.mkdir(parents=True, exist_ok=True)
    try:
        rows, summary, paired, samples, normal = run_cases(network, range(args.seeds), args.sample_seed,
                                                           args.population, args.steps)
    except ValueError as error:
        parser.error(str(error))
    write_csv(args.out / "runs.csv", rows)
    write_csv(args.out / "summary.csv", summary)
    write_csv(args.out / "paired.csv", paired)
    write_json(args.out / "sample_runs.json", samples)
    write_json(args.out / "network_used.json", network)
    metadata = {"python": platform.python_version(), "system": platform.system(), "machine": platform.machine(),
                "network": network["name"], "nodes": len(network["nodes"]), "roads": len(network["roads"]),
                "pairs": len(network["pairs"]), "study_roads": network.get("study_roads"),
                "population": args.population, "steps": args.steps, "evaluations_per_run": args.population * (args.steps + 1),
                "seeds": list(range(args.seeds)), "sensitivity_seeds": list(range(args.sensitivity_seeds)),
                "sample_seed": args.sample_seed}
    if args.sensitivity_seeds > 0:
        print("Đo giảm 50% sức chứa từng đường, từng lần một...", flush=True)
        sensitivity, sensitivity_raw = scan_roads(network, normal, range(args.sensitivity_seeds),
                                                   args.population, args.steps)
        write_csv(args.out / "sensitivity.csv", sensitivity)
        write_csv(args.out / "sensitivity_runs.csv", sensitivity_raw)
    write_json(args.out / "environment.json", metadata)
    print(f"Đã ghi bảng số liệu tại {args.out.resolve()}")


if __name__ == "__main__":
    main()
