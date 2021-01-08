# Reference: https://gist.githubusercontent.com/brianhuey/bce4c495c9935a9f22c24ccbdd04aab5/raw/811178bd53581654aadd4e4c44bc545493b5ac3e/sports_scheduling.py
from ortools.constraint_solver import pywrapcp
# Python Implementation of
# https://github.com/google/or-tools/blob/master/examples/cpp/sports_scheduling.cc
# By Brian Huey
# Sports scheduling problem.
#
# We want to solve the problem of scheduling of team matches in a
# double round robin tournament.  Given a number of teams, we want
# each team to encounter all other teams, twice, once at home, and
# once away. Furthermore, you cannot meet the same team twice in the
# same half-season.
#
# Finally, there are constraints on the sequence of home or aways:
#   - You cannot have 3 consecutive homes or three consecutive aways.
#   - A break is a sequence of two homes or two aways, the overall objective
#     of the optimization problem is to minimize the total number of breaks.
#
# We model this problem with three matrices of variables, each with
# num_teams rows and 2*(num_teams - 1) columns: the var [i][j]
# corresponds to the match of team #i at day #j. There are
# 2*(num_teams - 1) columns because each team meets num_teams - 1
# opponents twice.

# - The 'opponent' var [i][j] is the index of the opposing team.
# - The 'home_away' var [i][j] is a boolean: 1 for 'playing away',
#   0 for 'playing at home'.
# - The 'opponent_and_home_away' var [i][j] is the 'opponent' var [i][j] +
#   num_teams * the 'home_away' var [i][j].
# This aggregated variable will be useful to state constraints of the model
# and to do search on it.
#
# We use an original approch in this model as most of the constraints will
# be pre-computed and asserted using an AllowedAssignment constraint (see
# Solver::MakeAllowedAssignment() in constraint_solver.h).
# In particular:
#   - Each day, we have a perfect matching between teams
#     (A meets B <=> B meets A, and A is at home <=> B is away).
#     A cannot meet itself.
#   - For each team, over the length of the tournament, we have constraints
#     on the sequence of home-aways. We will precompute all possible sequences
#     of home_aways, as well as the corresponding number of breaks for that
#     team.
#   - For a given team and a given day, the link between the opponent var,
#     the home_away var and the aggregated var (see third matrix of variables)
#     is also maintained using a AllowedAssignment constraint.
#

num_teams = 4
time_limit = 20000
run_all_heuristics = True
heuristic_period = 30
restart_log_size = 8.0


def computeOneDayOneTeamTuples(num_teams):
    """ Computes the tuple set that links opponents, home_away and
        signed_opponents on a single day for a single team.
        Input: num_teams int
        Output: list of length 3 tuples
    """
    tuples = []
    for home_away in [0, 1]:
        for opponent in range(num_teams):
            tuples.append(
                (opponent, home_away, opponent + home_away * num_teams)
            )
    return tuples


def addOneDayOneTeamConstraint(
    solver, opponent, home_away, signed_opponent, intra_day_tuples
):
    """ Links tuple set with labels to constraint variables.
        Creates constraints for a given team on a given day.
        Input: solver object, opponent list, home_away list,
               signed_opponent list, intra_day_tuples list of length 3 tuples
        Output: None
    """
    tmp_vars = []
    tmp_vars.append(opponent)
    tmp_vars.append(home_away)
    tmp_vars.append(signed_opponent)
    solver.Add(solver.AllowedAssignments(tmp_vars, intra_day_tuples))


