"""Sàng lọc tình huống, khóa danh sách, rồi xác nhận bằng seed mới."""

import argparse
import json
import platform
import random
import statistics
from pathlib import Path

from experiments import write_csv, write_json
from research.oracle import reference
from research.scenarios import screen_cases
from solver import DEFAULT_POPULATION, DEFAULT_STEPS, solve

OUT = Path(__file__).resolve().parent / "results"
METHODS = ("GA", "WOA")
SCREEN_SEEDS = range(8)
CONFIRM_SEEDS = range(1000, 1030)
BUDGET = DEFAULT_POPULATION * (DEFAULT_STEPS + 1)


def near_target(ref):
    if ref["status"] == "certified" and ref["lower_bound"] is not None:
        return 1.01 * ref["lower_bound"]
    return None


def gap_percent(cost, ref):
    lower = ref["lower_bound"]
    if cost is not None and ref["status"] == "certified" and lower > 0:
        return 100 * (cost - lower) / lower
    return None


def run_trial(case, algorithm, seed, ref, updates=DEFAULT_STEPS):
    calls = 0
    first_valid = None
    first_hit = None
    target = near_target(ref)

    def observe(score):
        # Đếm ngay tại lần chấm. Ứng viên được lưu lại không làm tăng bộ đếm.
        nonlocal calls, first_valid, first_hit
        calls += 1
        if score["valid"]:
            if first_valid is None:
                first_valid = calls
            if target is not None and first_hit is None and score["total_minutes"] <= target:
                first_hit = calls

    run = solve(case["problem"], algorithm, steps=updates, seed=seed, on_evaluate=observe)
    budget = DEFAULT_POPULATION * (updates + 1)
    if calls != budget or run["calls"] != calls:
        raise RuntimeError("Lượt chấm của hai phương pháp cần đúng ngân sách.")
    score = run["evaluation"]
    cost = score["total_minutes"] if score["valid"] else None
    gap = gap_percent(cost, ref)
    if gap is not None and gap < -0.001:
        raise RuntimeError(f"Nghiệm tốt hơn cận dưới của chuẩn ở {case['id']}. Kiểm tra lại chuẩn.")
    row = {"case": case["id"], "family": case["family"], "algorithm": algorithm, "seed": seed,
           "reference_status": ref["status"], "lower_bound": ref["lower_bound"],
           "upper_bound": ref["upper_bound"], "target_1pct": target, "calls": calls,
           "valid": int(score["valid"]), "cost": cost, "gap_pct": gap,
           "hit_1pct": int(first_hit is not None) if target is not None else None,
           "first_valid_calls": first_valid, "first_hit_calls": first_hit,
           "violation": score["violation"], "unassigned": score["unassigned"], "seconds": run["seconds"]}
    return row, run["history"]


def med(numbers):
    return statistics.median(numbers) if numbers else None


def ert(rows, column):
    hits = [row[column] for row in rows if row[column] is not None]
    if not hits:
        return None
    return (sum(hits) + rows[0]["calls"] * (len(rows) - len(hits))) / len(hits)


def summary(rows):
    first = rows[0]
    gaps = [row["gap_pct"] for row in rows if row["gap_pct"] is not None]
    costs = [row["cost"] for row in rows if row["cost"] is not None]
    q1 = q3 = med(gaps)
    if len(gaps) > 1:
        q1, _, q3 = statistics.quantiles(gaps, n=4, method="inclusive")
    return {"case": first["case"], "family": first["family"], "algorithm": first["algorithm"],
            "runs": len(rows), "reference_status": first["reference_status"],
            "valid": sum(row["valid"] for row in rows),
            "hit_1pct": sum(row["hit_1pct"] for row in rows) if first["target_1pct"] is not None else None,
            "median_cost": med(costs), "best_cost": min(costs) if costs else None,
            "median_gap_pct": med(gaps), "q1_gap_pct": q1, "q3_gap_pct": q3,
            "median_first_valid_calls": med([row["first_valid_calls"] for row in rows if row["first_valid_calls"] is not None]),
            "median_first_hit_calls": med([row["first_hit_calls"] for row in rows if row["first_hit_calls"] is not None]),
            "ert_valid_calls": ert(rows, "first_valid_calls"), "ert_1pct_calls": ert(rows, "first_hit_calls"),
            "median_final_violation": med([row["violation"] for row in rows]),
            "median_seconds": med([row["seconds"] for row in rows])}


