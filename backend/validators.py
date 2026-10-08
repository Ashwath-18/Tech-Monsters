from typing import Dict, Any, List, Set
from collections import defaultdict

def validate_netlist(netlist: Dict[str, Any]) -> List[str]:
    """
    Performs deterministic electrical and topological validation on a circuit netlist.
    Returns a list of specific, human-readable problem descriptions.
    If the netlist is valid, returns an empty list [].
    """
    problems: List[str] = []

    if not isinstance(netlist, dict):
        return ["Netlist must be a JSON object containing a 'components' list."]

    components = netlist.get("components")
    if not isinstance(components, list) or len(components) == 0:
        return ["Netlist must contain a non-empty 'components' list."]

    component_ids: Set[str] = set()
    node_connections = defaultdict(list)
    v_sources = []
    all_nodes: Set[str] = set()

    for idx, comp in enumerate(components):
        if not isinstance(comp, dict):
            problems.append(f"Component item at index {idx} is not a valid JSON object.")
            continue

        comp_id = comp.get("id")
        comp_type = comp.get("type")
        value = comp.get("value")
        nodes = comp.get("nodes")

        # Check ID
        if not comp_id or not isinstance(comp_id, str):
            problems.append(f"Component at index {idx} has missing or non-string 'id'.")
            comp_id = f"UNKNOWN_{idx}"
        elif comp_id in component_ids:
            problems.append(f"Duplicate component ID '{comp_id}'. Each component must have a unique ID.")
        component_ids.add(comp_id)

        # Check Type
        if not comp_type or not isinstance(comp_type, str) or comp_type.upper() not in {"R", "V", "I"}:
            problems.append(f"Component '{comp_id}' has invalid type '{comp_type}'. Supported types: 'R', 'V', 'I'.")

        # Check Value
        if value is None or not isinstance(value, (int, float)) or value <= 0:
            problems.append(f"Component '{comp_id}' must have a positive numeric value (> 0), got: {value}")

        # Check Nodes
        if not isinstance(nodes, list) or len(nodes) != 2:
            problems.append(f"Component '{comp_id}' must have a 'nodes' list with exactly 2 nodes, got: {nodes}")
            continue

        n1, n2 = str(nodes[0]).strip(), str(nodes[1]).strip()
        if not n1 or not n2:
            problems.append(f"Component '{comp_id}' contains an empty node name: {nodes}")
            continue

        if n1 == n2:
            problems.append(f"Component '{comp_id}' is short-circuited across the same node '{n1}'.")

        all_nodes.add(n1)
        all_nodes.add(n2)
        node_connections[n1].append(comp_id)
        node_connections[n2].append(comp_id)

        if comp_type and comp_type.upper() == "V":
            v_sources.append({"id": comp_id, "nodes": {n1, n2}, "raw_nodes": [n1, n2], "val": value})

    # 1. Ground Node Check
    if "0" not in all_nodes:
        problems.append("Circuit is missing a ground reference node. Exactly one node must be named '0'.")

    # 2. Floating / Disconnected Nodes Check
    # Every node in a closed DC circuit must connect to at least 2 components
    for node, attached_comps in node_connections.items():
        if len(attached_comps) < 2:
            comp_name = attached_comps[0] if attached_comps else "unknown"
            problems.append(f"Node '{node}' is floating/dangling (connected only to '{comp_name}'). Recheck connection near {comp_name}.")

    # 3. Graph Connectivity Check (No isolated sub-graphs)
    if all_nodes and len(node_connections) > 1:
        # Build adjacency graph
        adj = defaultdict(set)
        for comp in components:
            nodes = comp.get("nodes", [])
            if isinstance(nodes, list) and len(nodes) == 2:
                n1, n2 = str(nodes[0]).strip(), str(nodes[1]).strip()
                adj[n1].add(n2)
                adj[n2].add(n1)

        visited = set()
        start_node = "0" if "0" in all_nodes else next(iter(all_nodes))
        queue = [start_node]
        visited.add(start_node)

        while queue:
            curr = queue.pop(0)
            for neighbor in adj[curr]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        unreachable = all_nodes - visited
        if unreachable:
            problems.append(f"Isolated sub-circuit detected. Nodes {sorted(list(unreachable))} are not connected to ground reference '0'.")

    # 4. Voltage Source Loop / Parallel Voltage Source Contradictions
    # Check if two voltage sources are directly connected across the same two nodes
    for i in range(len(v_sources)):
        for j in range(i + 1, len(v_sources)):
            v1 = v_sources[i]
            v2 = v_sources[j]
            if v1["nodes"] == v2["nodes"]:
                problems.append(
                    f"Illegal voltage source loop: '{v1['id']}' and '{v2['id']}' are placed directly in parallel across nodes {list(v1['nodes'])}."
                )

    return problems
