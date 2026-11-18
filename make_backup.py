"""Ghép số đo đã lưu thành một trang xem lại chạy offline."""

import argparse
import csv
from html import escape
import json
import math
from pathlib import Path

from experiments import compare_paired, summarize
from model import cut_proof, make_problem
from solver import ALGORITHMS, solve
from views import COLORS, INK, LINE, MUTED, chart_limits, chart_series, edge_label, road_segment, road_style


def number(value, digits=2):
    if value is None or value == "":
        return "·"
    return f"{float(value):,.{digits}f}"


def map_svg(problem, score):
    network = problem["network"]
    dense = len(network["nodes"]) > 20
    radius = 5.5 if dense else 14
    important = network.get("study_roads", [])
    connections = {(road["from"], road["to"]) for road in problem["roads"]}
    coords = {}
    for node, data in network["nodes"].items():
        coords[node] = (30 + 380 * data[0], 14 + 202 * data[1])
    svg = ['<svg viewBox="0 0 440 230" role="img" aria-label="Bản đồ phân luồng theo cạnh">']
    labels = []
    for index, road in enumerate(problem["roads"]):
        x1, y1, x2, y2 = road_segment(coords, road, radius, connections)
        dx, dy = x2 - x1, y2 - y1
        length = max(1, math.hypot(dx, dy))
        ux, uy = dx / length, dy / length
        flow = score["edge_flows"][index]
        color, width, dash = road_style(road["capacity"], flow)
        dashes = ' stroke-dasharray="5 5"' if dash else ""
        arrow_length = 6 if dense else 9
        arrow_half = 2.5 if dense else 4
        a, b = x2 - arrow_length * ux, y2 - arrow_length * uy
        arrow = f"{x2:.1f},{y2:.1f} {a + arrow_half * uy:.1f},{b - arrow_half * ux:.1f} {a - arrow_half * uy:.1f},{b + arrow_half * ux:.1f}"
        title = f"{road['id']} {road['from']} → {road['to']}: {flow:.2f} / {road['capacity']:g} xe"
        svg.append(f'<g><title>{escape(title)}</title><line x1="{x1:.1f}" y1="{y1:.1f}" x2="{a:.1f}" y2="{b:.1f}" stroke="{color}" stroke-width="{width}"{dashes}/><polygon points="{arrow}" fill="{color}"/></g>')
        if not dense or road["id"] in important:
            x, y = edge_label(road["id"], x1, y1, x2, y2, dense)
            labels.append(f'<g><title>{escape(title)}</title><rect x="{x-16:.1f}" y="{y-9:.1f}" width="32" height="18" rx="3" fill="white" stroke="{LINE}"/><text x="{x:.1f}" y="{y:.1f}" class="node-text" fill="{color}">{escape(road["id"])}</text></g>')
    svg.extend(labels)
    for node, (x, y) in coords.items():
        special = node.startswith(("O", "T"))
        fill, foreground = (INK, "white") if special else ("white", INK)
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{fill}" stroke="{INK}" stroke-width="1.5"/>')
        if dense and special:
            svg.append(f'<text x="{x:.1f}" y="{y-14:.1f}" class="node-text" fill="{INK}">{escape(node)}</text>')
        elif not dense:
            svg.append(f'<text x="{x:.1f}" y="{y:.1f}" class="node-text" fill="{foreground}">{escape(node)}</text>')
    svg.append('</svg>')
    return "".join(svg)


