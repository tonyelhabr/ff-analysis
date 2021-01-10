from __future__ import print_function
from ortools.sat.python import cp_model


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, games, n_team, n_show=6):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._games = games
        self._n_team = n_team
        self._n_show = n_show
        self._n_sol = 0

    def on_solution_callback(self):
        self._n_sol += 1
        # if self._n_sol in self._sols:
        if self._n_sol <= self._n_show:
            print(f'Solution {self._n_sol}.')
            for g in self._games:
                # v = self._games(g)
                # print(self._games.keys())
                # print(self._games.values())
                # print('%s=%i' % (g, v), end=' ')
                # print(self.Value(g))
                # print(g)
                # print(self._games.keys())
                pass

    def get_n_sol(self):
        return self._n_sol
