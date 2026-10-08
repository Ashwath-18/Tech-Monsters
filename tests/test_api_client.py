import urllib.request
import json
import os

def test_api():
    # 1. Health
    with urllib.request.urlopen("http://127.0.0.1:8000/health") as resp:
        health_data = json.loads(resp.read().decode("utf-8"))
        print("Health Check:", health_data)
        assert health_data.get("status") == "ok"

    # 2. Solve endpoint
    solve_payload = {
        "netlist": {
            "components": [
                {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
                {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
                {"id": "R2", "type": "R", "value": 1000.0, "nodes": ["N2", "0"]}
            ]
        }
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/solve",
        data=json.dumps(solve_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        solve_data = json.loads(resp.read().decode("utf-8"))
        print("Solve Endpoint:", solve_data.get("is_valid"), solve_data.get("solved", {}).get("node_voltages"))
        assert solve_data.get("is_valid") is True

    # 3. Check student answer
    check_payload = {
        "netlist": solve_payload["netlist"],
        "solved": solve_data["solved"],
        "student_claim": "Node N2 voltage is 5.0V"
    }
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/check",
        data=json.dumps(check_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        check_data = json.loads(resp.read().decode("utf-8"))
        print("Check Student Claim:", check_data.get("explanation")[:60], "...")

    print("\nALL API ENDPOINTS TESTED AND PASSING!")

if __name__ == "__main__":
    test_api()
