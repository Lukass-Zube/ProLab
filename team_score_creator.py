import json
from nba_api.stats.endpoints import leaguedashteamstats

# Fetch the team stats for the season
team_stats = leaguedashteamstats.LeagueDashTeamStats(season='2024-25')
stats_df = team_stats.get_data_frames()[0]

# Define positive (good) and negative (bad) attributes based on available stats
positive_attributes = ['W_PCT', 'FG_PCT', 'FG3_PCT', 'FT_PCT', 'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'PFD', 'PTS', 'PLUS_MINUS']
negative_attributes = ['TOV', 'PF', 'BLKA']  # Including "BLKA" as a "bad" attribute

# Prepare the JSON structure
teams_scores = []
for _, row in stats_df.iterrows():
    # Calculate the score as sum of good attributes - sum of bad attributes
    team_score = sum(row[attr] for attr in positive_attributes) - sum(row[attr] for attr in negative_attributes)
    team_data = {
        "TEAM_NAME": row['TEAM_NAME'],
        "TEAM_ID": row['TEAM_ID'],
        "SCORE": team_score
    }
    teams_scores.append(team_data)

# Write the data to a JSON file
output_path = 'team_scores.json'  # Save path
with open(output_path, 'w') as json_file:
    json.dump(teams_scores, json_file, indent=4)

print(f"JSON file created at: {output_path}")
