"""In dữ liệu của một lần chọn bố mẹ và sinh con để kiểm lại animation."""

import json
import random

from algorithms import ga
from algorithms.common import initial_population


class DrawLog:
    """Dùng bộ bốc số thường và ghi lại đúng thứ tự đã bốc."""

    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.draws = []

    def remember(self, value):
        self.draws.append(value)
        return value

    def randrange(self, stop):
        return self.remember(self.rng.randrange(stop))

    def random(self):
        return self.remember(self.rng.random())

    def uniform(self, low, high):
        return self.remember(self.rng.uniform(low, high))


def make_trace():
    population_seed = 19
    draw_seed = 73
    center = [0.32, 0.68]
    population = initial_population(2, 6, population_seed)

    def score(genes):
        return sum((gene - target) ** 2 for gene, target in zip(genes, center))

    scores = [{"rank": (score(genes),)} for genes in population]
    rng = DrawLog(draw_seed)
    first = ga.select_parent(population, scores, rng)
    first_draw = rng.draws.copy()
    rng.draws.clear()
    second = ga.select_parent(population, scores, rng)
    second_draw = rng.draws.copy()
    rng.draws.clear()
    details = {"crossover": 0, "mutation": 0}
    child = ga.make_child(first, second, rng, details)
    # Ví dụ cố định có lai và đúng một lần đột biến ở gene y.
    if details != {"crossover": 1, "mutation": 1} or len(rng.draws) != 6:
        raise RuntimeError("Toán tử GA thay đổi, cần cập nhật dữ liệu minh họa.")
    cross_draw, weight_x, weight_y, test_x, test_y, delta_y = rng.draws
    if not test_y < 0.5 <= test_x:
        raise RuntimeError("Ví dụ hiện tại cần đúng gene y đột biến.")
    cross = [
        weight_x * first[0] + (1 - weight_x) * second[0],
        weight_y * first[1] + (1 - weight_y) * second[1],
    ]
    if child != [cross[0], max(0.0, min(1.0, cross[1] + delta_y))]:
        raise RuntimeError("Dữ liệu minh họa chưa khớp kết quả toán tử.")
    return {
        "population_seed": population_seed,
        "draw_seed": draw_seed,
        "center": center,
        "population": [
            {"id": f"P{index + 1}", "genes": genes, "score": score(genes)}
            for index, genes in enumerate(population)
        ],
        "tournaments": [first_draw, second_draw],
        "winners": [population.index(first), population.index(second)],
        "cross": {"draw": cross_draw, "weights": [weight_x, weight_y], "genes": cross, "score": score(cross)},
        "mutation": {"draws": [test_x, test_y], "delta_y": delta_y, "genes": child, "score": score(child)},
    }


if __name__ == "__main__":
    print(json.dumps(make_trace(), indent=2))
