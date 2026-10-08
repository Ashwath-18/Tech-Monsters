// CircuitCheck Frontend Application Logic
let API_BASE = window.location.protocol.startsWith("http") ? window.location.origin : "http://127.0.0.1:8000";

// Comprehensive verified samples with exact netlist, solved MNA data, and schematics
const SAMPLES = {
  case_a: {
    title: "10V Series (1k-1k)",
    desc: "Voltage divider with two 1kΩ resistors",
    image: "../samples/case_01.jpg",
    netlist: {
      components: [
        { id: "V1", type: "V", value: 10.0, nodes: ["N1", "0"] },
        { id: "R1", type: "R", value: 1000.0, nodes: ["N1", "N2"] },
        { id: "R2", type: "R", value: 1000.0, nodes: ["N2", "0"] }
      ],
      uncertain: []
    },
    solved: {
      node_voltages: { "0": 0.0, "N1": 10.0, "N2": 5.0 },
      components: [
        { id: "V1", type: "V", value: 10.0, nodes: ["N1", "0"], voltage_drop: 10.0, current: 0.005, power: 0.05 },
        { id: "R1", type: "R", value: 1000.0, nodes: ["N1", "N2"], voltage_drop: 5.0, current: 0.005, power: 0.025 },
        { id: "R2", type: "R", value: 1000.0, nodes: ["N2", "0"], voltage_drop: 5.0, current: 0.005, power: 0.025 }
      ],
      total_resistor_power: 0.05
    },
    svg: `<svg viewBox="0 0 440 240" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="blur"/><feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <!-- Battery V1 -->
      <circle cx="70" cy="120" r="22" stroke="#3b82f6" stroke-width="2.5" fill="#0d1424" filter="url(#glow-cyan)"/>
      <text x="70" y="115" fill="#f8fafc" font-size="14" text-anchor="middle" font-weight="bold">+</text>
      <text x="70" y="133" fill="#f8fafc" font-size="14" text-anchor="middle" font-weight="bold">-</text>
      <text x="70" y="165" fill="#38bdf8" font-size="12" font-family="'JetBrains Mono', monospace" text-anchor="middle" font-weight="bold">V1: 10V</text>
      <!-- Wires -->
      <path d="M 70 98 L 70 50 L 160 50" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <!-- Node N1 -->
      <circle cx="160" cy="50" r="5" fill="#00f0ff"/>
      <text x="160" y="36" fill="#00f0ff" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">N1 (10V)</text>
      <!-- Resistor R1 -->
      <path d="M 160 50 L 175 35 L 195 65 L 215 35 L 235 65 L 255 35 L 270 50" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="220" y="24" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">R1: 1kΩ</text>
      <!-- Node N2 -->
      <path d="M 270 50 L 350 50 L 350 80" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="350" cy="80" r="5" fill="#00f0ff"/>
      <text x="365" y="75" fill="#00f0ff" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace">N2 (5V)</text>
      <!-- Resistor R2 -->
      <path d="M 350 80 L 335 95 L 365 115 L 335 135 L 365 155 L 335 175 L 350 190" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="385" y="140" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace">R2: 1kΩ</text>
      <!-- Bottom Rail & Ground -->
      <path d="M 350 190 L 350 200 L 70 200 L 70 142" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="210" cy="200" r="4" fill="#94a3b8"/>
      <path d="M 200 208 L 220 208 M 204 214 L 216 214 M 208 220 L 212 220" stroke="#94a3b8" stroke-width="2.5"/>
      <text x="210" y="235" fill="#94a3b8" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">GND Node 0 (0V)</text>
    </svg>`
  },
  case_b: {
    title: "12V Divider (2k-1k)",
    desc: "2:1 voltage divider (8V & 4V drops)",
    image: "../samples/case_02.jpg",
    netlist: {
      components: [
        { id: "V1", type: "V", value: 12.0, nodes: ["N1", "0"] },
        { id: "R1", type: "R", value: 2000.0, nodes: ["N1", "N2"] },
        { id: "R2", type: "R", value: 1000.0, nodes: ["N2", "0"] }
      ],
      uncertain: []
    },
    solved: {
      node_voltages: { "0": 0.0, "N1": 12.0, "N2": 4.0 },
      components: [
        { id: "V1", type: "V", value: 12.0, nodes: ["N1", "0"], voltage_drop: 12.0, current: 0.004, power: 0.048 },
        { id: "R1", type: "R", value: 2000.0, nodes: ["N1", "N2"], voltage_drop: 8.0, current: 0.004, power: 0.032 },
        { id: "R2", type: "R", value: 1000.0, nodes: ["N2", "0"], voltage_drop: 4.0, current: 0.004, power: 0.016 }
      ],
      total_resistor_power: 0.048
    },
    svg: `<svg viewBox="0 0 440 240" xmlns="http://www.w3.org/2000/svg">
      <circle cx="70" cy="120" r="22" stroke="#3b82f6" stroke-width="2.5" fill="#0d1424"/>
      <text x="70" y="115" fill="#f8fafc" font-size="14" text-anchor="middle" font-weight="bold">+</text>
      <text x="70" y="133" fill="#f8fafc" font-size="14" text-anchor="middle" font-weight="bold">-</text>
      <text x="70" y="165" fill="#38bdf8" font-size="12" font-family="'JetBrains Mono', monospace" text-anchor="middle" font-weight="bold">V1: 12V</text>
      <path d="M 70 98 L 70 50 L 160 50" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="160" cy="50" r="5" fill="#00f0ff"/>
      <text x="160" y="36" fill="#00f0ff" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">N1 (12V)</text>
      <path d="M 160 50 L 175 35 L 195 65 L 215 35 L 235 65 L 255 35 L 270 50" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="220" y="24" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">R1: 2kΩ</text>
      <path d="M 270 50 L 350 50 L 350 80" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="350" cy="80" r="5" fill="#00f0ff"/>
      <text x="365" y="75" fill="#00f0ff" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace">N2 (4V)</text>
      <path d="M 350 80 L 335 95 L 365 115 L 335 135 L 365 155 L 335 175 L 350 190" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="385" y="140" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace">R2: 1kΩ</text>
      <path d="M 350 190 L 350 200 L 70 200 L 70 142" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="210" cy="200" r="4" fill="#94a3b8"/>
      <path d="M 200 208 L 220 208 M 204 214 L 216 214 M 208 220 L 212 220" stroke="#94a3b8" stroke-width="2.5"/>
      <text x="210" y="235" fill="#94a3b8" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">GND Node 0 (0V)</text>
    </svg>`
  },
  case_c: {
    title: "10V Parallel (1k || 1k)",
    desc: "Dual branch current division (20mA total)",
    image: "../samples/case_03.jpg",
    netlist: {
      components: [
        { id: "V1", type: "V", value: 10.0, nodes: ["N1", "0"] },
        { id: "R1", type: "R", value: 1000.0, nodes: ["N1", "0"] },
        { id: "R2", type: "R", value: 1000.0, nodes: ["N1", "0"] }
      ],
      uncertain: []
    },
    solved: {
      node_voltages: { "0": 0.0, "N1": 10.0 },
      components: [
        { id: "V1", type: "V", value: 10.0, nodes: ["N1", "0"], voltage_drop: 10.0, current: 0.02, power: 0.2 },
        { id: "R1", type: "R", value: 1000.0, nodes: ["N1", "0"], voltage_drop: 10.0, current: 0.01, power: 0.1 },
        { id: "R2", type: "R", value: 1000.0, nodes: ["N1", "0"], voltage_drop: 10.0, current: 0.01, power: 0.1 }
      ],
      total_resistor_power: 0.2
    },
    svg: `<svg viewBox="0 0 440 240" xmlns="http://www.w3.org/2000/svg">
      <circle cx="70" cy="120" r="22" stroke="#3b82f6" stroke-width="2.5" fill="#0d1424"/>
      <text x="70" y="115" fill="#f8fafc" font-size="14" text-anchor="middle" font-weight="bold">+</text>
      <text x="70" y="133" fill="#f8fafc" font-size="14" text-anchor="middle" font-weight="bold">-</text>
      <text x="70" y="165" fill="#38bdf8" font-size="12" font-family="'JetBrains Mono', monospace" text-anchor="middle" font-weight="bold">V1: 10V</text>
      <path d="M 70 98 L 70 50 L 350 50" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="210" cy="50" r="5" fill="#00f0ff"/>
      <text x="210" y="34" fill="#00f0ff" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">Node N1 (10V)</text>
      <!-- Branch R1 -->
      <path d="M 210 50 L 210 80 L 195 95 L 225 115 L 195 135 L 225 155 L 195 175 L 210 190 L 210 200" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="245" y="140" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace">R1: 1kΩ</text>
      <!-- Branch R2 -->
      <path d="M 350 50 L 350 80 L 335 95 L 365 115 L 335 135 L 365 155 L 335 175 L 350 190 L 350 200" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="385" y="140" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace">R2: 1kΩ</text>
      <!-- Bottom Return -->
      <path d="M 350 200 L 70 200 L 70 142" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="140" cy="200" r="4" fill="#94a3b8"/>
      <path d="M 130 208 L 150 208 M 134 214 L 146 214 M 138 220 L 142 220" stroke="#94a3b8" stroke-width="2.5"/>
      <text x="140" y="235" fill="#94a3b8" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">GND Node 0 (0V)</text>
    </svg>`
  },
  case_d: {
    title: "12V Series-Parallel",
    desc: "4kΩ in series with (6kΩ || 3kΩ)",
    image: "../samples/case_04.jpg",
    netlist: {
      components: [
        { id: "V1", type: "V", value: 12.0, nodes: ["N1", "0"] },
        { id: "R1", type: "R", value: 4000.0, nodes: ["N1", "N2"] },
        { id: "R2", type: "R", value: 6000.0, nodes: ["N2", "0"] },
        { id: "R3", type: "R", value: 3000.0, nodes: ["N2", "0"] }
      ],
      uncertain: []
    },
    solved: {
      node_voltages: { "0": 0.0, "N1": 12.0, "N2": 4.0 },
      components: [
        { id: "V1", type: "V", value: 12.0, nodes: ["N1", "0"], voltage_drop: 12.0, current: 0.002, power: 0.024 },
        { id: "R1", type: "R", value: 4000.0, nodes: ["N1", "N2"], voltage_drop: 8.0, current: 0.002, power: 0.016 },
        { id: "R2", type: "R", value: 6000.0, nodes: ["N2", "0"], voltage_drop: 4.0, current: 0.000667, power: 0.002667 },
        { id: "R3", type: "R", value: 3000.0, nodes: ["N2", "0"], voltage_drop: 4.0, current: 0.001333, power: 0.005333 }
      ],
      total_resistor_power: 0.024
    },
    svg: `<svg viewBox="0 0 460 250" xmlns="http://www.w3.org/2000/svg">
      <circle cx="60" cy="125" r="22" stroke="#3b82f6" stroke-width="2.5" fill="#0d1424"/>
      <text x="60" y="120" fill="#f8fafc" font-size="14" text-anchor="middle" font-weight="bold">+</text>
      <text x="60" y="138" fill="#f8fafc" font-size="14" text-anchor="middle" font-weight="bold">-</text>
      <text x="60" y="170" fill="#38bdf8" font-size="12" font-family="'JetBrains Mono', monospace" text-anchor="middle" font-weight="bold">12V DC</text>
      <path d="M 60 103 L 60 50 L 130 50" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="130" cy="50" r="5" fill="#00f0ff"/>
      <text x="130" y="34" fill="#00f0ff" font-size="11" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">N1 (12V)</text>
      <!-- R1 -->
      <path d="M 130 50 L 145 35 L 165 65 L 185 35 L 205 65 L 225 35 L 240 50" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="185" y="24" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">R1: 4kΩ</text>
      <!-- Node N2 -->
      <circle cx="260" cy="50" r="5" fill="#00f0ff"/>
      <text x="260" y="34" fill="#00f0ff" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">Node N2 (4V)</text>
      <!-- Branch R2 (upper parallel) -->
      <path d="M 240 50 L 300 50 L 315 35 L 335 65 L 355 35 L 375 65 L 395 35 L 410 50 L 430 50 L 430 200" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="365" y="24" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">R2: 6kΩ</text>
      <!-- Branch R3 (lower parallel) -->
      <path d="M 260 50 L 260 120 L 300 120 L 315 105 L 335 135 L 355 105 L 375 135 L 395 105 L 410 120 L 430 120" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="365" y="98" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">R3: 3kΩ</text>
      <!-- Bottom Return -->
      <path d="M 430 200 L 60 200 L 60 147" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="210" cy="200" r="4" fill="#94a3b8"/>
      <path d="M 200 208 L 220 208 M 204 214 L 216 214 M 208 220 L 212 220" stroke="#94a3b8" stroke-width="2.5"/>
      <text x="210" y="235" fill="#94a3b8" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">GND Node 0 (0V)</text>
    </svg>`
  },
  case_e: {
    title: "Current Source 2mA into 5k",
    desc: "Ideal 2mA source driving 5kΩ resistor",
    image: "../samples/case_05.jpg",
    netlist: {
      components: [
        { id: "I1", type: "I", value: 0.002, nodes: ["0", "N1"] },
        { id: "R1", type: "R", value: 5000.0, nodes: ["N1", "0"] }
      ],
      uncertain: []
    },
    solved: {
      node_voltages: { "0": 0.0, "N1": 10.0 },
      components: [
        { id: "I1", type: "I", value: 0.002, nodes: ["0", "N1"], voltage_drop: -10.0, current: 0.002, power: -0.02 },
        { id: "R1", type: "R", value: 5000.0, nodes: ["N1", "0"], voltage_drop: 10.0, current: 0.002, power: 0.02 }
      ],
      total_resistor_power: 0.02
    },
    svg: `<svg viewBox="0 0 440 240" xmlns="http://www.w3.org/2000/svg">
      <!-- Current Source I1 -->
      <circle cx="90" cy="120" r="24" stroke="#f59e0b" stroke-width="2.5" fill="#0d1424"/>
      <path d="M 90 135 L 90 105 M 84 112 L 90 105 L 96 112" stroke="#fbbf24" stroke-width="2.5" fill="none"/>
      <text x="90" y="165" fill="#fbbf24" font-size="12" font-family="'JetBrains Mono', monospace" text-anchor="middle" font-weight="bold">I1: 2mA</text>
      <!-- Top Wire to Node N1 -->
      <path d="M 90 96 L 90 50 L 310 50" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="310" cy="50" r="5" fill="#00f0ff"/>
      <text x="310" y="34" fill="#00f0ff" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">Node N1 (10V)</text>
      <!-- Resistor R1 -->
      <path d="M 310 50 L 310 80 L 295 95 L 325 115 L 295 135 L 325 155 L 295 175 L 310 190 L 310 200" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="345" y="140" fill="#34d399" font-size="12" font-weight="bold" font-family="'JetBrains Mono', monospace">R1: 5kΩ</text>
      <!-- Bottom Return & GND -->
      <path d="M 310 200 L 90 200 L 90 144" stroke="#94a3b8" stroke-width="2.5" fill="none"/>
      <circle cx="200" cy="200" r="4" fill="#94a3b8"/>
      <path d="M 190 208 L 210 208 M 194 214 L 206 214 M 198 220 L 202 220" stroke="#94a3b8" stroke-width="2.5"/>
      <text x="200" y="235" fill="#94a3b8" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">GND Node 0 (0V)</text>
    </svg>`
  },
  case_f: {
    title: "Wheatstone Bridge (Balanced)",
    desc: "Balanced bridge network with zero bridge current",
    image: "../samples/case_06.jpg",
    netlist: {
      components: [
        {"id": "V1", "type": "V", "value": 10.0, "nodes": ["N1", "0"]},
        {"id": "R1", "type": "R", "value": 1000.0, "nodes": ["N1", "N2"]},
        {"id": "R2", "type": "R", "value": 2000.0, "nodes": ["N2", "0"]},
        {"id": "R3", "type": "R", "value": 2000.0, "nodes": ["N1", "N3"]},
        {"id": "R4", "type": "R", "value": 4000.0, "nodes": ["N3", "0"]},
        {"id": "Rg", "type": "R", "value": 500.0, "nodes": ["N2", "N3"]}
      ],
      uncertain: []
    },
    solved: {
      node_voltages: { "0": 0.0, "N1": 10.0, "N2": 6.667, "N3": 6.667 },
      components: [
        { id: "V1", type: "V", value: 10.0, nodes: ["N1", "0"], voltage_drop: 10.0, current: 0.005, power: 0.05 },
        { id: "R1", type: "R", value: 1000.0, nodes: ["N1", "N2"], voltage_drop: 3.333, current: 0.003333, power: 0.01111 },
        { id: "R2", type: "R", value: 2000.0, nodes: ["N2", "0"], voltage_drop: 6.667, current: 0.003333, power: 0.02222 },
        { id: "R3", type: "R", value: 2000.0, nodes: ["N1", "N3"], voltage_drop: 3.333, current: 0.001667, power: 0.00556 },
        { id: "R4", type: "R", value: 4000.0, nodes: ["N3", "0"], voltage_drop: 6.667, current: 0.001667, power: 0.01111 },
        { id: "Rg", type: "R", value: 500.0, nodes: ["N2", "N3"], voltage_drop: 0.0, current: 0.0, power: 0.0 }
      ],
      total_resistor_power: 0.05
    },
    svg: `<svg viewBox="0 0 460 250" xmlns="http://www.w3.org/2000/svg">
      <circle cx="50" cy="125" r="20" stroke="#3b82f6" stroke-width="2" fill="#0d1424"/>
      <text x="50" y="120" fill="#f8fafc" font-size="12" text-anchor="middle" font-weight="bold">+</text>
      <text x="50" y="136" fill="#f8fafc" font-size="12" text-anchor="middle" font-weight="bold">-</text>
      <text x="50" y="165" fill="#38bdf8" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">V1: 10V</text>
      <!-- Top Rail to Bridge Apex N1 -->
      <path d="M 50 105 L 50 35 L 240 35" stroke="#94a3b8" stroke-width="2" fill="none"/>
      <circle cx="240" cy="35" r="5" fill="#00f0ff"/>
      <text x="240" y="22" fill="#00f0ff" font-size="11" font-weight="bold" font-family="'JetBrains Mono', monospace" text-anchor="middle">N1 (10V)</text>
      <!-- Bridge Diamond Arms -->
      <path d="M 240 35 L 170 110" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="180" y="70" fill="#34d399" font-size="11" font-family="'JetBrains Mono', monospace">R1: 1k</text>
      <path d="M 240 35 L 310 110" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="280" y="70" fill="#34d399" font-size="11" font-family="'JetBrains Mono', monospace">R3: 2k</text>
      <!-- Middle Bridge Rg -->
      <path d="M 170 110 L 310 110" stroke="#10b981" stroke-width="2.5" stroke-dasharray="4" fill="none"/>
      <text x="240" y="102" fill="#fbbf24" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">Rg: 500Ω (I=0A)</text>
      <!-- Nodes N2 & N3 -->
      <circle cx="170" cy="110" r="5" fill="#00f0ff"/>
      <text x="135" y="115" fill="#00f0ff" font-size="11" font-family="'JetBrains Mono', monospace">N2: 6.67V</text>
      <circle cx="310" cy="110" r="5" fill="#00f0ff"/>
      <text x="325" y="115" fill="#00f0ff" font-size="11" font-family="'JetBrains Mono', monospace">N3: 6.67V</text>
      <!-- Bottom Bridge Arms -->
      <path d="M 170 110 L 240 185" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="180" y="160" fill="#34d399" font-size="11" font-family="'JetBrains Mono', monospace">R2: 2k</text>
      <path d="M 310 110 L 240 185" stroke="#10b981" stroke-width="2.5" fill="none"/>
      <text x="280" y="160" fill="#34d399" font-size="11" font-family="'JetBrains Mono', monospace">R4: 4k</text>
      <!-- Bottom Ground 0 -->
      <circle cx="240" cy="185" r="5" fill="#94a3b8"/>
      <path d="M 240 185 L 50 185 L 50 145" stroke="#94a3b8" stroke-width="2" fill="none"/>
      <path d="M 230 195 L 250 195 M 234 200 L 246 200 M 238 205 L 242 205" stroke="#94a3b8" stroke-width="2"/>
      <text x="240" y="222" fill="#94a3b8" font-size="10" font-family="'JetBrains Mono', monospace" text-anchor="middle">GND Node 0 (0V)</text>
    </svg>`
  }
};

