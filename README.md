# 🏆 Solver Benchmark Dashboard

An interactive Streamlit dashboard for benchmarking and comparing constraint programming and optimization solvers.

## 🌐 Live Application

👉 **Solver Benchmark Dashboard**: https://toulbar2.streamlit.app

The application can be used directly from your browser without installation.

---

## ✨ Features

- Compare multiple solvers simultaneously
- Interactive performance visualization
- Cactus plots
- Objective value comparison
- Lower bound comparison
- Search node analysis
- Pairwise solver comparison
- Global performance summary
- XCSP3-inspired ranking system
- Detailed per-instance analysis

---

## 📂 Input Data Format

The application expects a CSV file where each row represents a benchmark instance.

### Mandatory Column

| Column | Type | Description |
|----------|----------|----------|
| Problem | string | Instance name |

### Instance Statistics

| Column | Type | Description |
|----------|----------|----------|
| nbvar | int | Number of variables |
| max_dom | int | Maximum domain size |
| nbconstr | int | Number of constraints |
| max_arity | int | Maximum constraint arity |

---

## 🤖 Solver Results Format

For each solver `S`, the following columns may be provided:

| Column | Type | Description |
|----------|----------|----------|
| S_bestsol | float | Best objective value found |
| S_cputime | float | CPU time (seconds) |
| S_status | string | Solver status |
| S_bestbound | float | Best bound found |
| S_nbnodes | int | Number of explored search nodes |

### Example

| Problem | SolverA_bestsol | SolverA_cputime | SolverA_status |
|----------|----------|----------|----------|
| instance1 | 125 | 2.34 | OPT |

---

## 📊 Solver Status

| Status | Meaning |
|----------|----------|
| OPT | Optimal solution found and proven |
| FEAS | Feasible solution found but optimality not proven |
| UNK | No solution returned or timeout |
| Error | Runtime, memory, parser, or execution error |

---

# 📈 Available Visualizations

## Cactus Plot

Displays the number of solved instances as a function of CPU time.

Useful for comparing overall solver efficiency.

---

## Objective Plot

Compares objective values obtained by selected solvers.

---

## Lower Bound Plot

Compares best lower bounds reported by solvers.

Available when bound information is provided.

---

## Nodes Plot

Compares the number of search nodes explored by each solver.

Available when node statistics are provided.

---

## Pairwise Comparison

Direct solver-versus-solver comparison on:

- CPU Time
- Objective Value
- Best Bound
- Number of Nodes

---

# 🏆 Global Comparison

The Global Comparison table summarizes solver performance.

| Column | Meaning |
|----------|----------|
| OPT | Number of optimal solutions |
| FEAS | Number of feasible solutions |
| Timeout | Number of timeouts |
| Error | Number of execution failures |
| Total Time | Total CPU time |
| BEST | Number of instances won according to the BEST criterion |

## BEST Criterion

For each benchmark instance, the best solver is selected according to:

1. OPT status
2. FEAS status
3. Best objective value
4. Lowest CPU time

This criterion is used only for comparison purposes and does not affect XCSP3 ranking scores.

---

# 🥇 XCSP3 Competition Ranking

The ranking system follows principles inspired by the XCSP3 Competition.

Official website:

https://www.xcsp.org/competitions/

---

## Ranking Columns

| Column | Meaning |
|----------|----------|
| OPT | Number of optimality proofs |
| FEAS | Number of feasible solutions |
| BEST | Number of benchmark wins according to the BEST criterion |
| BB1 | Number of best-bound awards without optimality proof |
| BB2 | Number of best-bound awards when optimality is proven elsewhere |
| SCORE | Total competition score |

---

## Scoring Rules

### OPT

Solver proves optimality.

**Score: +1**

---

### BB1

The solver provides the best known bound among all competitors and no solver proves that this bound is optimal.

**Score: +1**

---

### BB2

The solver provides the best known bound among all competitors but another solver proves optimality.

**Score: +0.5**

---

### Notes

- The best bound may be shared by several solvers.
- Multiple solvers can receive BB1 or BB2 points on the same instance.

---

# 🚀 Installation

Clone the repository:

```bash
git clone "https://github.com/sewaguidio/Stage-INRAE.git"
cd "Stage-INRAE/Application"
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the dashboard:

```bash
streamlit run app.py
```

---

# 📥 Data Sources

The dashboard supports:

- Local CSV upload
- Remote CSV via URL
- Default dataset hosted on GitHub

---

# 🔍 Typical Use Cases

- Constraint Programming Solver Evaluation
- Optimization Solver Benchmarking
- Research Experiments
- Competition Result Analysis
- Solver Regression Testing
- Performance Profiling

---
