#%%
import sys
from ortools.constraint_solver import pywrapcp

#%%
n_tm = 4
solver = pywrapcp.Solver('schedule')
# Creates the variables.
# The array index is the column, and the value is the row.
tms = [
    solver.IntVar(0, n_tm - 1, f'tm{str(i).zfill(2)}') for i in range(n_tm)
]

# All rows must be different.
solver.Add(solver.AllDifferent(tms))
[solver.Add(tms[i] == i)  for i in range(n_tm)]

#%%
import os
os.sched_getaffinity()

#%%



# All columns must be different because the indices of tms are all different.

# No two tms can be on the same diagonal.
solver.Add(solver.AllDifferent([tms[i] + i for i in range(n_tm)]))
solver.Add(solver.AllDifferent([tms[i] - i for i in range(n_tm)]))

db = solver.Phase(
    tms, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE
)
solver.NewSearch(db)

# Iterates through the solutions, displaying each.
num_solutions = 0

while solver.NextSolution():
# Displays the solution just computed.
for i in range(n_tm):
    for j in range(n_tm):
        if tms[j].Value() == i:
            # There is a queen in column j, row i.
            print("Q", end=" ")
        else:
            print("_", end=" ")
    print()
print()
num_solutions += 1

solver.EndSearch()

print()
print("Solutions found:", num_solutions)
print("Time:", solver.WallTime(), "ms")
# %%
