# Animal Sound Search System

## Overview
A system to store and search animal sounds using MFCCs and cosine similarity.

## Dataset
- 200 WAV/MP3 files, 10 species (Bird, Cat, etc.), 20 files each.
- Stored in `sounds_data/`.

## System
- **Admin Page**: Uploads sounds to UploadThing, stores in SQLite.
- **User Page**: Uploads a sound, returns top 3 similar sounds.
- **Server**: Flask with `/api/process-sound`,  `/api/search-sounds`.
- **Database**: SQLite (`animal_sounds.db`).

## Feature Extraction, Storage, and Search
- **Extraction**:
  - MFCCs (13 coefficients) are extracted using `librosa` at 44.1 kHz, mono.
  - Steps: Download audio, compute MFCCs, average over time, normalize.
  - Used for both database seeding and user searches.
- **Storage**:
  - SQLite database (`animal_sounds.db`) stores `file_name`, `species`, `url`, and `mfcc_features`.
  - `mfcc_features` is a JSON string of 13 normalized MFCCs.
- **Search**:
  - Input audio’s MFCCs are extracted and compared to all stored MFCCs.
  - Cosine similarity ranks matches; top 3 are returned.
  - Results include file name, species, URL, and similarity score.

## Process Flow
1. User uploads a WAV/MP3 file via the web interface.
2. The file is uploaded to UploadThing, which returns a URL.
3. The URL is sent to the Flask server’s /api/search-sounds endpoint.
4. The server downloads the audio, extracts 13 MFCCs, and normalizes them.
5. Cosine similarity compares the input MFCCs to all stored MFCCs in the database.
6. The top 3 matches (fileName, species, url, similarity) are returned and displayed.

```
[User Audio File (WAV/MP3)]
         |
         v
[Svelte User Page: UploadButton]
         |
         v
[UploadThing: Stores File, Returns URL]
         |
         v
[Svelte: Sends URL to Flask /api/search-sounds]
         |
         v
[Flask Server]
    |----------------------------|
    | [Download Audio]          |
    | [Extract MFCCs]           |
    | [Compare with DB MFCCs]    |
    | [SQLite: animal_sounds.db] |
    |----------------------------|
         |
         v
[Return Top 3 Matches: fileName, species, url, similarity]
         |
         v
[Svelte User Page: Display Results]


```

## Setup
1. Run Flask: `cd python_mfcc_server; python app.py`.
2. Run Svelte: `cd animal_sound_search_web; npm run dev`.
4. Access: `http://localhost:5173`.
