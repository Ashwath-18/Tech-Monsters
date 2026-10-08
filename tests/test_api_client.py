import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestApiClient(unittest.TestCase):

    def test_health_endpoint(self):
        resp = client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "ok")

    def test_solve_endpoint(self):
        solve_payload = {
            "netlist": {
                "components": [
                    {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                    {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
                    {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N2", "0"]}
                ]
            }
        }
        resp = client.post("/api/solve", json=solve_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("is_valid"))
        self.assertEqual(data["solved"]["node_voltages"]["N2"], 5.0)

    @patch("main.explain_student_mistake")
    def test_check_student_claim_endpoint(self, mock_explain):
        mock_explain.return_value = "Correct! Node N2 potential is verified at 5.000 V via Modified Nodal Analysis."
        check_payload = {
            "netlist": {
                "components": [
                    {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                    {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
                    {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N2", "0"]}
                ]
            },
            "solved": {
                "node_voltages": {"0": 0.0, "N1": 10.0, "N2": 5.0},
                "components": [
                    {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"], "voltage_drop": 10.0, "current": 0.005, "power": 0.05},
                    {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"], "voltage_drop": 5.0, "current": 0.005, "power": 0.025},
                    {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N2", "0"], "voltage_drop": 5.0, "current": 0.005, "power": 0.025}
                ]
            },
            "student_claim": "Node N2 voltage is 5.0V"
        }
        resp = client.post("/api/check", json=check_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("explanation", data)
        self.assertTrue(len(data["explanation"]) > 0)
        self.assertIn("Node N2", data["explanation"])

if __name__ == "__main__":
    unittest.main()

