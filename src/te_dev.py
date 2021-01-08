#%%
import os
import csv
from ortools.sat.python import cp_model


class PartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, vars, n_t, n_w, n_show, verbose=True):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._vars = vars
        self._n_t = n_t
        self._n_w = n_w
        self._sols = set(range(n_show))
        self._n_sol = 0
        self._verbose = verbose

    def on_solution_callback(self):
        self._n_sol += 1
        if self._verbose:
            if self._n_sol in self._sols:
                print('Solution %i' % self._n_sol)
                for t1 in range(self._n_t):
                    for t2 in range(self._n_t):
                        if t1 != t2:
                            print(
                                'Team %i plays team %i in week %i' %
                                (t1, t2, self.Value(vars[(t1, t2)]))
                            )

        for i in self._sols:
            sols = self.__getter(solver)
            line = ', '.join(['%s=%i' % (k, v) for (k, v) in row.items()])
            print(line)
            # print(f'solution: {self._n_sol}')

    def n_sol(self):
        return self._n_sol

    def get_csv_writer(self, csvname):
        self.__csvfile = open(csvname, 'w', newline='')
        fieldnames = ['tm1', 'tm2', 'wk']
        writer = csv.DictWriter(self.__csvfile, fieldnames=fieldnames)
        writer.writeheader()
        return writer


#%%
n_t = 3
n_w = n_t  # - 1
model = cp_model.CpModel()

#%%
vars = {}
for t1 in range(n_t):
    for t2 in range(n_t):
        if t1 != t2:
            vars[(t1, t2)] = model.NewIntVar(1, n_w, f'{t1:02}_{t2:02}')
for t1 in range(n_t):
    for t2 in range(n_t):
        if t1 != t2:
            model.Add(vars[(t1, t2)] == vars[(t2, t1)])

# Each team can only play in 1 game each week
for t1 in range(n_t):
    model.AddAllDifferent([vars[(t1, t2)] for t2 in range(n_t) if t1 != t2])

for t2 in range(n_t):
    model.AddAllDifferent([vars[(t1, t2)] for t1 in range(n_t) if t1 != t2])

# %%
# Creates the solver and solve.
solver = cp_model.CpSolver()
solution_printer = PartialSolutionPrinter(vars, n_t, n_w, range(6))
status = solver.SearchForAllSolutions(model, solution_printer)

print('Solve status: %s' % solver.StatusName(status))
print('Statistics')
print('  - conflicts : %i' % solver.NumConflicts())
print('  - branches  : %i' % solver.NumBranches())
print('  - wall time : %f s' % solver.WallTime())
print('  - solutions found: %i' % solution_printer.n_sol())
# %%
