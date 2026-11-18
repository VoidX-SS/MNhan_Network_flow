"""Lối vào chung cho form, CLI và các bài đo. Chỗ này giữ phép so sánh công bằng."""

import random

from algorithms import ga, woa
from algorithms.common import initial_population
from model import evaluate

ALGORITHMS = {"GA": ga.solve, "WOA": woa.solve}
DEFAULT_POPULATION = 32
DEFAULT_STEPS = 90
DEFAULT_SEED = 7


def check_settings(size, steps, seed):
    if not isinstance(size, int) or not 4 <= size <= 200:
        raise ValueError("Số ứng viên cần là số nguyên từ 4 đến 200.")
    if not isinstance(steps, int) or not 1 <= steps <= 600:
        raise ValueError("Số vòng cần là số nguyên từ 1 đến 600.")
    if not isinstance(seed, int) or not 0 <= seed <= 2_147_483_647:
        raise ValueError("Seed cần là số nguyên từ 0 đến 2147483647.")


def solve(problem, algorithm, size=DEFAULT_POPULATION, steps=DEFAULT_STEPS,
          seed=DEFAULT_SEED, on_step=None, on_evaluate=None):
    if algorithm not in ALGORITHMS:
        raise ValueError("Chọn GA hoặc WOA.")
    check_settings(size, steps, seed)
    # Hai bên bốc chung bộ vé mở màn. Mỗi thuật toán tự bốc bước tiếp theo.
    population = initial_population(problem["dimension"], size, seed)
    rng = random.Random(seed + 1)

    def score(genes):
        result = evaluate(problem, genes)
        if on_evaluate is not None:
            on_evaluate(result)
        return result

    result = ALGORITHMS[algorithm](population, score, steps, rng, on_step)
    result["algorithm"] = algorithm
    result["seed"] = seed
    return result
