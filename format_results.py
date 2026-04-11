import csv
import sys
import json


page_title = "Results"
default_cutoff = 1200

# Header constants from the results file
bestsol_postfix = "_bestsol"
cputime_postfix = "_cputime"
status_postfix = "_status"
bestbound_postfix = "_bestbound"
nbnodes_postfix = "_nbnodes"
filename_column = "Problem"
probstat_columns = ["nbvar", "max_dom", "nbconstr", "max_arity"]

# CSS classes
timed_out_class = "timed_out"
opt_best_class = "opt_best"
opt_ok_class = "opt_ok"
err_class = "error"


class SolverResult(object):

    def __init__(self, bestsol, cputime, status, bestbound, nbnodes):
        self.bestsol_text = bestsol
        if bestsol == "?":
            self.bestsol = sys.maxint
        else:
            self.bestsol = float(bestsol)
            self.bestsol = int(self.bestsol)

        self.bestbound_text = bestbound
        if bestbound == "?":
            self.bestbound = sys.minint
        else:
            self.bestbound = float(bestbound)
            self.bestbound = int(self.bestbound)
        
        self.nbnodes_text = nbnodes
        if nbnodes == "?":
            self.nbnodes = sys.maxint
        else:
            self.nbnodes = int(nbnodes)

        self.cputime_text = cputime
        try:
            self.cputime = float(cputime)
            self.cputime_text = cputime
        except:
            self.cputime = default_cutoff

        self.status = status

    def timed_out(self):
        return self.status == "UNK"

    def is_opt(self):
        return self.status == "OPT"

    def is_err(self):
        return self.cputime_text in ["MZN", "mem", "ARITY", "32-bit"]

    def get_ratio_to_best(self, best):
        try:
            if self.bestsol != 0:
                return (1.0 - (float(self.bestsol) - float(best.bestsol)) / float(self.bestsol)) * 0.5
            else:
                return 1.0
        except:
            return 1.0

    def __lt__(self, other):
        if (other.status == "UNK" and self.status[0] == "FEAS") or\
           (other.status == "FEAS" and self.status == "OPT"):
            return True

        if self.bestsol < other.bestsol:
            return True
        
        if self.bestsol == other.bestsol and self.cputime < other.cputime:
            return True

        return False


def read_results(filename):
    solver_names = []
    rows = []
    with open(filename, "rt") as f:
        reader = csv.DictReader(f, delimiter=" ")

        fieldnames = reader.fieldnames
        for x in fieldnames:
            if x != filename_column and x not in probstat_columns:
                solver_name = x
                solver_name = solver_name.replace(bestsol_postfix, "")
                solver_name = solver_name.replace(cputime_postfix, "")
                solver_name = solver_name.replace(status_postfix, "")
                solver_name = solver_name.replace(bestbound_postfix, "")
                solver_name = solver_name.replace(nbnodes_postfix, "")
                if solver_name not in solver_names:
                    solver_names.append(solver_name)

        for row in reader:
            problem = row[filename_column]
            stats = dict((name, int(row[name])) for name in probstat_columns)

            row_results = {}
            for solver_name in solver_names:
                bestsol = row["%s%s" % (solver_name, bestsol_postfix)]
                cputime = row["%s%s" % (solver_name, cputime_postfix)]
                status = row["%s%s" % (solver_name, status_postfix)]
                bestbound = row["%s%s" % (solver_name, bestbound_postfix)]
                nbnodes = row["%s%s" % (solver_name, nbnodes_postfix)]

                res = SolverResult(bestsol, cputime, status, bestbound, nbnodes)
                row_results[solver_name] = res

            best_result = min(row_results.values())
            rows.append((problem, stats, row_results, best_result))

    return solver_names, rows


# ===================== CACTUS =====================

def compute_cactus_data(solver_names, rows):
    data = {}

    for solver in solver_names:
        pairs = []

        for problem, _, row_results, _ in rows:
            res = row_results[solver]

            if res.is_opt():
                try:
                    t = float(res.cputime)
                    if t >= 0:
                        pairs.append((t, problem))
                except:
                    pass

        pairs.sort(key=lambda x: x[0])
        data[solver] = pairs

    return data


def cactus_plot_div(solver_names, rows):
    cactus_data = compute_cactus_data(solver_names, rows)

    traces = []

    for solver in solver_names:
        pairs = cactus_data[solver]

        times = [p[0] for p in pairs]
        problems = [p[1] for p in pairs]
        x = range(1, len(times) + 1)

        traces.append({
            "x": list(x),
            "y": times,
            "mode": "lines+markers",
            "name": "%s [%d solved]" % (solver, len(times)),
            "text": problems,
            "hovertemplate":
                "Solver: " + solver + "<br>" +
                "Problem: %{text}<br>" +
                "Solved: %{x}<br>" +
                "Time: %{y:.3f}s<br>" +
                "<extra></extra>"
        })

    checkbox_html = "".join(
        "<label><input type='checkbox' checked onchange='filterAll()' value='%s'> %s</label><br>"
        % (s, s)
        for s in solver_names
    )

    layout = {
        "title": "Cactus Plot",
        "xaxis": {"title": "Solved Instances"},
        "yaxis": {"title": "CPU Time (s)"}
    }

    return """
<div>%s</div>
<div id="cactus_plot" style="width:70%%;height:600px;"></div>

<script>
var data = %s;
var layout = %s;
var all_solvers = %s;

Plotly.newPlot('cactus_plot', data, layout);

function filterAll() {

    var checked = [];
    var inputs = document.querySelectorAll("input[type=checkbox]");

    for (var i = 0; i < inputs.length; i++) {
        if (inputs[i].checked) checked.push(inputs[i].value);
    }

    // Plot
    var vis = [];
    for (var i = 0; i < data.length; i++) {
        var name = data[i].name.split(" ")[0];
        vis.push(checked.indexOf(name) !== -1);
    }

    Plotly.restyle('cactus_plot', {"visible": vis});

    // Table
    for (var i = 0; i < all_solvers.length; i++) {
        var solver = all_solvers[i];
        var visible = checked.indexOf(solver) !== -1;

        var elems = document.querySelectorAll(".solver_" + solver);

        for (var j = 0; j < elems.length; j++) {
            elems[j].style.display = visible ? "" : "none";
        }
    }
}
</script>
""" % (checkbox_html, json.dumps(traces), json.dumps(layout), json.dumps(solver_names))