// Global App State
let currentFile = null;
let currentAnalysisData = null;
let isBackendOnline = false;

// DOM Elements
const fileInput = document.getElementById("fileInput");
const dropzone = document.getElementById("dropzone");
const previewWrapper = document.getElementById("previewWrapper");
const previewImage = document.getElementById("previewImage");
const dropzonePrompt = document.getElementById("dropzonePrompt");
const previewInfoTag = document.getElementById("previewInfoTag");
const analyzeBtn = document.getElementById("analyzeBtn");
const analyzeSpinner = document.getElementById("analyzeSpinner");
const clearInputBtn = document.getElementById("clearInputBtn");
const zoomBtn = document.getElementById("zoomBtn");
const replaceBtn = document.getElementById("replaceBtn");

const emptyState = document.getElementById("emptyState");
const analysisTab = document.getElementById("analysisTab");
const schematicTab = document.getElementById("schematicTab");
const netlistTab = document.getElementById("netlistTab");
const repairTab = document.getElementById("repairTab");
const analysisSubtitle = document.getElementById("analysisSubtitle");

const nodeVoltagesGrid = document.getElementById("nodeVoltagesGrid");
const componentTableBody = document.getElementById("componentTableBody");
const statusBanner = document.getElementById("statusBanner");
const statusTitle = document.getElementById("statusTitle");
const statusDesc = document.getElementById("statusDesc");
const bannerMeta = document.getElementById("bannerMeta");
const uncertainBox = document.getElementById("uncertainBox");
const uncertainList = document.getElementById("uncertainList");
const netlistEditor = document.getElementById("netlistEditor");
const repairTimeline = document.getElementById("repairTimeline");
const repairCountBadge = document.getElementById("repairCountBadge");
const schematicContainer = document.getElementById("schematicContainer");

