# User Authentication Based on Mouse Characteristics #

## Load Packages ##
import pandas as pd
import numpy as np
import os
import pickle
import time
from datetime import datetime
from multiprocessing import Pool, cpu_count
from scipy import stats
from scipy.signal import find_peaks

def log_message(message):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def remove_outlier(df):
    """Remove records where mouse moves out of the remote desktop client."""
    log_message("Removing out-of-bound records...")
    df = df[(df['x'] < 65535) & (df['y'] < 65535)].copy()
    df.reset_index(drop=True, inplace=True)
    log_message(f"Removed out-of-bound records. Remaining records: {len(df)}")
    return df.copy()

def fill_in_scroll(df):
    """Fill in coordinates during mouse scrolling."""
    log_message("Filling in scroll coordinates...")
    df.loc[df['button'] == "Scroll", ['x', 'y']] = np.nan
    df['x'] = df['x'].ffill()
    df['y'] = df['y'].ffill()
    log_message("Scroll coordinates filled")
    return df.copy()

def change_from_prev_rec(df):
    """Calculate changes from the previous record."""
    log_message("Calculating movement changes...")
    # distance from the last position
    df['distance_from_previous'] = np.sqrt((df['x'].diff())**2 + (df['y'].diff())**2)
    
    # elapsed time from the previous movement
    df['elapsed_time_from_previous'] = df['client timestamp'].diff()
    
    # angle of the current position
    df['angle'] = np.arctan2(df['y'], df['x']) * 180 / np.pi
    df['angle_movement'] = df['angle'].diff()
    # movement angle
    df['angle_movement_abs'] = abs(df['angle_movement']) 
    
    log_message("Movement changes calculated")
    return df.copy()

def classify_categ(df):
    """Classify mouse actions into categories."""
    log_message("Classifying mouse actions...")
    # initialize
    df['categ'] = np.nan
    
    # double click: press -> release -> press -> release, same button
    df.loc[(df['state'] == 'Pressed') & (df.shift(-1)['state'] == 'Released') \
           & (df.shift(-2)['state'] == 'Pressed') \
           & (df.shift(-3)['state'] == 'Released') \
           & (df.shift(-1)['button'] == df.shift(-2)['button']) \
           & (df.shift(-2)['elapsed_time_from_previous'] <= 5) \
           , 'categ'] = 'double_click'
    
    log_message("Processing double clicks...")
    # Fill in other records for double-click
    i = 0
    while i <= len(df.index)-4:
        if df.iloc[i]['categ'] == 'double_click':
            df.loc[i+1, 'categ'] = 'double_click'
            df.loc[i+2, 'categ'] = 'double_click'
            df.loc[i+3, 'categ'] = 'double_click'
            i += 4
        else:
            i += 1
    del i 
    
    log_message("Processing single clicks...")
    # single click
    df.loc[(df['state'] == 'Pressed') & (df.shift(-1)['state'] == 'Released') \
           & (df['categ'].isna() == True) & (df['button'] == 'Left')
           , 'categ'] = 'left_click'

    df.loc[(df['state'] == 'Pressed') & (df.shift(-1)['state'] == 'Released') \
           & (df['categ'].isna() == True) & (df['button'] == 'Right')
           , 'categ'] = 'right_click'
    
    log_message("Processing drags...")
    # drag: press -> drag -> release
    df.loc[((df['state'] == 'Pressed') & (df.shift(-1)['state'] == 'Drag')) \
           | (df['state'] == 'Drag') \
           | ((df['state'] == 'Released') & (df.shift()['state'] == 'Drag')), 'categ'] = 'drag'
    
    log_message("Processing moves and scrolls...")
    # move
    df.loc[(df['state'] == 'Move'), 'categ'] = 'move'
    
    # scroll
    df.loc[(df['state'].isin(['Down', 'Up'])), 'categ'] = 'scroll'
    
    df['categ'] = df['categ'].ffill()

    # add an empty row at the very end of the dataframe
    filllastrow = pd.DataFrame(columns = df.columns)
    filllastrow.loc[0, 'categ'] = 'move'
    df = pd.concat([df, filllastrow])

    log_message("Assigning action IDs...")
    # Each mouse action will have an ID for later aggregation
    df['action_cnt'] = 0
    action_cnt = 0
    categ_current = np.nan

    # Process actions backwards
    for i in range(len(df.index)-2, -1, -1):
        if i == len(df.index)-2:
            categ_current = df.iloc[i]['categ']
            
        if ((df.iloc[i]['categ'] != df.iloc[i+1]['categ']) 
             & (df.iloc[i]['categ'] != 'move')) \
            | ((df.iloc[i]['categ'] != 'drag') \
             & (df.iloc[i+1]['categ'] == 'drag')) \
            | ((df.iloc[i+1]['elapsed_time_from_previous'] > 5) \
             & (df.iloc[i]['categ'] == 'move') \
             & (df.iloc[i+1]['categ'] == 'move')) \
            | ((df.iloc[i+1]['elapsed_time_from_previous'] > 5) \
             & (df.iloc[i]['categ'] == 'scroll') \
             & (df.iloc[i+1]['categ'] == 'scroll')):
            action_cnt -= 1
            categ_current = df.iloc[i]['categ']
            df.loc[i, 'action_cnt'] = action_cnt
            df.loc[i, 'categ_agg'] = categ_current
        else:
            df.loc[i, 'action_cnt'] = action_cnt
            df.loc[i, 'categ_agg'] = categ_current

    # reverse the action IDs
    df['action_cnt'] = df['action_cnt'] - action_cnt

    # remove the last empty row
    df = df.iloc[:-1]

    del action_cnt, filllastrow, categ_current
    
    log_message(f"Mouse actions classified. Total actions: {df['action_cnt'].nunique()}")
    return df.copy()

