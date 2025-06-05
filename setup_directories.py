import os
import shutil

def setup_directories():
    # Get the base directory (where this script is located)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define directory paths
    data_dir = os.path.join(base_dir, 'data')
    models_dir = os.path.join(base_dir, 'models')
    scalers_dir = os.path.join(base_dir, 'scalers')
    
    # Create directories
    for dir_path in [data_dir, models_dir, scalers_dir]:
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Move data files if they exist in the root directory
    data_files = ['Train_Mouse.csv', 'Test_Mouse.csv']
    for file in data_files:
        src = os.path.join(base_dir, file)
        dst = os.path.join(data_dir, file)
        if os.path.exists(src):
            shutil.move(src, dst)
            print(f"Moved {file} to data directory")

if __name__ == "__main__":
    setup_directories() 