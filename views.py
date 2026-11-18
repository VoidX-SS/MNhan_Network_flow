"""Bản đồ và biểu đồ. Chỉ vẽ số đã chấm, không sửa luồng giao thông."""

import math

INK = "#152d3b"
MUTED = "#526774"
LINE = "#dbe6eb"
GA_COLOR = "#087b70"
WOA_COLOR = "#5e4abd"
COLORS = {"GA": GA_COLOR, "WOA": WOA_COLOR}


def road_style(capacity, flow):
    if capacity == 0:
        return "#8a99a6", 2, (5, 5)
    ratio = flow / capacity
    if ratio > 1 + 1e-8:
        return "#b52936", 5, ()
    if ratio >= 0.9:
        return "#cc621d", 4, ()
    if ratio >= 0.7:
        return "#9b7313", 4, ()
    if flow > 0:
        return GA_COLOR, 3, ()
    return "#a7bac3", 2, ()


def edge_label(road_id, x1, y1, x2, y2, dense=False):
    if dense:
        x, y = (x1 + x2) / 2, (y1 + y2) / 2
        if abs(y2 - y1) > abs(x2 - x1):
            return x + 15, y
        return x, y - 11
    # Tách nhãn ở những chỗ hai đường vẽ chéo qua nhau.
    fractions = {"E02": 0.34, "E03": 0.34, "E06": 0.27, "E07": 0.30,
                 "E09": 0.69, "E11": 0.66, "E12": 0.66}
    fraction = fractions.get(road_id, 0.5)
    return x1 + (x2 - x1) * fraction, y1 + (y2 - y1) * fraction


def road_segment(coords, road, radius, connections):
    start, end = road["from"], road["to"]
    x1, y1 = coords[start]
    x2, y2 = coords[end]
    length = max(1.0, math.hypot(x2 - x1, y2 - y1))
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    # Hai chiều chung một đoạn vật lý được vẽ hơi lệch nhau để nhìn rõ mũi tên.
    offset = 3 if (end, start) in connections else 0
    return (x1 + radius * ux - offset * uy, y1 + radius * uy + offset * ux,
            x2 - (radius + 1) * ux - offset * uy, y2 - (radius + 1) * uy + offset * ux)


def draw_map(canvas, problem, evaluation, selected, on_pick):
    canvas.delete("all")
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    if width < 100 or height < 100:
        return
    nodes = problem["network"]["nodes"]
    dense = len(nodes) > 20
    radius = 7 if dense else 15
    important = problem["network"].get("study_roads", [])
    connections = {(road["from"], road["to"]) for road in problem["roads"]}
    coords = {}
    for node in nodes:
        coords[node] = (20 + nodes[node][0] * (width - 40), 22 + nodes[node][1] * (height - 54))
    title = "Năm hành lang qua lát cắt giữa mạng" if dense else "Qua hành lang A/B → C/D"
    canvas.create_text(width / 2, 15, text=title, fill=MUTED, font="TkDefaultFont")
    labels = []
    for index, road in enumerate(problem["roads"]):
        road_id = road["id"]
        x1, y1, x2, y2 = road_segment(coords, road, radius, connections)
        flow = evaluation["edge_flows"][index] if evaluation else 0
        color, thickness, dash = road_style(road["capacity"], flow)
        tag = "road_" + road_id
        if road_id == selected:
            canvas.create_line(x1, y1, x2, y2, fill="#d3e5f3", width=thickness + 7, tags=tag)
        canvas.create_line(x1, y1, x2, y2, fill=color, width=thickness, dash=dash,
                           arrow="last", arrowshape=(5, 7, 3) if dense else (9, 11, 4), tags=tag)
        canvas.tag_bind(tag, "<Button-1>", lambda event, rid=road_id: on_pick(rid))
        if not dense or road_id in important or road_id == selected:
            tx, ty = edge_label(road_id, x1, y1, x2, y2, dense)
            labels.append((road_id, tx, ty, color, tag))
    for road_id, x, y, color, tag in labels:
        fill = "#eaf3fb" if road_id == selected else "#ffffff"
        canvas.create_rectangle(x - 17, y - 9, x + 17, y + 9, fill=fill, outline=LINE, tags=tag)
        canvas.create_text(x, y, text=road_id, fill=color, font="TkSmallCaptionFont", tags=tag)
    for node, (x, y) in coords.items():
        special = node.startswith(("O", "T"))
        fill = INK if special else "#ffffff"
        fg = "white" if special else INK
        canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=fill, outline=INK, width=1.5)
        if dense and special:
            canvas.create_text(x, y - 16, text=node, fill=INK, font="TkSmallCaptionFont")
        elif not dense:
            canvas.create_text(x, y, text=node, fill=fg, font="TkHeadingFont")


def chart_series(runs):
    # Chi phí chỉ có ý nghĩa khi phương án đã chở đủ xe và không vượt tải.
    show_cost = any(run["evaluation"]["valid"] for run in runs.values())
    series = {}
    for algorithm, run in runs.items():
        points = []
        for record in run["history"]:
            score = record["evaluation"]
            if show_cost:
                if score["valid"]:
                    points.append((record["calls"], score["total_minutes"]))
            else:
                points.append((record["calls"], score["violation"]))
        series[algorithm] = points
    return series, show_cost


def chart_limits(runs, series):
    values = [value for points in series.values() for _, value in points]
    low = min(values)
    high = max(values)
    pad = max((high - low) * 0.08, abs(high) * 0.0001, 0.01)
    start = min(run["history"][0]["calls"] for run in runs.values())
    end = max(run["calls"] for run in runs.values())
    return start, end, max(0, low - pad), high + pad


def draw_chart(canvas, runs, step):
    canvas.delete("all")
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    if width < 120 or height < 120:
        return
    if not runs:
        canvas.create_text(width / 2, height / 2, text="Bấm chạy để xem đường hội tụ", fill=MUTED)
        return
    series, show_cost = chart_series(runs)
    first, last, low, high = chart_limits(runs, series)
    left, top, right, bottom = 72, 35, width - 20, height - 60

    def xy(calls, value):
        x = left + (right - left) * (calls - first) / (last - first)
        y = bottom - (bottom - top) * (value - low) / (high - low)
        return x, y

    title = "Xe·phút (chỉ nghiệm hợp lệ)" if show_cost else "Mức vi phạm (nhỏ hơn tốt hơn)"
    canvas.create_text(left, 17, text=title, anchor="w", fill=MUTED)
    for tick in range(4):
        value = low + (high - low) * tick / 3
        _, y = xy(first, value)
        canvas.create_line(left, y, right, y, fill=LINE)
        label = f"{value:,.2f}" if high - low < 1 else f"{value:,.1f}"
        canvas.create_text(left - 7, y, text=label, anchor="e", fill=MUTED)
    for calls in [first, (first + last) // 2, last]:
        x, _ = xy(calls, low)
        canvas.create_text(x, bottom + 14, text=f"{calls:,}", fill=MUTED)
    canvas.create_text((left + right) / 2, bottom + 35, text="Số lượt chấm", fill=MUTED)
    cursor = runs["GA"]["history"][step]["calls"]
    cursor_x, _ = xy(cursor, low)
    canvas.create_line(cursor_x, top, cursor_x, bottom, fill="#879cac", dash=(3, 4))
    for algorithm, points in series.items():
        line = []
        for calls, value in points:
            line.extend(xy(calls, value))
        if len(line) >= 4:
            canvas.create_line(*line, fill=COLORS[algorithm], width=2.5)
        if line:
            x, y = line[-2:]
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=COLORS[algorithm], outline="")
