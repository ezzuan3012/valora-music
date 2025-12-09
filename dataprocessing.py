# In dataprocessing.py
import pandas as pd
import numpy as np
import os
from tqdm import tqdm

# --- Configuration ---
FILE_A = 'spotify_huggingface.csv'
FILE_B = 'data_moods.csv'
OUTPUT_FILE = 'combined_processed.csv'

# These are the 11 features present in BOTH datasets.
TRAINING_FEATURES = [
    'danceability', 'energy', 'key', 'loudness', 'speechiness', 
    'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo',
    'time_signature'
]

# --- Function to create the 4 Quadrant Moods ---
def get_quadrant_mood(row):
    try:
        # We need both valence and energy to determine the mood
        valence = float(row['valence'])
        energy = float(row['energy'])
    except (ValueError, TypeError):
        return np.nan # Not enough data

    if valence >= 0.5 and energy >= 0.5:
        return 'Happy/Energetic'
    elif valence >= 0.5 and energy < 0.5:
        return 'Calm/Peaceful'
    elif valence < 0.5 and energy >= 0.5:
        return 'Angry/Tense'
    else: # valence < 0.5 and energy < 0.5
        return 'Sad/Melancholy'

# --- Function to create Super-Genres ---
def create_super_genre(genre_str):
    if not isinstance(genre_str, str):
        return np.nan # Return NaN if the genre is blank
    genre = genre_str.lower()
    if 'rock' in genre or 'punk' in genre or 'alternative' in genre or 'grunge' in genre or 'indie' in genre:
        return 'Rock/Alternative'
    if 'electronic' in genre or 'house' in genre or 'techno' in genre or 'trance' in genre or 'edm' in genre or 'dance' in genre or 'dubstep' in genre:
        return 'Electronic/Dance'
    if 'pop' in genre or 'r-n-b' in genre or 'soul' in genre or 'funk' in genre:
        return 'Pop/R&B/Soul'
    if 'hip-hop' in genre or 'rap' in genre:
        return 'Hip-Hop'
    if 'jazz' in genre or 'blues' in genre or 'reggae' in genre:
        return 'Jazz/Blues/Reggae'
    if 'classical' in genre or 'acoustic' in genre or 'ambient' in genre or 'piano' in genre:
        return 'Classical/Acoustic'
    if 'metal' in genre:
        return 'Metal'
    return 'Other'

# --- Main Processing Function ---
def process_data():
    tqdm.pandas(desc="Applying functions")
    
    # --- Load Dataset A (spotify_huggingface.csv) ---
    print(f"Loading {FILE_A}...")
    try:
        df_a = pd.read_csv(FILE_A)
        if df_a.columns[0].startswith('Unnamed'):
            df_a = df_a.drop(df_a.columns[0], axis=1)
        cols_to_keep_a = ['track_id', 'track_name', 'artists', 'track_genre'] + TRAINING_FEATURES
        df_a = df_a[cols_to_keep_a]
        print(f"Loaded {len(df_a)} rows from {FILE_A}.")
    except Exception as e:
        print(f"Error loading {FILE_A}: {e}"); return

    # --- Load Dataset B (data_moods.csv) ---
    print(f"\nLoading {FILE_B}...")
    try:
        df_b = pd.read_csv(FILE_B)
        cols_rename_b = {
            'id': 'track_id', 'name': 'track_name', 'artist': 'artists',
            **{feature: feature for feature in TRAINING_FEATURES}
        }
        df_b = df_b[list(cols_rename_b.keys())]
        df_b = df_b.rename(columns=cols_rename_b)
        df_b['track_genre'] = np.nan
        print(f"Loaded {len(df_b)} rows from {FILE_B}.")
    except Exception as e:
        print(f"Error loading {FILE_B}: {e}"); return

    # --- Combine Datasets ---
    print("\nCombining datasets...")
    df_combined = pd.concat([df_a, df_b], ignore_index=True, sort=False)
    
    # --- Clean Data ---
    df_combined = df_combined.drop_duplicates(subset=['track_id'], keep='first')
    df_combined = df_combined.dropna(subset=TRAINING_FEATURES)
    print(f"Total rows after deduplication & cleaning: {len(df_combined)}")
    
    # --- Create Labels ---
    print("Creating super-genre labels...")
    df_combined['super_genre'] = df_combined['track_genre'].progress_apply(create_super_genre)
    
    print("Creating 4-quadrant mood labels...")
    df_combined['mood'] = df_combined.progress_apply(get_quadrant_mood, axis=1)

    # --- Final Output ---
    # Now we drop any rows that couldn't get a mood (e.g., missing valence/energy)
    df_final = df_combined.dropna(subset=['mood'])
    
    # We will keep 'super_genre' even if it's NaN, we can predict it later
    final_columns = ['track_id', 'track_name', 'artists', 'mood', 'super_genre'] + TRAINING_FEATURES
    df_final = df_final[final_columns]
    
    print("\n--- Processing Complete ---")
    print(f"\nFinal dataset has {len(df_final)} clean tracks with mood labels.")
    print("\nMood Distribution:")
    print(df_final['mood'].value_counts())
    print("\nSuper-Genre Distribution (Partial):")
    print(df_final['super_genre'].value_counts())
    
    # --- Save to File ---
    try:
        df_final.to_csv(OUTPUT_FILE, index=False)
        print(f"\n✅ Successfully saved cleaned data to '{OUTPUT_FILE}'.")
    except Exception as e:
        print(f"\nError: Could not save file. {e}")

# --- Run the Script ---
if __name__ == "__main__":
    try:
        from tqdm import tqdm
        tqdm.pandas()
    except ImportError:
        print("Installing 'tqdm' for progress bars...")
        import subprocess, sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "tqdm"])
        from tqdm import tqdm
        tqdm.pandas()
        
    process_data()