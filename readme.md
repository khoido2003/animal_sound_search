# Animal Sound Search

## Overview

Animal Sound Search is a web application that allows users to upload animal audio files (WAV format) and find similar sounds based on audio features like RMSE, silence ratio, and frequency magnitude. The project consists of a Flask backend for audio processing and similarity search, and a Svelte frontend for user interaction. The backend processes audio files, extracts features, stores them in a SQLite database, and serves audio via an API. The frontend provides pages to upload new sounds and search for similar ones, displaying results with playable audio links.

## Project Structure

```
E:\ptit\animal_sound_search\
├── python_mfcc_server\       # Flask backend
│   ├── app.py                # Main Flask application
│   ├── dataset\              # Input audio files (e.g., Bird\bird1.wav)
│   ├── processed_dataset\    # Normalized audio files (e.g., Bird\bird_1.wav)
│   ├── animal_sounds.db      # SQLite database for audio features
│   ├── venv\                 # Python virtual environment
│   └── requirements.txt      # Python dependencies
├── svelte-app\               # Svelte frontend
│   ├── src\
│   │   ├── routes\
│   │   │   └── +page.svelte  # Main page with upload and search
│   ├── package.json          # Node.js dependencies
│   └── vite.config.js        # Vite configuration
└── README.md                 # This file
```

## Backend (`python_mfcc_server`)

### Functionality

The Flask backend (`app.py`) handles audio processing, storage, and similarity search:

- **Dataset Processing**:
  - Reads WAV files from `dataset` (e.g., `dataset\Chicken\chicken1.wav`).
  - Normalizes audio to a fixed duration (2 seconds) with silence padding.
  - Saves processed files to `processed_dataset` (e.g., `processed_dataset\Chicken\chicken_1.wav`).
  - Extracts features (RMSE, silence ratio, frequency magnitude) and stores them in `animal_sounds.db`.

- **API Endpoints**:
  - `/api/process-sound` (POST): Processes uploaded audio files, normalizes them, extracts features, and stores them in the database.
  - `/api/search-sounds` (POST): Accepts an audio URL, computes features, and returns the top 3 similar sounds based on feature similarity.
  - `/api/audio/<path:path>` (GET): Serves audio files from `processed_dataset` (e.g., `http://localhost:5000/api/audio/Chicken/chicken_1.wav`).

- **Database**:
  - SQLite database (`animal_sounds.db`) stores audio metadata and features:
    - `file_name`: Name of the processed file (e.g., `chicken_1.wav`).
    - `species`: Animal category (e.g., `Chicken`).
    - `url`: URL to access the audio (e.g., `http://localhost:5000/api/audio/Chicken/chicken_1.wav`).
    - `rmse`, `silence`, `freq_mag`: JSON-encoded feature vectors.

### Dependencies

- `flask`: Web framework for API endpoints.
- `flask-cors`: Handles CORS for frontend requests.
- `librosa`: Audio processing and feature extraction.
- `numpy`: Numerical computations.
- `pandas`: Data handling (used minimally).
- `soundfile`: WAV file reading/writing.
- `sqlalchemy`: SQLite database management.
- `requests`: Downloads audio from URLs.

See `requirements.txt` for version details.

## Frontend (`svelte-app`)

The Svelte frontend provides a user interface to:
- Upload new animal sounds via the “Add New Animal Sound” page.
- Search for similar sounds via the “Find Similar Animal Sounds” page, displaying the top 3 matches with “Listen” links to play audio.

Key files:
- `src/routes/+page.svelte`: Main page with upload and search forms, displaying results with audio links.

## Setup Instructions

### Prerequisites

- **Python 3.8+**: For the Flask backend.
- **Node.js 16+**: For the Svelte frontend.
- **Git**: For cloning the repository (optional).
- **WAV Audio Files**: Place animal sounds in `python_mfcc_server\dataset\<species>` (e.g., `dataset\Chicken\chicken1.wav`).

### Backend Setup

1. **Navigate to Backend Directory**:
   ```bash
   cd E:\ptit\animal_sound_search\python_mfcc_server
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   (venv) pip install -r requirements.txt
   ```
   Or manually:
   ```bash
   (venv) pip install flask flask-cors librosa numpy pandas soundfile sqlalchemy requests
   ```

4. **Prepare Dataset**:
   - Create `dataset` folder with subfolders for each species (e.g., `dataset\Bird`, `dataset\Chicken`).
   - Add WAV files (e.g., `dataset\Chicken\chicken1.wav`).


5. **Run the Server**:
   ```bash
   (venv) python app.py
   ```
   - The server processes `dataset`, creates `processed_dataset` and `animal_sounds.db`, and runs at `http://localhost:5000`.

### Frontend Setup

1. **Navigate to Frontend Directory**:
   ```bash
   cd E:\ptit\animal_sound_search\svelte-app
   ```

2. **Install Dependencies**:
   ```bash
   npm install
   ```

3. **Run the Development Server**:
   ```bash
   npm run dev
   ```
   - The frontend runs at `http://localhost:5173`.

### Usage

1. **Add New Sounds**:
   - Open `http://localhost:5173`.
   - Go to “Add New Animal Sound.”
   - Upload a WAV file, specify the species, and submit.
   - The backend processes the file and stores it.

2. **Search for Similar Sounds**:
   - Go to “Find Similar Animal Sounds.”
   - Upload a test WAV file.
   - View the top 3 similar sounds with “Listen” links to play audio.

## API Details

### `/api/process-sound` (POST)

- **Request**:
  ```json
  {
    "fileName": "chicken_new.wav",
    "species": "Chicken",
    "url": "https://example.com/chicken_new.wav"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Audio chicken_new.wav processed and stored"
  }
  ```

### `/api/search-sounds` (POST)

- **Request**:
  ```json
  {
    "url": "https://example.com/test.wav"
  }
  ```
- **Response**:
  ```json
  {
    "results": [
      {
        "fileName": "chicken_13.wav",
        "species": "Chicken",
        "url": "http://localhost:5000/api/audio/Chicken/chicken_13.wav",
        "similarity": 0.9999
      },
      ...
    ]
  }
  ```

### `/api/audio/<path:path>` (GET)

- Serves audio files from `processed_dataset`.
- Example: `http://localhost:5000/api/audio/Chicken/chicken_13.wav`


