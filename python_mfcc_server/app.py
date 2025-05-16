from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import librosa
import numpy as np
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import requests
import os
import json
import soundfile as sf
import pandas as pd

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Database setup (SQLite)
DATABASE_URL = "sqlite:///animal_sounds.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Define SQL table for animal_sounds
class AnimalSound(Base):
    __tablename__ = 'animal_sounds'
    id = Column(Integer, primary_key=True)
    file_name = Column(String(255), nullable=False, unique=True)
    species = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    rmse = Column(Text, nullable=False)
    silence = Column(Text, nullable=False)
    freq_mag = Column(Text, nullable=False)

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Configuration
INPUT_DIR = "dataset"
OUTPUT_DIR = "processed_dataset"
BASE_URL = "http://localhost:5000/api/audio"  
TARGET_DURATION = 2.0
SILENCE_DURATION = 0.2
TOP_N_FILES = 20
WEIGHT_SILENCE = 0.1
WEIGHT_RMSE = 0.3
WEIGHT_FREQ_MAG = 0.3

# Core functions
def normalize_duration(audio, sr, target_duration=2.0, silence_duration=0.2):
    target_length = int(sr * target_duration)
    silence = np.zeros(int(sr * silence_duration))
    segments = []
    current_length = 0
    while current_length < target_length:
        remaining = target_length - current_length
        if len(audio) <= remaining:
            segments.append(audio)
            current_length += len(audio)
        else:
            segments.append(audio[:remaining])
            current_length += remaining
            break
        if current_length + len(silence) <= target_length:
            segments.append(silence)
            current_length += len(silence)
        else:
            break
    looped = np.concatenate(segments)
    if len(looped) < target_length:
        looped = np.pad(looped, (0, target_length - len(looped)), mode='constant')
    return looped[:target_length]

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def process_dataset():
    for animal in os.listdir(INPUT_DIR):
        animal_folder = os.path.join(INPUT_DIR, animal)
        if not os.path.isdir(animal_folder):
            continue
        file_durations = []
        for file in os.listdir(animal_folder):
            if file.endswith(".wav"):
                file_path = os.path.join(animal_folder, file)
                try:
                    duration = librosa.get_duration(path=file_path)
                    file_durations.append((file, duration))
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
        file_durations.sort(key=lambda x: x[1])
        selected_files = file_durations[:TOP_N_FILES]
        output_animal_folder = os.path.join(OUTPUT_DIR, animal)
        ensure_dir(output_animal_folder)
        for idx, (file, _) in enumerate(selected_files, start=1):
            src = os.path.join(animal_folder, file)
            new_filename = f"{animal.lower()}_{idx}.wav"
            dst = os.path.join(output_animal_folder, new_filename)
            try:
                y, sr = librosa.load(src, sr=None)
                y_fixed = normalize_duration(y, sr, TARGET_DURATION)
                sf.write(dst, y_fixed, sr)
                # Store in database with Flask-served URL
                audio_url = f"{BASE_URL}/{animal}/{new_filename}"
                features = extract_features_single(dst)
                session = Session()
                new_sound = AnimalSound(
                    file_name=new_filename,
                    species=animal,
                    url=audio_url,
                    rmse=json.dumps(features["rmse"]),
                    silence=json.dumps(features["silence"]),
                    freq_mag=json.dumps(features["freq_mag"])
                )
                session.add(new_sound)
                session.commit()
                session.close()
            except Exception as e:
                print(f"Error processing {src}: {e}")
        print(f"Processed {animal}: {len(selected_files)} files")

def compute_rmse(y, sr):
    FRAME_SIZE = 1024
    HOP_LENGTH = 512
    rms = librosa.feature.rms(y=y, frame_length=FRAME_SIZE, hop_length=HOP_LENGTH)[0]
    arr = np.array_split(rms, 8)
    result = []
    for segment in arr:
        sum_diff = 0
        count = 0
        for j in range(len(segment) - 1):
            current = segment[j]
            next_val = segment[j + 1]
            if current != 0:
                sum_diff += abs(current - next_val) / current * 100
            count += 1
        avg_diff = sum_diff / count if count != 0 else 0
        result.append(float(avg_diff))
    return result

def compute_silence_ratio(y, sr):
    segment_size = len(y) // 8
    result = []
    for i in range(8):
        start = i * segment_size
        end = min((i + 1) * segment_size, len(y))
        segment = y[start:end]
        median = np.median(segment)
        threshold = median * 0.3
        above_threshold = sum(1 for x in segment if x > threshold)
        silence_percent = 100 - (above_threshold / (end - start)) * 100
        result.append(float(silence_percent))
    return result