const kpiTotalPower = document.getElementById("kpiTotalPower");
const kpiNodeCount = document.getElementById("kpiNodeCount");
const kpiCompCount = document.getElementById("kpiCompCount");
const kpiCompBreakdown = document.getElementById("kpiCompBreakdown");
const kpiMaxVoltage = document.getElementById("kpiMaxVoltage");
const kpiMaxNodeName = document.getElementById("kpiMaxNodeName");

const tableFilterInput = document.getElementById("tableFilterInput");
const exportCsvBtn = document.getElementById("exportCsvBtn");
const copyNetlistBtn = document.getElementById("copyNetlistBtn");
const downloadNetlistBtn = document.getElementById("downloadNetlistBtn");
const reSolveBtn = document.getElementById("reSolveBtn");

const studentClaimInput = document.getElementById("studentClaimInput");
const checkAnswerBtn = document.getElementById("checkAnswerBtn");
const checkSpinner = document.getElementById("checkSpinner");
const studentFeedbackBox = document.getElementById("studentFeedbackBox");
const studentFeedbackText = document.getElementById("studentFeedbackText");
const feedbackTitle = document.getElementById("feedbackTitle");
const feedbackIcon = document.getElementById("feedbackIcon");
const closeFeedbackBtn = document.getElementById("closeFeedbackBtn");

