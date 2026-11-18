"""Mốc số cho bài chia luồng trên tập tuyến cho trước.

GA, WOA và giao diện chạy độc lập với phần này. NumPy và SciPy chỉ cần
khi dựng mốc nghiên cứu. Các cận đều tính bằng xe·phút, với sai số số thực.
"""

from model import EPSILON, cut_proof, evaluate


CERTIFIED_GAP_PERCENT = 0.01
LP_OPTIONS = {"primal_feasibility_tolerance": 1e-10, "dual_feasibility_tolerance": 1e-10}


def _answer(status, reason, lower=None, upper=None, genes=None, violation_lower=None):
    gap = None
    if lower is not None and upper is not None:
        if lower > 0:
            gap = 100 * (upper - lower) / lower
        elif upper == 0:
            gap = 0.0
    return {"status": status, "reason": reason, "lower_bound": lower,
            "upper_bound": upper, "gap_percent": gap, "genes": genes,
            "minimum_violation_lower": violation_lower}


def _linear_bound(cost, matrix, limits, multipliers, groups, np):
    """Cận dưới của chi phí tuyến tính, kể cả khi đối ngẫu còn sai số nhỏ.

    Mỗi nhóm biến cộng bằng 1. Với λ ≤ 0, từ A z ≤ b suy ra λ A z ≥ λ b.
    Phần chi phí còn lại của mỗi nhóm thấp nhất ở tuyến có hệ số nhỏ nhất.
    """
    adjusted = cost - matrix.T @ multipliers
    capacity_term = limits @ multipliers
    route_terms = [float(np.min(adjusted[group])) for group in groups]
    # Chừa một khoảng an toàn nhỏ khi cộng và trừ bằng số thực.
    scale = 1 + abs(capacity_term) + sum(abs(value) for value in route_terms)
    return float(capacity_term + sum(route_terms) - 1e-10 * scale)


def _overflow_bound(matrix, capacities, demand_matrix, groups, np, linprog, sparse):
    """Nới sức chứa bằng biến s, rồi lấy cận dưới của tổng số xe vượt sức chứa."""
    roads, dimensions = matrix.shape
    pair_count = len(groups)
    relaxed = linprog(
        np.concatenate((np.zeros(dimensions), np.ones(roads))),
        A_ub=sparse.hstack((sparse.csr_matrix(matrix), -sparse.eye(roads)), format="csr"),
        b_ub=capacities,
        A_eq=sparse.hstack((sparse.csr_matrix(demand_matrix), sparse.csr_matrix((pair_count, roads))), format="csr"),
        b_eq=np.ones(pair_count),
        method="highs",
        options=LP_OPTIONS,
    )
    if not relaxed.success:
        return None
    # λ ≥ −1 để hệ số của mỗi biến nới s vẫn không âm.
    multipliers = np.clip(relaxed.ineqlin.marginals, -1, 0)
    return max(0.0, _linear_bound(np.zeros(dimensions), matrix, capacities, multipliers, groups, np))


