import streamlit as st
import pandas as pd
import sys
import plotly.graph_objects as go
import plotly.express as px
import numpy as np


st.set_page_config(page_title="Solver Dashboard", layout="wide")

# ===================== CONSTANTS =====================

default_cutoff = 1200

bestsol_postfix = "_bestsol"
cputime_postfix = "_cputime"
status_postfix = "_status"
bestbound_postfix = "_bestbound"
nbnodes_postfix = "_nbnodes"

filename_column = "Problem"
probstat_columns = ["nbvar", "max_dom", "nbconstr", "max_arity"]


def generate_solver_colors(solver_names):
    palette = px.colors.qualitative.Plotly  # palette propre

    colors = {}
    for i, s in enumerate(solver_names):
        colors[s] = palette[i % len(palette)]

    return colors

# ===================== CLASS =====================

class SolverResult:
    def __init__(self, bestsol, cputime, status, bestbound, nbnodes):
        self.bestsol_text = bestsol
        self.bestsol = int(float(bestsol)) if bestsol != "?" else sys.maxsize

        self.bestbound = int(float(bestbound)) if bestbound != "?" else -sys.maxsize
        self.nbnodes = int(nbnodes) if nbnodes != "?" else sys.maxsize

        try:
            self.cputime = float(cputime)
        except:
            self.cputime = default_cutoff

        self.cputime_text = cputime
        self.status = status

    def is_opt(self): return self.status == "OPT"
    def is_feas(self): return self.status.startswith("FEAS")
    def is_timeout(self): return self.status == "UNK"
    def is_err(self): return self.cputime_text in ["MZN", "mem", "ARITY", "32-bit"]

# ===================== BEST =====================

def get_best_result(results):
    return min(
        results.values(),
        key=lambda r: (
            0 if r.is_opt() else 1 if r.is_feas() else 2,
            r.bestsol,
            r.cputime
        )
    )

# ===================== READ =====================

def read_results(df):
    solver_names = []
    rows = []

    for col in df.columns:
        if col != filename_column and col not in probstat_columns:
            name = col
            for s in [bestsol_postfix, cputime_postfix, status_postfix,
                      bestbound_postfix, nbnodes_postfix]:
                name = name.replace(s, "")
            if name not in solver_names:
                solver_names.append(name)

    for _, row in df.iterrows():
        problem = row[filename_column]
        stats = {k: int(row[k]) for k in probstat_columns}

        results = {}
        for s in solver_names:
            results[s] = SolverResult(
                row[f"{s}{bestsol_postfix}"],
                row[f"{s}{cputime_postfix}"],
                row[f"{s}{status_postfix}"],
                row[f"{s}{bestbound_postfix}"],
                row[f"{s}{nbnodes_postfix}"],
            )

        rows.append((problem, stats, results))

    return solver_names, rows

def compute_ranking(solver_names, rows):

    # ===================== INIT =====================
    df = pd.DataFrame(index=solver_names)
    df["OPT"] = 0
    df["FEAS"] = 0
    df["BEST"] = 0
    df["BB1"] = 0
    df["BB2"] = 0
    df["SCORE"] = 0.0

    # ===================== LOOP =====================
    for _, _, results in rows:
        # filter ONLY selected solvers (IMPORTANT)
        results = {s: results.get(s) for s in solver_names}
        results = {s: r for s, r in results.items() if r is not None}

        if not results:
            continue
        # best solver (for "BEST" column)
        best_solver = get_best_result(
            {s: results[s] for s in solver_names if s in results}
        )

        # best bound (CORRECT metric)
        best_bound = min(
            (r.bestsol for r in results.values() if not r.is_err()),
            default=None
        )

        # solvers proving OPT
        opt_solvers = {s for s, r in results.items() if r.is_opt()}

        for s in solver_names:

            r = results.get(s)
            if r is None or r.is_err():
                continue

            # ===================== METRICS =====================
            if r == best_solver:
                df.loc[s, "BEST"] += 1

            if r.is_opt():
                df.loc[s, "OPT"] += 1
                df.loc[s, "SCORE"] += 1.0
                continue

            if r.is_feas():
                df.loc[s, "FEAS"] += 1



            # ===================== BB SCORE =====================

            if best_bound is not None and r.bestsol == best_bound:

                if len(opt_solvers) == 0:
                    df.loc[s, "SCORE"] += 1.0   # BB1
                    df.loc[s, "BB1"] += 1  # BB1
                else:
                    df.loc[s, "SCORE"] += 0.5   # BB2
                    df.loc[s, "BB2"] += 1   # BB2

    # ===================== FINAL SCORE =====================
    df = df.sort_values("SCORE", ascending=False)

    return df


