# User Authentication Based on Mouse Characteristics #

## Load Packages ##
import pandas as pd
import numpy as np
import os
import pickle
import time
from datetime import datetime

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
    
    end_time = time.time()
    log_message(f"File processing completed in {end_time - start_time:.2f} seconds")
    return df

def main():
    start_time = time.time()
    log_message("Starting feature engineering process...")
    
    # Set up data directories
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'raw', 'training')
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'processed')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    log_message(f"Using data directory: {data_dir}")
    
    # Process all training files
    all_data = []
    total_files = 0
    processed_files = 0
    
    # First count total files
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if '.' not in file:
                total_files += 1
    
    log_message(f"Found {total_files} files to process")
    
    for root, dirs, files in os.walk(data_dir):
        for file in files:
            if '.' in file:
                continue
                
            file_path = os.path.join(root, file)
            user = os.path.basename(os.path.dirname(file_path))
            session = file
            
            processed_files += 1
            log_message(f"Processing file {processed_files}/{total_files}: {user}/{session}")
            
            df = process_file(file_path)
            df['user'] = user
            df['session'] = session
            all_data.append(df)
    
    log_message("Combining all processed data...")
    all_train = pd.concat(all_data, ignore_index=True)
    
    log_message("Saving processed data...")
    with open(os.path.join(output_dir, 'all_training_aggregation.pickle'), 'wb') as f:
        pickle.dump(all_train, f)
    
    end_time = time.time()
    log_message(f"Feature engineering completed in {end_time - start_time:.2f} seconds")
    log_message(f"Total records processed: {len(all_train)}")

if __name__ == "__main__":
    main() 