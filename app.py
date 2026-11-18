"""Form Tkinter. Nút bấm lấy dữ liệu, solver giải, Canvas kể lại kết quả."""

import argparse
import tkinter as tk
from tkinter import filedialog, font, messagebox, ttk
from pathlib import Path
from queue import Empty, Queue
from threading import Thread

from experiments import write_json
from model import NETWORK_FILES, cut_proof, load_network, make_problem
from solver import ALGORITHMS, DEFAULT_POPULATION, DEFAULT_SEED, DEFAULT_STEPS, check_settings, solve
from views import COLORS, INK, LINE, MUTED, draw_chart, draw_map

BACKGROUND = "#eff5f7"
WHITE = "#ffffff"


class TrafficApp:
    def __init__(self, root, network=None):
        self.root = root
        self.network = load_network() if network is None else network
        self.case_names = {case["name"]: key for key, case in self.network["cases"].items()}
        self.road_names = {f"{road['id']}   {road['from']} → {road['to']}": road["id"] for road in self.network["roads"]}
        self.results = {}
        self.queue = Queue()
        self.busy = False
        self.playing = False
        self.play_job = None
        self.step = 0
        self.selected = self.network.get("focus_road", "E05")
        if self.selected not in self.road_names.values():
            self.selected = next(iter(self.road_names.values()))
        self.algorithm = tk.StringVar(value="GA")
        self.case = tk.StringVar(value=next(iter(self.case_names)))
        self.road = tk.StringVar(value=next(label for label in self.road_names if self.road_names[label] == self.selected))
        self.capacity = tk.StringVar()
        self.demands = []
        for pair in self.network["pairs"]:
            self.demands.append(tk.StringVar())
        self.seed = tk.StringVar(value=str(DEFAULT_SEED))
        self.population = tk.StringVar(value=str(DEFAULT_POPULATION))
        self.steps = tk.StringVar(value=str(DEFAULT_STEPS))
        self.status = tk.StringVar(value="Sẵn sàng chạy.")
        self.locked_inputs = []

        root.title(self.network["name"] + " | GA và WOA")
        root.geometry("1280x820")
        root.minsize(1030, 720)
        root.configure(bg=BACKGROUND)
        self.setup_styles()
        self.build_header()
        body = ttk.Frame(root, padding=(16, 14))
        body.pack(fill="both", expand=True)
        controls = ttk.Frame(body, padding=15, style="Card.TFrame")
        controls.pack(side="left", fill="y", padx=(0, 14))
        self.build_controls(controls)
        workspace = ttk.Frame(body)
        workspace.pack(side="left", fill="both", expand=True)
        self.build_workspace(workspace)
        self.reset_case()

    def setup_styles(self):
        self.font_family = font.nametofont("TkDefaultFont").actual("family")
        available = font.families()
        for family in ("Segoe UI", "DejaVu Sans", "Arial"):
            if family in available:
                self.font_family = family
                break
        for name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkSmallCaptionFont"):
            font.nametofont(name).configure(family=self.font_family, size=10)
        font.nametofont("TkSmallCaptionFont").configure(size=9, weight="bold")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=BACKGROUND)
        style.configure("Card.TFrame", background=WHITE)
        style.configure("TLabel", background=BACKGROUND, foreground=INK)
        style.configure("Card.TLabel", background=WHITE, foreground=INK)
        style.configure("Muted.TLabel", background=WHITE, foreground=MUTED)
        style.configure("Heading.TLabel", background=WHITE, foreground=INK, font=(self.font_family, 12, "bold"))
        style.configure("TButton", padding=(9, 6))
        style.configure("Accent.TButton", background=COLORS["GA"], foreground=WHITE, font=(self.font_family, 10, "bold"))
        style.map("Accent.TButton", background=[("disabled", "#91a7a6"), ("active", "#09675f")],
                  foreground=[("disabled", WHITE)])
        style.configure("TNotebook", background=BACKGROUND, borderwidth=0)
        style.configure("TNotebook.Tab", padding=(13, 7))
        style.configure("Treeview", rowheight=26, fieldbackground=WHITE, foreground=INK)
        style.configure("Treeview.Heading", font=(self.font_family, 9, "bold"))
        style.configure("Horizontal.TProgressbar", background=COLORS["GA"], troughcolor=LINE)
        style.configure("TRadiobutton", background=WHITE, foreground=INK)

    def build_header(self):
        header = tk.Frame(self.root, bg=INK, padx=22, pady=11)
        header.pack(fill="x")
        tk.Label(header, text="TRÍ TUỆ NHÂN TẠO   /   ĐỒ ÁN CUỐI KỲ", bg=INK, fg="#9bded4",
                 font=(self.font_family, 9, "bold")).pack(anchor="w")
        tk.Label(header, text="Điều phối luồng giao thông", bg=INK, fg=WHITE,
                 font=(self.font_family, 22, "bold")).pack(anchor="w")
        scale = f"{len(self.network['nodes'])} nút  •  {len(self.network['roads'])} cạnh có hướng  •  {len(self.network['pairs'])} cặp nguồn và đích"
        tk.Label(header, text=scale,
                 bg=INK, fg="#d3e5eb", font=(self.font_family, 10)).pack(anchor="w", pady=(1, 0))

    def entry(self, parent, variable, width):
        widget = ttk.Entry(parent, textvariable=variable, width=width, justify="right")
        self.locked_inputs.append((widget, "normal"))
        return widget

    def build_controls(self, panel):
        ttk.Label(panel, text="01   Thiết lập kịch bản", style="Heading.TLabel").pack(anchor="w")
        box = ttk.Combobox(panel, textvariable=self.case, values=list(self.case_names), state="readonly", width=25)
        box.pack(fill="x", pady=(8, 5))
        box.bind("<<ComboboxSelected>>", self.reset_case)
        self.locked_inputs.append((box, "readonly"))
        self.description = ttk.Label(panel, style="Muted.TLabel", wraplength=228, justify="left")
        self.description.pack(anchor="w", pady=(0, 14))

        ttk.Label(panel, text="Nhu cầu (xe mỗi kỳ)", style="Heading.TLabel").pack(anchor="w", pady=(0, 5))
        demand_grid = ttk.Frame(panel, style="Card.TFrame")
        demand_grid.pack(fill="x")
        demand_grid.columnconfigure(0, weight=1)
        demand_grid.columnconfigure(1, weight=1)
        for index, pair in enumerate(self.network["pairs"]):
            row = ttk.Frame(demand_grid, style="Card.TFrame")
            row.grid(row=index // 2, column=index % 2, sticky="ew", padx=(0, 7), pady=3)
            ttk.Label(row, text=f"{pair['from']} → {pair['to']}", style="Card.TLabel").pack(side="left")
            self.entry(row, self.demands[index], 5).pack(side="right", padx=(4, 0))
        ttk.Label(panel, text="Sức chứa một đoạn", style="Heading.TLabel").pack(anchor="w", pady=(14, 5))
        row = ttk.Frame(panel, style="Card.TFrame")
        row.pack(fill="x")
        roads = ttk.Combobox(row, textvariable=self.road, values=list(self.road_names), state="readonly", width=14)
        roads.pack(side="left", fill="x", expand=True, padx=(0, 7))
        roads.bind("<<ComboboxSelected>>", self.change_road)
        self.locked_inputs.append((roads, "readonly"))
        self.entry(row, self.capacity, 7).pack(side="right")
        ttk.Label(panel, text="Đặt 0 để đóng đoạn được chọn.", style="Muted.TLabel").pack(anchor="w", pady=(5, 13))

        ttk.Label(panel, text="Thiết lập lượt chạy", style="Heading.TLabel").pack(anchor="w", pady=(0, 5))
        for label, variable in [("Seed", self.seed), ("Quần thể", self.population), ("Số vòng", self.steps)]:
            row = ttk.Frame(panel, style="Card.TFrame")
            row.pack(fill="x", pady=3)
            ttk.Label(row, text=label, style="Card.TLabel").pack(side="left")
            self.entry(row, variable, 10).pack(side="right")
        self.run_button = ttk.Button(panel, text="Chạy GA + WOA", style="Accent.TButton", command=self.start_run)
        self.run_button.pack(fill="x", pady=(15, 5))
        reset = ttk.Button(panel, text="Nạp lại kịch bản", command=self.reset_case)
        reset.pack(fill="x")
        self.locked_inputs.append((reset, "normal"))
        self.progress = ttk.Progressbar(panel, maximum=100)
        self.progress.pack(fill="x", pady=(12, 6))
        ttk.Label(panel, textvariable=self.status, style="Muted.TLabel", wraplength=228).pack(anchor="w")

    def build_workspace(self, parent):
        summary = ttk.Frame(parent)
        summary.pack(fill="x", pady=(0, 8))
        self.cards = {}
        for algorithm in ALGORITHMS:
            card = ttk.Frame(summary, padding=(12, 8), style="Card.TFrame")
            card.pack(side="left", fill="x", expand=True, padx=(0, 6))
            tk.Label(card, text=algorithm, fg=COLORS[algorithm], bg=WHITE,
                     font=(self.font_family, 11, "bold")).pack(anchor="w")
            self.cards[algorithm] = ttk.Label(card, text="Chưa chạy", style="Card.TLabel", width=27)
            self.cards[algorithm].pack(anchor="w")
        self.budget = ttk.Label(summary, text="02   Kết quả", padding=(10, 8), justify="right")
        self.budget.pack(side="right")

        tabs = ttk.Notebook(parent)
        tabs.pack(fill="both", expand=True)
        preview = ttk.Frame(tabs, padding=12, style="Card.TFrame")
        detail = ttk.Frame(tabs, padding=12, style="Card.TFrame")
        tabs.add(preview, text="Bản đồ & tiến trình")
        tabs.add(detail, text="Số liệu từng cạnh và tuyến")
        replay = ttk.Frame(preview, style="Card.TFrame")
        replay.pack(fill="x", pady=(0, 5))
        ttk.Label(replay, text="Bản đồ", style="Heading.TLabel").pack(side="left", padx=(0, 6))
        for name in ALGORITHMS:
            ttk.Radiobutton(replay, text=name, variable=self.algorithm, value=name, command=self.render).pack(side="left")
        self.slider = ttk.Scale(replay, from_=0, to=1, command=self.change_step)
        self.slider.pack(side="left", fill="x", expand=True, padx=10)
        self.slider.state(["disabled"])
        self.step_label = ttk.Label(replay, text="Chờ chạy", style="Muted.TLabel", width=16)
        self.step_label.pack(side="left")
        self.play_button = ttk.Button(replay, text="Phát lại", command=self.toggle_play, state="disabled", width=7)
        self.play_button.pack(side="right")

        plots = ttk.Frame(preview, style="Card.TFrame")
        plots.pack(fill="both", expand=True)
        plots.columnconfigure(0, weight=6)
        plots.columnconfigure(1, weight=5)
        plots.rowconfigure(0, weight=1)
        self.map_canvas = tk.Canvas(plots, bg="#f6fafb", highlightthickness=1, highlightbackground=LINE, width=310, height=280)
        self.map_canvas.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.map_canvas.bind("<Configure>", self.render_map)
        self.chart_canvas = tk.Canvas(plots, bg=WHITE, highlightthickness=1, highlightbackground=LINE, width=280, height=280)
        self.chart_canvas.grid(row=0, column=1, sticky="nsew")
        self.chart_canvas.bind("<Configure>", self.render_chart)
        ttk.Label(preview, text="Xanh <70%  |  Vàng 70–90%  |  Cam 90–100%  |  Đỏ vượt tải  |  Nét đứt: đóng",
                  style="Muted.TLabel", wraplength=700).pack(anchor="w", pady=(6, 3))
        self.road_info = ttk.Label(preview, style="Card.TLabel", wraplength=700)
        self.road_info.pack(anchor="w")
        self.proof_info = ttk.Label(preview, style="Muted.TLabel", wraplength=700)
        self.proof_info.pack(anchor="w", pady=(3, 0))

        detail_head = ttk.Frame(detail, style="Card.TFrame")
        detail_head.pack(fill="x", pady=(0, 6))
        self.table_caption = ttk.Label(detail_head, text="Chờ lượt chạy", style="Heading.TLabel")
        self.table_caption.pack(side="left")
        self.save_button = ttk.Button(detail_head, text="Lưu lượt chạy JSON", command=self.export_run, state="disabled")
        self.save_button.pack(side="right")
        self.edges = self.make_table(detail, ["Cạnh", "Nối", "Xe", "Sức chứa", "Tải %", "Phút/xe"], [62, 120, 80, 90, 75, 85], 8)
        dense = len(self.network["nodes"]) > 20
        route_width = 790 if dense else 290
        self.routes = self.make_table(detail, ["Cặp", "Tuyến", "Xe", "Trạng thái"], [100, route_width, 88, 130], 7, dense)

    def make_table(self, parent, headings, widths, height, horizontal=False):
        panel = ttk.Frame(parent, style="Card.TFrame")
        panel.pack(fill="both", expand=True, pady=(0, 6))
        table = ttk.Treeview(panel, columns=headings, show="headings", height=height)
        for title, width in zip(headings, widths):
            table.heading(title, text=title)
            table.column(title, width=width, anchor="center", minwidth=55, stretch=not horizontal)
        if horizontal:
            scroll_x = ttk.Scrollbar(panel, orient="horizontal", command=table.xview)
            table.configure(xscrollcommand=scroll_x.set)
            scroll_x.pack(side="bottom", fill="x")
        scroll = ttk.Scrollbar(panel, orient="vertical", command=table.yview)
        table.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        table.pack(side="left", fill="both", expand=True)
        return table

    def current_case_id(self):
        return self.case_names[self.case.get()]

    def reset_case(self, event=None):
        self.stop_play()
        case = self.network["cases"][self.current_case_id()]
        self.description.configure(text=case["description"])
        for index, amount in enumerate(case["demand"]):
            self.demands[index].set(str(amount))
        self.problem = make_problem(self.network, self.current_case_id())
        self.selected = self.road_names[self.road.get()]
        self.change_road()
        self.progress.configure(value=0)
        self.status.set("Sẵn sàng. Có thể chỉnh nhu cầu và một sức chứa.")
        self.clear_results()

    def change_road(self, event=None):
        road_id = self.road_names[self.road.get()]
        preset = self.network["cases"][self.current_case_id()]
        for road in self.network["roads"]:
            if road["id"] == road_id:
                self.capacity.set(str(preset["capacity"].get(road_id, road["capacity"])))
                break

    def clear_results(self):
        self.results = {}
        self.step = 0
        self.slider.set(0)
        self.slider.state(["disabled"])
        self.play_button.state(["disabled"])
        self.save_button.state(["disabled"])
        self.render()

    def start_run(self):
        if self.busy:
            return
        try:
            demands = [float(value.get()) for value in self.demands]
            road_id = self.road_names[self.road.get()]
            problem = make_problem(self.network, self.current_case_id(), demands, {road_id: float(self.capacity.get())})
            size, steps, seed = int(self.population.get()), int(self.steps.get()), int(self.seed.get())
            check_settings(size, steps, seed)
        except ValueError as error:
            messagebox.showerror("Xem lại dữ liệu", f"Dùng dấu chấm cho số lẻ. Seed, quần thể và số vòng cần là số nguyên.\n{error}")
            return
        self.stop_play()
        self.problem = problem
        self.selected = road_id
        self.clear_results()
        self.busy = True
        self.run_button.state(["disabled"])
        for widget, _ in self.locked_inputs:
            widget.configure(state="disabled")
        self.progress.configure(value=0)
        self.status.set("Đang chấm hai quần thể...")
        # Bếp tính toán chạy riêng. Quầy giao diện chỉ nhận món qua hàng đợi.
        thread = Thread(target=self.worker, args=(problem, size, steps, seed), daemon=True)
        thread.start()
        self.root.after(45, self.poll_worker)

    def worker(self, problem, size, steps, seed):
        results = {}
        try:
            for index, name in enumerate(ALGORITHMS):
                def progress(record):
                    step = record["step"]
                    if step % max(1, steps // 16) == 0 or step == steps:
                        self.queue.put(("progress", (name, step, steps, 50 * (index + step / steps))))

                results[name] = solve(problem, name, size, steps, seed, progress)
        except Exception as error:
            self.queue.put(("error", str(error)))
            return
        self.queue.put(("done", results))

    def poll_worker(self):
        while True:
            try:
                message, value = self.queue.get_nowait()
            except Empty:
                break
            if message == "progress":
                name, step, steps, percent = value
                self.progress.configure(value=percent)
                self.status.set(f"{name} đang chạy vòng {step}/{steps}")
            else:
                self.busy = False
                self.run_button.state(["!disabled"])
                for widget, state in self.locked_inputs:
                    widget.configure(state=state)
                if message == "error":
                    self.status.set("Xem lại thiết lập rồi chạy lại.")
                    messagebox.showerror("Lượt chạy chưa hoàn tất", value)
                else:
                    self.results = value
                    maximum = len(self.results["GA"]["history"]) - 1
                    self.slider.configure(to=maximum)
                    self.slider.state(["!disabled"])
                    self.slider.set(maximum)
                    self.step = maximum
                    self.play_button.state(["!disabled"])
                    self.save_button.state(["!disabled"])
                    self.status.set("Đã chạy xong. Chọn GA/WOA hoặc kéo thanh để xem lại.")
                    self.render()
        if self.busy:
            self.root.after(45, self.poll_worker)

    def change_step(self, value):
        if self.results:
            self.step = round(float(value))
            self.render()

    def toggle_play(self):
        if self.playing:
            self.stop_play()
            return
        if self.results:
            if self.step == len(self.results["GA"]["history"]) - 1:
                self.slider.set(0)
                self.change_step(0)
            self.playing = True
            self.play_button.configure(text="Dừng")
            self.advance()

    def advance(self):
        if not self.playing:
            return
        maximum = len(self.results["GA"]["history"]) - 1
        if self.step >= maximum:
            self.stop_play()
            return
        new_step = min(maximum, self.step + max(1, maximum // 100))
        self.slider.set(new_step)
        self.change_step(new_step)
        self.play_job = self.root.after(52, self.advance)

    def stop_play(self):
        self.playing = False
        if self.play_job is not None:
            self.root.after_cancel(self.play_job)
            self.play_job = None
        self.play_button.configure(text="Phát lại")

    def evaluation(self):
        if self.results:
            return self.results[self.algorithm.get()]["history"][self.step]["evaluation"]
        return None

    def pick_road(self, road_id):
        self.selected = road_id
        self.render_map()

    def render_map(self, event=None):
        if not hasattr(self, "problem"):
            return
        evaluation = self.evaluation()
        draw_map(self.map_canvas, self.problem, evaluation, self.selected, self.pick_road)
        for index, road in enumerate(self.problem["roads"]):
            if road["id"] == self.selected:
                label = f"{road['id']}  {road['from']} → {road['to']}  |  Sức chứa {road['capacity']:g} xe"
                if evaluation:
                    label += f"  |  Luồng {evaluation['edge_flows'][index]:.2f} xe"
                    minutes = evaluation["edge_minutes"][index]
                    if minutes is not None:
                        label += f"  |  {minutes:.2f} phút/xe"
                self.road_info.configure(text=label)
                break

    def render_chart(self, event=None):
        draw_chart(self.chart_canvas, self.results, self.step)

    def render_tables(self, evaluation):
        self.edges.delete(*self.edges.get_children())
        self.routes.delete(*self.routes.get_children())
        if not evaluation:
            self.table_caption.configure(text="Chạy để xem số liệu")
            return
        self.table_caption.configure(text=f"{self.algorithm.get()}  |  Vòng {self.step}  |  {'Hợp lệ' if evaluation['valid'] else 'Phương án thử vi phạm'}")
        for index, road in enumerate(self.problem["roads"]):
            flow = evaluation["edge_flows"][index]
            capacity = road["capacity"]
            minutes = evaluation["edge_minutes"][index]
            ratio = f"{100 * flow / capacity:.1f}%" if capacity else "Đóng"
            duration = f"{minutes:.2f}" if minutes is not None else "Đóng"
            self.edges.insert("", "end", values=(road["id"], f"{road['from']} → {road['to']}",
                                                  f"{flow:.2f}", f"{capacity:g}", ratio, duration))
        for index, pair in enumerate(self.problem["pairs"]):
            for route_index, route in enumerate(pair["routes"]):
                flow = evaluation["route_flows"][index][route_index]
                self.routes.insert("", "end", values=(f"{pair['from']} → {pair['to']}", " → ".join(route["path"]),
                                                       f"{flow:.2f}", "Mở" if route["open"] else "Đóng"))

    def render(self):
        proof = cut_proof(self.problem)
        note = "Bản đồ ở vòng đang xem. Bấm cạnh để đọc số, hoặc mở bảng để xem toàn mạng."
        if proof:
            note = f"Vô nghiệm theo lát cắt. {proof['demand']:g} xe cần qua, còn {proof['capacity']:g} chỗ. Các cạnh: {', '.join(proof['roads'])}."
        evaluation = self.evaluation()
        if evaluation and not evaluation["valid"]:
            note += f"  |  Xe chưa gán {evaluation['unassigned']:.2f}. Vượt tải cộng theo cạnh {evaluation['overflow']:.2f}."
        self.proof_info.configure(text=note)
        for name in ALGORITHMS:
            label = "Chưa chạy"
            if self.results:
                score = self.results[name]["history"][self.step]["evaluation"]
                if score["valid"]:
                    label = f"Hợp lệ  |  {score['total_minutes']:,.2f} xe·phút"
                else:
                    label = f"Vi phạm  |  {score['violation']:.2f} điểm"
            self.cards[name].configure(text=label)
        if self.results:
            record = self.results["GA"]["history"][self.step]
            self.budget.configure(text=f"{record['calls']:,} lượt chấm / bên\nSeed {self.results['GA']['seed']}")
            self.step_label.configure(text=f"Vòng {self.step}/{len(self.results['GA']['history']) - 1}")
        else:
            self.budget.configure(text="02   Kết quả")
            self.step_label.configure(text="Chờ chạy")
        self.render_map()
        self.render_chart()
        self.render_tables(evaluation)

    def export_run(self):
        filename = filedialog.asksaveasfilename(defaultextension=".json", initialfile="luot_chay.json",
                                                filetypes=[("JSON", "*.json")])
        if filename:
            snapshot = {"network": self.network["name"], "case": self.problem["id"],
                        "demand": [pair["demand"] for pair in self.problem["pairs"]],
                        "capacity": {road["id"]: road["capacity"] for road in self.problem["roads"]},
                        "proof": cut_proof(self.problem), "runs": self.results}
            try:
                write_json(Path(filename), snapshot)
                self.status.set("Đã lưu số liệu và các vòng replay.")
            except OSError as error:
                messagebox.showerror("Chưa lưu được", str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--network", choices=NETWORK_FILES, default="main", help="main là mạng 50 nút, small là mạng 8 nút.")
    args = parser.parse_args()
    root = tk.Tk()
    TrafficApp(root, load_network(NETWORK_FILES[args.network]))
    root.mainloop()


if __name__ == "__main__":
    main()
