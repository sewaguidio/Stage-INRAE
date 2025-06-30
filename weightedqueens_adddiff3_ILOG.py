import sys
import random
import time
from docplex.cp.model import*

context.params.set_attribute('Presolve', 'Off')
context.params.set_attribute('Workers', 1)
random.seed(123456789)
for N in [4,6,8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30] :
    
    model = CpoModel()
    
    # Variables
    Q = [model.integer_var(0, N - 1, f'Q_{i}') for i in range(N)]
    Qu = [model.integer_var(0, 2 * N - 1, f'Qu_{i}') for i in range(N)]
    Ql = [model.integer_var(0, 2 * N - 1, f'Ql_{i}') for i in range(N)]
    
    # Contraintes diagonales
    for i in range(N):
        model.add(Qu[i] == Q[i] + i)
        model.add(Ql[i] == Q[i] - i + (N - 1))
    
    # Contraintes AllDifferent
    model.add(model.all_diff(Q))
    model.add(model.all_diff(Qu))
    model.add(model.all_diff(Ql))
    
    # Coûts unaires aléatoires
    cost_terms = []
    for i in range(N):
        costs = [random.randint(1, N) for _ in range(N)]
        cost_terms.append(model.element(costs, Q[i]))
    
    # Objectif
    model.add(model.minimize(model.sum(cost_terms)))
    
    # Résolution
    start_time = time.time()
    sol = model.solve(LogVerbosity='Quiet', TimeLimit=300)
    end_time = time.time()
    elapsed = end_time - start_time
    
    # Infos internes
    if sol:
        cost = int(sol.get_objective_values()[0])
    
        print(f"N: {N} Optimum: {cost} time: {elapsed:.3f} seconds.")
    else:
        print("No solution found.")