const apiStatusBadge = document.getElementById("apiStatusBadge");
const apiStatusText = document.getElementById("apiStatusText");
const quickGuideBtn = document.getElementById("quickGuideBtn");
const guideModal = document.getElementById("guideModal");
const closeGuideModalBtn = document.getElementById("closeGuideModalBtn");
const zoomModal = document.getElementById("zoomModal");
const modalZoomImg = document.getElementById("modalZoomImg");
const closeZoomModalBtn = document.getElementById("closeZoomModalBtn");
const toastContainer = document.getElementById("toastContainer");

// Initialize API Ping
async function checkApiHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2500) });
    if (res.ok) {
      isBackendOnline = true;
      apiStatusBadge.className = "badge badge-status status-ready";
      apiStatusText.textContent = "Backend: Online";
    } else {
      throw new Error();
    }
  } catch (err) {
    isBackendOnline = false;
    apiStatusBadge.className = "badge badge-status status-offline";
    apiStatusText.textContent = "Engine: Standalone";
  }
}
checkApiHealth();
setInterval(checkApiHealth, 15000);

// File Upload Handlers
fileInput.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file) handleSelectedFile(file);
});

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file && file.type.startsWith("image/")) {
    handleSelectedFile(file);
  }
});

// Global Paste handler for screenshots (Ctrl+V)
window.addEventListener("paste", (e) => {
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith("image/")) {
      const file = item.getAsFile();
      if (file) {
        handleSelectedFile(file);
        showToast("Pasted image from clipboard!", "info");
        break;
      }
    }
  }
});

