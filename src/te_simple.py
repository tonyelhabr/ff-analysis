#%%
from __future__ import print_function
from ortools.sat.python import cp_model


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, games, n_team, n_show=None):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._games = games
        self._n_show = n_show
        self._n_team = n_team
        self._n_sol = 0

    def on_solution_callback(self):
        self._n_sol += 1
        if self._n_show is None or self._n_sol <= self._n_show:
            print(f'Solution {self._n_sol}.')
            for team1 in range(self._n_team):
                for team2 in range(self._n_team):
                    if team1 != team2:
                        print(self.Value().keys())
                        print(
                            f'Team {team1 + 1} plays team {team2 + 1} in week {self.Value(self._games[(team1, team2)])}'
                        )

    def get_n_sol(self):
        return self._n_sol


n_team = 6
n_week = n_team - 1
model = cp_model.CpModel()
games = {}
for team1 in range(n_team):
    for team2 in range(n_team):
        if team1 != team2:
            games[(team1, team2)
                 ] = model.NewIntVar(1, n_week, f'{team1:02}_{team2:02}')

for team1 in range(n_team):
    for team2 in range(n_team):
        if team1 != team2:
            model.Add(games[(team1, team2)] == games[(team2, team1)])

for team in range(n_team):
    model.AddAllDifferent(
        [games[(team, team2)] for team2 in range(n_team) if team != team2]
    )

for team in range(n_team):
    model.AddAllDifferent(
        [games[(team1, team)] for team1 in range(n_team) if team != team1]
    )

solver = cp_model.CpSolver()
solution_printer = SolutionPrinter(games, n_team=n_team, n_show=1)
status = solver.SearchForAllSolutions(model, solution_printer)

print(f'Solve status: {solver.StatusName(status)}')
print('Statistics')
print(f'  - conflicts : {solver.NumConflicts()}')
print(f'  - branches  : {solver.NumBranches()}')
print(f'  - wall time : {solver.WallTime()} s')
print(f'  - solutions found: {solution_printer.get_n_sol()}')
#%%
# %%
