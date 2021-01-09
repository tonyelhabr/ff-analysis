#%%
from ortools.sat.python import cp_model


class PartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, games, n_t, n_w, sols):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._games = games
        self._sols = set(sols)
        self._n_t = n_t
        self._n_w = n_w
        self._n_sol = 0

    def on_solution_callback(self):
        self._n_sol += 1
        if self._n_sol in self._sols:
            print('Solution %i' % self._n_sol)
            for t1 in range(self._n_t):
                for t2 in range(self._n_t):
                    if t1 != t2:
                        print(
                            'Team %i plays team %i in week %i' %
                            (t1, t2, self.Value(games[(t1, t2)]))
                        )

    def n_sol(self):
        return self._n_sol


#%%
n_t = 4
n_w = n_t - 1
model = cp_model.CpModel()
games = {}
for t1 in range(n_t):
    for t2 in range(n_t):
        if t1 != t2:
            games[(t1, t2)] = model.NewIntVar(1, n_w, f'{t1:02}_{t2:02}')

for t1 in range(n_t):
    for t2 in range(n_t):
        if t1 != t2:
            model.Add(games[(t1, t2)] == games[(t2, t1)])

# Each team can only play in 1 game each week
for t in range(n_t):
    model.AddAllDifferent([games[(t, t2)] for t2 in range(n_t) if t != t2])

for t in range(n_t):
    model.AddAllDifferent([games[(t1, t)] for t1 in range(n_t) if t1 != t])

# %%
# Creates the solver and solve.
solver = cp_model.CpSolver()
solution_printer = PartialSolutionPrinter(games, n_t, n_w, range(6))
status = solver.SearchForAllSolutions(model, solution_printer)

#%%
status

#%%
print('Solve status: %s' % solver.StatusName(status))
print('Statistics')
print('  - conflicts : %i' % solver.NumConflicts())
print('  - branches  : %i' % solver.NumBranches())
print('  - wall time : %f s' % solver.WallTime())
print('  - solutions found: %i' % solution_printer.n_sol())
# %%