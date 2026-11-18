import random
import unittest

from algorithms import ga, woa
from algorithms.common import initial_population
from experiments import compare_paired, row_for
from model import cut_proof, evaluate, load_network, make_problem, road_time
from solver import solve


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.network = load_network("network_8.json")
        self.mini = make_problem(load_network("mini.json"), "split")

    def test_hand_calculation(self):
        half = evaluate(self.mini, [0.5, 0.5])
        unequal = evaluate(self.mini, [0.6, 0.4])
        self.assertEqual(half["edge_flows"], [50] * 4)
        self.assertAlmostEqual(half["total_minutes"], 205.9259259259)
        self.assertAlmostEqual(unequal["total_minutes"], 208.3437037037)
        self.assertTrue(half["valid"])
        self.assertLess(half["rank"], unequal["rank"])

    def test_overflow_on_two_edges(self):
        score = evaluate(self.mini, [0.8, 0.2])
        self.assertFalse(score["valid"])
        self.assertEqual(score["overflow"], 10)
        self.assertEqual(score["unassigned"], 0)

    def test_zero_weights_split_equally(self):
        self.assertEqual(evaluate(self.mini, [0, 0])["route_flows"], [[50, 50]])

    def test_closed_edge_removed_before_decoding(self):
        problem = make_problem(self.network, "closed")
        score = evaluate(problem, [0] * problem["dimension"])
        self.assertEqual(score["edge_flows"][4], 0)
        self.assertIsNone(road_time(3, 0, 0))
        for index, pair in enumerate(problem["pairs"]):
            self.assertAlmostEqual(sum(score["route_flows"][index]), pair["demand"])
            for j, route in enumerate(pair["routes"]):
                if not route["open"]:
                    self.assertEqual(score["route_flows"][index][j], 0)

    def test_no_open_route_keeps_unassigned_demand(self):
        problem = make_problem(load_network("mini.json"), "split", overrides={"SA": 0, "SB": 0})
        score = evaluate(problem, [1, 1])
        self.assertEqual(score["unassigned"], 100)
        self.assertFalse(score["valid"])
        self.assertEqual(cut_proof(problem)["capacity"], 0)
        self.assertIsNone(row_for(problem, solve(problem, "GA", 4, 2))["total_vehicle_minutes"])

    def test_zero_demand(self):
        problem = make_problem(self.network, "closed", [0, 0])
        score = evaluate(problem, [1] * problem["dimension"])
        self.assertEqual(score["total_minutes"], 0)
        self.assertTrue(score["valid"])

    def test_cut_certificate(self):
        proof = cut_proof(make_problem(self.network, "cut"))
        self.assertEqual(proof["demand"], 292)
        self.assertEqual(proof["capacity"], 282)
        self.assertIsNone(cut_proof(make_problem(self.network, "closed")))

    def test_reject_invalid_numbers(self):
        with self.assertRaises(ValueError):
            make_problem(self.network, "normal", [float("nan"), 0])
        with self.assertRaises(ValueError):
            make_problem(self.network, "normal", overrides={"E05": 0.01})
        with self.assertRaises(ValueError):
            make_problem(self.network, "normal", overrides={"khong_co": 20})


class MainNetworkTests(unittest.TestCase):
    def setUp(self):
        self.network = load_network()

    def test_50_nodes_and_roads_all_participate_in_routes(self):
        problem = make_problem(self.network, "normal")
        nodes = set()
        edges = set()
        for pair in problem["pairs"]:
            for route in pair["routes"]:
                nodes.update(route["path"])
                edges.update(route["roads"])
        self.assertEqual(len(nodes), 50)
        self.assertEqual(nodes, set(self.network["nodes"]))
        self.assertEqual(len(edges), 61)
        self.assertEqual(len(edges), len(problem["roads"]))
        self.assertEqual(problem["dimension"], 25)

    def test_main_peak_cut(self):
        problem = make_problem(self.network, "cut")
        proof = cut_proof(problem)
        self.assertEqual(proof["demand"], 590)
        self.assertEqual(proof["capacity"], 520)
        self.assertEqual(proof["roads"], self.network["study_roads"])

    def test_closure_seed_7_can_still_serve_normal_demand(self):
        problem = make_problem(self.network, "closed")
        for algorithm in ("GA", "WOA"):
            score = solve(problem, algorithm, seed=7)["evaluation"]
            self.assertTrue(score["valid"])
            self.assertEqual(score["edge_flows"][22], 0)


class SolverTests(unittest.TestCase):
    def setUp(self):
        self.problem = make_problem(load_network(), "normal")

    def test_equal_start_and_seed_reproducibility(self):
        ga_run = solve(self.problem, "GA", 12, 10, 4)
        woa_run = solve(self.problem, "WOA", 12, 10, 4)
        self.assertEqual(ga_run["history"][0], woa_run["history"][0])
        again = solve(self.problem, "WOA", 12, 10, 4)
        self.assertEqual(woa_run["genes"], again["genes"])
        self.assertEqual(woa_run["history"], again["history"])

    def test_real_budget_and_history(self):
        for engine in [ga, woa]:
            called = []
            population = initial_population(self.problem["dimension"], 8, 2)
            saved = [genes.copy() for genes in population]

            def evaluate_and_count(genes):
                called.append(genes)
                self.assertTrue(all(0 <= gene <= 1 for gene in genes))
                return evaluate(self.problem, genes)

            run = engine.solve(population, evaluate_and_count, 5, random.Random(3))
            self.assertEqual(len(called), 48)
            self.assertEqual(run["calls"], 48)
            self.assertEqual(population, saved)
            keys = [record["evaluation"]["rank"] for record in run["history"]]
            self.assertEqual(keys, sorted(keys, reverse=True))

    def test_small_instance_reaches_known_answer(self):
        mini = make_problem(load_network("mini.json"), "split")
        for algorithm in ["GA", "WOA"]:
            result = solve(mini, algorithm, seed=7)["evaluation"]
            self.assertTrue(result["valid"])
            self.assertAlmostEqual(result["total_minutes"], 205.9259259259, delta=0.001)

    def test_paired_comparison_drops_invalid_runs(self):
        def row(valid, value):
            return {"case": "normal", "valid": valid, "total_vehicle_minutes": value}
        counts = compare_paired([row(1, 50), row(0, None), row(1, 70)],
                                [row(1, 60), row(1, 80), row(1, 70.001)])
        self.assertEqual(counts["paired_valid"], 2)
        self.assertEqual(counts["GA_lower"], 1)
        self.assertEqual(counts["ties"], 1)


if __name__ == "__main__":
    unittest.main()