def computeOneDayTuples(num_teams):
    """ Computes all valid combinations of signed_opponent for a single day
        and all teams.
        Input: num_teams int
        Returns: list of length n lists of length t ints where n is number of
                 solutions and t is number of teams and ints correspond to the
                 team
    """
    day_tuples = []
    solver = pywrapcp.Solver('ComputeOneDayTuples')

    # We create the variables.
    opponents = [
        solver.IntVar(0, num_teams - 1, 'opponent_') for i in range(num_teams)
    ]
    home_aways = [solver.BoolVar('home_away_') for i in range(num_teams)]
    signed_opponents = [
        solver.IntVar(0, 2 * num_teams - 1, 'signed_opponent_')
        for i in range(num_teams)
    ]

    # No teams play twice in a single day
    solver.Add(solver.AllDifferent(opponents))

    # Cannot play against itself
    for i in range(num_teams):
        solver.AddConstraint(opponents[i] != i)

    # Matching constraint (vars[i] == j, vars[j] == i)
    for i in range(num_teams):
        for j in range(num_teams):
            if i != j:
                solver.AddConstraint(
                    solver.IsEqualCstVar(opponents[i], j) ==
                    solver.IsEqualCstVar(opponents[j], i)
                )

    # num_teams/2 teams are home
    solver.Add(solver.SumEquality(home_aways, num_teams / 2))

    # Link signed_opponents, home_away and opponents
    one_day_one_team_tuples = computeOneDayOneTeamTuples(num_teams)
    for team_index in range(num_teams):
        tmp_vars = []
        tmp_vars.append(opponents[team_index])
        tmp_vars.append(home_aways[team_index])
        tmp_vars.append(signed_opponents[team_index])
        solver.Add(solver.AllowedAssignments(tmp_vars, one_day_one_team_tuples))

    # if A meets B at home, B meets A away
    for first_team in range(num_teams):
        first_home_away = home_aways[first_team]
        # Element = home_aways[opponents[first_team]]
        second_home_away = solver.Element(home_aways, opponents[first_team])
        # negation
        reverse_second_home_away = 1 - second_home_away
        solver.AddConstraint(first_home_away == reverse_second_home_away)

    # Search for solutions and fill day_tuples
    db = solver.Phase(
        signed_opponents, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE
    )
    solver.NewSearch(db)
    while solver.NextSolution():
        solution = []
        for i in range(num_teams):
            solution.append(signed_opponents[i].Value())
        day_tuples.append(solution)
    solver.EndSearch()
    print(str(len(day_tuples)) + ' solutions to the one-day matching problem.')
    return day_tuples


def addOneTeamConstraints(
    solver, opponents, home_aways, signed_opponents, home_away_tuples,
    break_var, num_teams
):
    """ Adds all constraints relating to one team and the complete schedule.
        Input: solver object, opponent list, home_away list,
               signed_opponent list, home_away_tuples list of length d tuples
               where d is length of season, break_var IntVar, num_teams int
        Output: None
    """
    half_season = num_teams - 1
    # Each team meet all opponents once by half season
    for half in [0, 1]:
        for team_index in range(num_teams):
            tmp_vars = []
            for day in range(half_season):
                tmp_vars.append(opponents[half * half_season + day])
            solver.Add(solver.AllDifferent(tmp_vars))
    # We meet each opponent once at home and once away per full season.
    for team_index in range(num_teams):
        solver.Add(solver.AllDifferent(signed_opponents))
    # Constraint per team on home_aways
    for i in range(num_teams):
        tmp_vars = list(home_aways)
        tmp_vars.append(break_var)
        solver.Add(solver.AllowedAssignments(tmp_vars, home_away_tuples))


def computeOneTeamHomeAwayTuples(num_teams):
    """ Computes all valid tuples for home_away variables for a single team
        on the full length of the season.
        Input: num_teams int
        Returns n x d+1 - n = number of combinations, d is days in season, 1
        extra position for the total number of breaks in the season
    """
    home_away_tuples = []
    print('Compute possible sequence of home and aways for any team')
    half_season = num_teams - 1
    full_season = 2 * half_season
    solver = pywrapcp.Solver('compute_home_aways')
    home_aways = [solver.BoolVar('home_away_') for i in range(full_season)]
    # Can't have 3 consecutive home or away games
    for day in range(full_season - 2):
        tmp_vars = []
        tmp_vars.append(home_aways[day])
        tmp_vars.append(home_aways[day + 1])
        tmp_vars.append(home_aways[day + 2])
        partial_sum = solver.Sum(tmp_vars)
        solver.AddConstraint(solver.BetweenCt(partial_sum, 1, 2))
    db = solver.Phase(
        home_aways, solver.CHOOSE_FIRST_UNBOUND, solver.ASSIGN_MIN_VALUE
    )
    solver.NewSearch(db)
    while solver.NextSolution():
        solution = []
        for i in range(full_season):
            solution.append(home_aways[i].Value())
        breaks = 0
        # A 'break' is a sequence of two homes or two aways
        for i in range(full_season - 1):
            breaks += solution[i] == solution[i + 1]
        solution.append(breaks)
        home_away_tuples.append(solution)
    solver.EndSearch()
    print(
        str(len(home_away_tuples)) +
        ' combinations of home_aways for a team on the full season'
    )
    return home_away_tuples


