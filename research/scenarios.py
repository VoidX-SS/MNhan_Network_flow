"""Các kịch bản đặt trước khi đo. Mỗi kịch bản dùng cùng bộ chấm của đồ án."""

from copy import deepcopy
import random

from model import load_network, make_problem


BRIDGES = ("E05", "E14", "E23", "E32", "E41")
LANES = range(1, 6)


def _record(network, case_id, family, hypothesis):
    problem = make_problem(network, case_id)
    return {"id": case_id, "family": family, "description": problem["description"],
            "hypothesis": hypothesis, "problem": problem}


def _variant(network, case_id, name, family, description, hypothesis, demand, capacity=None):
    # Tách bảng kịch bản. Có thể dùng lại bản đồ vì hàm chuẩn bị chỉ đọc nó.
    snapshot = network.copy()
    snapshot["cases"] = {case_id: {"name": name, "description": description,
                                  "demand": list(demand), "capacity": capacity or {}}}
    return _record(snapshot, case_id, family, hypothesis)


def _switch(start, end, column):
    """Các nút đi qua khi đổi hàng ở cùng một cột, kể cả hai đầu."""
    direction = 1 if start <= end else -1
    return [f"N{lane}{column}" for lane in range(start, end + direction, direction)]


def _route(source, entry, exit_, target):
    # Đổi hàng ở cột 2, sang bờ kia ở cột 4→5, rồi đổi hàng ở cột 7.
    return ([f"O{source}", f"N{source}1"] + _switch(source, entry, 2)
            + [f"N{entry}3", f"N{entry}4", f"N{exit_}5", f"N{exit_}6"]
            + _switch(exit_, target, 7) + [f"N{target}8", f"T{target}"])


def _endpoints(network, origins, destinations):
    snapshot = network.copy()
    snapshot["pairs"] = []
    for source, target in zip(origins, destinations):
        snapshot["pairs"].append({"from": f"O{source}", "to": f"T{target}",
                                  "routes": [_route(source, lane, lane, target) for lane in LANES]})
    return snapshot


def _crossing(shared):
    """Hai luồng cắt nhau. Chi phí lúc vắng và nhu cầu giống nhau ở hai bản."""
    nodes = {"O1": [0.06, 0.49, "O1"], "T1": [0.94, 0.49, "T1"],
             "O2": [0.48, 0.06, "O2"], "T2": [0.48, 0.94, "T2"],
             "B1": [0.46, 0.76, "Vòng 1"], "B2": [0.72, 0.44, "Vòng 2"]}
    if shared:
        nodes.update({"Jin": [0.42, 0.42, "Nút giao vào"], "Jout": [0.58, 0.58, "Nút giao ra"]})
        middle = [("Jin", "Jout"), ("Jin", "Jout")]
    else:
        nodes.update({"L1": [0.35, 0.49, "L1"], "R1": [0.62, 0.49, "R1"],
                      "L2": [0.48, 0.34, "L2"], "R2": [0.48, 0.64, "R2"]})
        middle = [("L1", "R1"), ("L2", "R2")]

    roads = []

    def add_road(start, end, minutes, capacity):
        roads.append({"id": f"J{len(roads) + 1:02}", "from": start, "to": end,
                      "minutes": minutes, "capacity": capacity})

    pairs = []
    for index, (entry, exit_) in enumerate(middle, 1):
        source, target, bypass = f"O{index}", f"T{index}", f"B{index}"
        add_road(source, entry, 0.7, 100)
        if not shared or index == 1:
            add_road(entry, exit_, 0.4, 80 if shared else 100)
        add_road(exit_, target, 0.7, 100)
        add_road(source, bypass, 1.45, 90)
        add_road(bypass, target, 1.45, 90)
        pairs.append({"from": source, "to": target,
                      "routes": [[source, entry, exit_, target], [source, bypass, target]]})
    return {"name": "Nút giao dùng chung" if shared else "Giao khác mức",
            "nodes": nodes, "roads": roads, "pairs": pairs}


