# Hand-Drawn DC Circuit Test Samples & Ground Truth Benchmarks

This directory holds verified test circuit images for evaluating the multimodal schematic extraction and Modified Nodal Analysis (MNA) solver.

## Available Test Cases

| File | Circuit Type | Key Values & Topology | Ground Truth File |
| :--- | :--- | :--- | :--- |
| **`case_01.jpg`** | 10V Series Divider | $V_1 = 10\text{V}$, $R_1 = 1\text{k}\Omega$, $R_2 = 1\text{k}\Omega$ | [`case_01_series.json`](file:///c:/Users/sujay/Desktop/hacktoberfest/eval/cases/case_01_series.json) |
| **`case_02.jpg`** | 12V Divider | $V_1 = 12\text{V}$, $R_1 = 2\text{k}\Omega$, $R_2 = 1\text{k}\Omega$ | [`case_02_divider.json`](file:///c:/Users/sujay/Desktop/hacktoberfest/eval/cases/case_02_divider.json) |
| **`case_03.jpg`** | 10V Parallel | $V_1 = 10\text{V}$, $R_1 = 1\text{k}\Omega \parallel R_2 = 1\text{k}\Omega$ | [`case_03_parallel.json`](file:///c:/Users/sujay/Desktop/hacktoberfest/eval/cases/case_03_parallel.json) |
| **`case_04.jpg`** | 12V Series-Parallel | $V_1 = 12\text{V}$, $R_1 = 4\text{k}\Omega$ in series with $(R_2 = 6\text{k}\Omega \parallel R_3 = 3\text{k}\Omega)$ | [`case_04_series_parallel.json`](file:///c:/Users/sujay/Desktop/hacktoberfest/eval/cases/case_04_series_parallel.json) |
| **`case_05.jpg`** | Current Source | $I_1 = 2\text{mA}$ ideal source driving $R_1 = 5\text{k}\Omega$ | [`case_05_current_src.json`](file:///c:/Users/sujay/Desktop/hacktoberfest/eval/cases/case_05_current_src.json) |
| **`case_06.jpg`** | Wheatstone Bridge | $V_1 = 10\text{V}$, $R_1 = 1\text{k}\Omega, R_2 = 2\text{k}\Omega, R_3 = 2\text{k}\Omega, R_4 = 4\text{k}\Omega, R_g = 500\Omega$ | [`case_06_bridge.json`](file:///c:/Users/sujay/Desktop/hacktoberfest/eval/cases/case_06_bridge.json) |

## How to Test
1. Drag and drop any `.jpg` file from this folder into the web dropzone at `http://localhost:8000/`.
2. Or use the 1-click **Verified Test Bench Library** buttons in the web interface.
