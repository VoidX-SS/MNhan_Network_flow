"""Cửa sổ Qt đọc kết quả của hai thuật toán trong solver.py."""

import argparse
import os
from pathlib import Path
import sys
from threading import Thread

try:
    from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuick import QQuickWindow
except ImportError:
    raise SystemExit("Cài giao diện bằng python -m pip install -r qt_demo/requirements.txt. "
                     "Có thể dùng python app.py để mở giao diện Tk.") from None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from model import cut_proof
from research.scenarios import screen_cases
from solver import ALGORITHMS, DEFAULT_POPULATION, DEFAULT_STEPS, solve
from views import chart_limits, chart_series


CASE_IDS = ("normal", "many_to_one", "light", "cut")


def selected_cases():
    indexed = {item["id"]: item for item in screen_cases()}
    return [indexed[key]["problem"] for key in CASE_IDS]


def make_scene(problem):
    network = problem["network"]
    origins = {pair["from"] for pair in problem["pairs"]}
    destinations = {pair["to"] for pair in problem["pairs"]}
    nodes = network["nodes"]
    # Tránh chồng nét ở hai cạnh ngược chiều.
    directed = {(road["from"], road["to"]) for road in problem["roads"]}
    roads = []
    for road in problem["roads"]:
        start, end = road["from"], road["to"]
        roads.append({"code": road["id"], "start": start, "end": end,
                      "x1": nodes[start][0], "y1": nodes[start][1],
                      "x2": nodes[end][0], "y2": nodes[end][1],
                      "capacity": road["capacity"], "twoWay": (end, start) in directed})
    proof = cut_proof(problem)
    proof_text = ""
    if proof:
        proof_text = (f"Vô nghiệm theo lát cắt. {proof['demand']:g} xe cần qua, "
                      f"sức chứa chỉ {proof['capacity']:g} xe mỗi kỳ.")
    return {"name": problem["name"], "description": problem["description"],
            "nodes": [{"name": key, "x": value[0], "y": value[1],
                       "terminal": key in origins or key in destinations}
                      for key, value in nodes.items()],
            "roads": roads, "roadNames": [road["code"] for road in roads],
            "pairs": [{"name": f"{pair['from']} → {pair['to']}", "demand": pair["demand"]}
                      for pair in problem["pairs"]],
            "totalDemand": sum(pair["demand"] for pair in problem["pairs"]),
            "proof": proof_text, "focus": network.get("focus_road", "E23")}


class Controller(QObject):
    sceneChanged = Signal()
    frameChanged = Signal()
    chartChanged = Signal()
    stateChanged = Signal()
    completed = Signal(object, str)

    def __init__(self, case_index=0):
        super().__init__()
        self.cases = selected_cases()
        self.case_index = case_index
        self._scene = make_scene(self.cases[case_index])
        self.results = {}
        self._chart = {}
        self.step = 0
        self.busy = False
        self.error = ""
        self.worker = None
        self.completed.connect(self._finish)

    @Property("QVariantList", constant=True)
    def labels(self):
        return [case["name"] for case in self.cases]

    @Property("QVariantMap", notify=sceneChanged)
    def scene(self):
        return self._scene

    @Property(int, notify=sceneChanged)
    def caseIndex(self):
        return self.case_index

    @Property(bool, notify=stateChanged)
    def working(self):
        return self.busy

    @Property(str, notify=stateChanged)
    def errorText(self):
        return self.error

    @Property(int, constant=True)
    def steps(self):
        return DEFAULT_STEPS

    @Property(int, constant=True)
    def budget(self):
        return DEFAULT_POPULATION * (DEFAULT_STEPS + 1)

    @Property("QVariantMap", notify=chartChanged)
    def chart(self):
        return self._chart

    @Property("QVariantMap", notify=frameChanged)
    def frame(self):
        snapshot = {"ready": bool(self.results), "step": self.step, "calls": 0}
        for name in ALGORITHMS:
            run = self.results.get(name)
            if not run:
                snapshot[name] = {"ready": False, "flows": []}
                continue
            record = run["history"][self.step]
            score = record["evaluation"]
            snapshot["calls"] = record["calls"]
            snapshot[name] = {"ready": True, "valid": score["valid"],
                              "minutes": score["total_minutes"], "violation": score["violation"],
                              "flows": score["edge_flows"]}
        return snapshot

    @Slot(int)
    def chooseCase(self, index):
        if self.busy or not 0 <= index < len(self.cases) or index == self.case_index:
            return
        self.case_index = index
        self._scene = make_scene(self.cases[index])
        self._clear_run()
        self.sceneChanged.emit()
        self.stateChanged.emit()

    def _clear_run(self):
        self.step = 0
        self.results = {}
        self.error = ""
        self._chart = {}
        self.frameChanged.emit()
        self.chartChanged.emit()

    @Slot(int)
    def startRun(self, seed):
        if self.busy:
            return
        self.busy = True
        self._clear_run()
        self.stateChanged.emit()
        problem = self.cases[self.case_index]
        self.worker = Thread(target=self._solve, args=(problem, seed), daemon=True)
        self.worker.start()

    def _solve(self, problem, seed):
        # Giao diện vẫn đáp ứng trong lúc Python chấm từng ứng viên.
        try:
            results = {name: solve(problem, name, seed=seed) for name in ALGORITHMS}
        except Exception as error:
            self.completed.emit({}, str(error))
            return
        self.completed.emit(results, "")

    @Slot(object, str)
    def _finish(self, results, error):
        self.results = results
        self.error = error
        self.busy = False
        if results:
            self.step = len(results["GA"]["history"]) - 1
            series, valid = chart_series(results)
            first, last, low, high = chart_limits(results, series)
            self._chart = {"ready": True, "valid": valid, "first": first, "last": last,
                           "low": low, "high": high,
                           "GA": [list(point) for point in series["GA"]],
                           "WOA": [list(point) for point in series["WOA"]]}
        self.frameChanged.emit()
        self.chartChanged.emit()
        self.stateChanged.emit()

    @Slot(int)
    def chooseStep(self, step):
        if not self.results:
            return
        self.step = min(max(0, step), self.steps)
        self.frameChanged.emit()


def create_window(case_index=0, seed=1000):
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication([])
    controller = Controller(case_index)
    engine = QQmlApplicationEngine()
    engine.setInitialProperties({"controller": controller, "initialSeed": seed})
    engine.load(QUrl.fromLocalFile(str(Path(__file__).with_name("Main.qml"))))
    return app, controller, engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASE_IDS, default="normal")
    parser.add_argument("--seed", type=int, default=1000)
    args = parser.parse_args()
    if not 0 <= args.seed <= 2_147_483_647:
        parser.error("seed cần nằm từ 0 đến 2147483647")
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    app, controller, engine = create_window(CASE_IDS.index(args.case), args.seed)
    if not engine.rootObjects():
        raise SystemExit("Cửa sổ QML chưa mở được.")
    status = app.exec()
    if controller.worker is not None:
        controller.worker.join()
    # Hủy QML trước bộ điều khiển Python để các binding kết thúc đúng thứ tự.
    del engine
    return status


if __name__ == "__main__":
    raise SystemExit(main())
