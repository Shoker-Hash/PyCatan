from Managers.GameDirector import GameDirector
import pandas as pd
import numpy as np

def main():
    player_points = []
    wins_per_player = [0, 0, 0, 0]
    game_director = GameDirector()
    player_names = [k["player"] for k in game_director.game_manager.bot_manager.players]

    try:
        games_to_play = int(input("Number of games to be played: "))
    except ValueError:
        games_to_play = 0
    if isinstance(games_to_play, int) and games_to_play > 0:
        for i in range(games_to_play):
            print("......")
            winner_id, player_points_this_game = game_director.game_start(i + 1)
            player_points.append(player_points_this_game)
            wins_per_player[winner_id] = wins_per_player[winner_id] + 1
    else:
        print("......")
        print("Invalid quantity")
    print("------------------------")
    print("SUMMARY:")
    for i in range(4):
        print("J" + str(i) + "'s wins: " + str(wins_per_player[i]))
    player_points = np.array(player_points)

    info_to_df = {}
    for id, player in enumerate(player_names):
        info_to_df[player] = player_points[:,id]

    print(pd.DataFrame(info_to_df).head(5))
    game_director.trace_loader.export_every_game_to_file()
    return


if __name__ == "__main__":
    main()
