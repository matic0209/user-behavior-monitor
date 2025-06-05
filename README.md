# Mouse Dynamics User Authentication

This project implements a machine learning model to identify users based on their mouse movement patterns.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Prepare data:
- Place `Train_Mouse.csv` in the project root directory
- The CSV file should have the following columns:
  - uid: unique identifier for each mouse event
  - session_id: session identifier
  - user_id: user identifier
  - timestamp: event timestamp
  - event_type: mouse event type (1=release, 2=move, 3=wheel, 4=drag, 5=click)
  - screen_x: x coordinate
  - screen_y: y coordinate

## Training

Run the training script:
```bash
python mouse_dynamics.py
```

This will:
1. Load and process the training data
2. Extract features from mouse movements
3. Train a neural network model
4. Save the trained model and related components

## Output Files

After training, the following files will be generated:
- `mouse_dynamics_model/`: Trained model
- `mouse_dynamics_scaler/`: Feature scaler
- `user_encoder.pkl`: User ID encoder

## Model Details

The model uses the following features:
- Center points of mouse movements
- Click center points
- Initial mouse position
- Movement radius
- Movement slope
- Event type frequencies
- Movement speed metrics
- Number of points

The model architecture is a multilayer perceptron with:
- Input layer: 17 features
- Hidden layer: 40 neurons
- Output layer: number of users 