def add_velocity_features(df):
    """Add velocity and acceleration related features."""
    log_message("Adding velocity features...")
    
    # Velocity features
    df['velocity'] = df['distance_from_previous'] / df['elapsed_time_from_previous']
    df['velocity_x'] = df['x'].diff() / df['elapsed_time_from_previous']
    df['velocity_y'] = df['y'].diff() / df['elapsed_time_from_previous']
    
    # Acceleration features
    df['acceleration'] = df['velocity'].diff() / df['elapsed_time_from_previous']
    df['acceleration_x'] = df['velocity_x'].diff() / df['elapsed_time_from_previous']
    df['acceleration_y'] = df['velocity_y'].diff() / df['elapsed_time_from_previous']
    
    # Jerk (rate of change of acceleration)
    df['jerk'] = df['acceleration'].diff() / df['elapsed_time_from_previous']
    
    # Angular velocity
    df['angular_velocity'] = df['angle_movement'] / df['elapsed_time_from_previous']
    
    return df

def add_trajectory_features(df):
    """Add features related to mouse movement trajectory."""
    log_message("Adding trajectory features...")
    
    # Curvature
    df['curvature'] = df['angle_movement'] / df['distance_from_previous']
    
    # Direction changes
    df['direction_change'] = (df['angle_movement'].abs() > 45).astype(int)
    
    # Straightness (ratio of direct distance to actual path length)
    window_size = 10
    df['path_length'] = df['distance_from_previous'].rolling(window=window_size).sum()
    df['direct_distance'] = np.sqrt(
        (df['x'] - df['x'].shift(window_size))**2 + 
        (df['y'] - df['y'].shift(window_size))**2
    )
    df['straightness'] = df['direct_distance'] / df['path_length']
    
    # Movement complexity
    df['movement_complexity'] = df['angle_movement_abs'].rolling(window=window_size).std()
    
    return df

def add_temporal_features(df):
    """Add time-based features."""
    log_message("Adding temporal features...")
    
    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['client timestamp'], unit='s')
    
    # Time-based features
    df['hour'] = df['datetime'].dt.hour
    df['minute'] = df['datetime'].dt.minute
    df['second'] = df['datetime'].dt.second
    df['day_of_week'] = df['datetime'].dt.dayofweek
    
    # Time intervals
    df['time_since_start'] = (df['datetime'] - df['datetime'].iloc[0]).dt.total_seconds()
    
    # Action duration
    df['action_duration'] = df.groupby('action_cnt')['elapsed_time_from_previous'].transform('sum')
    
    return df

def add_statistical_features(df):
    """Add statistical features using rolling windows."""
    log_message("Adding statistical features...")
    
    window_sizes = [5, 10, 20, 50]
    features = ['velocity', 'acceleration', 'angle_movement', 'distance_from_previous']
    
    for window in window_sizes:
        for feature in features:
            # Basic statistics
            df[f'{feature}_mean_{window}'] = df[feature].rolling(window=window).mean()
            df[f'{feature}_std_{window}'] = df[feature].rolling(window=window).std()
            df[f'{feature}_min_{window}'] = df[feature].rolling(window=window).min()
            df[f'{feature}_max_{window}'] = df[feature].rolling(window=window).max()
            df[f'{feature}_range_{window}'] = df[f'{feature}_max_{window}'] - df[f'{feature}_min_{window}']
            
            # Advanced statistics
            df[f'{feature}_skew_{window}'] = df[feature].rolling(window=window).skew()
            df[f'{feature}_kurt_{window}'] = df[feature].rolling(window=window).kurt()
            
            # Peak detection
            peaks, _ = find_peaks(df[feature].abs(), distance=window)
            df[f'{feature}_peaks_{window}'] = 0
            df.loc[peaks, f'{feature}_peaks_{window}'] = 1
    
    return df

