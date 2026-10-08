import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from solver import solve_circuit, SolverError

class TestCircuitSolver(unittest.TestCase):

    def test_case_a_series_voltage_divider(self):
        """Case a: 10V, R1=1k, R2=1k series: I=5mA, mid node=5V"""
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
                {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N2", "0"]}
            ]
        }
        result = solve_circuit(netlist)
        self.assertEqual(result["node_voltages"]["N1"], 10.0)
        self.assertEqual(result["node_voltages"]["N2"], 5.0)
        self.assertEqual(result["node_voltages"]["0"], 0.0)

        comp_map = {c["id"]: c for c in result["components"]}
        self.assertAlmostEqual(comp_map["R1"]["current"], 0.005, places=5)
        self.assertAlmostEqual(comp_map["R2"]["current"], 0.005, places=5)
        self.assertAlmostEqual(comp_map["V1"]["current"], 0.005, places=5)

    def test_case_b_unequal_series_resistors(self):
        """Case b: 12V, R1=2k, R2=1k series: V across R2 = 4V"""
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 12.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 2000.0, "nodes": ["N1", "N2"]},
                {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N2", "0"]}
            ]
        }
        result = solve_circuit(netlist)
        self.assertEqual(result["node_voltages"]["N1"], 12.0)
        self.assertEqual(result["node_voltages"]["N2"], 4.0)

        comp_map = {c["id"]: c for c in result["components"]}
        self.assertAlmostEqual(comp_map["R2"]["voltage_drop"], 4.0, places=5)
        self.assertAlmostEqual(comp_map["R1"]["voltage_drop"], 8.0, places=5)
        self.assertAlmostEqual(comp_map["R1"]["current"], 0.004, places=5)

    def test_case_c_parallel_resistors(self):
        """Case c: 10V across two 1k in parallel: 10mA each, 20mA total"""
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]},
                {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]}
            ]
        }
        result = solve_circuit(netlist)
        self.assertEqual(result["node_voltages"]["N1"], 10.0)

        comp_map = {c["id"]: c for c in result["components"]}
        self.assertAlmostEqual(comp_map["R1"]["current"], 0.010, places=5)
        self.assertAlmostEqual(comp_map["R2"]["current"], 0.010, places=5)
        self.assertAlmostEqual(comp_map["V1"]["current"], 0.020, places=5)

    def test_case_d_series_parallel_combination(self):
        """Case d: 12V, R1=4k series with (R2=6k || R3=3k): total I=2mA, V across parallel pair = 4V"""
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 12.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 4000.0, "nodes": ["N1", "N2"]},
                {"id": "R2", "type": "R", "value": 6000.0, "nodes": ["N2", "0"]},
                {"id": "R3", "type": "R", "value": 3000.0, "nodes": ["N2", "0"]}
            ]
        }
        result = solve_circuit(netlist)
        self.assertEqual(result["node_voltages"]["N1"], 12.0)
        self.assertEqual(result["node_voltages"]["N2"], 4.0)

        comp_map = {c["id"]: c for c in result["components"]}
        self.assertAlmostEqual(comp_map["R1"]["current"], 0.002, places=5)
        self.assertAlmostEqual(comp_map["V1"]["current"], 0.002, places=5)
        self.assertAlmostEqual(comp_map["R2"]["voltage_drop"], 4.0, places=5)
        self.assertAlmostEqual(comp_map["R3"]["voltage_drop"], 4.0, places=5)

    def test_case_e_current_source_into_resistor(self):
        """Case e: 2mA current source into 5k to ground: V=10V"""
        netlist = {
            "components": [
                {"id": "I1", "type": "I", "value": 0.002, "nodes": ["0", "N1"]},
                {"id": "R1", "type": "R", "value": 5000.0, "nodes": ["N1", "0"]}
            ]
        }
        result = solve_circuit(netlist)
        self.assertAlmostEqual(result["node_voltages"]["N1"], 10.0, places=5)

        comp_map = {c["id"]: c for c in result["components"]}
        self.assertAlmostEqual(comp_map["R1"]["current"], 0.002, places=5)
        self.assertAlmostEqual(comp_map["R1"]["voltage_drop"], 10.0, places=5)

    def test_invalid_missing_ground(self):
        netlist = {
            "components": [
                {"id": "R1", "type": "R", "value": 100.0, "nodes": ["N1", "N2"]}
            ]
        }
        with self.assertRaises(SolverError):
            solve_circuit(netlist)

    def test_voltage_source_reversed_polarity_flips_node_voltages(self):
        """Swapping the two nodes of a 10V voltage source flips the sign of every node voltage."""
        # Standard polarity: V1 nodes = ["N1", "0"] -> V(N1) = +10V, V(N2) = +5V
        netlist_standard = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
                {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N2", "0"]}
            ]
        }
        res_std = solve_circuit(netlist_standard)
        self.assertEqual(res_std["node_voltages"]["N1"], 10.0)
        self.assertEqual(res_std["node_voltages"]["N2"], 5.0)
        self.assertEqual(res_std["node_voltages"]["0"], 0.0)

        # Reversed polarity: V1 nodes = ["0", "N1"] -> V(N1) = -10V, V(N2) = -5V
        netlist_reversed = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["0", "N1"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
                {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N2", "0"]}
            ]
        }
        res_rev = solve_circuit(netlist_reversed)
        self.assertEqual(res_rev["node_voltages"]["0"], 0.0)

        # Every node voltage must have flipped sign
        for node, v_std in res_std["node_voltages"].items():
            self.assertIn(node, res_rev["node_voltages"])
            v_rev = res_rev["node_voltages"][node]
            self.assertAlmostEqual(v_rev, -v_std, places=5)

if __name__ == "__main__":
    unittest.main()
