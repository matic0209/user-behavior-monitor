# Mouse Dynamics Analysis

A comprehensive system for analyzing and monitoring mouse dynamics for user behavior analysis and authentication.

## Project Structure

```
mouse_dynamics/
├── configs/                 # Configuration files
│   └── config.yaml         # Main configuration file
├── data/                   # Data directory
│   ├── training_files/     # Training data files
│   ├── test_files/        # Test data files
│   └── public_labels.csv  # Public labels for test data
├── logs/                   # Log files directory
├── models/                 # Saved models directory
├── src/                    # Source code
│   ├── data/              # Data processing modules
│   │   └── feature_engineering.py
│   ├── models/            # Model training and evaluation
│   │   ├── mouse_dynamics.py
│   │   └── train_model.py
│   └── utils/             # Utility functions
│       └── event_capture.py
└── tests/                 # Test files
```

## Features

- Comprehensive mouse dynamics feature extraction (280+ features)
- Real-time mouse event monitoring
- User behavior analysis and authentication
- XGBoost-based classification model
- Configurable parameters and thresholds

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the system:
- Edit `configs/config.yaml` to set your desired parameters
- Adjust feature extraction parameters as needed

## Usage

1. Train the model:
```bash
python src/models/train_model.py
```

2. Monitor mouse events:
```bash
python src/utils/event_capture.py
```

## Configuration

The system can be configured through `configs/config.yaml`:

- Data paths and directories
- Model parameters
- Feature extraction settings
- Logging configuration

## Features

The system extracts 280+ features from mouse movements, including:

1. Basic Features (11)
   - Position features
   - Click features
   - Time features

2. Movement Features (15)
   - Speed features
   - Acceleration features
   - Jerk features
   - Angle features

3. Event Features (20)
   - Event counts and ratios
   - Event timing features

4. Time Series Features (24)
   - Rolling statistics
   - Window-based analysis

5. Spatial Features (7)
   - Grid distribution
   - Quadrant distribution

6. Frequency Domain Features (9)
   - FFT features
   - Velocity analysis

## License

This project is licensed under the MIT License - see the LICENSE file for details.

BALABIT MOUSE CHALLENGE DATA SET
================================

This repository contains the **[Balabit Mouse Dynamics Challenge][balabit]** data set which includes timing and positioning information of mouse pointers. It can be used for evaluating the performance of behavioral biometric algorithms based on mouse dynamics for user authentication/identification purposes.  
We make the data set accessible to researchers and experts in the fields of IT security and data science with the hope of contributing to research and providing a benchmark data set.  
The data set was first made public during a data science competition on [datapallet.io][datapallet]. The files and descriptions in this repository originate from the challenge itself.  

[balabit]: https://medium.com/balabit-unsupervised/releasing-the-balabit-mouse-dynamics-challenge-data-set-a15a016fba6c
[datapallet]: https://datapallet.io

## The Challenge

The goal of the challenge was to protect a set of users from the unauthorized usage of their accounts by learning the characteristics of how they use their mouses.  

During their work, these users usually log in to remote servers with their remote desktop client. A network monitoring device is set between the client and the remote computer that inspects all traffic as described by the RDP protocol. This includes the mouse interactions of the user that is transmitted from the client to the server during the remote session.  

Once in a while, a user account is stolen and is being used illegally, i.e., by a person that is not the legit owner of the account.  

How can you detect such misuses?  
Fortunately, you have access to the data that was recorded by the network monitoring device. Also, it is supposed that the way a person moves their mouse is specific to them and can be used as a kind of behavioral biometric identifier.  
If you could in fact identify the typical patterns of each user, you would be able to easily notice a stolen account by seeing that the mouse movement data going from the account to the remote server is not characteristic of the owner of said account.  

You have to build a model that can fulfil this task.  

## Session Files

The 'training_files' folder contains 10 folders, one for every user account in the system. In each of these folders, you are given the data of a few remote sessions that are known to be carried out by the legal owners of the respective user accounts.  

The 'test_files' folder contains also 10 folders. Each folder represents a user account, and comprises the data of several shorter sessions. Each of these test sessions was recorded as the session of the respective user account; however, the true identity of the user in a test session is unknown.  

The fields of each session file is to be translated as follows:  
- *record timestamp*: elapsed time (in sec) since the start of the session as recorded by the netork monitoring device  
- *client timestamp*: elapsed time (in sec) since the start of the session as recorded by the RDP client  
- *button*: the current condition of the mouse buttons  
- *state*: additional information about the current state of the mouse  
- *x*: the x coordinate of the cursor on the screen  
- *y*: the y coordinate of the cursor on the screen  

## Labels

In the challenge, for each test session file the task was to provide an anomaly score between 0 and 1 that tells how unlikely it is that the remote session was carried out by the respective user account. Submissions were judged on the area under the ROC curve. The AUC was calculated in a global manner (all predictions together).  

The 'public_labels.csv' file contains the labels of the *public part* of the test data (i.e., those that contributed to the public leaderboard score). Each row describes whether a certain test session capture a legal or an illegal session.  

## Attack Model

Although this data set is offered as benchmark data for detecting illegal account usages, during its creation no such misuses were carried out. All recorded data reflect work executed during authenticated remote sessions that have not been hijacked. The attacks are imitated. For each user, in order to simulate illegal usage of his/her account, data from other users are artificially mixed into the test data of said user. Since all users engage in the same kind of unspecified administative tasks, the data from the artificial attackers do not reflect malicious activities.  

## Citation

If you are using the data in your publication, please cite it as follows:  

Fülöp, Á., Kovács, L., Kurics, T., Windhager-Pokol, E. (2016). *Balabit Mouse Dynamics Challenge data set*. Available at: https://github.com/balabit/Mouse-Dynamics-Challenge  

## Contact

If you wish to contact the authors you may reach them through the [maintainer][maintainer] of this repository or find them with a search engine.

[maintainer]: https://github.com/DataOmbudsman

