import argparse
import os
import csv
import re
from functools import partial
from ortools.sat.python import cp_model


class SolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(
        self,
        games,
        n_t,
        n_w,
        getter,
        n_show=2,
        limit=100,
        path_csv='output.csv',
        verbose=True
    ):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._games = games
        self._getter = getter
        self._n_t = n_t
        self._n_w = n_w
        self._n_show = n_show
        self._sols = set(range(n_show))
        self._n_sol = 0
        self._limit = limit
        self._verbose = verbose
        self._writer = self.get_csv_writer(path_csv)

    def on_solution_callback(self):
        self._n_sol += 1
        if self._n_sol >= self._limit:
            print(f'Stopping search after {self._limit} solutions.')
            self.StopSearch()

        # if self._verbose:
        if self._n_sol in self._sols and self._n_sol <= self._n_show and self._n_sol <= self._limit:
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
            # line = ', '.join(['%s=%i' % (k, v) for (k, v) in row.items()])
            # line = ', '.join([f'{k}={str(v)}' for (k, v) in row.items()])
            # line = f'idx={str(i+1)}, ' + line
            # print(line)
            # print(f'solution: {self._n_sol}')
            self._writer.writerow(row)

        # self._writer.writerow({})

    def n_sol(self):
        return self._n_sol

    def get_csv_writer(self, path):
        self._path_csv = open(path, 'w', newline='')
        fields = ['idx', 'tm1', 'tm2', 'wk']
        writer = csv.DictWriter(self._path_csv, fieldnames=fields)
        writer.writeheader()
        return writer


def coalesce_idx(solver):
    if solver is None:
        return 0
    return solver._n_sol


def get_assigned_games(solver, games):
    assigned_games = [
        {
            'idx': coalesce_idx(solver),
            'tm1': t1,
            'tm2': t2,
            'wk': solver.Value(games[(t1, t2)])
        } for t1, t2 in games.keys()
    ]
    return assigned_games


def check_file_collision(name):
    # check for any existing file
    idx = 1
    match = re.search(r'\.csv', name)
    if not match:
        name += '.csv'

    res = name
    while os.path.exists(res):
        res = re.sub(r'\.csv', '_{}.csv'.format(idx), name)
        idx += 1
    return res


# def csv_dump_results(games, name):

#     path = check_file_collision(name)
#     with open(path, 'w', newline='') as file:
#         fields = ['tm1', 'tm2', 'wk']
#         # fields = ['idx', 'tm1', 'tm2', 'wk']
#         writer = csv.DictWriter(file, fieldnames=fields)

#         writer.writeheader()
#         for row in games:
#             writer.writerow(row)
#         # for i, row in games.items():
#         #     writer.writerow([i, row])
#     return path


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
    # for t in range(n_t):
    #     model.AddAllDifferent([games[(t1, t)] for t1 in range(n_t) if t1 != t])

    return (model, games)


def solution_search_model(
    model,
    games,
    n_t,
    n_w,
    n_show=2,
    limit=100,
    time=None,
    verbose=None,
    name=None
):

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time
    # solver.parameters.log_search_progress = verbose
    printer = SolutionPrinter(
        games=games,
        n_t=n_t,
        n_w=n_w,
        n_show=n_show,
        limit=limit,
        verbose=verbose,
        getter=partial(get_assigned_games, games=games),
        path_csv=check_file_collision(name)
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

    # assigned_games = get_assigned_games(solver=solver, games=games)
    if status != cp_model.OPTIMAL and solver.WallTime() >= time:
        print(f'Solver reached maximum time allowed {time}.')
        print(
            'A better solution might be found by adding more time using the --time command line option'
        )
    # if name:
    #     csv_dump_results(games=assigned_games, name=name)
    return status


def main():
    '''Entry point of the program.'''
    parser = argparse.ArgumentParser(
        description='Solve sports league match play assignment problem.'
    )
    parser.add_argument(
        '--teams',
        type=int,
        dest='n_t',
        # required=True,
        default=10,
        help='Number of teams in the league'
    )
    parser.add_argument(
        '--name',
        type=str,
        dest='name',
        # default='output',
        default=None,
        help='Name of file to dump the team assignments. Default is output'
    )

    parser.add_argument(
        '--all',
        default=True,
        action='store_true',
        help='Whether to find all possible combinations.'
    )

    parser.add_argument(
        '--time',
        type=int,
        dest='time',
        default=6000,
        help='Maximum run time for solver, in seconds. Default is 3 seconds.'
    )

    parser.add_argument(
        '--limit',
        type=int,
        dest='limit',
        default=100000000,
        help=
        'Maximum number of solutions to return if `all=True`. Default is 100.'
    )

    parser.add_argument(
        '--show',
        type=int,
        dest='n_show',
        default=2,
        help='How many solutions to print out if `all=True`. Default is 2.'
    )

    parser.add_argument(
        '--verbose',
        default=False,
        action='store_true',
        help='Turn on some print statements.'
    )
    args = parser.parse_args()
    n_t = args.n_t
    n_w = n_t - 1
    time = args.time
    limit = args.limit
    name = args.name
    if name is None:
        name = f'output-n_tm={n_t}-time={time}-limit={limit}'
    verbose = args.verbose
    (model, games) = model_games(n_t=n_t, n_w=n_w)
    (solver, status) = solution_search_model(
        model=model,
        games=games,
        n_t=n_t,
        n_w=n_w,
        n_show=args.n_show,
        limit=limit,
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