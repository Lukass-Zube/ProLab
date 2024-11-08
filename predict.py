from nba_api.stats.static import teams

def predict_winner(first_team, second_team):
    matching_teams1 = teams.find_teams_by_full_name(first_team)
    matching_teams2 = teams.find_teams_by_full_name(second_team)
    error_message = "Team not found"

    # Check first team
    if not matching_teams1:
        return error_message, None
        
    # Check second team
    if not matching_teams2:
        return error_message, None
        
    # Both teams found, get their info
    team_info1 = matching_teams1[0]  # Get the first match
    team_id1 = team_info1['id']
    team_name1 = team_info1['full_name']
    
    team_info2 = matching_teams2[0]  # Get the first match
    team_id2 = team_info2['id']
    team_name2 = team_info2['full_name']
    
    # Load and parse team scores from JSON
    import json
    with open('team_scores.json', 'r') as f:
        team_scores = json.load(f)
    
    # Find scores for both teams
    team1_score = None
    team2_score = None
    for team in team_scores:
        if team['TEAM_ID'] == team_id1:
            team1_score = team['SCORE']
        if team['TEAM_ID'] == team_id2:
            team2_score = team['SCORE']
            
    # Compare scores and return winner/loser
    if team1_score > team2_score:
        return team_name1, team_name2
    else:
        return team_name2, team_name1