# https://notebook.community/IBMDecisionOptimization/docplex-examples/examples/cp/jupyter/sports_scheduling
#%%
from docplex.cp.model import *
import numpy as np
import pandas as pd

NB_TEAMS = 10
TEAMS = range(NB_TEAMS)
NUMBER_OF_MATCHES_TO_PLAY = 1
NB_WEEKS = 9
#%%

TEAM_DIV1 = ['Team ' + str(tm + 1) for tm in range(NB_TEAMS)]
TEAM_DIV1
#%%
mdl = CpoModel(name="SportsScheduling")

# Variables of the model
plays = {}
for i in range(NUMBER_OF_MATCHES_TO_PLAY):
    for t1 in TEAMS:
        for t2 in TEAMS:
            if t1 != t2:
                plays[(t1, t2, i)] = integer_var(
                    1,
                    NB_WEEKS,
                    name="team1_{}_team2_{}_match_{}".format(t1, t2, i)
                )
# %%
# Constraints of the model
for t1 in TEAMS:
    for t2 in TEAMS:
        if t2 != t1:
            for i in range(NUMBER_OF_MATCHES_TO_PLAY):
                mdl.add(plays[(t1, t2, i)] == plays[(t2, t1, i)])
# %%
for t1 in TEAMS:
    mdl.add(
        all_diff(
            [
                plays[(t1, t2, i)] for t2 in TEAMS if t2 != t1
                for i in range(NUMBER_OF_MATCHES_TO_PLAY)
            ]
        )
    )


def intra_divisional_pair(t1, t2):
    return 1


# # Some intradivisional games should be in the first half
# mdl.add(sum([intra_divisional_pair(t1, t2) * allowed_assignments(plays[(t1, t2, i)], FIRST_HALF_WEEKS)
#              for t1 in TEAMS for t2 in [a for a in TEAMS if a != t1]
#              for i in range(NUMBER_OF_MATCHES_TO_PLAY)]) >= NB_FIRST_HALF_WEEKS)

#%%
sm = []
for t1 in TEAMS:
    for t2 in TEAMS:
        if t1 != t2:
            if not intra_divisional_pair(t1, t2):
                for i in range(NUMBER_OF_MATCHES_TO_PLAY):
                    sm.append(plays[(t1, t2, i)])
mdl.add(maximize(sum(sm)))

#%%
n = 25
from docplex.cp.config import context
context.solver.agent = 'local'
context.solver.local.execfile = 'C:\\Program Files\\IBM\\ILOG\\CPLEX_Studio_Community201\\cpoptimizer\\bin\\x64_win64\\cpoptimizer.exe'
msol = mdl.solve(TimeLimit=n)

# %%
if msol:
    abb = [list() for i in range(NB_WEEKS)]
    for t1 in TEAMS:
        for t2 in TEAMS:
            if t1 != t2:
                for i in range(NUMBER_OF_MATCHES_TO_PLAY):
                    x = abb[msol.get_value(plays[(t1, t2, i)]) - 1]
                    x.append((TEAM_DIV1[t1], TEAM_DIV1[t2]))

    matches = [
        (week, t1, t2, where, intra) for week in range(NB_WEEKS)
        for (t1, t2, where, intra) in abb[week]
    ]
    matches_bd = pd.DataFrame(matches)

#%%
matches_bd
# %%
matches_bd.to_csv('games.csv', index=False)
# %%
