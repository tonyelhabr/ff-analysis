
library(tidyverse)
# library(ffsched)

league_id <- 899513
weeks <- 12
league_size <- 10
season <- 2020
sims <- 100000
tries <- 0.1 * sims

options(
  readr.num_columns = 0,
  ffsched.dir_data = 'data'
)

# debugonce(ffsched::do_simulate_standings)
standings_sims <-
  ffsched::do_simulate_standings(
    league_id = league_id,
    league_size = league_size,
    season = season,
    weeks = weeks,
    sims = sims,
    tries = tries
  )
standings_sims

standings_sims_n <-
  standings_sims %>% 
  count(team_id, team, rank, sort = TRUE) %>% 
  group_by(team_id, team) %>% 
  mutate(frac = n / sum(n)) %>% 
  ungroup()
standings_sims_n

standings_sims_n_top <-
  standings_sims_n %>% 
  group_by(rank) %>% 
  slice_max(n, with_ties = FALSE) %>%  
  ungroup()
standings_sims_n_top

standings_sims_n_top <-
  standings_sims_n %>% 
  group_by(team) %>% 
  summarize(
    tot = sum(n),
    rank_avg = sum(rank * n)  / tot
  ) %>% 
  ungroup() %>% 
  mutate(rank_tot = row_number(rank_avg)) %>% 
  arrange(rank_tot)
standings_sims_n_top

scores <- 
  ffsched::scrape_espn_ff_scores(
    league_id = league_id,
    league_size = league_size,
    season = season,
    weeks = weeks
  )
scores

standings_actual <-
  scores %>% 
  mutate(w = if_else(pf > pa, 1, 0)) %>% 
  group_by(team, team_id) %>% 
  summarize(
    across(c(w, pf), sum)
  ) %>% 
  ungroup() %>% 
  mutate(rank_w = min_rank(-w)) %>% 
  group_by(rank_w) %>% 
  mutate(
    rank_tiebreak = row_number(-pf) - 1L
  ) %>% 
  ungroup() %>% 
  mutate(rank = rank_w + rank_tiebreak)
standings_actual

teams <-
  tibble(
    team_lab = c(
      'Aggie Boomer',
      'Never Safe For Work',
      'Never Googled a Thing In My Life',
      'Just Here So That I Don\'t Get Fined',
      'Former Degenerate Gambler',
      '[Autodraft]',
      'Andrew Luck Stan',
      'Tacommissioner',
      'The Juggernaut',
      'Tony El Tigre'
    ),
    team_id = c(10, 8, 2, 4, 6, 3, 9, 1, 5, 7)
  )

.factor_cols <- function(data) {
  data %>% 
    left_join(
      standings_sims_n_top %>% 
        select(team, rank_tot, rank_avg)
    ) %>% 
    left_join(standings_actual) %>% 
    left_join(teams) %>% 
    mutate(
      across(team_lab, ~fct_reorder(.x, -rank_tot)),
      across(rank, ordered)
    )
}

ffsched::theme_set_update_ffsched()

.pts <- function(x) {
  as.numeric(grid::convertUnit(grid::unit(x, 'pt'), 'mm'))
}

viz_standings_tile <-
  standings_sims_n %>% 
  .factor_cols() %>% 
  ggplot() +
  aes(x = rank, y = team_lab) +
  geom_tile(aes(fill = frac), alpha = 0.5, na.rm = FALSE) +
  geom_tile(
    data = standings_actual %>% .factor_cols(),
    fill = NA,
    color = 'black',
    size = 3
  ) +
  geom_text(
    aes(label = scales::percent(frac, accuracy = 1.1)), 
    color = 'black', 
    size = .pts(14),
    fontface = 'bold'
  ) +
  scale_fill_viridis_c(option = 'C', begin = 0.2, end = 1) +
  guides(fill = FALSE) +
  theme(
    panel.grid.major = element_blank(),
    plot.caption = ggtext::element_markdown()
  ) +
  labs(
    title = 'Simulated final regular season standings positions',
    subtitle = 'Based on 100k unique schedules',
    caption = '**Viz**: @Tony ElHabr | **Data**: 2020 fantasy football league',
    x = NULL,
    y = NULL
  )
viz_standings_tile

ggsave(
  plot = viz_standings_tile, 
  filename = file.path('figs', 'viz_standings_tile_2020.png'), 
  type = 'cairo', 
  width = 12,
  height = 8
)
