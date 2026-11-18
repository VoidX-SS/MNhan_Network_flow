import importlib.util
import unittest

from Extras.tight_cut_witness import witness_genes
from model import cut_proof, evaluate, load_network, make_problem
from research.oracle import reference
from research.scenarios import scale_case, screen_cases
from solver import solve


class ResearchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {case["id"]: case["problem"] for case in screen_cases()}

    def test_exact_evaluation_probe_does_not_change_search(self):
        problem = self.cases["normal"]
        for method in ("GA", "WOA"):
            measured = []
            a = solve(problem, method, size=8, steps=4, seed=3, on_evaluate=measured.append)
            b = solve(problem, method, size=8, steps=4, seed=3)
            self.assertEqual(len(measured), 40)
            self.assertEqual(a["calls"], len(measured))
            self.assertEqual(a["history"], b["history"])
            self.assertEqual(a["evaluation"]["rank"], min(score["rank"] for score in measured))

    def test_coordinates_are_only_for_drawing(self):
        for method in ("GA", "WOA"):
            a = solve(self.cases["normal"], method, size=8, steps=4, seed=3)
            b = solve(self.cases["irregular_layout"], method, size=8, steps=4, seed=3)
            self.assertEqual(a["history"], b["history"])

    def test_tight_cut_has_constructive_witness(self):
        problem = self.cases["tight_cut_100"]
        self.assertIsNone(cut_proof(problem))
        self.assertTrue(evaluate(problem, witness_genes(problem))["valid"])
        self.assertEqual(cut_proof(self.cases["cut"])["capacity"], 520)

    def test_subdividing_roads_preserves_feasible_cost(self):
        small = scale_case(50)
        large = scale_case(5000)
        self.assertEqual(len(large["network"]["nodes"]), 5000)
        self.assertEqual(small["dimension"], large["dimension"])
        genes = [1.0] * small["dimension"]
        self.assertAlmostEqual(evaluate(small, genes)["total_minutes"],
                               evaluate(large, genes)["total_minutes"], places=7)

    @unittest.skipUnless(importlib.util.find_spec("scipy"), "Cần SciPy để kiểm chuẩn số.")
    def test_oracle_encloses_hand_calculated_optimum(self):
        problem = make_problem(load_network("mini.json"), "split")
        bounds = reference(problem)
        exact = 205.92592592592592
        self.assertEqual(bounds["status"], "certified")
        self.assertLessEqual(bounds["lower_bound"], exact)
        self.assertAlmostEqual(bounds["upper_bound"], exact, places=7)
        self.assertEqual(reference(self.cases["cut"])["status"], "infeasible")


if __name__ == "__main__":
    unittest.main()
