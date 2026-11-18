"""Chấm một cách chia xe. GA và WOA đều dùng đúng người chấm này."""

import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
NETWORK_FILES = {"main": "network.json", "small": "network_8.json"}
EPSILON = 1e-7


def load_network(filename="network.json"):
    with (DATA / filename).open(encoding="utf-8") as file:
        return json.load(file)


def make_problem(network, case_id, demand=None, overrides=None):
    """Chụp lại dữ liệu của một lần chạy. Sửa trên form không đổi case gốc."""
    case = network["cases"][case_id]
    if demand is None:
        demand = case["demand"]
    if len(demand) != len(network["pairs"]):
        raise ValueError("Cần đúng một nhu cầu cho mỗi cặp nguồn và đích.")
    for amount in demand:
        if not math.isfinite(amount) or not 0 <= amount <= 100_000:
            raise ValueError("Nhu cầu phải từ 0 đến 100000 xe mỗi kỳ.")

    capacities = case["capacity"].copy()
    if overrides:
        capacities.update(overrides)
    roads = []
    road_positions = {}
    road_ids = set()
    for source_road in network["roads"]:
        road = source_road.copy()
        road_id = road["id"]
        pair = (road["from"], road["to"])
        if road_id in road_ids or pair in road_positions:
            raise ValueError("Các đoạn đường cần ID và cặp đầu cuối riêng.")
        if pair[0] not in network["nodes"] or pair[1] not in network["nodes"]:
            raise ValueError("Đoạn đường nối tới một nút chưa khai báo.")
        road["capacity"] = capacities.get(road_id, road["capacity"])
        if not math.isfinite(road["capacity"]) or not 0 <= road["capacity"] <= 100_000:
            raise ValueError("Sức chứa phải từ 0 đến 100000 xe mỗi kỳ.")
        if 0 < road["capacity"] < 1:
            raise ValueError("Đặt sức chứa bằng 0 để đóng đoạn, hoặc ít nhất 1 xe mỗi kỳ.")
        if not math.isfinite(road["minutes"]) or road["minutes"] <= 0:
            raise ValueError("Thời gian đường vắng phải lớn hơn 0.")
        road_ids.add(road_id)
        road_positions[pair] = len(roads)
        roads.append(road)
    if set(capacities) - road_ids:
        raise ValueError("Có mã đường không nằm trong bản đồ.")

    # Đổi mỗi tuyến thành danh sách chỉ số cạnh để chấm nhiều lần cho nhanh.
    # Ví dụ [O1, A, C, T1] dùng các cạnh E01, E05, E10.
    pairs = []
    dimension = 0
    for pair_index, source_pair in enumerate(network["pairs"]):
        routes = []
        start = source_pair["from"]
        end = source_pair["to"]
        for path in source_pair["routes"]:
            if len(path) < 2 or path[0] != start or path[-1] != end or len(set(path)) != len(path):
                raise ValueError("Tuyến phải đi đúng nguồn, đúng đích và không lặp nút.")
            indices = []
            is_open = True
            for index in range(len(path) - 1):
                connection = (path[index], path[index + 1])
                if connection not in road_positions:
                    raise ValueError("Có tuyến dùng đoạn đường chưa khai báo.")
                position = road_positions[connection]
                indices.append(position)
                if roads[position]["capacity"] == 0:
                    is_open = False
            routes.append({"path": path, "roads": indices, "open": is_open, "gene": dimension})
            dimension += 1
        pairs.append({"from": start, "to": end, "demand": demand[pair_index], "routes": routes})
    if dimension == 0:
        raise ValueError("Cần ít nhất một tuyến ứng viên trong dữ liệu.")
    return {"id": case_id, "name": case["name"], "description": case["description"],
            "network": network, "roads": roads, "pairs": pairs, "dimension": dimension}


def road_time(free_time, capacity, flow):
    """Đường càng đông thì mỗi xe càng tốn phút. Cạnh đóng không tính giờ."""
    if capacity == 0:
        return None
    return free_time * (1 + 0.15 * (flow / capacity) ** 4)


def evaluate(problem, genes):
    """Đổi trọng số thành xe, cộng luồng cạnh và tính điểm."""
    roads = problem["roads"]
    edge_flows = [0.0] * len(roads)
    route_flows = []
    unassigned_by_pair = []
    for pair in problem["pairs"]:
        routes = pair["routes"]
        demand = pair["demand"]
        flows = [0.0] * len(routes)
        open_count = 0
        weight_sum = 0.0
        for route in routes:
            if route["open"]:
                open_count += 1
                weight_sum += genes[route["gene"]]

        # Tưởng tượng chia bánh theo số phiếu. Tuyến đóng bị gạch tên.
        # Nếu mọi tuyến mở đều được 0 phiếu thì chia đều cho chúng.
        unassigned = 0.0
        if open_count == 0:
            unassigned = demand
        else:
            for index, route in enumerate(routes):
                if not route["open"]:
                    continue
                if weight_sum == 0:
                    flow = demand / open_count
                else:
                    flow = demand * genes[route["gene"]] / weight_sum
                flows[index] = flow
                for road_index in route["roads"]:
                    edge_flows[road_index] += flow
        route_flows.append(flows)
        unassigned_by_pair.append(unassigned)

    total_minutes = 0.0
    edge_minutes = []
    overflows = []
    for index, road in enumerate(roads):
        flow = edge_flows[index]
        capacity = road["capacity"]
        minutes = road_time(road["minutes"], capacity, flow)
        edge_minutes.append(minutes)
        overflows.append(max(0.0, flow - capacity))
        if minutes is not None:
            total_minutes += flow * minutes
    unassigned = sum(unassigned_by_pair)
    overflow = sum(overflows)
    violation = unassigned + overflow
    valid = violation <= EPSILON
    rank = (violation, total_minutes)
    if valid:
        rank = (0.0, total_minutes)
    return {"rank": rank, "valid": valid, "violation": violation,
            "total_minutes": total_minutes, "unassigned": unassigned,
            "unassigned_by_pair": unassigned_by_pair, "overflow": overflow,
            "overflows": overflows, "edge_flows": edge_flows,
            "edge_minutes": edge_minutes, "route_flows": route_flows}


def cut_proof(problem):
    """Nếu tìm được một 'cửa ra' quá chật thì đủ để chứng minh vô nghiệm."""
    network = problem["network"]
    # Một vài lát cắt đọc được bằng mắt, không chạy một thuật toán tối ưu thứ ba.
    partitions = list(network.get("cuts", []))
    for pair in problem["pairs"]:
        partitions.append([pair["from"]])
        partitions.append([node for node in network["nodes"] if node != pair["to"]])
    for left in partitions:
        required = sum(pair["demand"] for pair in problem["pairs"]
                       if pair["from"] in left and pair["to"] not in left)
        crossing = [road for road in problem["roads"] if road["from"] in left and road["to"] not in left]
        capacity = sum(road["capacity"] for road in crossing)
        if required > capacity + EPSILON:
            return {"demand": required, "capacity": capacity,
                    "roads": [road["id"] for road in crossing]}
    return None