function handleSelectedFile(file) {
  currentFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImage.src = e.target.result;
    previewWrapper.style.display = "flex";
    dropzonePrompt.style.display = "none";
    analyzeBtn.disabled = false;
    clearInputBtn.style.display = "inline-flex";

    const kbSize = (file.size / 1024).toFixed(1);
    previewInfoTag.textContent = `${file.name || "Pasted image"} (${kbSize} KB)`;

    // Remove active state from sample cards
    document.querySelectorAll(".sample-card").forEach(c => c.classList.remove("active"));
  };
  reader.readAsDataURL(file);
}

clearInputBtn.addEventListener("click", () => {
  currentFile = null;
  fileInput.value = "";
  previewImage.src = "";
  previewWrapper.style.display = "none";
  dropzonePrompt.style.display = "block";
  analyzeBtn.disabled = true;
  clearInputBtn.style.display = "none";
});

replaceBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  fileInput.click();
});

zoomBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  if (previewImage.src) {
    modalZoomImg.src = previewImage.src;
    zoomModal.style.display = "flex";
  }
});

// Modals
closeZoomModalBtn.addEventListener("click", () => { zoomModal.style.display = "none"; });
zoomModal.addEventListener("click", (e) => { if (e.target === zoomModal) zoomModal.style.display = "none"; });

quickGuideBtn.addEventListener("click", () => { guideModal.style.display = "flex"; });
closeGuideModalBtn.addEventListener("click", () => { guideModal.style.display = "none"; });
guideModal.addEventListener("click", (e) => { if (e.target === guideModal) guideModal.style.display = "none"; });

