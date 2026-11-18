"""WOA cơ bản theo ba nhánh của Mirjalili và Lewis (2016)."""

import math
from time import perf_counter

from algorithms.common import best_index, checkpoint, finish, score_population


def move_whale(position, leader, population, a, rng, details):
    # Một bộ số ngẫu nhiên dùng chung cho cả vector của một cá voi.
    r1 = rng.random()
    r2 = rng.random()
    A = 2 * a * r1 - a
    C = 2 * r2
    p = rng.random()
    new_position = []
    if p < 0.5:
        target = leader
        if abs(A) >= 1:
            target = rng.choice(population)
            details["explore"] += 1
        else:
            details["encircle"] += 1
        for index in range(len(position)):
            D = abs(C * target[index] - position[index])
            new_position.append(target[index] - A * D)
    else:
        # Xoắn quanh phương án tốt nhất. l là một số mới mỗi lần xoắn.
        details["spiral"] += 1
        l = rng.uniform(-1.0, 1.0)
        b = 1.0
        spiral = math.exp(b * l) * math.cos(2 * math.pi * l)
        for index in range(len(position)):
            D_prime = abs(leader[index] - position[index])
            new_position.append(leader[index] + D_prime * spiral)
    for index in range(len(new_position)):
        if new_position[index] < 0 or new_position[index] > 1:
            details["clipped"] += 1
            new_position[index] = max(0.0, min(1.0, new_position[index]))
    return new_position


def solve(population, evaluate, steps, rng, on_step=None):
    started = perf_counter()
    size = len(population)
    scores = score_population(population, evaluate)
    best = best_index(scores)
    leader = population[best]
    leader_score = scores[best]
    history = []
    details = {"encircle": 0, "explore": 0, "spiral": 0, "clipped": 0}
    checkpoint(history, 0, size, leader_score, on_step)

    for step in range(1, steps + 1):
        # Vòng đầu a = 2, vòng cuối a = 0 nếu có ít nhất hai vòng.
        a = 2 * (1 - (step - 1) / max(1, steps - 1))
        next_population = []
        # Tất cả cá voi nhìn cùng ảnh chụp của bầy trước khi cùng di chuyển.
        for position in population:
            next_population.append(move_whale(position, leader, population, a, rng, details))
        scores = score_population(next_population, evaluate)
        best = best_index(scores)
        if scores[best]["rank"] < leader_score["rank"]:
            leader = next_population[best]
            leader_score = scores[best]
        population = next_population
        checkpoint(history, step, size, leader_score, on_step)
    return finish(leader, history, started, details)
