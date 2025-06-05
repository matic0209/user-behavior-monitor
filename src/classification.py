# User Authentication Based on Mouse Characteristics #

## Load Packages ##
import pandas as pd
import numpy as np
import os
import pickle
import time
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

# preprocessing
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score

# Set random seed
np.random.seed(0)

def log_message(message):
    """Print timestamped log message"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def load_and_split_data():
    """Load processed data and split into train/validation sets."""
    log_message("Loading processed data...")
    # Load processed data
    with open('all_training_aggregation.pickle', 'rb') as f:
        all_train = pickle.load(f)
    
    log_message("Getting file paths...")
    # Get all training file paths
    file_paths = []
    for root, dirs, files in os.walk('training_files'):
        for file in files:
            if '.' not in file:
                file_paths.append(os.path.join(root, file))
    
    log_message(f"Found {len(file_paths)} files")
    
    # Randomly split into train/validation (66/34 split)
    log_message("Splitting data into train/validation sets...")
    draw_train = np.random.randint(low=0, high=len(file_paths), 
                                 size=np.floor(len(file_paths)*0.66).astype('int'))
    train_users = list(map(lambda x: x.split(os.path.sep)[-2], 
                          [file_paths[y] for y in draw_train]))
    train_sessions = list(map(lambda x: x.split(os.path.sep)[-1], 
                            [file_paths[y] for y in draw_train]))
    
    # Get validation set
    draw_val = list(set(range(len(file_paths))) - set(draw_train))
    val_users = list(map(lambda x: x.split(os.path.sep)[-2], 
                        [file_paths[y] for y in draw_val]))
    val_sessions = list(map(lambda x: x.split(os.path.sep)[-1], 
                          [file_paths[y] for y in draw_val]))
    
    # Split data
    df_train = all_train[all_train['user'].isin(train_users) & 
                        all_train['session'].isin(train_sessions)]
    df_val = all_train[all_train['user'].isin(val_users) & 
                      all_train['session'].isin(val_sessions)]
    
    log_message(f"Split complete. Training set: {len(df_train)} records, Validation set: {len(df_val)} records")
    return df_train, df_val

def prepare_features(df_train, df_val):
    """Prepare features for training and validation."""
    log_message("Preparing features...")
    le_user = LabelEncoder()
    le_categ = LabelEncoder()
    oh_categ = OneHotEncoder()
    
    # Process training data
    log_message("Processing training data...")
    y_train = le_user.fit_transform(df_train['user'])
    df_train['categ_le'] = le_categ.fit_transform(df_train['categ_agg'])
    
    # One-hot encode categories
    vec_size = df_train['categ_agg'].nunique()
    df_train[['oh_categ{}'.format(i) for i in range(vec_size)]] = \
        pd.DataFrame(oh_categ.fit_transform(
            df_train['categ_le'].values.reshape(len(df_train['categ_le']), 1)).todense(),
            index=df_train.index)
    
    X_train = df_train.drop(['categ_agg', 'session', 'categ_le', 'user'], axis=1)
    
    # Process validation data
    log_message("Processing validation data...")
    y_val = le_user.transform(df_val['user'])
    df_val['categ_le'] = le_categ.transform(df_val['categ_agg'])
    df_val[['oh_categ{}'.format(i) for i in range(vec_size)]] = \
        pd.DataFrame(oh_categ.transform(
            df_val['categ_le'].values.reshape(len(df_val['categ_le']), 1)).todense(),
            index=df_val.index)
    
    X_val = df_val.drop(['categ_agg', 'session', 'categ_le', 'user'], axis=1)
    
    log_message("Feature preparation completed")
    return X_train, y_train, X_val, y_val, le_user

def train_models(X_train, y_train, X_val, y_val, le_user):
    """Train models for each user."""
    log_message("Starting model training...")
    models = {}
    train_scores = {}
    val_scores = {}
    
    for user in le_user.classes_:
        log_message(f"\nTraining model for {user}")
        
        # Prepare data for this user
        df = X_train.copy()
        df['is_illegal'] = 0
        df.loc[df['user'] != user, 'is_illegal'] = 1
        X = df.drop(['is_illegal'], axis=1)
        y = df['is_illegal']
        
        # Train model
        clf = LGBMClassifier(random_state=0)
        clf.fit(X, y)
        models[user] = clf
        
        # Calculate training score
        train_auc = roc_auc_score(y, clf.predict_proba(X)[:, 1])
        train_scores[user] = train_auc
        log_message(f"Training AUC: {train_auc:.4f}")
        
        # Calculate validation score
        df_val = X_val.copy()
        df_val['is_illegal'] = 0
        df_val.loc[df_val['user'] != user, 'is_illegal'] = 1
        X_v = df_val.drop(['is_illegal'], axis=1)
        y_v = df_val['is_illegal']
        
        val_auc = roc_auc_score(y_v, clf.predict_proba(X_v)[:, 1])
        val_scores[user] = val_auc
        log_message(f"Validation AUC: {val_auc:.4f}")
    
    return models, train_scores, val_scores

def main():
    start_time = time.time()
    log_message("Starting classification process...")
    
    # Load and split data
    df_train, df_val = load_and_split_data()
    
    # Prepare features
    X_train, y_train, X_val, y_val, le_user = prepare_features(df_train, df_val)
    
    # Train models
    models, train_scores, val_scores = train_models(X_train, y_train, X_val, y_val, le_user)
    
    # Save models
    log_message("\nSaving models...")
    with open('models.pickle', 'wb') as f:
        pickle.dump(models, f)
    
    # Print final results
    log_message("\nFinal Results:")
    log_message("\nTraining Scores:")
    for user, score in train_scores.items():
        log_message(f"{user}: {score:.4f}")
    
    log_message("\nValidation Scores:")
    for user, score in val_scores.items():
        log_message(f"{user}: {score:.4f}")
    
    end_time = time.time()
    log_message(f"\nClassification completed in {end_time - start_time:.2f} seconds")

if __name__ == "__main__":
    main() 