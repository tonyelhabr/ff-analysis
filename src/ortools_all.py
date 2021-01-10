#%%
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
            print(f'Schedule {self._n_sol}.')
            for team1 in range(self._n_team):
                for team2 in range(self._n_team):
                    if team1 != team2:
                        print(
                            f'Team {team1 + 1} vs. Team {team2 + 1} in Round {self.Value(self._games[(team1, team2)])}'
                        )

    def get_n_sol(self):
        return self._n_sol


n_team = 4
n_w = n_team - 1
model = cp_model.CpModel()
games = {}
for team1 in range(n_team):
    for team2 in range(n_team):
        if team1 != team2:
            games[(team1, team2)] = model.NewIntVar(1, n_w, f'{team1:02}_{team2:02}')

for team1 in range(n_team):
    for team2 in range(n_team):
        if team1 != team2:
            model.Add(games[(team1, team2)] == games[(team2, team1)])


# Each team can only play in 1 game each week
for t in range(n_team):
    model.AddAllDifferent(
        [games[(t, team2)] for team2 in range(n_team) if t != team2]
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

# %%