def paired_summary(ga, woa):
    # Hiệu âm nghĩa là GA có chi phí thấp hơn ở cặp đó.
    differences = []
    relative = []
    ga_only = woa_only = 0
    for a, b in zip(ga, woa):
        if a["seed"] != b["seed"]:
            raise RuntimeError("Ghép sai seed.")
        ga_only += int(a["valid"] and not b["valid"])
        woa_only += int(b["valid"] and not a["valid"])
        if a["valid"] and b["valid"]:
            delta = a["cost"] - b["cost"]
            differences.append(delta)
            if a["lower_bound"] is not None and a["lower_bound"] > 0:
                relative.append(100 * delta / a["lower_bound"])
    low = high = None
    if len(relative) >= 6:
        # Lấy mẫu lại theo cả cặp seed để mô tả độ dao động của trung vị.
        rng = random.Random(2026)
        replicas = [statistics.median(rng.choices(relative, k=len(relative))) for _ in range(1200)]
        quantiles = statistics.quantiles(replicas, n=40, method="inclusive")
        low, high = quantiles[0], quantiles[-1]
    return {"case": ga[0]["case"], "both_valid": len(differences), "GA_only_valid": ga_only,
            "WOA_only_valid": woa_only, "GA_cost_lower": sum(x < -0.01 for x in differences),
            "WOA_cost_lower": sum(x > 0.01 for x in differences),
            "median_GA_minus_WOA_cost": med(differences), "median_relative_delta_pct": med(relative),
            "paired_bootstrap_low_pct": low, "paired_bootstrap_high_pct": high}


def curve(case_id, algorithm, histories, ref):
    target = near_target(ref)
    rows = []
    for checkpoints in zip(*histories):
        evaluations = [record["evaluation"] for record in checkpoints]
        valid = [score for score in evaluations if score["valid"]]
        hits = None
        if target is not None:
            hits = sum(score["total_minutes"] <= target for score in valid)
        gaps = [gap_percent(score["total_minutes"], ref) for score in valid]
        rows.append({"case": case_id, "algorithm": algorithm, "calls": checkpoints[0]["calls"],
                     "runs": len(evaluations), "valid": len(valid), "hit_1pct": hits,
                     "median_valid_gap_pct": med([gap for gap in gaps if gap is not None]),
                     "median_violation": med([score["violation"] for score in evaluations])})
    return rows


def run_cases(cases, catalog, seeds, out, phase):
    raw = []
    summaries = []
    pairs = []
    curves = []
    for case in cases:
        ref = catalog[case["id"]]["reference"]
        method_rows = {name: [] for name in METHODS}
        method_histories = {name: [] for name in METHODS}
        for seed in seeds:
            order = METHODS if seed % 2 == 0 else METHODS[::-1]
            for algorithm in order:
                row, history = run_trial(case, algorithm, seed, ref)
                method_rows[algorithm].append(row)
                if phase == "confirm":
                    method_histories[algorithm].append(history)
        pairs.append(paired_summary(method_rows["GA"], method_rows["WOA"]))
        for name in METHODS:
            raw.extend(method_rows[name])
            summaries.append(summary(method_rows[name]))
            if phase == "confirm":
                curves.extend(curve(case["id"], name, method_histories[name], ref))
        a, b = summaries[-2:]
        print(f"{phase:7} {case['id']:25} GA {a['valid']}/{a['runs']} · WOA {b['valid']}/{b['runs']} hợp lệ", flush=True)
    write_csv(out / f"{phase}_runs.csv", raw)
    write_csv(out / f"{phase}_summary.csv", summaries)
    write_csv(out / f"{phase}_paired.csv", pairs)
    if curves:
        write_csv(out / "confirm_curves.csv", curves)
    return raw, summaries, pairs


def catalog_cases(cases):
    catalog = {}
    for case in cases:
        problem = case["problem"]
        ref = reference(problem)
        catalog[case["id"]] = {"family": case["family"], "description": case["description"],
                               "hypothesis": case["hypothesis"], "nodes": len(problem["network"]["nodes"]),
                               "roads": len(problem["roads"]), "pairs": len(problem["pairs"]),
                               "dimension": problem["dimension"], "demand": sum(pair["demand"] for pair in problem["pairs"]),
                               "reference": {key: value for key, value in ref.items() if key != "genes"}}
    return catalog