# ===================== HTML =====================

def format_stats(stats):
    ret = "<table class='stat'>"
    for p in probstat_columns:
        ret += "<tr><td class='title'>%s:</td><td class='value'>%d</td></tr>" % (p, stats[p])
    ret += "</table>"
    return ret


def format_result(res):
    return """<table class="result">
<tr><td class='title'>S:</td><td class='value'>%s</td></tr>
<tr><td class='title'>O:</td><td class='value'>%s</td></tr>
<tr><td class='title'>T:</td><td class='value'>%s</td></tr>
<tr><td class='title'>B:</td><td class='value'>%s</td></tr>
<tr><td class='title'>N:</td><td class='value'>%s</td></tr>
</table>""" % (res.status, res.bestsol_text, res.cputime_text, res.bestbound, res.nbnodes)

def html_legend(shading):
    shading_html = ""
    if shading:
        shading_html = """<tr><td style="background-color: rgba(176,255,0,0.5)">Text</td><td>Non-optimal solutions are shaded by ratio to the best.</td></tr>"""

    return """
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
<tr><td class='title'>T</td><td>
Time in seconds<br/>
</td></tr>


</table><br>

<table class="resultstable">
<tr><td class="%s">Text</td><td>Optimal solution with the best CPU time</td></tr>
<tr><td class="%s">Text</td><td>Optimal solution within time limit</td></tr>
%s
<tr><td class="%s">Text</td><td>Time out</td></tr>
<tr><td class="%s">Text</td><td>Error</td></tr>
</table>
<br/>
""" % (opt_best_class, opt_ok_class, shading_html, timed_out_class, err_class)


def html_header():
    return """<html>
<head>
<title>%s</title>
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
<style>
.resultstable, .resultstable th, .resultstable td {
    border: 1px solid black;
}
.resultstable td { padding: 4px; }

.stat, .result { width: 100%%; }

.value { text-align: right; }

.%s { background-color: #FFDF7F; }
.%s { background-color: #00FF00; }
.%s { background-color: #AFFF00; }
.%s { background-color: #FFAFAF; }

</style>
</head>
<body>
""" % (page_title, timed_out_class, opt_best_class, opt_ok_class, err_class)


def html_footer():
    return "</body></html>"


# ===================== MAIN HTML =====================

def format_html(solver_names, rows, out_f=sys.stdout, header_interval=sys.maxint, shading=True):

    solver_headers = "".join(
        "<th class='solver_%s'>%s</th>" % (s, s)
        for s in solver_names
    )

    table_header = "<table class='resultstable'>"
    table_header_row = "<tr><th>%s</th><th>Stats</th><th>Best Solver</th>%s</tr>" % (
        filename_column, solver_headers
    )

    table_footer = "</table>"

    print >> out_f, html_header()

    print >> out_f, "<h2>Cactus Plot</h2>"
    print >> out_f, cactus_plot_div(solver_names, rows)
   
    print >> out_f, html_legend(shading)
    print >> out_f, table_header

    for i, row in enumerate(rows):
        problem, stats, row_results, best_result = row

        if i % header_interval == 0:
            print >> out_f, table_header_row

        print >> out_f, "<tr><td>%s</td><td>%s</td><td>%s</td>" % (
            problem,
            format_stats(stats),
            format_result(best_result)
        )

        for solver_name in solver_names:
            res = row_results[solver_name]
            tdclass = ""

            if res.is_err():
                tdclass = err_class
            elif res.timed_out():
                tdclass = timed_out_class
            elif res is best_result:
                tdclass = opt_best_class
            elif res.is_opt():
                tdclass = opt_ok_class

            if shading and not tdclass and res.status.startswith("FEAS"):
                try:
                    d = res.get_ratio_to_best(best_result)
                    tdclass = "\" style=\"background-color: rgba(176,255,0,%.4f);" % d
                except:
                    pass

            print >> out_f, "<td class=\"solver_%s %s\">%s</td>" % (
                solver_name,
                tdclass,
                format_result(res)
            )

        print >> out_f, "</tr>"

    print >> out_f, table_footer
    print >> out_f, html_footer()


# ===================== MAIN =====================

def main():
    solver_names, rows = read_results("results.csv")

    f = open("results.html", "w")
    format_html(solver_names, rows, out_f=f)
    f.close()

    print "Generated: results.html"


if __name__ == '__main__':
    main()