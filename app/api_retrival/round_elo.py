import pandas as pd
import session_retrival as fn

def _prev_round_col(df, round):
    """Get the previous round column (handles non-consecutive round numbers)."""
    # Round columns are typically int or float - find the largest existing col < round
    numeric_cols = [c for c in df.columns if isinstance(c, (int, float)) and c < round]
    return max(numeric_cols) if numeric_cols else None


def add_elo_rating(year, round, previous_elo, elo_type, k_modifiers, round_results):


    if len(previous_elo) == 0:
        player_elo = round_results[["DriverId", "FirstName", "LastName", "ConstructorName", "GridPosition"]]
        player_elo[0] = 1000  # Use 0 as initial round for new season
        new_elo_frame = player_elo
        prev_col = 0
    else:
        new_elo_frame = previous_elo.copy()
        prev_col = _prev_round_col(new_elo_frame, round)
        if prev_col is None:
            prev_col = 0
            new_elo_frame[0] = 1000  # Fallback if no previous rounds
    new_elo_frame[round] = new_elo_frame[prev_col]
    new_drivers_rows = check_new_drivers(round_results, previous_elo, elo_type)
    if new_drivers_rows[1] == True:
        new_elo_frame = pd.concat([new_elo_frame, new_drivers_rows[0]], ignore_index=True)

    
    new_elo_frame = calculate_elo(round_results, elo_type, new_elo_frame, round, prev_col, k_modifiers)



    


    return new_elo_frame

def calculate_elo(round_results, elo_type, new_elo_frame, round, prev_round_col, k_modifiers):
    for _, player_A in round_results[["DriverId", "RacePosition", "GridPosition", "ConstructorName"]].iterrows():
        for _, player_B in round_results[["DriverId", "RacePosition", "GridPosition", "ConstructorName"]].iterrows():

            
            elo_A = new_elo_frame[new_elo_frame[elo_type] == player_A[elo_type]][prev_round_col].iloc[0]
            elo_B = new_elo_frame[new_elo_frame[elo_type] == player_B[elo_type]][prev_round_col].iloc[0]
            
            
            actual_result_A = determine_actual_Result(player_A["RacePosition"],player_B["RacePosition"] )
            player_A_chance = determine_win_chance(elo_A, elo_B)
            #could make it so the big function passes in a k value (maybe not possible cos its diff, or maybe so the function passes in what to use to get k value)
            a = 1
            if k_modifiers is not None:
                
                
                k_modifiers = k_modifiers.drop_duplicates(subset=["ConstructorName"], keep="first")
                
                a = calculate_k_combined(actual_result_A, k_modifiers[k_modifiers["ConstructorName"] == player_A["ConstructorName"]][round].values[0], k_modifiers[k_modifiers["ConstructorName"] == player_B["ConstructorName"]][round].values[0]) 
            
            new_player_A_elo = (a*calculate_k(player_A["GridPosition"], player_B["GridPosition"]))*(actual_result_A - player_A_chance)
            
            new_elo_frame.loc[new_elo_frame[elo_type] == player_A[elo_type], round] += new_player_A_elo
            
    return new_elo_frame
    
def calculate_k(gridPositionA, gridPositionB):
    k = 30
    k += gridPositionA - gridPositionB
    if str(gridPositionA) == "nan" or str(gridPositionB) == "nan":
        return 30
    #k += 7*calculate_k_combined(constructor_A, constructor_B)
    return k

def calculate_k_combined(A_result, constructor_A, constructor_B):
    if constructor_B == 0:
        return(0)
    k = (constructor_B - constructor_A)/(constructor_B) + 1
    if A_result == 0 and k > 1: #this guy lost, and his car was worse
        k = k-1
    elif A_result == 0 and k < 1: #lost and car was deemed better eg k=0.3
        k = k+1
    return(k)


def determine_win_chance(elo_rating_A, elo_rating_B):
    exp1 = 1
    
    exp2 = 1 + 10**((elo_rating_B - elo_rating_A)/400)
    
    return exp1/exp2

def determine_actual_Result(rank_A, rank_B):

    if rank_A == rank_B:
        return 0.5
    elif rank_A < rank_B:
        return 1
    elif rank_B < rank_A:
        return 0
    
    return 0.5
    

def check_new_drivers(session, existing_elo, elo_type):
        bol = False
        all_new_rows = pd.DataFrame()
        
        if len(existing_elo) != 0:
            for _, player_A in session[[elo_type]].iterrows():
                if player_A.values[0] in existing_elo[elo_type].values:
                    pass
                else:
                    new_row = pd.DataFrame()
                    bol = True
                    new_row[elo_type] = session[session[elo_type] == player_A.values[0]][elo_type]
                    new_row["FirstName"] = session[session[elo_type] == player_A.values[0]]["FirstName"]
                    new_row["LastName"] = session[session[elo_type] == player_A.values[0]]["LastName"]
                    for i in existing_elo.columns:
                        if i not in [elo_type, 'FirstName', 'LastName']:
                            new_row[i] = 1000
                    all_new_rows = pd.concat([all_new_rows, new_row], ignore_index=True)

        
        return all_new_rows, bol
                
                
def get_season_elos(year):

    elo_types = ["DriverId", "ConstructorName", "Combined"]
    j = pd.DataFrame()
    m = pd.DataFrame()
    player_elo = pd.DataFrame()

    round_count = fn.get_rounds_count(year)

    
    for i in range(1,round_count+1):
        print("XXX", i)
        res = fn.get_session(year, i)
        j = add_elo_rating(year, i, j, elo_types[1], None, res)
       
     
        m = add_elo_rating(year, i, m, elo_types[0], j[["ConstructorName", i]], res) 
       
        player_elo = add_elo_rating(year, i, player_elo, elo_types[0], None, res) 
    


    j.drop(columns=['FirstName', 'LastName', 'DriverId', 'GridPosition'], inplace=True)
    j = j.drop_duplicates(subset=["ConstructorName"], keep="first")

    m.drop(columns=['ConstructorName', 'GridPosition'], inplace=True)
    player_elo.drop(columns=['GridPosition', 'ConstructorName'], inplace=True)
    return  (player_elo, j, m)


if __name__ == "__main__":
    #fn1.get_rounds_count(2017)
    x = get_season_elos(2021)
    print(x)

        