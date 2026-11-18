"""GA số thực. Chọn bố mẹ, trộn cách chia xe, rồi thử vài thay đổi nhỏ."""

from time import perf_counter

from algorithms.common import best_index, checkpoint, finish, score_population


def select_parent(population, scores, rng):
    # Bốc 3 tấm vé, giữ ứng viên có điểm tốt nhất trong 3 tấm.
    winner = rng.randrange(len(population))
    for _ in range(2):
        candidate = rng.randrange(len(population))
        if scores[candidate]["rank"] < scores[winner]["rank"]:
            winner = candidate
    return population[winner]


def make_child(first, second, rng, details):
    child = first.copy()
    if rng.random() < 0.9:
        details["crossover"] += 1
        # Mỗi ô là một núm vặn. Con lấy một giá trị nằm giữa hai bố mẹ.
        for index in range(len(child)):
            ratio = rng.random()
            child[index] = ratio * first[index] + (1 - ratio) * second[index]
    for index in range(len(child)):
        if rng.random() < 1 / len(child):
            details["mutation"] += 1
            moved = child[index] + rng.uniform(-0.25, 0.25)
            child[index] = max(0.0, min(1.0, moved))
    return child


def solve(population, evaluate, steps, rng, on_step=None):
    started = perf_counter()
    size = len(population)
    scores = score_population(population, evaluate)
    best = best_index(scores)
    leader = population[best]
    leader_score = scores[best]
    history = []
    details = {"crossover": 0, "mutation": 0, "elite_kept": 0}
    checkpoint(history, 0, size, leader_score, on_step)

    for step in range(1, steps + 1):
        children = []
        for _ in range(size):
            first = select_parent(population, scores, rng)
            second = select_parent(population, scores, rng)
            children.append(make_child(first, second, rng, details))
        child_scores = score_population(children, evaluate)
        best = best_index(child_scores)
        if child_scores[best]["rank"] < leader_score["rank"]:
            leader = children[best]
            leader_score = child_scores[best]
        else:
            # Cất lại phương án cũ nếu thế hệ con chưa có phương án tốt hơn.
            worst = 0
            for index in range(1, size):
                if child_scores[index]["rank"] > child_scores[worst]["rank"]:
                    worst = index
            if leader_score["rank"] < child_scores[worst]["rank"]:
                children[worst] = leader
                child_scores[worst] = leader_score
                details["elite_kept"] += 1
        population = children
        scores = child_scores
        checkpoint(history, step, size, leader_score, on_step)
    return finish(leader, history, started, details)
