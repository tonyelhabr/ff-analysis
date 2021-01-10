
# library(tidyverse)
reticulate::use_condaenv('ortools-ff-analysis')
cp_model <- reticulate::import('ortools.sat.python.cp_model')

n_team <- 4L
seq_team <- 1L:n_team
n_week <- n_team - 1L

games <- list()
games_chr <- list()
model <- cp_model$CpModel()
# model$NewIntVar(1L, 2L, name = '2_1')
for(team1 in seq_team) {
  for(team2 in seq_team) {
    if(team1 != team2) {
      nm <- sprintf('%d_%d', team1, team2)
      cat(nm, sep = '\n')
      games[[nm]] <- model$NewIntVar(1L, n_week, name = nm)
      games_chr[[nm]] <- nm
    }
  }
}
# str(model) 

for(team1 in seq_team) {
  for(team2 in seq_team) {
    if(team1 != team2) {
      model$Add(games[[sprintf('%d_%d', team1, team2)]] == games[[sprintf('%d_%d', team2, team1)]])
    }
  }
}
# str(model)

# games %>% pluck(2)
# class(games[[1]])
# class(games_chr[[1]])

for(team1 in seq_team) {
  games2 <- c()
  for(team2 in seq_team) {
    if(team1 != team2) {
      games2 <- c(games[[sprintf('%d_%d', team1, team2)]], games2)
      # games2 <- c(as.character(games[[sprintf('%d_%d', team1, team2)]]), games2)
    }
  }
  model$AddAllDifferent(games2)
  # games2 <- games[[sprintf('%d_%d', tm, team2)]])
}
str(model)
class(model)
str(model)

# model$AddAllDifferent(games[sprintf('%d_%d', tm, tms2)])
solver <- cp_model$CpSolver()
solver

# opt_err <- getOption('error')
# opt_err
# options(error = recover)
# options(error = NULL)
CpSolverSolutionCallback <- cp_model$CpSolverSolutionCallback
SolutionPrinter <-
  reticulate::PyClass(
    'SolutionPrinter',
    inherit = CpSolverSolutionCallback,
    defs = list(
      `__init__` = function(self, games, n_team) {
        print('initializing')
        # browser()
        cp_model$CpSolverSolutionCallback$`__init__`(self)
        self$games <- games
        self$n_team <- n_team
        self$n_sol <- 0
        # browser()
        NULL
      },
      on_solution_callback = function(self) {
        printer('in callback')
        self$n_sol <- self$n_sol + 1
      }
    )
  )
# reticulate::source_python('src/ortools_function2.py')
# printer <- SolutionPrinter
printer <- SolutionPrinter(games = games, n_team = n_team)
# printer <- cp_model$CpSolverSolutionCallback
debugonce(SolutionPrinter)
status <- solver$SearchForAllSolutions(model, printer)
status

library(tidyverse)
tibble(
  n = seq(2, 14, by = 2),
  k1 = c(1, 1, 6, 6240, 1225566720, 252282619805368320, 98758655816833727741338583040)
) %>% 
  mutate(
    n_factor = factorial(n - 1),
    solutions = k1 * n_factor
  ) %>% 
  knitr::kable()
