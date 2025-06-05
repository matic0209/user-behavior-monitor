import kagglehub
import os
import shutil

def download_dataset():
    print("Downloading mouse dynamics dataset...")
    dataset_path = kagglehub.dataset_download('jaafarnejm/mouse-dynamics-for-user-authentication')
    
    # Move the CSV files to the root directory
    for file in os.listdir(dataset_path):
        if file.endswith('.csv'):
            src = os.path.join(dataset_path, file)
            dst = os.path.join(os.getcwd(), file)
            shutil.copy2(src, dst)
            print(f"Copied {file} to project root directory")
    
    print("Dataset download and setup completed!")

if __name__ == "__main__":
    download_dataset() 