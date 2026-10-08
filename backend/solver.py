import numpy as np
from typing import Dict, Any, List

class SolverError(Exception):
    """Raised when Modified Nodal Analysis cannot solve the circuit."""
    pass

def solve_circuit(netlist: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves a linear DC circuit using Modified Nodal Analysis (MNA).
    
    Netlist format:
    {
      "components": [
        {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
        {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
        {"id": "I1", "type": "I", "value": 0.002, "nodes": ["0", "N1"]}
      ]
    }
    
    Conventions:
    - Base SI units (Ohms, Volts, Amps).
    - Ground node is named "0" with V("0") = 0.0 V.
    - For V: nodes are [positive, negative].
    - For I: current flows through the source from nodes[0] to nodes[1].
    """
    components = netlist.get("components", [])
    if not components:
        raise SolverError("Netlist contains no components.")

    # Collect all unique nodes
    all_nodes = set()
    v_sources = []
    r_components = []
    i_sources = []

    for comp in components:
        comp_id = comp.get("id", "")
        comp_type = comp.get("type", "").upper()
        nodes = comp.get("nodes", [])
        value = float(comp.get("value", 0.0))

        if len(nodes) != 2:
            raise SolverError(f"Component {comp_id} must connect exactly 2 nodes, got: {nodes}")

        all_nodes.add(str(nodes[0]))
        all_nodes.add(str(nodes[1]))

        if comp_type == "R":
            if value <= 0:
                raise SolverError(f"Resistor {comp_id} must have a positive non-zero resistance, got {value}")
            r_components.append(comp)
        elif comp_type == "V":
            v_sources.append(comp)
        elif comp_type == "I":
            i_sources.append(comp)
        else:
            raise SolverError(f"Unsupported component type: {comp_type}")

    if "0" not in all_nodes:
        raise SolverError("Ground reference node '0' is missing from the circuit.")

    # Non-ground nodes
    non_ground_nodes = sorted([n for n in all_nodes if n != "0"])
    n_nodes = len(non_ground_nodes)
    node_to_idx = {n: i for i, n in enumerate(non_ground_nodes)}

    m_vsrc = len(v_sources)
    total_dim = n_nodes + m_vsrc

    if total_dim == 0:
        return {"node_voltages": {"0": 0.0}, "components": [], "total_power": 0.0}

    # Initialize MNA matrices: A * x = z
    A = np.zeros((total_dim, total_dim), dtype=float)
    z = np.zeros(total_dim, dtype=float)

    # 1. Fill conductance from resistors into G matrix (top-left n_nodes x n_nodes)
    for comp in r_components:
        n1, n2 = str(comp["nodes"][0]), str(comp["nodes"][1])
        r_val = float(comp["value"])
        g = 1.0 / r_val

        idx1 = node_to_idx.get(n1)
        idx2 = node_to_idx.get(n2)

        if idx1 is not None:
            A[idx1, idx1] += g
        if idx2 is not None:
            A[idx2, idx2] += g
        if idx1 is not None and idx2 is not None:
            A[idx1, idx2] -= g
            A[idx2, idx1] -= g

    # 2. Fill independent current sources into RHS z
    # Current flows from node0 to node1 (leaves node0, enters node1)
    for comp in i_sources:
        n1, n2 = str(comp["nodes"][0]), str(comp["nodes"][1])
        i_val = float(comp["value"])

        idx1 = node_to_idx.get(n1)
        idx2 = node_to_idx.get(n2)

        # KCL: sum of currents leaving node = 0 => G*v + I_leaving = 0 => G*v = -I_leaving = I_entering
        if idx1 is not None:
            z[idx1] -= i_val  # leaving n1
        if idx2 is not None:
            z[idx2] += i_val  # entering n2

    # 3. Fill independent voltage sources
    # For V_k: V(nodes[0]) - V(nodes[1]) = value
    for k, comp in enumerate(v_sources):
        n_pos, n_neg = str(comp["nodes"][0]), str(comp["nodes"][1])
        v_val = float(comp["value"])
        v_row = n_nodes + k

        idx_pos = node_to_idx.get(n_pos)
        idx_neg = node_to_idx.get(n_neg)

        # Voltage equation: V_pos - V_neg = v_val
        if idx_pos is not None:
            A[v_row, idx_pos] = 1.0
            A[idx_pos, v_row] = 1.0  # Current leaving positive terminal into circuit
        if idx_neg is not None:
            A[v_row, idx_neg] = -1.0
            A[idx_neg, v_row] = -1.0 # Current returning into negative terminal

        z[v_row] = v_val

    # Solve linear system
    try:
        x = np.linalg.solve(A, z)
    except np.linalg.LinAlgError as e:
        raise SolverError(f"Circuit cannot be solved (singular or ill-conditioned matrix): {str(e)}")

    # Extract node voltages
    node_voltages = {"0": 0.0}
    for n, idx in node_to_idx.items():
        node_voltages[n] = float(x[idx])

    # Compute component voltages, currents, and power
    solved_components = []
    total_resistor_power = 0.0

    for comp in components:
        comp_id = comp.get("id", "")
        comp_type = comp.get("type", "").upper()
        n1, n2 = str(comp["nodes"][0]), str(comp["nodes"][1])
        val = float(comp.get("value", 0.0))

        v1 = node_voltages[n1]
        v2 = node_voltages[n2]
        v_drop = v1 - v2  # potential difference from node 0 to node 1

        if comp_type == "R":
            current = v_drop / val  # Current flowing from n1 to n2
            power = abs(v_drop * current)
            total_resistor_power += power
        elif comp_type == "V":
            # Find the index of this voltage source
            v_idx = v_sources.index(comp)
            # x[n_nodes + v_idx] has sign such that -x is current leaving positive terminal into circuit
            i_del = -float(x[n_nodes + v_idx])
            current = i_del
            power = val * current  # positive = delivering power
        elif comp_type == "I":
            current = val  # Fixed source current from n1 to n2
            power = v_drop * current
        else:
            current = 0.0
            power = 0.0

        solved_components.append({
            "id": comp_id,
            "type": comp_type,
            "value": val,
            "nodes": [n1, n2],
            "voltage_drop": round(v_drop, 6),
            "current": round(current, 6),
            "power": round(power, 6)
        })

    # Format node voltages nicely
    formatted_node_voltages = {k: round(v, 6) for k, v in node_voltages.items()}

    return {
        "node_voltages": formatted_node_voltages,
        "components": solved_components,
        "total_resistor_power": round(total_resistor_power, 6)
    }