def select_cases(catalog, summaries, pairs):
    scores = {(row["case"], row["algorithm"]): row for row in summaries}
    paired = {row["case"]: row for row in pairs}
    eligible = [key for key, case in catalog.items()
                if key not in {"normal", "cut", "irregular_layout"}
                and case["reference"]["status"] in {"certified", "feasible_uncertified"}]
    if not eligible:
        raise ValueError("Chưa có ca ngoài mốc được kiểm chứng khả thi để khóa danh sách.")

    def valid_count(case_id, name):
        return scores[(case_id, name)]["valid"]

    def hit_difference(case_id):
        return abs((scores[(case_id, "GA")]["hit_1pct"] or 0) - (scores[(case_id, "WOA")]["hit_1pct"] or 0))

    def relative_difference(case_id):
        return abs(paired[case_id]["median_relative_delta_pct"] or 0)

    size = len(SCREEN_SEEDS)
    hard = [key for key in eligible if valid_count(key, "GA") + valid_count(key, "WOA") < 2 * size]
    if hard:
        difficult = min(hard, key=lambda key: (-abs(valid_count(key, "GA") - valid_count(key, "WOA")),
                                               valid_count(key, "GA") + valid_count(key, "WOA"), key))
    else:
        difficult = min(eligible, key=lambda key: (-hit_difference(key), key))
    quality = [key for key in eligible if key != difficult and catalog[key]["reference"]["status"] == "certified"
               and min(valid_count(key, "GA"), valid_count(key, "WOA")) >= 6]
    if not quality:
        raise ValueError("Chưa có ca đủ lượt hợp lệ và có chuẩn số để chọn theo chất lượng.")
    other = [key for key in quality if catalog[key]["family"] != catalog[difficult]["family"]]
    best_contrast = min(other or quality, key=lambda key: (-hit_difference(key), -relative_difference(key), key))
    return [{"case": "normal", "role": "mốc ngày thường"},
            {"case": difficult, "role": "case khó tìm nghiệm hợp lệ"},
            {"case": best_contrast, "role": "case chênh lệch chất lượng"},
            {"case": "cut", "role": "vô nghiệm có chứng cứ"}]


def check_coordinate_control(raw):
    columns = ("valid", "cost", "violation", "first_valid_calls", "first_hit_calls")
    baseline = {(row["algorithm"], row["seed"]): row for row in raw if row["case"] == "normal"}
    controls = [row for row in raw if row["case"] == "irregular_layout"]
    for row in controls:
        other = baseline[(row["algorithm"], row["seed"])]
        if any(row[column] != other[column] for column in columns):
            raise RuntimeError("Đổi tọa độ đã thay đổi số liệu. Kiểm tra topology và bộ chấm.")
    return len(controls)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("screen", "confirm"))
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    cases = screen_cases()
    if args.phase == "screen":
        try:
            import scipy
        except ImportError:
            parser.error("Cài gói nghiên cứu bằng python -m pip install -r research/requirements.txt.")
        catalog = catalog_cases(cases)
        write_json(out / "catalog.json", catalog)
        raw, summaries, pairs = run_cases(cases, catalog, SCREEN_SEEDS, out, "screen")
        try:
            shortlist = select_cases(catalog, summaries, pairs)
        except ValueError as error:
            parser.error(str(error))
        write_json(out / "shortlist.json", shortlist)
        print("Đã khóa shortlist", [row["case"] for row in shortlist], flush=True)
        write_json(out / "protocol_run.json", {"population": DEFAULT_POPULATION, "updates": DEFAULT_STEPS,
                                                 "calls_per_trial": BUDGET, "screen_seeds": list(SCREEN_SEEDS),
                                                 "confirm_seeds": list(CONFIRM_SEEDS), "python": platform.python_version(),
                                                 "scipy": scipy.__version__, "system": platform.platform(),
                                                 "coordinate_control_matches": check_coordinate_control(raw)})
    else:
        catalog = json.loads((out / "catalog.json").read_text(encoding="utf-8"))
        shortlist = json.loads((out / "shortlist.json").read_text(encoding="utf-8"))
        by_id = {case["id"]: case for case in cases}
        run_cases([by_id[row["case"]] for row in shortlist], catalog, CONFIRM_SEEDS, out, "confirm")


if __name__ == "__main__":
    main()