def screen_cases():
    """Trả về các ca cố định, theo thứ tự dùng trong vòng sàng lọc."""
    network = load_network()
    normal = network["cases"]["normal"]["demand"]
    cases = [
        _record(network, "normal", "mốc", "Mốc để đo số lượt hợp lệ và sai số chi phí."),
        _record(network, "peak", "nhu cầu", "Nhu cầu cao hơn làm thu hẹp các cách chia hợp lệ."),
        _record(network, "incident", "sự cố", "Giảm sức chứa nhưng giữ đủ tuyến để phân phối lại xe."),
        _record(network, "closed", "sự cố", "Đóng một hành lang ở ngày thường, bốn lối còn lại đủ sức chứa tổng."),
        _record(network, "cut", "vô nghiệm", "Lát cắt chỉ còn 520 chỗ cho 590 xe nên cả hai phải báo vô nghiệm theo mô hình."),
    ]
    cases.append(_variant(network, "light", "Nhu cầu thấp", "nhu cầu",
                          "Còn 40% nhu cầu ngày thường, sức chứa giữ nguyên.",
                          "Kiểm tra tốc độ tối ưu chi phí khi ràng buộc sức chứa ít gây khó.",
                          [value * 0.4 for value in normal]))
    cases.append(_variant(network, "skewed", "Nhu cầu lệch theo nguồn", "nhu cầu",
                          "Giữ tổng 460 xe, tập trung nhu cầu tại O1 và O3.",
                          "Cùng tổng nhu cầu nhưng các tuyến có thể tranh một số đoạn nhiều hơn.",
                          [140, 45, 145, 55, 75]))

    # Chỉ đổi sức chứa trên năm cạnh qua lát cắt. Tổng lần lượt 480, 464, 460.
    for percent, values in [(96, [93, 99, 109, 91, 88]),
                            (99, [88, 92, 107, 88, 89]),
                            (100, [88, 92, 108, 87, 85])]:
        cases.append(_variant(network, f"tight_cut_{percent}", f"Lát cắt tải gần {percent}%", "lát cắt hẹp",
                              f"460 xe chia qua năm đoạn có tổng sức chứa {sum(values)}.",
                              "Khi phần dư nhỏ, thuật toán phải phối hợp nhiều trọng số để chạm miền hợp lệ.",
                              normal, dict(zip(BRIDGES, values))))
    cases.append(_variant(network, "double_close_feasible", "Đóng hai hành lang", "sự cố",
                          "Đóng E14 và E23, 330 xe đi qua ba hành lang còn mở.",
                          "Nhiều đoạn cùng đóng làm thay đổi các tuyến khả dụng và tỷ lệ tìm được nghiệm.",
                          [65, 65, 70, 62, 68], {"E14": 0, "E23": 0}))
    cases.append(_variant(network, "isolate_od", "Cô lập O1", "vô nghiệm",
                          "Đóng E01 là lối ra duy nhất của O1. O1 vẫn phát 90 xe.",
                          "Tổng sức chứa giữa mạng có thể còn dư dù một nguồn hoàn toàn mất lối đi.",
                          normal, {"E01": 0}))

    sparse = deepcopy(network)
    for pair_index, pair in enumerate(sparse["pairs"], 1):
        pair["routes"] = [path for lane, path in enumerate(pair["routes"], 1) if abs(lane - pair_index) <= 1]
    cases.append(_variant(sparse, "sparse_routes", "Mỗi cặp chỉ đi hàng gần", "tập tuyến",
                          "Giữ tuyến đi thẳng và các tuyến đổi tối đa một hàng. Có 13 trọng số.",
                          "Giảm chiều tìm kiếm đồng thời bớt khả năng đổi tuyến; cần đọc cả chất lượng và số chiều.",
                          normal))

    detour = deepcopy(network)
    for road in detour["roads"]:
        start, end = road["from"], road["to"]
        if start.startswith("N") and end.startswith("N") and start[1] != end[1]:
            road["minutes"] *= 3
    cases.append(_variant(detour, "far_detour", "Đóng E23 và đổi hàng lâu hơn", "chi phí",
                          "Cùng ca đóng E23, thời gian đường vắng trên đường đổi hàng nhân ba.",
                          "So với closed để tách ảnh hưởng chi phí đường vòng khỏi tính khả thi.", normal, {"E23": 0}))

    irregular = deepcopy(network)
    positions = [node[:2] for node in irregular["nodes"].values()]
    random.Random(216).shuffle(positions)
    for node, position in zip(irregular["nodes"].values(), positions):
        node[:2] = position
    cases.append(_variant(irregular, "irregular_layout", "Đổi vị trí vẽ", "đối chứng",
                          "Xáo tọa độ nút, giữ nguyên cạnh, thời gian, sức chứa và các tuyến.",
                          "Đối chứng âm. Với cùng seed, lịch sử điểm số và nghiệm phải trùng normal.", normal))

    # Tăng cùng bốn sức chứa ở hai ca để tránh một đoạn chung biến thành lỗi tầm thường.
    terminal_capacity = {road: 520 for road in ("E19", "E20", "E26", "E27")}
    cases.append(_variant(_endpoints(network, LANES, [3] * 5), "many_to_one", "Nhiều nguồn, một đích", "nguồn đích",
                          "Năm nguồn đi về T3. Tổng 460 xe, vẫn có năm lựa chọn hành lang mỗi cặp.",
                          "Đo tác động dồn xe về một đầu ra khi đoạn cuối có đủ sức chứa.", normal, terminal_capacity))
    cases.append(_variant(_endpoints(network, [3] * 5, LANES), "one_to_many", "Một nguồn, nhiều đích", "nguồn đích",
                          "O3 cấp xe cho năm đích. Tổng 460 xe, vẫn có năm lựa chọn hành lang mỗi cặp.",
                          "Đo tác động chia luồng ở một đầu vào khi đoạn đầu có đủ sức chứa.", normal, terminal_capacity))
    cases.append(_variant(_endpoints(network, LANES, reversed(LANES)), "cross_od_swap", "Đảo đích giữa các hàng", "nguồn đích",
                          "Đảo thứ tự đích từ T5 đến T1 để nhiều tuyến phải đổi hàng.",
                          "Hai luồng tranh sức chứa khi cùng dùng đoạn đổi hàng có hướng.", normal))

    shortcuts = deepcopy(network)
    shortcuts["roads"] += [
        {"id": "X1", "from": "N24", "to": "N35", "minutes": 0.62, "capacity": 95},
        {"id": "X2", "from": "N34", "to": "N25", "minutes": 0.66, "capacity": 95},
    ]
    for lane, pair in enumerate(shortcuts["pairs"], 1):
        pair["routes"] += [_route(lane, 2, 3, lane), _route(lane, 3, 2, lane)]
    cases.append(_variant(shortcuts, "shortcuts", "Thêm hai lối tắt", "tập tuyến",
                          "Thêm hai cạnh chéo qua lát cắt và 10 tuyến ứng viên. Có 35 trọng số.",
                          "Mở thêm lựa chọn có thể giảm chi phí chuẩn, đồng thời tăng chiều tìm kiếm.", normal))

    cases.append(_variant(_crossing(False), "overpass", "Hai luồng giao khác mức", "giao cắt",
                          "Hai tuyến nhanh cắt nhau trên hình, sức chứa độc lập. Mỗi nhóm có 70 xe và một đường vòng.",
                          "Nét cắt nhau trên hình không tự tạo xung đột trong đồ thị.", [70, 70]))
    cases.append(_variant(_crossing(True), "at_grade", "Hai luồng qua nút giao chung", "giao cắt",
                          "Hai tuyến nhanh chia một đoạn có sức chứa 80 xe. Mỗi nhóm có 70 xe và một đường vòng.",
                          "Phải đổi tuyến do hai nhóm thực sự dùng chung tài nguyên. Đây là mô hình sức chứa gộp.", [70, 70]))
    return cases


