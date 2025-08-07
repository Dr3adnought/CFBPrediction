import cfbd
import os
import time
from dotenv import load_dotenv

from cfbd.rest import ApiException

load_dotenv()

api_key = os.getenv("CFBD_API_KEY")

configuration = cfbd.Configuration(
    host="https://api.collegefootballdata.com",
    access_token=api_key
)

POSITION_STAT_MAP = {
    'QB': ['passing', 'rushing', 'receiving', 'fumbles'],
    'RB': ['rushing', 'receiving', 'fumbles'],
    'WR': ['receiving', 'rushing', 'fumbles'],
    'TE': ['receiving', 'rushing', 'fumbles'],
    'FB': ['rushing', 'receiving', 'fumbles'],
    'DB': ['defensive', 'interceptions', 'fumbles'],
    'CB': ['defensive', 'interceptions', 'fumbles'],
    'S': ['defensive', 'interceptions', 'fumbles'],
    'LB': ['defensive', 'interceptions', 'fumbles'],
    'DE': ['defensive', 'interceptions', 'fumbles'],
    'DT': ['defensive', 'interceptions', 'fumbles'],
    'DL': ['defensive', 'interceptions', 'fumbles'],
    'K': ['kicking'],
    'P': ['punting'],
    'LS': [],
    'OL': []
}


def fetch_advanced_stats(team_name: str, year: int):

    try:
        if not configuration.access_token:
            raise ValueError(
                "API key not found. Please set the CFBD_API_KEY environment variable "
                "in a .env file or your system environment."
            )

        with cfbd.ApiClient(configuration) as api_client:

            stats_api = cfbd.StatsApi(api_client)
            print(f"Fetching advanced stats for {team_name} in {year}...")
            response = stats_api.get_advanced_season_stats(year=year, team=team_name)

            if response:
                return response[0].to_dict()
            else:
                print(f"No advanced stats found for {team_name} in {year}. Please check the team name and year.")
                return None
    except ApiException as e:
        print(f"CFBD API Error for {team_name}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for {team_name}: {e}")
        return None


def compare_teams(team_a_name: str, team_b_name: str, year: int):
    print(f"--- Comparing Advanced Season Stats for {team_a_name} vs {team_b_name} ({year}) ---")

    stats_a = fetch_advanced_stats(team_a_name, year)
    stats_b = fetch_advanced_stats(team_b_name, year)

    if not stats_a or not stats_b:
        return

    display_categories = ['total', 'offense', 'defense']

    for category_name in display_categories:
        print(f"\n--- {category_name.capitalize()} ---")

        stats_a_cat = stats_a.get(category_name)
        stats_b_cat = stats_b.get(category_name)

        if stats_a_cat and stats_b_cat and isinstance(stats_a_cat, dict) and isinstance(stats_b_cat, dict):
            print(f"{'Statistic':<30}{team_a_name:<20}{team_b_name:<20}")
            print("-" * 70)

            for stat_name in sorted(stats_a_cat.keys()):
                value_a = stats_a_cat.get(stat_name, "N/A")
                value_b = stats_b_cat.get(stat_name, "N/A")
                print(f"{stat_name.replace('_', ' ').title():<30}{str(value_a):<20}{str(value_b):<20}")


def get_player_position(player_name: str, team_name: str, year: int) -> str | None:
    try:
        if not configuration.access_token:
            raise ValueError(
                "API key not found. Please set the CFBD_API_KEY environment variable "
                "in a .env file or your system environment."
            )

        with cfbd.ApiClient(configuration) as api_client:
            roster_api = cfbd.RosterApi(api_client)
            roster = roster_api.get_roster(team=team_name, year=year)

            for player in roster:
                if player.name.lower() == player_name.lower():
                    return player.position
    except ApiException as e:
        print(f"CFBD API Error while fetching roster for {team_name}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while fetching roster: {e}")

    return None


def get_player_stats_by_name(player_name: str, team_name: str, year: int):
    print(f"--- Searching for stats for {player_name} on {team_name} ({year}) ---")

    position = get_player_position(player_name, team_name, year)

    if not position:
        print(
            f"Could not find player '{player_name}' or team '{team_name}' in the roster for {year}. Please check the names and try again.")
        return

    categories = POSITION_STAT_MAP.get(position.upper(), None)

    if not categories:
        print(
            f"Player position '{position}' is not supported for detailed stats fetching. Supported positions are {list(POSITION_STAT_MAP.keys())}.")
        return

    combined_stats = {}
    try:
        with cfbd.ApiClient(configuration) as api_client:
            stats_api = cfbd.StatsApi(api_client)

            for category in categories:
                print(f"Fetching {category} stats...")
                response = stats_api.get_player_season_stats(
                    year=year,
                    team=team_name,
                    category=category
                )

                if response:
                    player_stats = next((p.to_dict() for p in response if p.player.lower() == player_name.lower()),
                                        None)

                    if player_stats:
                        for stat_name, value in player_stats.items():
                            if stat_name not in ['player', 'team', 'conference', 'athlete_id', 'category']:
                                combined_stats[f"{category}_{stat_name}"] = value

            if combined_stats:
                print(f"\n--- Player Stats for {player_name} ({position}) ---")

                for stat_key in sorted(combined_stats.keys()):
                    value = combined_stats[stat_key]
                    display_key = stat_key.replace('_', ' ').title().replace('Passing ', '').replace('Rushing ',
                                                                                                     '').replace(
                        'Receiving ', '').replace('Fumbles ', '')

                    if 'passing_' in stat_key:
                        display_key = f"Passing {display_key}"
                    elif 'rushing_' in stat_key:
                        display_key = f"Rushing {display_key}"
                    elif 'receiving_' in stat_key:
                        display_key = f"Receiving {display_key}"
                    elif 'fumbles_' in stat_key:
                        display_key = f"Fumbles {display_key}"

                    print(f"{display_key:<35}: {value}")

            else:
                print(f"No stats found for {player_name} on team '{team_name}' in {year}.")

    except ApiException as e:
        print(f"CFBD API Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    print("Welcome to the College Football Stats Comparator and Player Lookup!")

    while True:
        print("\nWhat would you like to do?")
        print("1. Compare two teams' advanced stats")
        print("2. Look up a player's season stats")
        print("3. Exit")

        choice = input("Enter your choice (1, 2, or 3): ")

        if choice == '1':
            team_a_name = input("Enter the name of the first team: ")
            team_b_name = input("Enter the name of the second team: ")
            year_input = input("Enter the year: ")

            try:
                year = int(year_input)
                compare_teams(team_a_name, team_b_name, year)
            except ValueError:
                print("Invalid year. Please enter a valid integer for the year.")

        elif choice == '2':
            player_name = input("Enter the player's full name (e.g., 'Joe Burrow'): ")
            team_name = input("Enter the player's team: ")
            year_input = input("Enter the year: ")

            try:
                year = int(year_input)
                get_player_stats_by_name(player_name, team_name, year)
            except ValueError:
                print("Invalid year. Please enter a valid integer for the year.")

        elif choice == '3':
            print("Exiting. Goodbye!")
            break

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


