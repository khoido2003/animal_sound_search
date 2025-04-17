from flask import Flask, request, jsonify
from flask_cors import CORS
import librosa
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
import os
import json
from scipy.spatial.distance import cosine

app = Flask(__name__)

# Enable CORS for requests from Svelte app (e.g., http://localhost:5173)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Database setup (SQLite)
DATABASE_URL = "sqlite:///animal_sounds.db"  # Creates animal_sounds.db in project directory
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define SQL table for animal_sounds
class AnimalSound(Base):
    __tablename__ = 'animal_sounds'
    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False, unique=True)
    species = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    mfcc_features = Column(Text, nullable=False)  # JSON string of MFCC coefficients

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Function to extract and normalize MFCC features
def extract_mfcc(audio_url):
    try:
        # Download the audio file from the URL
        response = requests.get(audio_url)
        if response.status_code != 200:
            raise Exception("Failed to download audio")
        temp_file = "temp_audio.wav"
        with open(temp_file, 'wb') as f:
            f.write(response.content)

        # Load audio and extract MFCC
        y, sr = librosa.load(temp_file, sr=44100, mono=True)  # Standard sample rate, mono
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)  # 13 coefficients
        mfcc_mean = np.mean(mfcc, axis=1)  # Average over time
        # Normalize to unit length for precise cosine similarity
        mfcc_normalized = mfcc_mean / np.linalg.norm(mfcc_mean)
        if np.isnan(mfcc_normalized).any():
            raise Exception("Invalid MFCC features (contains NaN)")
        mfcc_list = mfcc_normalized.tolist()

        # Clean up temporary file
        os.remove(temp_file)
        return mfcc_list
    except Exception as e:
        raise Exception(f"Failed to extract MFCC: {str(e)}")

# Endpoint for admin uploads
@app.route('/api/process-sound', methods=['POST'])
def process_sound():
    try:
        data = request.get_json()
        file_name = data['fileName']
        species = data['species']
        url = data['url']

        # Validate inputs
        if not all([file_name, species, url]):
            return jsonify({"error": "Missing file_name, species, or url"}), 400

        # Extract MFCC features
        mfcc_features = extract_mfcc(url)
        mfcc_json = json.dumps(mfcc_features)  # Convert to JSON string

        # Store in database
        session = Session()
        new_sound = AnimalSound(
            file_name=file_name,
            species=species,
            url=url,
            mfcc_features=mfcc_json
        )
        session.add(new_sound)
        session.commit()
        session.close()

        return jsonify({"message": f"Audio {file_name} processed and stored"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Endpoint for user searches
@app.route('/api/search-sounds', methods=['POST'])
def search_sounds():
    try:
        data = request.get_json()
        url = data['url']

        # Extract MFCC features from user-uploaded sound
        query_mfcc = np.array(extract_mfcc(url))

        # Fetch all stored sounds
        session = Session()
        stored_sounds = session.query(AnimalSound).all()

        # Compute cosine similarity
        similarities = []
        for sound in stored_sounds:
            stored_mfcc = np.array(json.loads(sound.mfcc_features))
            similarity = 1 - cosine(query_mfcc, stored_mfcc)  # Convert distance to similarity
            similarities.append({
                'fileName': sound.file_name,
                'species': sound.species,
                'url': sound.url,
                'similarity': similarity
            })

        # Sort by similarity and take top 3
        similarities = sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:3]

        session.close()
        return jsonify({"results": similarities}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