def compute_frequency_magnitude(audio, sr, num_segments=8):
    X = np.fft.fft(audio)
    X_mag = np.abs(X)[:len(X) // 2]
    freqs = np.linspace(0, sr / 2, len(X_mag))
    segment_size = len(X_mag) // num_segments
    freq_bins = []
    magnitudes = []
    for i in range(num_segments):
        start = i * segment_size
        end = (i + 1) * segment_size if i != num_segments - 1 else len(X_mag)
        segment = X_mag[start:end]
        max_idx = np.argmax(segment)
        max_mag = segment[max_idx]
        abs_idx = start + max_idx
        freq_bins.append(float(freqs[abs_idx]))
        magnitudes.append(float(max_mag))
    return list(zip(freq_bins, magnitudes))

def extract_features_single(file_path):
    y, sr = librosa.load(file_path)
    return {
        "rmse": compute_rmse(y, sr),
        "silence": compute_silence_ratio(y, sr),
        "freq_mag": compute_frequency_magnitude(y, sr)
    }

def compute_similarity(vec1, vec2):
    sim = 0
    for i in range(8):
        s1, s2 = vec1["silence"][i], vec2["silence"][i]
        sim += abs(s1 - s2) / max(s1, s2, 1e-6) * WEIGHT_SILENCE
        r1, r2 = vec1["rmse"][i], vec2["rmse"][i]
        sim += abs(r1 - r2) / max(r1, r2, 1e-6) * WEIGHT_RMSE
        f1, m1 = vec1["freq_mag"][i]
        f2, m2 = vec2["freq_mag"][i]
        sim += abs(f1 - f2) / max(f1, f2, 1e-6) * WEIGHT_FREQ_MAG / 2
        sim += abs(m1 - m2) / max(m1, m2, 1e-6) * WEIGHT_FREQ_MAG / 2
    return sim

def download_and_normalize(url, output_path):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to download audio")
    temp_file = "temp_audio.wav"
    with open(temp_file, 'wb') as f:
        f.write(response.content)
    y, sr = librosa.load(temp_file, sr=None)
    y_fixed = normalize_duration(y, sr, TARGET_DURATION)
    sf.write(output_path, y_fixed, sr)
    os.remove(temp_file)
    return output_path

# New endpoint to serve audio files
@app.route('/api/audio/<path:path>')
def serve_audio(path):
    try:
        # Serve files from processed_dataset
        return send_from_directory(OUTPUT_DIR, path, mimetype='audio/wav')
    except Exception as e:
        return jsonify({"error": f"Audio file not found: {str(e)}"}), 404

# Endpoint for admin uploads
@app.route('/api/process-sound', methods=['POST'])
def process_sound():
    try:
        data = request.get_json()
        file_name = data['fileName']
        species = data['species']
        url = data['url']
        if not all([file_name, species, url]):
            return jsonify({"error": "Missing file_name, species, or url"}), 400
        # Download and normalize audio
        output_path = os.path.join(OUTPUT_DIR, species, file_name)
        ensure_dir(os.path.dirname(output_path))
        download_and_normalize(url, output_path)
        # Extract features
        features = extract_features_single(output_path)
        # Store in database with Flask-served URL
        audio_url = f"{BASE_URL}/{species}/{file_name}"
        session = Session()
        new_sound = AnimalSound(
            file_name=file_name,
            species=species,
            url=audio_url,
            rmse=json.dumps(features["rmse"]),
            silence=json.dumps(features["silence"]),
            freq_mag=json.dumps(features["freq_mag"])
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
        # Download and normalize test audio
        temp_output = "temp_test.wav"
        download_and_normalize(url, temp_output)
        # Extract features for test audio
        new_vec = extract_features_single(temp_output)
        # Fetch all stored sounds
        session = Session()
        stored_sounds = session.query(AnimalSound).all()
        # Compute similarities
        similarities = []
        for sound in stored_sounds:
            existing_vec = {
                "rmse": json.loads(sound.rmse),
                "silence": json.loads(sound.silence),
                "freq_mag": json.loads(sound.freq_mag)
            }
            score = compute_similarity(new_vec, existing_vec)
            # Convert score to similarity percentage
            similarity_percent = max(0, 100 - (score / 10) * 100)
            similarities.append({
                'fileName': sound.file_name,
                'species': sound.species,
                'url': sound.url,
                'similarity': similarity_percent / 100
            })
        # Sort by similarity and take top 3
        similarities = sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:3]
        session.close()
        os.remove(temp_output)
        return jsonify({"results": similarities}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400




if __name__ == '__main__':
    # Pre-process dataset on startup
    if not os.path.exists(OUTPUT_DIR) and os.path.exists(INPUT_DIR):
        print("Processing dataset...")
        process_dataset()
    app.run(host='0.0.0.0', port=5000, debug=True)