def scale_case(nodes):
    """Chia cạnh thành nhiều đoạn liên tiếp để đo chi phí xử lý khi đồ thị dài ra.

    Xe không có chỗ rẽ giữa một cạnh đã chia. Mỗi đoạn dùng sức chứa cũ và
    một phần thời gian cũ. Vì vậy chi phí, miền hợp lệ và 25 trọng số giữ nguyên
    về mặt toán học, sai khác nhỏ có thể đến từ làm tròn số thực.
    """
    network = load_network()
    old_nodes = len(network["nodes"])
    if not isinstance(nodes, int) or nodes < old_nodes:
        raise ValueError(f"Chọn số nút nguyên từ {old_nodes} trở lên.")
    roads = []
    chains = {}
    count, remainder = divmod(nodes - old_nodes, len(network["roads"]))
    cuts = [set(cut) for cut in network["cuts"]]

    for index, road in enumerate(network["roads"]):
        start, end = road["from"], road["to"]
        extra = count + (index < remainder)
        intermediates = []
        start_pos, end_pos = network["nodes"][start], network["nodes"][end]
        for part in range(1, extra + 1):
            label = f"{road['id']}_N{part}"
            ratio = part / (extra + 1)
            x = start_pos[0] + ratio * (end_pos[0] - start_pos[0])
            y = start_pos[1] + ratio * (end_pos[1] - start_pos[1])
            network["nodes"][label] = [x, y, label]
            intermediates.append(label)
            for cut in cuts:
                if start in cut:
                    cut.add(label)
        chains[(start, end)] = intermediates
        chain = [start] + intermediates + [end]
        for part, (first, second) in enumerate(zip(chain, chain[1:]), 1):
            roads.append({"id": f"{road['id']}_{part}", "from": first, "to": second,
                          "minutes": road["minutes"] / (extra + 1), "capacity": road["capacity"]})

    for pair in network["pairs"]:
        for index, path in enumerate(pair["routes"]):
            expanded = [path[0]]
            for start, end in zip(path, path[1:]):
                expanded.extend(chains[(start, end)])
                expanded.append(end)
            pair["routes"][index] = expanded
    network["roads"] = roads
    network["cuts"] = [sorted(cut) for cut in cuts]
    network["name"] = f"Mạng chia đoạn {nodes} nút"
    network.pop("focus_road")
    network.pop("study_roads")
    demand = network["cases"]["normal"]["demand"]
    case = _variant(network, f"scale_{nodes}", f"Quy mô {nodes} nút", "quy mô",
                    "Chia đoạn liên tiếp từ mạng gốc, giữ 25 trọng số và tổng thời gian từng chuỗi.",
                    "Chi phí xử lý tăng theo số cạnh và tổng lượt cạnh xuất hiện trong các tuyến.", demand)
    return case["problem"]
