"""Chạy thí nghiệm một lần trong terminal, kể cả trên máy chưa có Tkinter."""

import argparse

from model import NETWORK_FILES, cut_proof, load_network, make_problem
from solver import ALGORITHMS, DEFAULT_POPULATION, DEFAULT_SEED, DEFAULT_STEPS, solve


def print_run(problem, result):
    evaluation = result["evaluation"]
    print(f"\n{result['algorithm']} | seed {result['seed']} | {result['calls']} lần chấm | {result['seconds']:.3f} s")
    if evaluation["valid"]:
        print(f"Hợp lệ | Tổng thời gian {evaluation['total_minutes']:.2f} xe·phút")
    else:
        print("Chưa có cách chia hợp lệ trong lượt chạy này.")
        print(f"Xe chưa gán tuyến: {evaluation['unassigned']:.2f} | Vượt tải cộng theo cạnh: {evaluation['overflow']:.2f}")
    for index, pair in enumerate(problem["pairs"]):
        print(f"  {pair['from']} → {pair['to']} | {pair['demand']:g} xe")
        for route_index, route in enumerate(pair["routes"]):
            flow = evaluation["route_flows"][index][route_index]
            route_text = " → ".join(route["path"])
            note = " (đóng)" if not route["open"] else ""
            print(f"    {route_text:<27} {flow:8.2f} xe{note}")
    print("  Luồng/sức chứa theo cạnh:")
    for index, road in enumerate(problem["roads"]):
        flow = evaluation["edge_flows"][index]
        print(f"    {road['id']} {road['from']}→{road['to']:<3} {flow:8.2f} / {road['capacity']:g}")


def main():
    parser = argparse.ArgumentParser(description="So sánh GA và WOA trên một mạng giao thông.")
    parser.add_argument("--network", choices=NETWORK_FILES, default="main", help="main là mạng 50 nút, small là mạng 8 nút.")
    parser.add_argument("--case", default="normal", help="normal, peak, incident, closed, cut hoặc split để tính tay.")
    parser.add_argument("--algorithm", choices=["both", "GA", "WOA"], default="both")
    parser.add_argument("--population", type=int, default=DEFAULT_POPULATION)
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    filename = "mini.json" if args.case == "split" else NETWORK_FILES[args.network]
    network = load_network(filename)
    if args.case not in network["cases"]:
        parser.error("Chọn một kịch bản trong " + ", ".join(network["cases"]) + ".")
    problem = make_problem(network, args.case)
    print(f"{network['name']} | {len(network['nodes'])} nút | {len(network['roads'])} cạnh | {problem['name']}")
    proof = cut_proof(problem)
    if proof:
        print(f"Vô nghiệm theo lát cắt: {proof['demand']:g} xe cần qua, sức chứa {proof['capacity']:g} xe.")
    names = ALGORITHMS if args.algorithm == "both" else [args.algorithm]
    try:
        for name in names:
            print_run(problem, solve(problem, name, args.population, args.steps, args.seed))
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
