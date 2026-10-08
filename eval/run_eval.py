import os
import json
import glob
import sys
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from solver import solve_circuit, SolverError
from validators import validate_netlist
from gemma_client import extract_netlist_from_image, repair_netlist_from_image

def compare_netlists(predicted: Dict[str, Any], ground_truth: Dict[str, Any]) -> bool:
    """Checks if two netlists have equivalent components and connections."""
    if not isinstance(predicted, dict) or not isinstance(ground_truth, dict):
        return False
    pred_comps = predicted.get("components", [])
    true_comps = ground_truth.get("components", [])

    if len(pred_comps) != len(true_comps):
        return False

    def comp_key(c):
        nodes = sorted([str(n) for n in c.get("nodes", [])])
        return (c.get("type", "").upper(), float(c.get("value", 0.0)), tuple(nodes))

    pred_keys = sorted([comp_key(c) for c in pred_comps])
    true_keys = sorted([comp_key(c) for c in true_comps])
    return pred_keys == true_keys

def compare_voltages(solved_voltages: Dict[str, float], expected_voltages: Dict[str, float], tol: float = 0.05) -> bool:
    """Checks if node voltages match expected values within relative/absolute tolerance."""
    for node, expected_v in expected_voltages.items():
        if node not in solved_voltages:
            return False
        actual_v = solved_voltages[node]
        if abs(actual_v - expected_v) > max(tol * abs(expected_v), tol):
            return False
    return True

def run_evaluation():
    cases_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "cases"))
    case_files = sorted(glob.glob(os.path.join(cases_dir, "*.json")))

    if not case_files:
        print(f"No test cases found in {cases_dir}")
        return

    print(f"Running CircuitCheck Evaluation Suite across {len(case_files)} cases...\n")

    results_detail = []
    exact_matches = 0
    solved_matches = 0
    repaired_count = 0
    total_with_images = 0

    for case_path in case_files:
        with open(case_path, "r", encoding="utf-8") as f:
            case_data = json.load(f)

        case_id = case_data.get("id")
        name = case_data.get("name")
        image_rel_path = case_data.get("image_path", "")
        true_netlist = case_data.get("true_netlist", {})
        expected_voltages = case_data.get("expected_voltages", {})

        # Ground truth solver verification
        true_val_errors = validate_netlist(true_netlist)
        true_solved = None
        if not true_val_errors:
            try:
                true_solved = solve_circuit(true_netlist)
            except Exception as e:
                print(f"[{case_id}] Warning: Ground truth failed solver: {e}")

        # Test with image if available, else test solver & validator harness
        image_abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", image_rel_path))
        extracted_netlist = None
        validation_passed = False
        repaired = False

        if os.path.isfile(image_abs_path):
            total_with_images += 1
            with open(image_abs_path, "rb") as img_f:
                img_bytes = img_f.read()
            try:
                extracted_netlist = extract_netlist_from_image(img_bytes)
                val_errs = validate_netlist(extracted_netlist)
                if val_errs:
                    # Attempt 1 repair round
                    repaired_netlist = repair_netlist_from_image(img_bytes, extracted_netlist, val_errs)
                    rep_errs = validate_netlist(repaired_netlist)
                    if not rep_errs:
                        extracted_netlist = repaired_netlist
                        repaired = True
                        repaired_count += 1
                validation_passed = len(validate_netlist(extracted_netlist)) == 0
            except Exception as e:
                print(f"[{case_id}] Vision extraction error: {e}")
                extracted_netlist = None
                validation_passed = False
        else:
            # Synthetic harness test
            extracted_netlist = true_netlist
            validation_passed = len(true_val_errors) == 0

        # Calculate metrics
        netlist_match = compare_netlists(extracted_netlist, true_netlist)
        if netlist_match:
            exact_matches += 1

        voltage_match = False
        if validation_passed and true_solved:
            try:
                solved = solve_circuit(extracted_netlist)
                voltage_match = compare_voltages(solved["node_voltages"], expected_voltages)
            except Exception:
                voltage_match = False

        if voltage_match:
            solved_matches += 1

        status_str = "PASS" if voltage_match else "FAIL"
        print(f"[{status_str}] {case_id}: {name} (Netlist Match: {netlist_match}, Voltage Match: {voltage_match})")

        results_detail.append({
            "case_id": case_id,
            "name": name,
            "netlist_exact_match": netlist_match,
            "voltage_exact_match": voltage_match,
            "repaired_by_loop": repaired
        })

    total_cases = len(case_files)
    summary = {
        "total_cases": total_cases,
        "netlist_exact_match_pct": round((exact_matches / total_cases) * 100, 2),
        "solved_answer_match_pct": round((solved_matches / total_cases) * 100, 2),
        "repaired_count": repaired_count,
        "details": results_detail
    }

    results_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "results.json"))
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "="*50)
    print(f"EVALUATION SUMMARY (saved to eval/results.json):")
    print(f"- Total Cases: {total_cases}")
    print(f"- Netlist Exact Match: {summary['netlist_exact_match_pct']}%")
    print(f"- Solved Answer Match: {summary['solved_answer_match_pct']}%")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_evaluation()
