import argparse
import os
import csv
import re
from ortools.sat.python import cp_model


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(
        self,
        games,
        n_t,
        n_w,
        n_show,
        getter,
        path_csv='output.csv',
        verbose=True
    ):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._games = games
        self._getter = getter
        self._n_t = n_t
        self._n_w = n_w
        self._sols = set(range(n_show))
        self._n_sol = 0
        self._verbose = verbose
        self._writer = self.get_csv_writer(path_csv)

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
                                (t1, t2, self.Value(self._games[(t1, t2)]))
                            )

        sol = self._getter(solver=self, games=self._games)
        for row in sol:
            line = ', '.join(['%s=%i' % (k, v) for (k, v) in row.items()])
            # print(line)
            # print(f'solution: {self._n_sol}')
            self._writer.writerow(row)

    def n_sol(self):
        return self._n_sol

    def get_csv_writer(self, path):
        self._path_csv = open(path, 'w', newline='')
        fieldnames = ['tm1', 'tm2', 'wk']
        writer = csv.DictWriter(self._path_csv, fieldnames=fieldnames)
        writer.writeheader()
        return writer


def get_assigned_games(solver, games):
    # can't figure how to increment the game number inside the day
    # here, but I guess it is probably wrong anyway
    assigned_games = list()
    # for t1, t2 in games:

    # assigned_games = [
    #     {
    #         'tm1': t1 + 1,
    #         'tm2': t2 + 1,
    #         'wk':  x
    #     } for (t1, t2) in games
    # ]
    return list(assigned_games)


def check_file_collision(name):
    # check for any existing file
    idx = 1
    name += '.csv'
    while os.path.exists(name):
        name = re.sub(r'\.csv', '_{}.csv'.format(idx), name)
        idx += 1
    return name


def csv_dump_results(games, csv_name):

    checkname = check_file_collision(csv_name)
    with open(checkname, 'w', newline='') as csvfile:
        fieldnames = ['tm1', 'tm2', 'wk']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for row in games:
            writer.writerow(row)


def model_games(n_t=3, n_w=None):
    if n_w is None:
        n_w = n_t

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

    # # Don't think i even need this
    for t in range(n_t):
        model.AddAllDifferent([games[(t1, t)] for t1 in range(n_t) if t1 != t])

    return (model, games)


def solution_search_model(
    model, games, n_t, n_w, n_show=2, time=None, verbose=None, name=None
):

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time
    solver.parameters.log_search_progress = verbose
    printer = SolutionPrinter(
        games=games,
        n_t=n_t,
        n_w=n_w,
        n_show=n_show,
        verbose=verbose,
        getter=check_file_collision(name)
    )
    status = solver.SearchForAllSolutions(model, printer)

    print('Solve status: %s' % solver.StatusName(status))
    print('Statistics')
    print('  - conflicts : %i' % solver.NumConflicts())
    print('  - branches  : %i' % solver.NumBranches())
    print('  - wall time : %f s' % solver.WallTime())
    print('  - solutions found: %i' % printer.n_sol())
    return (solver, status)


def report_results(solver, status, games, time, name=None):

    if status == cp_model.INFEASIBLE:
        return status

    if status == cp_model.UNKNOWN:
        print('Not enough time allowed to compute a solution')
        print('Add more time using the --time command line option')
        return status

    print('Optimal objective value: %i' % solver.ObjectiveValue())

    assigned_games = get_assigned_games(solver, games)
    if status != cp_model.OPTIMAL and solver.WallTime() >= time:
        print(f'Solver reached maximum time allowed {time}.')
        print(
            'A better solution might be found by adding more time using the --time command line option'
        )
    if name and not cp_model.INFEASIBLE:
        csv_dump_results(assigned_games, name)


def main():
    '''Entry point of the program.'''
    parser = argparse.ArgumentParser(
        description='Solve sports league match play assignment problem.'
    )
    parser.add_argument(
        '-t,--teams',
        type=int,
        dest='n_t',
        # required=True,
        default=3,
        help='Number of teams in the league'
    )
    parser.add_argument(
        '--name',
        type=str,
        dest='name',
        default='output',
        help='Name of file to dump the team assignments. Default is output'
    )

    parser.add_argument(
        '--time',
        type=int,
        dest='time',
        default=3,
        help='Maximum run time for solver, in seconds. Default is 3 seconds.'
    )
    parser.add_argument(
        '--verbose', action='store_true', help='Turn on some print statements.'
    )
    args = parser.parse_args()
    n_t = args.n_t
    n_w = n_t
    time = args.time
    name = args.name
    verbose = args.verbose
    (model, games) = model_games(n_t=n_t, n_w=n_w)
    (solver, status) = solution_search_model(
        model=model,
        games=games,
        n_t=n_t,
        n_w=n_w,
        time=time,
        verbose=verbose,
        name=name
    )
    report_results(
        solver=solver, status=status, games=games, time=time, name=name
    )


if __name__ == '__main__':
    main()
    print('done')