def reference(problem):
    """Ước lượng F* bằng [lower_bound, upper_bound] trên cùng tập tuyến.

    `certified` nghĩa là khoảng tương đối rộng tối đa 0,01% theo phép tính
    số. `infeasible` nghĩa là có căn cứ từ lát cắt, cặp mất hết tuyến hoặc
    cận dưới dương của lượng vượt sức chứa. `unknown` giữ riêng ca chưa rõ.
    """
    cut = cut_proof(problem)
    if cut:
        shortage = cut["demand"] - cut["capacity"]
        return _answer("infeasible", "Lát cắt có nhu cầu vượt sức chứa.", violation_lower=float(shortage))

    positive_pairs = [pair for pair in problem["pairs"] if pair["demand"] > 0]
    if not positive_pairs:
        return _answer("certified", "Nhu cầu bằng 0.", 0.0, 0.0, [0.0] * problem["dimension"])

    grouped_routes = []
    unassigned = 0.0
    for pair in positive_pairs:
        routes = [route for route in pair["routes"] if route["open"]]
        if not routes:
            unassigned += pair["demand"]
        grouped_routes.append(routes)
    if unassigned > EPSILON:
        return _answer("infeasible", "Có nhu cầu nhưng cặp nguồn và đích đã mất hết tuyến đã khai báo.",
                       violation_lower=unassigned)
    if unassigned > 0:
        return _answer("unknown", "Nhu cầu chưa gán dương nhưng nằm trong dung sai của bộ chấm.")

    try:
        import numpy as np
        from scipy import sparse
        from scipy.optimize import LinearConstraint, linprog, minimize
    except ImportError:
        return _answer("unknown", "Cần NumPy và SciPy để dựng mốc số.")

    active_roads = [i for i, road in enumerate(problem["roads"]) if road["capacity"] > 0]
    dimensions = sum(len(routes) for routes in grouped_routes)
    if dimensions > 600 or len(active_roads) * dimensions > 1_000_000:
        return _answer("unknown", "Ca này vượt ngân sách ma trận dành cho mốc số.")

    # Mỗi z là tỷ lệ xe của một cặp đi tuyến tương ứng. A z là luồng trên cạnh.
    road_rows = {road_index: row for row, road_index in enumerate(active_roads)}
    matrix = np.zeros((len(active_roads), dimensions))
    demand_matrix = np.zeros((len(grouped_routes), dimensions))
    groups = []
    gene_indices = []
    column = 0
    for row, routes in enumerate(grouped_routes):
        first_column = column
        for route in routes:
            gene_indices.append(route["gene"])
            demand_matrix[row, column] = 1
            for road_index in route["roads"]:
                matrix[road_rows[road_index], column] = positive_pairs[row]["demand"]
            column += 1
        groups.append(slice(first_column, column))

    capacities = np.array([problem["roads"][i]["capacity"] for i in active_roads], dtype=float)
    free_time = np.array([problem["roads"][i]["minutes"] for i in active_roads], dtype=float)
    # Chia mỗi dòng cho sức chứa để LP xử lý những mức lưu lượng khác nhau.
    normalized = matrix / capacities[:, None]
    demand_rhs = np.ones(len(groups))
    cap_rhs = np.ones(len(capacities))

    def lp(cost):
        return linprog(cost, A_ub=normalized, b_ub=cap_rhs, A_eq=demand_matrix,
                       b_eq=demand_rhs, bounds=(0, 1), method="highs", options=LP_OPTIONS)

    free_cost = matrix.T @ free_time
    if not np.all(np.isfinite(free_cost)):
        return _answer("unknown", "Giá trị chi phí vượt khả năng biểu diễn số thực.")
    first = lp(free_cost / max(1.0, float(np.max(free_cost))))
    if not first.success:
        if first.status == 2:
            overflow_lower = _overflow_bound(matrix, capacities, demand_matrix, groups, np, linprog, sparse)
            if overflow_lower is not None and overflow_lower > EPSILON:
                return _answer("infeasible", "Cận dưới của tổng vượt sức chứa lớn hơn 0.",
                               violation_lower=overflow_lower)
        return _answer("unknown", f"LP chưa cho căn cứ đủ mạnh về tính khả thi. Mã trạng thái {first.status}.")

    def checked_candidate(values):
        shares = np.clip(values, 0, 1)
        if not np.all(np.isfinite(shares)):
            return None
        for group in groups:
            total = float(np.sum(shares[group]))
            if total <= 0:
                return None
            shares[group] /= total
        genes = [0.0] * problem["dimension"]
        for index, gene in enumerate(gene_indices):
            genes[gene] = float(shares[index])
        grade = evaluate(problem, genes)
        if not grade["valid"] or not np.isfinite(grade["total_minutes"]):
            return None
        return shares, genes, float(grade["total_minutes"])

    best = checked_candidate(first.x)
    if best is None:
        return _answer("unknown", "Nghiệm LP chưa vượt qua bộ chấm của chương trình.")
    scale = max(1.0, best[2])

    def objective(shares):
        flow = matrix @ shares
        return float(free_time @ (flow * (1 + 0.15 * (flow / capacities) ** 4))) / scale

    def gradient(shares):
        ratio = (matrix @ shares) / capacities
        # Đạo hàm của x * t0 * (1 + 0.15*(x/c)^4).
        return (matrix.T @ (free_time * (1 + 0.75 * ratio ** 4))) / scale

    refined = minimize(
        objective,
        best[0],
        jac=gradient,
        method="SLSQP",
        bounds=[(0, 1)] * dimensions,
        constraints=[LinearConstraint(demand_matrix, demand_rhs, demand_rhs),
                     LinearConstraint(normalized, -np.inf, cap_rhs)],
        options={"ftol": 1e-12, "maxiter": 400},
    )
    candidate = checked_candidate(refined.x)
    if candidate is not None and candidate[2] <= best[2]:
        best = candidate

    shares, genes, upper = best
    tangent = gradient(shares)
    linear = lp(tangent)
    multipliers = np.zeros(len(capacities))
    if linear.success:
        multipliers = np.minimum(0, linear.ineqlin.marginals)
    tangent_minimum = _linear_bound(tangent, normalized, cap_rhs, multipliers, groups, np)
    lower = max(0.0, float(scale * (objective(shares) - tangent @ shares + tangent_minimum)))
    if not np.isfinite(lower) or lower > upper:
        return _answer("feasible_uncertified", "Cận dưới cần kiểm lại do sai số số thực.", upper=upper, genes=genes)

    result = _answer("feasible_uncertified", "Có nghiệm khả thi, khoảng cận còn rộng.", lower, upper, genes)
    if result["gap_percent"] is not None and result["gap_percent"] <= CERTIFIED_GAP_PERCENT:
        result["status"] = "certified"
        result["reason"] = "Khoảng cận số đủ hẹp để dùng làm mốc gần tối ưu."
    return result