# ===================== GLOBAL TABLE =====================

def compute_global_table(solver_names, rows):
    data = []

    for s in solver_names:
        opt = feas = timeout = err = total_time = 0

        for _, _, results in rows:
            r = results[s]

            if r.is_opt(): opt += 1
            elif r.is_feas(): feas += 1
            elif r.is_timeout(): timeout += 1
            elif r.is_err(): err += 1

            total_time += r.cputime

        data.append({
            "solver": s,
            "OPT": opt,
            "FEAS": feas,
            "Timeout": timeout,
            "Error": err,
            "Total Time": round(total_time,2)
        })

    return pd.DataFrame(data)


# ===================== HTML TABLES =====================

def render_stats_table(stats):
    rows = "".join(
        f"<tr><td><b>{k}</b></td><td style='text-align:right'>{v}</td></tr>"
        for k, v in stats.items()
    )

    return f"""
    <table style="width:100%;border:1px solid black;border-collapse:collapse;">
        {rows}
    </table>
    """

def render_result_table(res, best):
    if res.is_err(): bg = "#FFAFAF"
    elif res.is_timeout(): bg = "#FFDF7F"
    elif res == best: bg = "#00FF00"
    elif res.is_opt(): bg = "#AFFF00"
    elif res.is_feas():
        alpha = min(max((1 - (res.bestsol - best.bestsol)/max(res.bestsol,1))*0.5, 0), 1)
        bg = f"rgba(176,255,0,{alpha})"
    else:
        bg = "white"

    return f"""
    <table style="width:100%;border:1px solid black;background:{bg};">
        <tr><td><b>S</b></td><td>{res.status}</td></tr>
        <tr><td><b>O</b></td><td>{res.bestsol_text}</td></tr>
        <tr><td><b>T</b></td><td>{res.cputime_text}</td></tr>
        <tr><td><b>B</b></td><td>{res.bestbound}</td></tr>
        <tr><td><b>N</b></td><td>{res.nbnodes}</td></tr>
    </table>
    """
def plot_cactus(solvers, rows, use_log=False):
    fig = go.Figure()

    for s in solvers:
        times = []
        problems = []

        for problem, _, results in rows:
            r = results[s]
            if r.is_opt():
                times.append(r.cputime)
                problems.append(problem)

        # sort by time
        sorted_pairs = sorted(zip(times, problems), key=lambda x: x[0])

        if not sorted_pairs:
            continue

        times, problems = zip(*sorted_pairs)

        fig.add_trace(go.Scatter(
            x=list(range(1, len(times) + 1)),
            y=list(times),
            mode="lines+markers",
            marker=dict(color=solver_colors[s]),
            line=dict(color=solver_colors[s]),
            name=f"{s} [{len(times)} solved]",
            customdata=list(problems),
            hovertemplate=
                "Solver: " + s + "<br>" +
                "Solved #: %{x}<br>" +
                "Problem: %{customdata}<br>" +
                "Time: %{y:.4f}s<extra></extra>"
        ))

    fig.update_layout(
        title="Cactus Plot",
        xaxis_title="Solved Instances",
        yaxis_title="CPU Time (s)",
        yaxis_type="log" if use_log else "linear",
        width=900,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)




