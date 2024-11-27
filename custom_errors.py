class TeamNotFoundError(Exception):
    def __init__(self, team_name):
        self.team_name = team_name
        super().__init__(f"Team not found: {team_name}")