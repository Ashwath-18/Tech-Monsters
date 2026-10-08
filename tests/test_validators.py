import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from validators import validate_netlist

class TestCircuitValidators(unittest.TestCase):

    def test_valid_circuit(self):
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
                {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N2", "0"]}
            ]
        }
        problems = validate_netlist(netlist)
        self.assertEqual(problems, [])

    def test_missing_ground(self):
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "N2"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]}
            ]
        }
        problems = validate_netlist(netlist)
        self.assertTrue(any("missing a ground reference" in p for p in problems))

    def test_floating_node(self):
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]},
                {"id": "R2", "type": "R", "value": 500.0, "nodes": ["N1", "N3"]}
            ]
        }
        problems = validate_netlist(netlist)
        self.assertTrue(any("floating/dangling" in p and "N3" in p for p in problems))

    def test_short_circuited_component(self):
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N1"]},
                {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]}
            ]
        }
        problems = validate_netlist(netlist)
        self.assertTrue(any("short-circuited across the same node" in p for p in problems))

    def test_negative_or_zero_value(self):
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": -50.0, "nodes": ["N1", "0"]}
            ]
        }
        problems = validate_netlist(netlist)
        self.assertTrue(any("positive numeric value" in p for p in problems))

    def test_parallel_voltage_source_loop(self):
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "V2", "type": "V", "value": 12.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]}
            ]
        }
        problems = validate_netlist(netlist)
        self.assertTrue(any("Illegal voltage source loop" in p for p in problems))

    def test_isolated_subcircuit(self):
        netlist = {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "0"]},
                {"id": "V2", "type": "V", "value": 5.0, "nodes": ["A", "B"]},
                {"id": "R2", "type": "R", "value": 200.0, "nodes": ["A", "B"]}
            ]
        }
        problems = validate_netlist(netlist)
        self.assertTrue(any("Isolated sub-circuit detected" in p for p in problems))

if __name__ == "__main__":
    unittest.main()
