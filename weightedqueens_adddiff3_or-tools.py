import sys
import random
import time
from ortools.sat.python import cp_model

random.seed(123456789)
for N in [4,6,8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30] :
    
    model = cp_model.CpModel()
    
    # Variables
    Q = [model.NewIntVar(0, N - 1, f'Q[{i}]') for i in range(N)]
    Qu = [model.NewIntVar(0, 2 * N - 1, f'Qu[{i}]') for i in range(N)]
    Ql = [model.NewIntVar(0, 2 * N - 1, f'Ql[{i}]') for i in range(N)]
    
    for i in range(N):
        model.Add(Qu[i] == Q[i] + i)
        model.Add(Ql[i] == Q[i] - i + (N - 1))
    
    model.AddAllDifferent(Q)
    model.AddAllDifferent(Qu)
    model.AddAllDifferent(Ql)
    
    # Coûts unaires aléatoires
    cost_terms = []
    for i in range(N):
        costs = [random.randint(1, N) for _ in range(N)]
        for val in range(N):
            b = model.NewBoolVar(f'Q[{i}] == {val}')
            model.Add(Q[i] == val).OnlyEnforceIf(b)
            model.Add(Q[i] != val).OnlyEnforceIf(b.Not())
            cost_terms.append(costs[val] * b)
    
    model.Minimize(sum(cost_terms))
    
    # Résolution
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 300
    solver.parameters.num_search_workers = 1
    start_time = time.time()
    status = solver.Solve(model)
    end_time = time.time()
    elapsed = end_time - start_time
    
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        print(f"N: {N} Optimum: {int(solver.ObjectiveValue())} time: {elapsed:.3f} seconds.")
    else:
        print("No solution found.")