def sportsScheduling(num_teams):
    """ Main function creates variables, constraints, search parameters and
        solution.
        Input: num_teams int
        Output: prints to console results and schedule
    """
    half_season = num_teams - 1
    full_season = 2 * half_season
    solver = pywrapcp.Solver('Sports Scheduling')
    # Variables
    # The index of the opponent of a team on a given day.
    opponents = [[] for i in range(num_teams)]
    # The location of the match (home or away)
    home_aways = [[] for i in range(num_teams)]
    # Disambiguated version of the opponent variable incorporating the
    # home_away result
    signed_opponents = [[] for i in range(num_teams)]
    for team_index in range(num_teams):
        opponents[team_index] = [
            solver.IntVar(
                0, num_teams - 1, 'opponent_' + str(team_index) + '_'
            ) for i in range(full_season)
        ]
        home_aways[team_index] = [
            solver.BoolVar('home_away_' + str(team_index) + '_')
            for i in range(full_season)
        ]
        signed_opponents[team_index] = [
            solver.IntVar(
                0, 2 * num_teams - 1,
                ('signed_opponent_' + str(team_index) + '_')
            ) for i in range(full_season)
        ]
    # Constraints
    # Produce all valid combinations of matchups for all teams for a given day.
    one_day_tuples = computeOneDayTuples(num_teams)
    for day in range(full_season):
        all_vars = []
        for i in range(num_teams):
            all_vars.append(signed_opponents[i][day])
        # For a given team, day, one_day_tuples sets the possible value
        # combinations that all_vars may take on.
        solver.AddConstraint(
            solver.AllowedAssignments(all_vars, one_day_tuples)
        )
    # Create signed_opponents, home_away and opponents tuple set
    one_day_one_team_tuples = computeOneDayOneTeamTuples(num_teams)
    for day in range(full_season):
        for team_index in range(num_teams):
            addOneDayOneTeamConstraint(
                solver, opponents[team_index][day], home_aways[team_index][day],
                signed_opponents[team_index][day], one_day_one_team_tuples
            )
    # Constraints on a team
    home_away_tuples = computeOneTeamHomeAwayTuples(num_teams)
    # We seek to minimize the sum values of team_breaks
    team_breaks = [
        solver.IntVar(0, full_season, 'team_break_') for i in range(num_teams)
    ]
    for team in range(num_teams):
        addOneTeamConstraints(
            solver, opponents[team], home_aways[team], signed_opponents[team],
            home_away_tuples, team_breaks[team], num_teams
        )
    # Search
    monitors = []
    # Objective
    objective_var = solver.Sum(team_breaks)
    objective_monitor = solver.Minimize(objective_var, 1)
    monitors.append(objective_monitor)
    # Store all variables in a single array
    all_signed_opponents = []
    for team_index in range(num_teams):
        for day in range(full_season):
            all_signed_opponents.append(signed_opponents[team_index][day])
    parameters = pywrapcp.DefaultPhaseParameters()
    parameters.run_all_heuristics = run_all_heuristics
    parameters.heuristic_period = heuristic_period
    parameters.restart_log_size = restart_log_size
    db = solver.DefaultPhase(all_signed_opponents, parameters)
    # Search log
    log = solver.SearchLog(100000, objective_monitor)
    monitors.append(log)
    # Search limit
    limit = solver.TimeLimit(time_limit)
    monitors.append(limit)
    # Solution collector
    collector = solver.LastSolutionCollector()
    for team_index in range(num_teams):
        collector.Add(opponents[team_index])
        collector.Add(home_aways[team_index])
    monitors.append(collector)
    # search
    solver.Solve(db, monitors)
    if collector.SolutionCount() == 1:
        print(
            'Solution found in ' + str(solver.WallTime()) + ' ms, and ' +
            str(solver.Failures()) + ' failures.'
        )
        for team_index in range(num_teams):
            line = ''
            for day in range(full_season):
                opponent = collector.Value(0, opponents[team_index][day])
                home_away = collector.Value(0, home_aways[team_index][day])
                line += (
                    'Day #' + str(day) + ' ' + str(team_index) + ' vs ' +
                    str(opponent) + ' home: ' + str(home_away) + '\n'
                )
            print(line)


sportsScheduling(num_teams)