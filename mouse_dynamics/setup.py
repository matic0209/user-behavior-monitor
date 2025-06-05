from setuptools import setup, find_packages

setup(
    name="mouse_dynamics",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "scikit-learn>=0.24.2",
        "xgboost>=1.4.2",
        "matplotlib>=3.4.2",
        "seaborn>=0.11.1",
        "pyyaml>=5.4.1",
        "optuna>=2.10.0",
        "joblib>=1.0.1",
        "tqdm>=4.62.2",
        "python-dotenv>=0.19.0"
    ],
    python_requires=">=3.8",
) 