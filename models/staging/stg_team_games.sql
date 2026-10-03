select
    team_id,
    team_name,
    game_date,
    is_home,
    won,
    last10_win_pct
from {{ source('raw', 'team_games') }}
