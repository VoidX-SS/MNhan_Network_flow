"""Đo thêm nút bằng cách chia cạnh, giữ nguyên số trọng số của bài toán."""

import argparse
import platform
import statistics
import tracemalloc
from pathlib import Path

from experiments import write_csv, write_json
from model import evaluate
from research.scenarios import scale_case
from solver import solve

SIZES = (50, 100, 250, 500, 1000, 2000, 5000)
SEEDS = (1000, 1001, 1002)
METHODS = ("GA", "WOA")
POPULATION = 16
UPDATES = 18
OUT = Path(__file__).resolve().parent / "results"


def measure_peak(nodes, method):
    # Tách lượt đo RAM khỏi lượt đo thời gian vì tracemalloc làm chậm Python.
    tracemalloc.start()
    try:
        problem = scale_case(nodes)
        run = solve(problem, method, POPULATION, UPDATES, SEEDS[0])
        _, peak = tracemalloc.get_traced_memory()
        return peak / (1024 * 1024), run["calls"]
    finally:
        tracemalloc.stop()


def size_info(problem):
    nodes_in_paths = set()
    edges_in_paths = set()
    incidence = 0
    for pair in problem["pairs"]:
        for route in pair["routes"]:
            nodes_in_paths.update(route["path"])
            edges_in_paths.update(route["roads"])
            incidence += len(route["roads"])
    nodes = len(problem["network"]["nodes"])
    roads = len(problem["roads"])
    if len(nodes_in_paths) != nodes or len(edges_in_paths) != roads:
        raise RuntimeError("Mỗi nút và cạnh ở phép đo quy mô cần nằm trên ít nhất một tuyến.")
    return {"nodes": nodes, "roads": roads, "path_edge_incidences": incidence,
            "dimension": problem["dimension"], "calls": POPULATION * (UPDATES + 1)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    summaries = []
    raw = []
    baseline = scale_case(SIZES[0])
    genes = [1.0] * baseline["dimension"]
    baseline_cost = evaluate(baseline, genes)["total_minutes"]
    for size in SIZES:
        problem = scale_case(size)
        info = size_info(problem)
        if info["nodes"] != size or info["dimension"] != len(genes):
            raise RuntimeError("Sai số nút hoặc số trọng số trong phép đo quy mô.")
        cost = evaluate(problem, genes)["total_minutes"]
        if abs(cost - baseline_cost) > 1e-7:
            raise RuntimeError("Chia cạnh đã đổi chi phí của cùng một ứng viên.")
        by_method = {method: [] for method in METHODS}
        for seed in SEEDS:
            order = METHODS if seed % 2 == 0 else METHODS[::-1]
            for method in order:
                run = solve(problem, method, POPULATION, UPDATES, seed)
                score = run["evaluation"]
                row = dict(info, algorithm=method, seed=seed, valid=int(score["valid"]), seconds=run["seconds"])
                if run["calls"] != info["calls"]:
                    raise RuntimeError("Sai ngân sách đo quy mô.")
                by_method[method].append(row)
                raw.append(row)
        for method, rows in by_method.items():
            peak_mib, calls = measure_peak(size, method)
            if calls != info["calls"]:
                raise RuntimeError("Lượt đo RAM sai ngân sách.")
            times = [row["seconds"] for row in rows]
            record = dict(info, algorithm=method, runs=len(rows), valid=sum(row["valid"] for row in rows),
                          median_seconds=statistics.median(times), max_seconds=max(times), peak_python_mib=peak_mib)
            summaries.append(record)
            print(f"{size:5} nút | {method:3} | {record['median_seconds']:.3f} s | {peak_mib:.2f} MiB", flush=True)
    write_csv(args.out / "scale_runs.csv", raw)
    write_csv(args.out / "scale_summary.csv", summaries)
    write_json(args.out / "scale_config.json", {"nodes": list(SIZES), "seeds": list(SEEDS), "memory_seed": SEEDS[0],
                                                "population": POPULATION, "updates": UPDATES,
                                                "machine": platform.machine(), "python": platform.python_version(),
                                                "platform": platform.platform()})


if __name__ == "__main__":
    main()
