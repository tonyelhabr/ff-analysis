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
            for team1 in range(self._n_team):
                # print(f'team 1: {team1}')
                for team2 in range(self._n_team):
                    # print(f'team 2: {team2}')
                    if team1 != team2:
                        # print(f'Team {team1 + 1} plays team {team2 + 1} in week {self.Value(self._games[(team1 + 1, team2 + 1)])}')
                        k = str(team1) + '_' + str(team2)
                        # v = self._games[k]
                        if k in self._games.keys():
                            print(f'team 1: {team1}')
                            print(f'team 2: {team2}')
                            print(k)
                            # print(self.Value(self._games[['1_2']]))
                        # print(v)
                        # print(f'week: {self.Value(v)}')
                        # for k, v in self._games.items():
                        #     # print(f'k, v = {k, v}')
                        #     print(f'Value = {self.Value(self._games[k])}')
                        #     # print('{self.Value(self._games[team1 + 1, team2 + 1)])}')
                        #     # pass

    def get_n_sol(self):
        return self._n_sol
