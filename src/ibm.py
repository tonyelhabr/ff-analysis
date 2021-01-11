# https://notebook.community/IBMDecisionOptimization/docplex-examples/examples/cp/jupyter/sports_scheduling
#%%
from docplex.cp.model import *
from docplex.cp.config import context
context.solver.agent = 'local'
context.solver.local.execfile = 'C:\\Program Files\\IBM\\ILOG\\CPLEX_Studio_Community201\\cpoptimizer\\bin\\x64_win64\\cpoptimizer.exe'
import numpy as np
import pandas as pd

n_team = 10
idx_tms = range(n_team)
n_h2h_gm = 1
n_wk = n_h2h_gm * (n_team - 1)
n_sec_solve = 25

#%%
tms = ['tm' + str(tm + 1).zfill(2) for tm in range(n_team)]
tms
#%%
prob = CpoModel(name='problem')

#%%
# decision variables: team t1 vs team t2 in gm i of n_h2h_gm
vars = {}
for i in range(n_h2h_gm):
    for t1 in idx_tms:
        for t2 in idx_tms:
            if t1 != t2:
                vars[(t1, t2, i)] = integer_var(
                    1, n_wk, name='tm1_{}_tm2_{}_gm_{}'.format(t1, t2, i)
                )
# %%
# If team t1 plays team t2 in week w, then team t2 must play team t1 in week w.
for t1 in idx_tms:
    for t2 in idx_tms:
        if t2 != t1:
            for i in range(n_h2h_gm):
                prob.add(vars[(t1, t2, i)] == vars[(t2, t1, i)])

# for a given week w, the values of play[t][w] must be unique for all teams t.
for t1 in idx_tms:
    prob.add(
        all_diff(
            [
                vars[(t1, t2, i)] for t2 in idx_tms if t2 != t1
                for i in range(n_h2h_gm)
            ]
        )
    )

#%%
# objective
obj = []
for t1 in idx_tms:
    for t2 in idx_tms:
        if t1 != t2:
            for i in range(n_h2h_gm):
                obj.append(vars[(t1, t2, i)])
prob.add(maximize(sum(obj)))

#%%
sol = prob.solve(TimeLimit=n_sec_solve)
# sol = prob.  (TimeLimit=n_sec_solve)

#%%
sol.print_solution()
#%%
prob.export_model('model')

# %%
if sol:
    abb = [list() for i in range(n_wk)]
    for t1 in idx_tms:
        for t2 in idx_tms:
            if t1 != t2:
                for i in range(n_h2h_gm):
                    x = abb[sol.get_value(vars[(t1, t2, i)]) - 1]
                    x.append((tms[t1], tms[t2]))

    gms = [(wk, t1, t2) for wk in range(n_wk) for (t1, t2) in abb[wk]]
    gms_df = pd.DataFrame(gms)

#%%
gms_df
# %%
gms_df.to_csv('gms2.csv', index=False)
# %%