def add_interaction_features(df):
    """Add features related to user interaction patterns."""
    log_message("Adding interaction features...")
    
    # Click patterns
    df['click_interval'] = df[df['categ'].isin(['left_click', 'right_click', 'double_click'])]['elapsed_time_from_previous']
    
    # Movement patterns
    df['movement_after_click'] = df['distance_from_previous'].shift(-1)
    df['time_after_click'] = df['elapsed_time_from_previous'].shift(-1)
    
    # Action sequence features
    df['action_sequence'] = df.groupby('action_cnt')['categ'].transform(lambda x: '_'.join(x))
    
    # Interaction density
    window_size = 100
    df['interaction_density'] = df['categ'].rolling(window=window_size).apply(
        lambda x: sum(x.isin(['left_click', 'right_click', 'double_click'])) / window_size
    )
    
    return df

def add_geometric_features(df):
    """Add geometric features related to mouse movement."""
    log_message("Adding geometric features...")
    
    # Area features
    df['area_covered'] = df['x'] * df['y']
    df['area_change'] = df['area_covered'].diff()
    
    # Distance from center
    center_x = df['x'].mean()
    center_y = df['y'].mean()
    df['distance_from_center'] = np.sqrt((df['x'] - center_x)**2 + (df['y'] - center_y)**2)
    
    # Screen quadrant
    df['quadrant'] = pd.cut(df['angle'], bins=[-180, -90, 0, 90, 180], labels=[1, 2, 3, 4])
    
    # Movement direction
    df['direction'] = pd.cut(df['angle'], bins=8, labels=range(8))
    
    return df

def process_file(file_path):
    """Process a single mouse movement file."""
    start_time = time.time()
    log_message(f"Starting to process file: {file_path}")
    
    df = pd.read_csv(file_path)
    log_message(f"File loaded. Initial records: {len(df)}")
    
    df = remove_outlier(df)
    df = fill_in_scroll(df)
    df = change_from_prev_rec(df)
    df = classify_categ(df)
    
    # Add new features
    df = add_velocity_features(df)
    df = add_trajectory_features(df)
    df = add_temporal_features(df)
    df = add_statistical_features(df)
    df = add_interaction_features(df)
    df = add_geometric_features(df)
    
    # Fill NaN values
    df = df.fillna(method='ffill').fillna(method='bfill').fillna(0)
    
    end_time = time.time()
    log_message(f"File processing completed in {end_time - start_time:.2f} seconds")
    return df

def process_file_wrapper(args):
    """Wrapper function for process_file to handle multiple arguments."""
    file_path, user, session = args
    try:
        df = process_file(file_path)
        df['user'] = user
        df['session'] = session
        return df
    except Exception as e:
        log_message(f"Error processing file {file_path}: {str(e)}")
        return None

def main():
    start_time = time.time()
    log_message("Starting feature engineering process...")
    
    # Set up data directories
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw', 'training')
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    log_message(f"Using data directory: {data_dir}")
    
    # Collect all files to process
    files_to_process = []
    total_files = 0
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if '.' not in file:
                total_files += 1
                file_path = os.path.join(root, file)
                user = os.path.basename(os.path.dirname(file_path))
                session = file
                files_to_process.append((file_path, user, session))
    
    log_message(f"Found {total_files} files to process")
    
    # Determine number of processes to use (use 75% of available CPU cores)
    num_processes = max(1, int(cpu_count() * 0.75))
    log_message(f"Using {num_processes} processes for parallel processing")
    
    # Process files in parallel
    with Pool(processes=num_processes) as pool:
        results = []
        for i, result in enumerate(pool.imap_unordered(process_file_wrapper, files_to_process)):
            if result is not None:
                results.append(result)
            log_message(f"Processed file {i+1}/{total_files}")
    
    log_message("Combining all processed data...")
    all_train = pd.concat(results, ignore_index=True)
    
    log_message("Saving processed data...")
    with open(os.path.join(output_dir, 'all_training_aggregation.pickle'), 'wb') as f:
        pickle.dump(all_train, f)
    
    end_time = time.time()
    log_message(f"Feature engineering completed in {end_time - start_time:.2f} seconds")
    log_message(f"Total records processed: {len(all_train)}")

if __name__ == "__main__":
    main() 