import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from sklearn.decomposition import PCA
from scipy.fft import fft
import logging

logger = logging.getLogger(__name__)

class FeatureExtractor:
    def __init__(self, config: Dict):
        self.config = config
        self.feature_config = config['features']
        
    def extract_features(self, df: pd.DataFrame) -> Optional[np.ndarray]:
        """Extract all features from mouse movement data"""
        try:
            logger.info(f"Extracting features from DataFrame with shape {df.shape}")
            
            # Map columns to expected names
            col_map = {
                'record timestamp': 'timestamp',
                'client timestamp': 'client_timestamp',
                'button': 'button',
                'state': 'state',
                'x': 'x',
                'y': 'y',
            }
            df = df.rename(columns=col_map)

            # Add event_type column for compatibility (optional: you may want to map 'button' and 'state' to event_type)
            # For now, just create a placeholder event_type column (all zeros)
            if 'event_type' not in df.columns:
                df['event_type'] = 0

            # Basic features
            basic_features = self._extract_basic_features(df)
            logger.info(f"Extracted {len(basic_features)} basic features")
            
            # Movement features
            movement_features = self._extract_movement_features(df)
            logger.info(f"Extracted {len(movement_features)} movement features")
            
            # Event features
            event_features = self._extract_event_features(df)
            logger.info(f"Extracted {len(event_features)} event features")
            
            # Time series features
            time_series_features = self._extract_time_series_features(df)
            logger.info(f"Extracted {len(time_series_features)} time series features")
            
            # Spatial features
            spatial_features = self._extract_spatial_features(df)
            logger.info(f"Extracted {len(spatial_features)} spatial features")
            
            # Frequency domain features
            freq_features = self._extract_frequency_features(df)
            logger.info(f"Extracted {len(freq_features)} frequency features")
            
            # Combine all features
            all_features = np.concatenate([
                basic_features,
                movement_features,
                event_features,
                time_series_features,
                spatial_features,
                freq_features
            ])
            
            logger.info(f"Total features extracted: {len(all_features)}")
            return all_features
            
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            return None
    
    def _extract_basic_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract basic position and timing features"""
        features = []
        
        # Position features
        features.extend([
            df['x'].mean(),  # center_x
            df['y'].mean(),  # center_y
            df['x'].iloc[0],  # first_x
            df['y'].iloc[0],  # first_y
            df['x'].std(),  # x_std
            df['y'].std(),  # y_std
        ])
        
        # Click features
        click_mask = df['event_type'] == 1
        if click_mask.any():
            features.extend([
                df.loc[click_mask, 'x'].mean(),  # center_click_x
                df.loc[click_mask, 'y'].mean(),  # center_click_y
            ])
        else:
            features.extend([0, 0])
            
        # Time features
        features.extend([
            df['timestamp'].max() - df['timestamp'].min(),  # session_duration
            df['timestamp'].diff().mean(),  # avg_time_interval
            df['timestamp'].diff().std(),  # time_interval_std
        ])
        
        return np.array(features)
    
    def _extract_movement_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract movement-related features"""
        features = []
        
        # Calculate distances
        dx = df['x'].diff()
        dy = df['y'].diff()
        distances = np.sqrt(dx**2 + dy**2)
        
        # Speed features
        dt = df['timestamp'].diff()
        speeds = distances / dt
        speeds = speeds.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        features.extend([
            speeds.mean(),  # avg_speed
            speeds.max(),  # max_speed
            speeds.std(),  # speed_std
        ])
        
        # Acceleration features
        accel = speeds.diff() / dt
        accel = accel.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        features.extend([
            accel.mean(),  # avg_accel
            accel.max(),  # max_accel
            accel.std(),  # accel_std
        ])
        
        # Jerk features
        jerk = accel.diff() / dt
        jerk = jerk.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        features.extend([
            jerk.mean(),  # avg_jerk
            jerk.max(),  # max_jerk
            jerk.std(),  # jerk_std
        ])
        
        # Angle features
        angles = np.arctan2(dy, dx)
        angle_changes = angles.diff()
        
        features.extend([
            angles.mean(),  # avg_angle
            angles.std(),  # angle_std
            angle_changes.mean(),  # avg_angle_change
            angle_changes.std(),  # angle_change_std
        ])
        
        return np.array(features)
    
    def _extract_event_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract features related to mouse events"""
        features = []
        
        # Event counts and ratios
        event_counts = df['event_type'].value_counts()
        total_events = len(df)
        
        for event_type in range(1, 6):  # 5 event types
            count = event_counts.get(event_type, 0)
            features.extend([
                count,  # event_count
                count / total_events,  # event_ratio
            ])
        
        # Event timing features
        for event_type in range(1, 6):
            event_times = df[df['event_type'] == event_type]['timestamp']
            if len(event_times) > 0:
                features.extend([
                    event_times.diff().mean(),  # avg_time_between_events
                    event_times.diff().std(),  # std_time_between_events
                ])
            else:
                features.extend([0, 0])
        
        return np.array(features)
    
    def _extract_time_series_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract time series based features"""
        features = []
        window_size = self.feature_config['window_size']
        
        # Calculate rolling statistics
        for col in ['x', 'y']:
            rolling_mean = df[col].rolling(window=window_size).mean()
            rolling_std = df[col].rolling(window=window_size).std()
            
            features.extend([
                rolling_mean.mean(),  # avg_rolling_mean
                rolling_std.mean(),  # avg_rolling_std
                rolling_mean.std(),  # std_rolling_mean
                rolling_std.std(),  # std_rolling_std
            ])
        
        # Calculate velocity and acceleration time series
        dx = df['x'].diff()
        dy = df['y'].diff()
        dt = df['timestamp'].diff()
        
        velocity = np.sqrt(dx**2 + dy**2) / dt
        velocity = velocity.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        acceleration = velocity.diff() / dt
        acceleration = acceleration.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        for series in [velocity, acceleration]:
            rolling_mean = pd.Series(series).rolling(window=window_size).mean()
            rolling_std = pd.Series(series).rolling(window=window_size).std()
            
            features.extend([
                rolling_mean.mean(),  # avg_rolling_mean
                rolling_std.mean(),  # avg_rolling_std
                rolling_mean.std(),  # std_rolling_mean
                rolling_std.std(),  # std_rolling_std
            ])
        
        return np.array(features)
    
    def _extract_spatial_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract spatial distribution features"""
        features = []
        n_grid = self.feature_config['n_grid']
        n_quadrants = self.feature_config['n_quadrants']
        
        # Grid distribution
        x_bins = np.linspace(df['x'].min(), df['x'].max(), n_grid + 1)
        y_bins = np.linspace(df['y'].min(), df['y'].max(), n_grid + 1)
        
        grid_counts = np.histogram2d(df['x'], df['y'], bins=[x_bins, y_bins])[0]
        grid_density = grid_counts / len(df)
        
        features.extend([
            grid_density.mean(),  # avg_grid_density
            grid_density.std(),  # std_grid_density
            np.max(grid_density),  # max_grid_density
        ])
        
        # Quadrant distribution
        x_center = df['x'].mean()
        y_center = df['y'].mean()
        
        quadrants = np.zeros(n_quadrants)
        for i in range(len(df)):
            x, y = df['x'].iloc[i], df['y'].iloc[i]
            if x >= x_center and y >= y_center:
                quadrants[0] += 1
            elif x < x_center and y >= y_center:
                quadrants[1] += 1
            elif x < x_center and y < y_center:
                quadrants[2] += 1
            else:
                quadrants[3] += 1
        
        quadrants = quadrants / len(df)
        features.extend(quadrants)  # quadrant_ratios
        
        return np.array(features)
    
    def _extract_frequency_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract frequency domain features"""
        features = []
        n_fft = self.feature_config['n_fft']
        
        # FFT of x and y coordinates
        for col in ['x', 'y']:
            signal = df[col].values
            if len(signal) > n_fft:
                signal = signal[:n_fft]
            elif len(signal) < n_fft:
                signal = np.pad(signal, (0, n_fft - len(signal)))
            
            fft_result = np.abs(fft(signal))
            features.extend([
                fft_result.mean(),  # avg_fft_magnitude
                fft_result.std(),  # std_fft_magnitude
                np.max(fft_result),  # max_fft_magnitude
            ])
        
        # FFT of velocity
        dx = df['x'].diff()
        dy = df['y'].diff()
        dt = df['timestamp'].diff()
        velocity = np.sqrt(dx**2 + dy**2) / dt
        velocity = velocity.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        signal = velocity.values
        if len(signal) > n_fft:
            signal = signal[:n_fft]
        elif len(signal) < n_fft:
            signal = np.pad(signal, (0, n_fft - len(signal)))
        
        fft_result = np.abs(fft(signal))
        features.extend([
            fft_result.mean(),  # avg_velocity_fft
            fft_result.std(),  # std_velocity_fft
            np.max(fft_result),  # max_velocity_fft
        ])
        
        return np.array(features) 