// Sample Card Click Handler
document.querySelectorAll(".sample-card").forEach((card) => {
  card.addEventListener("click", async () => {
    document.querySelectorAll(".sample-card").forEach(c => c.classList.remove("active"));
    card.classList.add("active");

    const key = card.getAttribute("data-sample");
    const sample = SAMPLES[key];
    if (!sample) return;

    // Load sample preview
    previewImage.src = sample.image;
    previewWrapper.style.display = "flex";
    dropzonePrompt.style.display = "none";
    clearInputBtn.style.display = "inline-flex";
    previewInfoTag.textContent = `Preset: ${sample.title}`;
    analyzeBtn.disabled = false;

    // Fetch or use precomputed solution
    try {
      const res = await fetch(`${API_BASE}/api/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ netlist: sample.netlist })
      });
      if (res.ok) {
        const data = await res.json();
        currentAnalysisData = {
          final_netlist: sample.netlist,
          solved: data.solved || sample.solved,
          is_valid: data.is_valid !== undefined ? data.is_valid : true,
          validation_errors: data.validation_errors || [],
          rounds_log: [
            { round: 1, action: "preset_library_load", passed: true, netlist: sample.netlist }
          ],
          svg: sample.svg
        };
      } else {
        throw new Error();
      }
    } catch {
      // Local instant fallback
      currentAnalysisData = {
        final_netlist: sample.netlist,
        solved: sample.solved,
        is_valid: true,
        validation_errors: [],
        rounds_log: [
          { round: 1, action: "preset_library_load", passed: true, netlist: sample.netlist }
        ],
        svg: sample.svg
      };
    }

    renderAnalysis(currentAnalysisData);
    showToast(`Loaded ${sample.title} successfully!`, "success");
  });
});

// Analyze Button (Multimodal Read / Solve)
analyzeBtn.addEventListener("click", async () => {
  const btnText = analyzeBtn.querySelector(".btn-text");
  btnText.textContent = "Processing with Gemma & MNA...";
  analyzeSpinner.style.display = "inline-block";
  analyzeBtn.disabled = true;

  if (currentFile) {
    const formData = new FormData();
    formData.append("file", currentFile);

    try {
      const res = await fetch(`${API_BASE}/api/read`, {
        method: "POST",
        body: formData,
        signal: AbortSignal.timeout(180000)
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: `Server HTTP ${res.status}: ${res.statusText}` }));
        throw new Error(err.detail || `Server returned error ${res.status}`);
      }
      const data = await res.json();
      currentAnalysisData = data;
      renderAnalysis(data);
      if (data.code === "OK") {
        showToast("Schematic digitized & solved successfully!", "success");
      } else {
        showToast(`[${data.code}] ${data.message}`, "error");
      }
    } catch (err) {
      const isTimeout = err.name === "TimeoutError" || err.message.toLowerCase().includes("timeout");
      const errCode = isTimeout ? "TIMEOUT" : "API_ERROR";
      const errMsg = isTimeout 
        ? "Schematic extraction request timed out after waiting for model response." 
        : `Network / server error: ${err.message}`;

      showToast(`[${errCode}] ${errMsg}`, "error");

      currentAnalysisData = {
        code: errCode,
        message: errMsg,
        final_netlist: {
          components: [],
          uncertain: [errMsg]
        },
        solved: null,
        is_valid: false,
        validation_errors: [errMsg],
        solver_error: errMsg,
        rounds_log: [
          { round: 1, action: "vision_extraction", passed: false, error: errCode, validation_errors: [errMsg] }
        ],
        repairs_needed: 0
      };
      renderAnalysis(currentAnalysisData);
    } finally {
      btnText.textContent = "Digitize & Solve Circuit";
      analyzeSpinner.style.display = "none";
      analyzeBtn.disabled = false;
    }
  } else {
    // If a sample is active without a file
    const activeSample = document.querySelector(".sample-card.active");
    if (activeSample) {
      const sampleKey = activeSample.getAttribute("data-sample");
      if (SAMPLES[sampleKey]) {
        renderAnalysis(currentAnalysisData || SAMPLES[sampleKey]);
      }
    }
    btnText.textContent = "Digitize & Solve Circuit";
    analyzeSpinner.style.display = "none";
    analyzeBtn.disabled = false;
  }
});

// Real KCL & Power Conservation Verifier
function checkKclKvlExact(solved) {
  if (!solved || !solved.components || !solved.node_voltages) return false;
  const nodeCurrents = {};
  let sourcePower = 0;
  let resistorPower = 0;

  for (const comp of solved.components) {
    if (!comp.nodes || comp.nodes.length !== 2) continue;
    const n1 = String(comp.nodes[0]);
    const n2 = String(comp.nodes[1]);
    const i = Number(comp.current) || 0;
    const p = Number(comp.power) || 0;
    const type = comp.type;

    if (type === "V") {
      // Voltage source: current leaves positive terminal (n1) into circuit
      nodeCurrents[n1] = (nodeCurrents[n1] || 0) - i;
      nodeCurrents[n2] = (nodeCurrents[n2] || 0) + i;
      sourcePower += p;
    } else if (type === "I") {
      // Current source: flows n1 to n2; power delivered is -(v_drop * current)
      nodeCurrents[n1] = (nodeCurrents[n1] || 0) + i;
      nodeCurrents[n2] = (nodeCurrents[n2] || 0) - i;
      sourcePower -= p;
    } else if (type === "R") {
      // Resistor: flows n1 to n2
      nodeCurrents[n1] = (nodeCurrents[n1] || 0) + i;
      nodeCurrents[n2] = (nodeCurrents[n2] || 0) - i;
      resistorPower += p;
    }
  }

  // Sum of currents at every node is about 0 (within numeric tolerance)
  for (const sumI of Object.values(nodeCurrents)) {
    if (Math.abs(sumI) > 1e-7) return false;
  }

  // Source power equals resistor power within 1e-9 relative
  const maxP = Math.max(Math.abs(sourcePower), Math.abs(resistorPower), 1e-12);
  const relDiff = Math.abs(sourcePower - resistorPower) / maxP;
  if (relDiff > 1e-9) return false;

  return true;
}

// Main Render Function
function renderAnalysis(data) {
  emptyState.style.display = "none";
  analysisTab.style.display = "block";

  // Update Netlist Editor
  netlistEditor.value = JSON.stringify(data.final_netlist || {}, null, 2);

  // Status Banner with verbatim Code and Message
  const code = data.code || (data.is_valid ? "OK" : "VALIDATION_FAILED");
  const msg = data.message || (data.validation_errors || []).join(" | ") || data.solver_error || "Analysis complete.";
  const statusIconBox = document.getElementById("statusIconBox");

  // Subtitle: only show "Deterministic solution computed" when status is OK
  if (code === "OK" && data.is_valid && data.solved) {
    analysisSubtitle.textContent = "Deterministic solution computed";
  } else {
    analysisSubtitle.textContent = msg;
  }

  if (code === "OK" && data.is_valid && data.solved) {
    statusBanner.className = "status-banner banner-success";
    statusTitle.textContent = "Solved: checks passed";
    statusDesc.innerHTML = `<span>${escapeHtml(msg)}</span><div class="banner-subline" style="margin-top: 4px; font-size: 13px; opacity: 0.85;">Compare the Visual Schematic with your photo to confirm the reading.</div>`;
    if (statusIconBox) {
      statusIconBox.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>';
    }
    // Real check: show KCL/KVL badge only if exact check passes
    const kclKvlExact = checkKclKvlExact(data.solved);
    bannerMeta.style.display = kclKvlExact ? "flex" : "none";
  } else if (code === "VALUES_MISSING") {
    statusBanner.className = "status-banner banner-warning";
    statusTitle.textContent = "Values Missing [VALUES_MISSING]";
    statusDesc.textContent = msg;
    if (statusIconBox) {
      statusIconBox.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
    }
    bannerMeta.style.display = "none";
    // Auto-focus Netlist JSON editor so user can enter values and re-solve
    const netlistTabBtn = document.querySelector('.tab-btn[data-tab="netlistTab"]');
    if (netlistTabBtn) netlistTabBtn.click();
  } else {
    statusBanner.className = "status-banner banner-error";
    statusTitle.textContent = `Verification Failed [${code}]`;
    statusDesc.textContent = msg;
    if (statusIconBox) {
      statusIconBox.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>';
    }
    bannerMeta.style.display = "none";
  }


  // Uncertainties
  const uncertain = data.final_netlist?.uncertain || [];
  if (uncertain.length > 0) {
    uncertainBox.style.display = "block";
    uncertainList.innerHTML = uncertain.map((u) => `<li>${escapeHtml(u)}</li>`).join("");
  } else {
    uncertainBox.style.display = "none";
  }

  // KPIs
  const voltages = data.solved?.node_voltages || {};
  const components = data.solved?.components || [];
  const totalPower = (data.solved?.total_resistor_power || 0) * 1000;
  
  kpiTotalPower.textContent = totalPower < 1000 ? `${totalPower.toFixed(2)} mW` : `${(totalPower / 1000).toFixed(3)} W`;
  kpiNodeCount.textContent = Object.keys(voltages).length;
  kpiCompCount.textContent = components.length;

  let maxV = 0;
  let maxNode = "0";
  for (const [n, v] of Object.entries(voltages)) {
    if (v > maxV) {
      maxV = v;
      maxNode = n;
    }
  }
  kpiMaxVoltage.textContent = `${maxV.toFixed(2)} V`;
  kpiMaxNodeName.textContent = `Peak at Node ${maxNode}`;

  // Breakdown summary
  const rCount = components.filter(c => c.type === "R").length;
  const vCount = components.filter(c => c.type === "V").length;
  const iCount = components.filter(c => c.type === "I").length;
  kpiCompBreakdown.textContent = `${rCount} Resistors · ${vCount} Volt · ${iCount} Curr`;

  // Render Node Voltages Grid
  nodeVoltagesGrid.innerHTML = "";
  for (const [node, v] of Object.entries(voltages)) {
    const isGround = node === "0";
    const percent = maxV > 0 ? Math.min(100, (v / maxV) * 100) : 0;
    const nodeItem = document.createElement("div");
    nodeItem.className = `node-item ${isGround ? "is-ground" : ""}`;
    nodeItem.setAttribute("data-node", node);
    nodeItem.innerHTML = `
      <div class="node-name">${isGround ? "Node 0 (GND)" : `Node ${node}`}</div>
      <div class="node-val">${v.toFixed(3)} V</div>
      <div class="node-bar-container">
        <div class="node-bar" style="width: ${percent}%;"></div>
      </div>
    `;
    nodeVoltagesGrid.appendChild(nodeItem);
  }

  // Render Component Table
  renderComponentTable(components);

  // Render Visual Schematic
  renderSchematicSvg(data);

  // Render Repair Timeline
  renderRepairLog(data.rounds_log || []);
}

function renderComponentTable(components) {
  componentTableBody.innerHTML = "";
  const filter = tableFilterInput.value.trim().toLowerCase();

  components.forEach((comp) => {
    if (filter && !comp.id.toLowerCase().includes(filter) && !comp.type.toLowerCase().includes(filter)) {
      return;
    }

    const tr = document.createElement("tr");
    tr.setAttribute("data-comp-id", comp.id);

    const currentFormatted = Math.abs(comp.current) < 0.01 
      ? `${(comp.current * 1000).toFixed(3)} mA` 
      : `${comp.current.toFixed(4)} A`;

    const powerFormatted = Math.abs(comp.power) < 0.01 
      ? `${(comp.power * 1000).toFixed(3)} mW` 
      : `${comp.power.toFixed(4)} W`;

    let typePillClass = "type-pill-r";
    let typeName = "Resistor";
    if (comp.type === "V") { typePillClass = "type-pill-v"; typeName = "Voltage Src"; }
    if (comp.type === "I") { typePillClass = "type-pill-i"; typeName = "Current Src"; }

    tr.innerHTML = `
      <td><strong>${escapeHtml(comp.id)}</strong></td>
      <td><span class="type-pill ${typePillClass}">${typeName}</span></td>
      <td>${formatComponentValue(comp.type, comp.value)}</td>
      <td class="nodes-cell">[${comp.nodes.map(n => escapeHtml(n)).join(" → ")}]</td>
      <td><strong>${comp.voltage_drop.toFixed(3)} V</strong></td>
      <td>${currentFormatted}</td>
      <td>${powerFormatted}</td>
    `;
    componentTableBody.appendChild(tr);
  });
}

tableFilterInput.addEventListener("input", () => {
  if (currentAnalysisData?.solved?.components) {
    renderComponentTable(currentAnalysisData.solved.components);
  }
});

// Render Visual Schematic SVG
function renderSchematicSvg(data) {
  if (data.svg) {
    schematicContainer.innerHTML = data.svg;
    return;
  }
  
  // Synthesize dynamic SVG if no preset SVG exists
  const components = data.solved?.components || data.final_netlist?.components || [];
  const voltages = data.solved?.node_voltages || {};

  let svgHtml = `<svg viewBox="0 0 500 280" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="#050811" rx="8"/>
    <text x="250" y="30" fill="#f8fafc" font-size="14" font-weight="bold" text-anchor="middle">Synthesized Schematic</text>
  `;

  let x = 60;
  components.forEach((c, idx) => {
    const cx = x + (idx * 90);
    if (c.type === "V") {
      svgHtml += `
        <circle cx="${cx}" cy="130" r="20" stroke="#3b82f6" stroke-width="2.5" fill="#0d1424"/>
        <text x="${cx}" y="125" fill="#f8fafc" font-size="12" text-anchor="middle" font-weight="bold">+</text>
        <text x="${cx}" y="141" fill="#f8fafc" font-size="12" text-anchor="middle" font-weight="bold">-</text>
        <text x="${cx}" y="170" fill="#38bdf8" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">${c.id}: ${c.value}V</text>
      `;
    } else if (c.type === "I") {
      svgHtml += `
        <circle cx="${cx}" cy="130" r="20" stroke="#f59e0b" stroke-width="2.5" fill="#0d1424"/>
        <path d="M ${cx} 142 L ${cx} 118 M ${cx-5} 124 L ${cx} 118 L ${cx+5} 124" stroke="#fbbf24" stroke-width="2" fill="none"/>
        <text x="${cx}" y="170" fill="#fbbf24" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">${c.id}: ${formatComponentValue('I', c.value)}</text>
      `;
    } else {
      svgHtml += `
        <path d="M ${cx-20} 130 L ${cx-12} 115 L ${cx-4} 145 L ${cx+4} 115 L ${cx+12} 145 L ${cx+20} 130" stroke="#10b981" stroke-width="2.5" fill="none"/>
        <text x="${cx}" y="105" fill="#34d399" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">${c.id}: ${formatComponentValue('R', c.value)}</text>
      `;
    }
  });

  svgHtml += `
    <path d="M 40 220 L 460 220" stroke="#94a3b8" stroke-width="2"/>
    <path d="M 240 228 L 260 228 M 244 234 L 256 234 M 248 240 L 252 240" stroke="#94a3b8" stroke-width="2"/>
    <text x="250" y="260" fill="#94a3b8" font-size="11" font-family="'JetBrains Mono', monospace" text-anchor="middle">GND (Node 0)</text>
  </svg>`;

  schematicContainer.innerHTML = svgHtml;
}

// Render Repair Log
function renderRepairLog(rounds) {
  const repairCount = rounds.length > 1 ? rounds.length - 1 : 0;
  repairCountBadge.textContent = `${repairCount}`;
  
  if (rounds.length === 0) {
    repairTimeline.innerHTML = `<p style="color: var(--text-muted); font-size: 13px;">No repairs logged.</p>`;
    return;
  }

  repairTimeline.innerHTML = rounds.map((r) => `
    <div class="timeline-item">
      <div class="timeline-header">
        <span class="timeline-title">Iteration ${r.round}: ${escapeHtml(r.action)}</span>
        <span class="badge ${r.passed ? 'badge-status status-ready' : 'badge-gemma'}">${r.passed ? 'Passed Checks' : 'Self-Repair Active'}</span>
      </div>
      ${r.validation_errors && r.validation_errors.length ? `<ul style="color: var(--warning-text); margin-left:20px; font-size:12px; margin-top:6px;">${r.validation_errors.map(e => `<li>${escapeHtml(e)}</li>`).join('')}</ul>` : '<p style="color: var(--success-text); font-size:12px; margin-top:4px;">All topological & electrical integrity rules satisfied.</p>'}
    </div>
  `).join("");
}

// Student Homework Answer Verifier
checkAnswerBtn.addEventListener("click", async () => {
  const claim = studentClaimInput.value.trim();
  if (!claim) {
    showToast("Please enter or select a calculation claim first.", "error");
    return;
  }
  if (!currentAnalysisData || !currentAnalysisData.final_netlist) {
    showToast("Please solve or load a circuit first.", "error");
    return;
  }

  checkAnswerBtn.disabled = true;
  checkSpinner.style.display = "inline-block";

  try {
    const res = await fetch(`${API_BASE}/api/check`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        netlist: currentAnalysisData.final_netlist,
        solved: currentAnalysisData.solved,
        student_claim: claim
      })
    });
    if (res.ok) {
      const data = await res.json();
      displayStudentFeedback(data.explanation);
    } else {
      throw new Error();
    }
  } catch {
    // Client-side intelligent verification fallback
    const explanation = generateDiagnosticFeedback(claim, currentAnalysisData);
    displayStudentFeedback(explanation);
  } finally {
    checkAnswerBtn.disabled = false;
    checkSpinner.style.display = "none";
  }
});

// Quick claim chip clicks
document.querySelectorAll(".claim-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const claim = chip.getAttribute("data-claim");
    studentClaimInput.value = claim;
    studentClaimInput.focus();
    checkAnswerBtn.click();
  });
});

function displayStudentFeedback(text) {
  studentFeedbackBox.style.display = "block";
  studentFeedbackText.textContent = text;
  
  if (text.toLowerCase().includes("correct") && !text.toLowerCase().includes("incorrect")) {
    feedbackTitle.textContent = "Calculation Verified: Correct! ✓";
    feedbackTitle.style.color = "var(--success-text)";
    feedbackIcon.textContent = "🎉";
  } else {
    feedbackTitle.textContent = "Diagnostic Homework Feedback";
    feedbackTitle.style.color = "var(--accent-purple)";
    feedbackIcon.textContent = "💡";
  }
}

closeFeedbackBtn.addEventListener("click", () => {
  studentFeedbackBox.style.display = "none";
});

function generateDiagnosticFeedback(claim, data) {
  const voltages = data.solved?.node_voltages || {};
  const comps = data.solved?.components || [];
  
  // Parse simple node patterns like "N2 is 4V" or "N1 = 12"
  const nodeMatch = claim.match(/N(\d+)[^\d]*(\d+(?:\.\d+)?)/i);
  if (nodeMatch) {
    const nodeName = `N${nodeMatch[1]}`;
    const claimedVal = parseFloat(nodeMatch[2]);
    if (nodeName in voltages) {
      const actualVal = voltages[nodeName];
      if (Math.abs(claimedVal - actualVal) < 0.05) {
        return `Correct! Node ${nodeName} potential is verified at ${actualVal.toFixed(3)} V via Modified Nodal Analysis (KCL equilibrium satisfied).`;
      } else {
        return `Not quite. Your calculation gave ${claimedVal} V for Node ${nodeName}, but the exact solved potential is ${actualVal.toFixed(3)} V. Check your voltage divider ratio or resistor drop along the branch.`;
      }
    }
  }

  // Parse component current patterns like "R1 is 5mA" or "R1 = 0.005"
  const compMatch = claim.match(/(R\d+|V\d+|I\d+)[^\d]*(\d+(?:\.\d+)?)\s*(m?A)?/i);
  if (compMatch) {
    const compId = compMatch[1].toUpperCase();
    let claimedVal = parseFloat(compMatch[2]);
    const isMilli = compMatch[3]?.toLowerCase() === "ma" || claim.toLowerCase().includes("ma");
    if (isMilli && claimedVal > 0.05) claimedVal /= 1000;

    const comp = comps.find(c => c.id === compId);
    if (comp) {
      const actualCurr = comp.current;
      if (Math.abs(claimedVal - actualCurr) < 0.0005) {
        return `Correct! The branch current through ${compId} is exactly ${(actualCurr * 1000).toFixed(3)} mA (Ohm's Law: I = ΔV / R = ${comp.voltage_drop.toFixed(2)}V / ${comp.value}Ω).`;
      } else {
        return `Your current estimate of ${compMatch[2]}${isMilli ? 'mA' : 'A'} for ${compId} differs from the MNA solution of ${(actualCurr * 1000).toFixed(3)} mA. Make sure you used the branch voltage drop ΔV (${comp.voltage_drop.toFixed(2)} V) rather than total source voltage.`;
      }
    }
  }

  return `Analyzed claim: "${claim}". The circuit is solved with ground reference Node 0 (0.00V). Check branch voltages and KCL node currents against the table values above.`;
}

// Re-Solve Button (Manual Netlist Edit)
reSolveBtn.addEventListener("click", async () => {
  try {
    const editedNetlist = JSON.parse(netlistEditor.value);
    const res = await fetch(`${API_BASE}/api/solve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ netlist: editedNetlist })
    });
    const data = await res.json();
    currentAnalysisData = {
      final_netlist: editedNetlist,
      solved: data.solved,
      is_valid: data.is_valid,
      validation_errors: data.validation_errors,
      rounds_log: [{ round: 1, action: "manual_edit_resolve", passed: data.is_valid }]
    };
    renderAnalysis(currentAnalysisData);
    showToast("Re-solved modified netlist with MNA!", "success");
  } catch (err) {
    showToast("Invalid JSON syntax: " + err.message, "error");
  }
});

// Copy & Download Netlist
copyNetlistBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(netlistEditor.value);
  showToast("Netlist JSON copied to clipboard!", "success");
});

downloadNetlistBtn.addEventListener("click", () => {
  const blob = new Blob([netlistEditor.value], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "circuit_netlist.json";
  a.click();
  URL.revokeObjectURL(url);
  showToast("Downloaded circuit_netlist.json", "info");
});

// Export CSV
exportCsvBtn.addEventListener("click", () => {
  if (!currentAnalysisData?.solved?.components) return;
  const comps = currentAnalysisData.solved.components;
  let csv = "Component,Type,Value,Nodes,Voltage_Drop_V,Current_A,Power_W\n";
  comps.forEach(c => {
    csv += `"${c.id}","${c.type}",${c.value},"${c.nodes.join('-')}",${c.voltage_drop},${c.current},${c.power}\n`;
  });
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "branch_analysis.csv";
  a.click();
  URL.revokeObjectURL(url);
  showToast("Exported branch_analysis.csv", "info");
});

// Tab Switching
document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((c) => (c.style.display = "none"));

    btn.classList.add("active");
    const target = document.getElementById(btn.getAttribute("data-tab"));
    if (target) target.style.display = "block";
  });
});

// Toast Notifications
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
    <span>${escapeHtml(message)}</span>
  `;
  toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(10px)";
    toast.style.transition = "all 0.25s";
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

function formatComponentValue(type, val) {
  if (type === "R") {
    if (val >= 1e6) return `${(val / 1e6).toFixed(1)} MΩ`;
    if (val >= 1e3) return `${(val / 1e3).toFixed(1)} kΩ`;
    return `${val} Ω`;
  }
  if (type === "V") return `${val} V`;
  if (type === "I") {
    if (val < 1e-3) return `${(val * 1e6).toFixed(1)} µA`;
    if (val < 1) return `${(val * 1e3).toFixed(1)} mA`;
    return `${val} A`;
  }
  return `${val}`;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
