"""Vẽ hình dùng trong báo cáo từ CSV đã đo."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

from views import COLORS

OUT = Path(__file__).resolve().parent / "results"
METHODS = ("GA", "WOA")


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def setup_axis(ax):
    ax.set_axisbelow(True)
    ax.grid(axis="y", color="#dbe6eb", linewidth=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color("#bac9d1")


def confirmation(path):
    rows = read_rows(path / "confirm_curves.csv")
    panels = [("normal", "Ngày thường", "hit_1pct", "Đạt trong 1% (%)"),
              ("many_to_one", "Năm nguồn về một đích", "valid", "Đã tìm được hợp lệ (%)"),
              ("light", "Tải nhẹ", "hit_1pct", "Đạt trong 1% (%)"),
              ("cut", "Cao điểm và đóng E23", "median_violation", "Vi phạm trung vị (điểm)")]
    fig, grid = plt.subplots(2, 2, figsize=(11.5, 6.9), layout="constrained")
    fig.suptitle("Hội tụ ở vòng xác nhận · 30 seed mới trên mỗi case", x=0.02, ha="left", weight="bold", fontsize=15)
    for ax, (key, title, metric, label) in zip(grid.flat, panels):
        for method in METHODS:
            group = [row for row in rows if row["case"] == key and row["algorithm"] == method]
            values = [float(row[metric]) for row in group]
            if metric != "median_violation":
                values = [100 * value / int(row["runs"]) for value, row in zip(values, group)]
            ax.plot([int(row["calls"]) for row in group], values, label=method,
                    color=COLORS[method], linewidth=2.2, linestyle="-" if method == "GA" else "--")
        ax.set_title(title, loc="left", weight="bold", color="#152d3b")
        ax.set_ylabel(label)
        ax.set_xlabel("Lượt chấm tích lũy")
        ax.set_xlim(0, 3000)
        if metric != "median_violation":
            ax.set_ylim(-2, 104)
            ax.set_yticks([0, 25, 50, 75, 100])
        setup_axis(ax)
        ax.legend(loc="best", frameon=False)
    fig.savefig(path / "Hoi_tu_xac_nhan.svg", facecolor="white")
    plt.close(fig)


def scaling(path):
    rows = read_rows(path / "scale_summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 4.2), layout="constrained")
    fig.suptitle("Chi phí khi tăng số nút · 25 trọng số và 304 lượt chấm", x=0.02, ha="left", weight="bold", fontsize=15)
    metrics = [("median_seconds", "Thời gian tìm kiếm trung vị (giây)"),
               ("peak_python_mib", "Đỉnh cấp phát Python (MiB)")]
    for ax, (metric, label) in zip(axes, metrics):
        for method in METHODS:
            group = [row for row in rows if row["algorithm"] == method]
            sizes = [int(row["nodes"]) for row in group]
            ax.plot(sizes, [float(row[metric]) for row in group], marker="o", label=method,
                    color=COLORS[method], linewidth=2, linestyle="-" if method == "GA" else "--")
        ax.set_xscale("log")
        ax.set_xticks(sizes)
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.set_xlabel("Số nút của mạng")
        ax.set_ylabel(label)
        setup_axis(ax)
        ax.legend(loc="upper left", frameon=False)
    fig.savefig(path / "Quy_mo.svg", facecolor="white")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()
    confirmation(args.out)
    scaling(args.out)


if __name__ == "__main__":
    main()