def plot_nodes(solvers, rows, use_log=False):

    fig = go.Figure()

    # ===================== PLOT =====================
    stats = []

    for s in solvers:

        values, problems = [], []

        for problem, _, results in rows:
            r = results.get(s)
            if r is None or r.is_err():
                continue

            values.append(r.nbnodes)
            problems.append(problem)

        if len(values) == 0:
            continue

        sorted_pairs = sorted(zip(values, problems), key=lambda x: x[0])
        values = [v for v, _ in sorted_pairs]
        problems = [p for _, p in sorted_pairs]

        # trace
        fig.add_trace(go.Scatter(
            x=list(range(1, len(values) + 1)),
            y=values,
            mode="lines+markers",
            marker=dict(color=solver_colors[s]),
            line=dict(color=solver_colors[s]),
            name=s,
            customdata=problems,
            hovertemplate=
                "Solver: " + s + "<br>" +
                "Problem: %{customdata}<br>" +
                "Nodes: %{y}<extra></extra>",
        ))

        # ===================== STATS =====================
        stats.append({
            "Solver": s,
            "Mean Nodes": np.mean(values),
            "Median Nodes": np.median(values),
            "Std Nodes": np.std(values)
        })

    fig.update_layout(
        title="Nodes Comparison",
        yaxis_type="log" if use_log else "linear",
        xaxis_title="Instances",
        yaxis_title="Nodes",
        width=900,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

    # ===================== TABLE =====================
    st.subheader("📊 Nodes Statistics")

    stats_df = pd.DataFrame(stats)

    # formatting for readability
    stats_df["Mean Nodes"] = stats_df["Mean Nodes"].round(2)
    stats_df["Median Nodes"] = stats_df["Median Nodes"].round(2)
    stats_df["Std Nodes"] = stats_df["Std Nodes"].round(2)

    st.dataframe(stats_df, use_container_width=True)

def plot_objective(solvers, rows, use_log=False):
    fig = go.Figure()

    for s in solvers:
        values, problems = prepare_metric_data(rows, s, "bestsol")

        fig.add_trace(go.Scatter(
            x=list(range(1, len(values) + 1)),
            y=values,
            mode="lines+markers+text",
            marker=dict(color=solver_colors[s]),
            line=dict(color=solver_colors[s]),
            name=s,
            customdata=problems,
            textposition="top center",
            hovertemplate=
                "Solver: " + s + "<br>" +
                "Problem: %{customdata}<br>" +
                "Objective: %{y}<extra></extra>",
        ))

    fig.update_layout(
        title="Objective Comparison",
        yaxis_type="log" if use_log else "linear",
        xaxis_title="Instances",
        yaxis_title="Objective",
        width=900,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_lowerbound(solvers, rows, use_log=False):
    fig = go.Figure()

    for s in solvers:
        values, problems = prepare_metric_data(rows, s, "bestbound")

        fig.add_trace(go.Scatter(
            x=list(range(1, len(values) + 1)),
            y=values,
            mode="lines+markers+text",
            marker=dict(color=solver_colors[s]),
            line=dict(color=solver_colors[s]),
            name=s,
            customdata=problems,
            textposition="top center",
            hovertemplate=
                "Solver: " + s + "<br>" +
                "Problem: %{customdata}<br>" +
                "Lower bound: %{y}<extra></extra>",
        ))

    fig.update_layout(
        title="Lower Bound Comparison",
        yaxis_type="log" if use_log else "linear",
        xaxis_title="Instances",
        yaxis_title="Lower Bound",
        width=900,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

def prepare_metric_data(rows, solver, metric):
    values = []
    problems = []

    for problem, _, results in rows:
        r = results[solver]
        if not r.is_err():
            values.append(getattr(r, metric))
            problems.append(problem)

    # sort by value but keep mapping
    sorted_pairs = sorted(zip(values, problems), key=lambda x: x[0])

    if not sorted_pairs:
        return [], []

    values, problems = zip(*sorted_pairs)
    return list(values), list(problems)


def pairwise_plot(rows, solver1, solver2, metric, use_log=False):


    # ===================== INIT =====================
    win1 = 0
    win2 = 0
    ties = 0

    x_win1, y_win1, p_win1 = [], [], []
    x_win2, y_win2, p_win2 = [], [], []
    x_tie, y_tie, p_tie = [], [], []

    # ===================== DATA =====================
    for problem, _, results in rows:

        r1 = results.get(solver1)
        r2 = results.get(solver2)

        if r1 is None or r2 is None:
            continue

        if r1.is_err() or r2.is_err():
            continue

        v1 = getattr(r1, metric)
        v2 = getattr(r2, metric)

        # skip invalid values (important for log scale)
        if use_log and (v1 <= 0 or v2 <= 0):
            continue

        if metric == "bestbound" :

            if v1 > v2:
                win1 += 1
                x_win1.append(v1)
                y_win1.append(v2)
                p_win1.append(problem)

            elif v1 < v2:
                win2 += 1
                x_win2.append(v1)
                y_win2.append(v2)
                p_win2.append(problem)

            else:
                ties += 1
                x_tie.append(v1)
                y_tie.append(v2)
                p_tie.append(problem)

        else :
            if v1 < v2:
                win1 += 1
                x_win1.append(v1)
                y_win1.append(v2)
                p_win1.append(problem)

            elif v1 > v2:
                win2 += 1
                x_win2.append(v1)
                y_win2.append(v2)
                p_win2.append(problem)

            else:
                ties += 1
                x_tie.append(v1)
                y_tie.append(v2)
                p_tie.append(problem)

    total_points = win1 + win2 + ties
    if total_points == 0:
        st.warning("No data to display")
        return

    fig = go.Figure()

    # ===================== SOLVER1 WINS =====================
    fig.add_trace(go.Scatter(
        x=x_win1,
        y=y_win1,
        mode="markers",
        name=f"{solver1} wins ({win1})",
        marker=dict(
            color=solver_colors[solver1],
            size=9,
            symbol="circle"
        ),
        customdata=p_win1,
        hovertemplate=
            f"<b>{solver1}</b>: %{{x}}<br>" +
            f"<b>{solver2}</b>: %{{y}}<br>" +
            "Problem: %{customdata}<extra></extra>",
    ))

    # ===================== SOLVER2 WINS =====================
    fig.add_trace(go.Scatter(
        x=x_win2,
        y=y_win2,
        mode="markers",
        name=f"{solver2} wins ({win2})",
        marker=dict(
            color=solver_colors[solver2],
            size=9,
            symbol="square"
        ),
        customdata=p_win2,
        hovertemplate=
            f"<b>{solver1}</b>: %{{x}}<br>" +
            f"<b>{solver2}</b>: %{{y}}<br>" +
            "Problem: %{customdata}<extra></extra>",
    ))

    # ===================== TIES =====================
    fig.add_trace(go.Scatter(
        x=x_tie,
        y=y_tie,
        mode="markers",
        name=f"Ties ({ties})",
        marker=dict(
            color="gray",
            size=9,
            symbol="diamond"
        ),
        customdata=p_tie,
        hovertemplate=
            f"<b>{solver1}</b>: %{{x}}<br>" +
            f"<b>{solver2}</b>: %{{y}}<br>" +
            "Problem: %{customdata}<extra></extra>",
    ))

    # ===================== DIAGONAL x = y =====================
    all_vals = x_win1 + x_win2 + x_tie + y_win1 + y_win2 + y_tie

    min_val = min(v for v in all_vals if v > 0)
    max_val = max(all_vals)

    fig.add_trace(go.Scatter(
        x=[min_val, max_val],
        y=[min_val, max_val],
        mode="lines",
        line=dict(color="black", dash="dash", width=2),
        name=f"{solver1} = {solver2}",
        hoverinfo="skip"
    ))

    # ===================== LAYOUT =====================
    fig.update_layout(
        title=f"⚔️ Pairwise: {solver1} vs {solver2} ({metric})",
        xaxis_type="log" if use_log else "linear",
        yaxis_type="log" if use_log else "linear",
        xaxis_title=solver1,
        yaxis_title=solver2,
        legend_title="Comparison",
        template="plotly_white",
        width=900,
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)



# ===================== UI =====================
st.title("🏆 Solver Benchmark Dashboard")

# ===================== DATA =====================

st.markdown("### 📂 Data Source")

data_choice = st.radio(
    "Choose data source:",
    ["Upload my data", "Use default dataset"]
)

df = None

if data_choice == "Upload my data":
    file = st.file_uploader("Upload CSV", type=["csv"])
    if file:
        df = pd.read_csv(file, delimiter=" ")

else:
    url = "https://raw.githubusercontent.com/sewaguidio/Stage-INRAE/main/results.csv"
    st.info("Using default dataset from GitHub")
    df = pd.read_csv(url, delimiter=" ")

# ===================== MAIN APP =====================

if df is not None:

    solver_names, rows = read_results(df)

    st.success(f"Loaded {len(rows)} instances and {len(solver_names)} solvers")

  
    # ===================== SIDEBAR =====================

    solver_colors = generate_solver_colors(solver_names)


    # -------- SOLVER CHECKBOXES --------
    st.sidebar.markdown("### 🧠 Select Solvers")



    selected_solvers = []

    for s in solver_names:
        checked = st.sidebar.checkbox(s, value=True)
        if checked:
            selected_solvers.append(s)

    # safety
    if len(selected_solvers) == 0:
        st.warning("Please select at least one solver")
        st.stop()

    st.sidebar.markdown(f"✔️ {len(selected_solvers)} solver(s) active")


    st.subheader("🎨 Solver Colors")

    st.markdown(
        "<div style='display:flex;flex-wrap:wrap;gap:10px;'>"
        + "".join([
            f"<div style='background:{solver_colors[s]};padding:6px 10px;border-radius:6px;color:white;'>"
            f"{s}</div>"
            for s in selected_solvers
        ])
        + "</div>",
        unsafe_allow_html=True
    )
    # -------- SOLVER CHECKBOXES --------
    st.sidebar.markdown("### 📊 Options")

    use_log = st.sidebar.checkbox("📊 Log scale (all plots)", value=False)
    exp = st.sidebar.checkbox("📊 Table expande", value=False)

    # -------- SEARCH --------
    st.sidebar.markdown("### 🔍 Filter")

    search_problem = st.sidebar.text_input("Search problem name")

    # -------- FILTER ROWS --------
    filtered_rows = []

    for problem, stats, results in rows:

        if search_problem and search_problem.lower() not in problem.lower():
            continue

        filtered_rows.append((problem, stats, results))

    # ===================== GLOBAL BEST PER ROW =====================

    def get_best_dynamic(results):
        return get_best_result({s: results[s] for s in selected_solvers})

    # ===================== KPI =====================

    st.markdown("### 📌 Overview")

    col1, col2, col3 = st.columns(3)

    col1.metric("Problems", len(filtered_rows))
    col2.metric("Active Solvers", len(selected_solvers))
    col3.metric("Total Runs", len(filtered_rows) * len(selected_solvers))

    # ===================== CACTUS =====================


    # ===================== ADVANCED PLOTS =====================

    st.subheader("📊 Advanced Analysis")

    tab0, tab1, tab2, tab3 = st.tabs([
        "📈 Cactus Plot",
        "🌳 Nodes",
        "🎯 Objective",
        "📉 Lower Bound"
    ])

    with tab0:
        plot_cactus(selected_solvers, filtered_rows, use_log)

    with tab1:
        plot_nodes(selected_solvers, filtered_rows, use_log)

    with tab2:
        plot_objective(selected_solvers, filtered_rows, use_log)

    with tab3:
        plot_lowerbound(selected_solvers, filtered_rows, use_log)

    # ===================== RANKING =====================

    st.subheader("⚔️ Pairwise Comparison")

    col1, col2, col3 = st.columns(3)

    with col1:
        solver1 = st.selectbox("Solver 1", selected_solvers)

    with col2:
        solver2 = st.selectbox("Solver 2", selected_solvers, index=1 if len(selected_solvers) > 1 else 0)

    with col3:
        metric = st.selectbox(
            "Metric",
            ["cputime", "nbnodes", "bestsol", "bestbound"]
        )


    if solver1 != solver2:
        pairwise_plot(filtered_rows, solver1, solver2, metric, use_log)

    st.subheader("🏆 Ranking")

    ranking_df = compute_ranking(selected_solvers, filtered_rows)
    st.dataframe(ranking_df, use_container_width=True)

    # ===================== GLOBAL TABLE =====================

    st.subheader("📊 Global Comparison")

    global_df = compute_global_table(selected_solvers, filtered_rows)

    colA, colB = st.columns([2, 1])

    with colA:
        search_solver = st.text_input("🔎 Search solver")

    with colB:
        sort_col = st.selectbox("Sort by", global_df.columns)

    if search_solver:
        global_df = global_df[
            global_df["solver"].str.contains(search_solver, case=False)
        ]

    global_df = global_df.sort_values(sort_col, ascending=False)

    st.dataframe(global_df, use_container_width=True)

    # ===================== LEGEND =====================

    st.subheader("🎨 Legend")

    st.markdown("""
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
        <div style="background:#00FF00;padding:6px;border-radius:5px;">🏆 Best SOL</div>
        <div style="background:#AFFF00;padding:6px;border-radius:5px;">✔ OPT</div>
        <div style="background:#B6FF00;padding:6px;border-radius:5px;">⚡ FEAS</div>
        <div style="background:#FFDF7F;padding:6px;border-radius:5px;">⏱ Timeout</div>
        <div style="background:#FFAFAF;padding:6px;border-radius:5px;">❌ Error</div>
    </div>
    """, unsafe_allow_html=True)

    # ===================== RESULTS =====================
    st.subheader("📋 Detailed Results")

    st.markdown("""
<table class="resultstable">
<tr><th class='title'>Key</th><th>Meaning</th></tr>
<tr><td class='title'>S</td><td>
OPT: Optimal solution found and proved<br/>
FEAS: Satisfiable, solution found<br/>
UNK: No solution returned
</td></tr>
<tr><td class='title'>O</td><td>Best objective value found</td></tr>
<tr><td class='title'>B</td><td>Best lower bound value found</td></tr>
<tr><td class='title'>N</td><td>number of nodes</td></tr>
<tr><td class='title'>T</td><td>Time in seconds<br/></td></tr>
</table>
<br>
""", unsafe_allow_html=True)

    

    for problem, stats, results in filtered_rows:

        # 👉 BEST is now dynamic based ONLY on selected solvers
        best = get_best_result({s: results[s] for s in selected_solvers})

        with st.expander(f"🔎 {problem}", expanded=exp):

            col1, col2 = st.columns([1, 2])

            with col1:
                st.markdown("**Stats**")
                st.markdown(render_stats_table(stats), unsafe_allow_html=True)

            with col2:
                st.markdown("**Best Solver (selected set)**")
                st.markdown(
                    render_result_table(best, best),
                    unsafe_allow_html=True
                )

            st.markdown("### ⚙️ Solvers")

            cols = st.columns(len(selected_solvers))

            for i, s in enumerate(selected_solvers):
                with cols[i]:
                    st.markdown(f"**{s}**")
                    st.markdown(
                        render_result_table(results[s], best),
                        unsafe_allow_html=True
                    )
