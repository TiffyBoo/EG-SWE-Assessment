import pandas as pd
import matplotlib.pyplot as plt

class ProcessGameState:
    def __init__(self):
        self.df = pd.read_parquet('game_state_frame_data.parquet')

    def extract_weapon_classes(self):
        weapon_classes = []
        for inventory in self.df['inventory']:
            classes = []
            if inventory is not None:
                for item in inventory:
                    classes.append(item['weapon_class'])
            weapon_classes.append(classes)

        self.df['weapon_class'] = weapon_classes

    def filter_by_boundary(self):
        boundary_points = [[-1735, 250], [-2024, 398], [-2806, 742], [-2472, 1233], [-1565, 580]]
        x_coords = [point[0] for point in boundary_points]
        y_coords = [point[1] for point in boundary_points]
        z_lower_bound = 285
        z_upper_bound = 421

        boundary_df = self.df[
            (self.df['x'].between(min(x_coords), max(x_coords))) &
            (self.df['y'].between(min(y_coords), max(y_coords))) &
            (self.df['z'].between(z_lower_bound, z_upper_bound))
        ]

        return boundary_df

    def process_game_state(self):
        self.extract_weapon_classes()
        boundary_df = self.filter_by_boundary()

        return boundary_df

    def calculate_entry_frequency(self, team_name):
        boundary_df = self.filter_by_boundary()
        team_df = boundary_df[(boundary_df['team'] == team_name) & (boundary_df['side'] == 'T')]
        unique_entries = team_df.groupby(['player', 'tick']).size().reset_index(name='count')
        entry_frequency = unique_entries.shape[0] 

        return entry_frequency
    
    def average_timer_bombsiteB(self):
        team2_t_df = self.df[
            (self.df['team'] == 'Team2') &
            (self.df['side'] == 'T') &
            (self.df['area_name'] == 'BombsiteB')
        ]

        total_timer = 0
        count = 0

        for round_num in team2_t_df['round_num'].unique():
            round_df = team2_t_df[team2_t_df['round_num'] == round_num]
            rifles = 0
            smgs = 0

            for player in ['Player5', 'Player6', 'Player7', 'Player8', 'Player9']:
                player_group = round_df[round_df['player'] == player]
                if len(player_group) > 0:
                    weapon_class = player_group['weapon_class'].values[0]
                    if 'Rifle' in weapon_class:
                        rifles += 1
                    elif 'SMG' in weapon_class:
                        smgs += 1

            if rifles >= 2 or smgs >= 2:
                count += 1
                last_clock_time = round_df['clock_time'].iloc[-1]
                minutes, seconds = map(int, last_clock_time.split(':'))
                total_timer += minutes * 60 + seconds

        avg_timer = total_timer / count if count > 0 else 0
        return avg_timer
    
    def generate_heatmap_bombsiteB(self):
        team2_ct_df = self.df[
            (self.df['team'] == 'Team1') &
            (self.df['side'] == 'CT') &
            (self.df['area_name'] == 'BombsiteB')
        ]

        heatmap_coordinates = team2_ct_df[['x', 'y']]

        heatmap = plt.imread('de_overpass_radar.jpeg')
        fig, ax = plt.subplots(figsize=(10, 10))

        x = heatmap_coordinates['x']
        y = heatmap_coordinates['y']

        ax.scatter((x * 0.75) - 120, (y * 0.60) + 480, color='red', alpha=0.25, zorder=1)
        ax.imshow(heatmap, extent=[-3000, 0, -1500, 1500], zorder=0)

        plt.show()


game_state_processor = ProcessGameState()
processed_df = game_state_processor.process_game_state()

team_name = 'Team2'
entry_frequency = game_state_processor.calculate_entry_frequency(team_name)
print("Frequency of", team_name, "entering via the boundary:", entry_frequency)

avg_timer_bombsiteB = game_state_processor.average_timer_bombsiteB()
print("Average Timer for Team2 on T side entering BombsiteB with at least 2 rifles or SMGs:", avg_timer_bombsiteB)

game_state_processor.generate_heatmap_bombsiteB()