def convergence_svg(runs):
    series, show_cost = chart_series(runs)
    first, last, low, high = chart_limits(runs, series)
    title = "Xe·phút ở nghiệm hợp lệ" if show_cost else "Điểm vi phạm (nhỏ hơn tốt hơn)"

    def xy(calls, value):
        return 92 + 610 * (calls - first) / (last - first), 185 - 145 * (value - low) / (high - low)

    svg = [f'<svg viewBox="0 0 730 230" role="img" aria-label="{title}"><text x="92" y="18">{title}</text>']
    for tick in range(4):
        value = low + (high - low) * tick / 3
        _, y = xy(first, value)
        svg.append(f'<line x1="92" x2="702" y1="{y:.1f}" y2="{y:.1f}" stroke="{LINE}"/><text x="80" y="{y+4:.1f}" text-anchor="end">{number(value, 1)}</text>')
    for calls in [first, (first + last) // 2, last]:
        x, _ = xy(calls, low)
        svg.append(f'<text x="{x:.1f}" y="207" text-anchor="middle">{number(calls, 0)}</text>')
    svg.append('<text x="397" y="225" text-anchor="middle">Số lượt chấm</text>')
    for algorithm, points in series.items():
        if not points:
            continue
        coordinates = [xy(calls, value) for calls, value in points]
        line = " ".join(f"{x:.1f},{y:.1f}" for x, y in coordinates)
        color = COLORS[algorithm]
        x, y = coordinates[-1]
        svg.append(f'<polyline points="{line}" stroke="{color}" stroke-width="2.5" fill="none"/><circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>')
    svg.append('</svg>')
    return "".join(svg)


def summary_table(rows):
    body = ""
    show_targets = "hit_1pct" in rows[0]
    for row in rows:
        best = number(row["best_valid_cost"])
        if row["best_valid_seed"]:
            best += f" (seed {row['best_valid_seed']})"
        hit_cell = ""
        if show_targets:
            hits = row["hit_1pct"]
            target_text = f"{hits}/{row['runs']}" if hits is not None else "·"
            hit_cell = f"<td>{target_text}</td>"
        body += (f'<tr><th scope="row">{row["algorithm"]}</th><td>{row["valid_runs"]}/{row["runs"]}</td>'
                 f'{hit_cell}'
                 f'<td>{number(row["median_valid_cost"])}</td><td>{number(row["q1_valid_cost"])} / {number(row["q3_valid_cost"])}</td>'
                 f'<td>{best}</td><td>{number(row["median_invalid_violation"])}</td></tr>')
    header = '<th>Trong 1%</th>' if show_targets else ''
    return (f'<div class="scroll"><table><thead><tr><th>Thuật toán</th><th>Hợp lệ</th>{header}<th>Trung vị hợp lệ</th>'
            '<th>Q1 / Q3 hợp lệ</th><th>Tốt nhất hợp lệ</th><th>Vi phạm trung vị<br>(lượt lỗi)</th></tr></thead>'
            f'<tbody>{body}</tbody></table></div>')


def show_case(problem, sample, rows, meta, paired):
    case_id = problem["id"]
    runs = sample["runs"]
    proof = sample["proof"]
    maps = ""
    for algorithm, run in runs.items():
        score = run["evaluation"]
        if score["valid"]:
            label = f'{number(score["total_minutes"])} xe·phút'
            note = "Hợp lệ"
        else:
            label = f'{number(score["violation"])} điểm vi phạm'
            note = "Phương án thử"
        maps += (f'<article class="panel"><div class="cap"><b style="color:{COLORS[algorithm]}">{algorithm}</b>'
                 f'<span>{note}</span></div><strong class="metric">{label}</strong>{map_svg(problem, score)}</article>')
    alert = ""
    if proof:
        alert = (f'<aside class="proof"><b>Chứng minh vô nghiệm.</b> {proof["demand"]:g} xe cần qua lát cắt, '
                 f'các cạnh {", ".join(proof["roads"])} chứa tổng cộng {proof["capacity"]:g} xe.</aside>')
    matching = int(paired["paired_valid"])
    paired_note = "Không có cặp seed cùng hợp lệ để so chi phí." if not matching else (
        f'Trong {matching} cặp cùng hợp lệ, GA thấp hơn {paired["GA_lower"]}, WOA thấp hơn {paired["WOA_lower"]}, '
        f'ngang nhau {paired["ties"]} với ngưỡng {paired["tie_tolerance_vehicle_minutes"]} xe·phút.')
    return (f'<section class="case" id="{case_id}"><div class="case-head"><div><h2>{escape(problem["name"])}</h2>'
            f'<p>{escape(problem["description"])}</p></div><span class="pill">Seed {meta["sample_seed"]} · '
            f'{number(meta["evaluations_per_run"], 0)} lượt chấm mỗi bên</span></div>{alert}<div class="maps">{maps}</div>'
            '<p class="legend">Xanh dưới 70% · vàng 70–90% · cam 90–100% · đỏ vượt tải · nét đứt đóng đường. Rê chuột lên mã cạnh để xem số xe.</p>'
            '<div class="evidence"><article class="panel"><div class="cap"><b>Tiến trình seed mẫu</b><span>GA xanh · WOA tím</span></div>'
            f'{convergence_svg(runs)}</article><article class="panel"><div class="cap"><b>Số liệu nhiều seed</b>'
            f'<span>Chi phí tính bằng xe·phút</span></div>{summary_table(rows)}<p class="fine">{paired_note}</p></article></div></section>')


STYLE = """
:root{font:15px/1.5 system-ui,sans-serif;color:#152d3b;background:#edf4f6}
*{box-sizing:border-box} body{margin:0} header{background:#152d3b;color:white;padding:27px 4vw 30px}
.wrap{width:min(1250px,94vw);margin:auto} .eyebrow{color:#9ee1d6;font-size:.78rem;font-weight:750;letter-spacing:.1em}
h1{font-size:clamp(1.6rem,4vw,2.55rem);letter-spacing:-.035em;margin:6px 0 2px} header p{margin:0;color:#d9e8ef}
main{padding:22px 0 35px} .controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
select{font:inherit;background:white;color:#152d3b;border:1px solid #b8ccd4;border-radius:7px;padding:8px 34px 8px 10px}
.case{margin-top:14px}.case-head,.cap{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
h2{margin:0;font-size:1.55rem}.case-head p{margin:3px 0 9px;color:#526774}.pill{border:1px solid #c3d8df;border-radius:999px;padding:5px 10px;font-size:.86rem;background:#f7fbfc}
.maps,.evidence{display:grid;grid-template-columns:1fr 1fr;gap:12px}.panel{background:white;border:1px solid #d6e4e9;border-radius:12px;padding:12px 15px;min-width:0}
.cap span,.legend,.fine{font-size:.83rem;color:#526774}.metric{display:block;font-size:1.38rem;margin-top:2px;letter-spacing:-.025em}
svg{width:100%;display:block;margin-top:5px}svg text{font-size:12px;fill:#526774}.node-text{font-weight:720;text-anchor:middle;dominant-baseline:central;fill:inherit}svg .node-text[fill="white"]{fill:white}svg .node-text[fill="#152d3b"]{fill:#152d3b}
.maps svg{max-height:215px}.evidence svg{max-height:218px}.proof{border-left:4px solid #b52936;background:#fff3f1;padding:8px 12px;margin:5px 0 10px}.scroll{overflow:auto}
table{width:100%;border-collapse:collapse;text-align:right;font-size:.82rem;margin-top:8px}td,th{border-bottom:1px solid #dbe6eb;padding:8px 5px}th:first-child{text-align:left}thead{color:#526774}.fine{margin:10px 0 0}footer{margin-top:19px;color:#526774;font-size:.83rem}
@media(max-width:760px){.evidence,.maps{grid-template-columns:1fr}.case-head{align-items:flex-start}.maps svg{max-height:240px}}
@media print{header{background:white;color:#152d3b;padding:0}.eyebrow,header p{color:#526774}.controls{display:none}main{padding-top:0}.panel{break-inside:avoid}.wrap{width:100%}}
"""


def saved_cases(directory):
    with (directory / "environment.json").open(encoding="utf-8") as file:
        meta = json.load(file)
    with (directory / "sample_runs.json").open(encoding="utf-8") as file:
        samples = json.load(file)
    with (directory / "summary.csv").open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    with (directory / "paired.csv").open(encoding="utf-8-sig", newline="") as file:
        paired = {row["case"]: row for row in csv.DictReader(file)}
    with (directory / "network_used.json").open(encoding="utf-8") as file:
        network = json.load(file)
    problems = [make_problem(network, case_id) for case_id in network["cases"]]
    return problems, samples, rows, meta, paired


def research_cases(directory):
    from research.scenarios import screen_cases

    protocol = json.loads((directory / "protocol_run.json").read_text(encoding="utf-8"))
    shortlist = json.loads((directory / "shortlist.json").read_text(encoding="utf-8"))
    seed = protocol["confirm_seeds"][0]
    meta = {"sample_seed": seed, "evaluations_per_run": protocol["calls_per_trial"]}
    by_id = {case["id"]: case["problem"] for case in screen_cases()}
    problems = [by_id[entry["case"]] for entry in shortlist]
    with (directory / "confirm_runs.csv").open(encoding="utf-8-sig", newline="") as file:
        measured = list(csv.DictReader(file))
    samples, rows, paired = {}, [], {}
    for problem in problems:
        case_id = problem["id"]
        samples[case_id] = {"proof": cut_proof(problem), "runs": {}}
        groups = {}
        for method in ALGORITHMS:
            samples[case_id]["runs"][method] = solve(problem, method, protocol["population"], protocol["updates"], seed)
            data = [row for row in measured if row["case"] == case_id and row["algorithm"] == method]
            groups[method] = [{"case": case_id, "algorithm": method, "seed": int(row["seed"]), "valid": int(row["valid"]),
                               "total_vehicle_minutes": float(row["cost"]) if row["cost"] else None,
                               "violation": float(row["violation"]), "seconds": float(row["seconds"]),
                               "first_valid_checkpoint_calls": int(row["first_valid_calls"]) if row["first_valid_calls"] else None}
                              for row in data]
            summary = summarize(groups[method])
            summary["hit_1pct"] = sum(int(row["hit_1pct"]) for row in data) if data[0]["hit_1pct"] else None
            rows.append(summary)
        paired[case_id] = compare_paired(groups["GA"], groups["WOA"])
    return problems, samples, rows, meta, paired


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--study", type=Path, help="Dùng kết quả vòng xác nhận thay vì lượt đo nhanh.")
    parser.add_argument("--out", type=Path, default=Path("DEMO_DU_PHONG.html"))
    args = parser.parse_args()
    if args.study:
        problems, samples, rows, meta, paired = research_cases(args.study)
    else:
        problems, samples, rows, meta, paired = saved_cases(args.results)
    network = problems[0]["network"]
    options = []
    cases = []
    for problem in problems:
        case_id = problem["id"]
        options.append(f'<option value="{case_id}">{escape(problem["name"])}</option>')
        cases.append(show_case(problem, samples[case_id],
                               [row for row in rows if row["case"] == case_id], meta, paired[case_id]))
    script = """const picker = document.getElementById('case');
function selectCase() {
  document.querySelectorAll('.case').forEach(function (section) {
    section.hidden = section.id !== picker.value;
  });
}
picker.addEventListener('change', selectCase);
selectCase();"""
    scale = f'{len(network["nodes"])} nút · {len(network["roads"])} cạnh có hướng · {len(network["pairs"])} cặp nguồn và đích'
    footer = "Số liệu vòng xác nhận nằm trong research/results/. Trong 1% dùng cận dưới của chuẩn số." if args.study else "Dữ liệu gốc nằm trong results/."
    document = (f'<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{escape(network["name"])} | Demo dự phòng</title><style>{STYLE}</style></head><body>'
                '<header><div class="wrap"><div class="eyebrow">ĐỒ ÁN AI &nbsp; / &nbsp; BẢN XEM LẠI OFFLINE</div>'
                f'<h1>Điều phối luồng giao thông</h1><p>{scale}. So sánh GA và WOA bằng dữ liệu đã đo.</p></div></header>'
                f'<main class="wrap"><div class="controls"><label for="case"><b>Kịch bản</b></label><select id="case">{"".join(options)}</select></div>'
                f'{"".join(cases)}<footer>Trang phát lại số đo lưu sẵn. {footer} Q1 và Q3 là hai tứ phân vị của chi phí ở các lượt hợp lệ.</footer></main>'
                f'<script>{script}</script></body></html>')
    args.out.write_text(document, encoding="utf-8")
    print(f"Đã tạo {args.out}")


if __name__ == "__main__":
    main()
