"""Quần thể ban đầu và cách giữ nhật ký chung cho hai thuật toán."""

import random
from time import perf_counter


def initial_population(dimension, size, seed):
    rng = random.Random(seed)
    population = []
    for _ in range(size):
        genes = []
        for _ in range(dimension):
            genes.append(rng.random())
        population.append(genes)
    return population


def score_population(population, evaluate):
    return [evaluate(genes) for genes in population]


def best_index(scores):
    best = 0
    for index in range(1, len(scores)):
        if scores[index]["rank"] < scores[best]["rank"]:
            best = index
    return best


def checkpoint(history, step, size, evaluation, on_step):
    # Lưu kết quả đã chấm để vẽ lại. Kéo thanh replay không chấm thêm lần nào.
    record = {"step": step, "calls": size * (step + 1), "evaluation": evaluation}
    history.append(record)
    if on_step is not None:
        on_step(record)


def finish(genes, history, start_time, details):
    last = history[-1]
    return {"genes": genes, "evaluation": last["evaluation"], "history": history,
            "calls": last["calls"], "seconds": perf_counter() - start_time,
            "details": details}
