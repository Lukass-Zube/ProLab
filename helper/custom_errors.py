class TeamNotFoundError(Exception):
    def __init__(self, team_name):
        self.team_name = team_name
        super().__init__(f"Team not found: {team_name}")

class NotEnoughGamesError(Exception):
    def __init__(self, team_name, num_games):
        self.team_name = team_name
        self.num_games = num_games
        super().__init__(f"Not enough games found for team: {team_name}. Required: {num_games}")