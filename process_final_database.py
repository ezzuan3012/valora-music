# In process_final_database.py
import pandas as pd
import joblib
import os
import numpy as np
from tqdm import tqdm

# --- Configuration ---
INPUT_FILE = 'combined_processed.csv'
MODELS_DIR = 'models'
OUTPUT_FILE = 'valora_database.csv' # The final file for the app

# --- 1. Load All Models and Processors ---
print("Loading all trained models and processors...")
try:
    # Load Mood Model files
    mood_model = joblib.load(os.path.join(MODELS_DIR, 'final_rf_model.joblib'))
    mood_scaler = joblib.load(os.path.join(MODELS_DIR, 'final_scaler.joblib'))
    mood_encoder = joblib.load(os.path.join(MODELS_DIR, 'final_encoder.joblib'))
    mood_model_features = mood_scaler.feature_names_in_ 
    
    # Load Genre Model files
    genre_model = joblib.load(os.path.join(MODELS_DIR, 'final_genre_model.joblib'))
    genre_scaler = joblib.load(os.path.join(MODELS_DIR, 'final_genre_scaler.joblib'))
    genre_encoder = joblib.load(os.path.join(MODELS_DIR, 'final_genre_encoder.joblib'))
    genre_model_features = genre_scaler.feature_names_in_
    
    print("✅ All models loaded successfully.")

except FileNotFoundError as e:
    print(f"FATAL ERROR: Could not load a required model file. {e}")
    print("Please run all 'train_...' scripts first.")
    exit()

# --- 2. Load the Combined Dataset ---
print(f"Loading dataset: {INPUT_FILE}...")
try:
    df = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    print(f"FATAL ERROR: Could not find '{INPUT_FILE}'.")
    print("Please run 'dataprocessing.py' first.")
    exit()

print(f"Loaded {len(df)} total tracks.")

# --- 3. Predict Missing MOODS ---
# We defined our moods from valence/energy for ALL tracks in dataprocessing.py
# So, we just need to standardize the labels for the app.
# The 'mood' column from data_moods.csv ('Happy', 'Sad', etc.)
# and the 'mood' column we created from valence/energy ('Happy/Energetic', etc.)
# are now mixed. Let's create ONE final 'app_mood' column.

print("Standardizing mood labels for the application...")
tqdm.pandas(desc="Standardizing Moods")

def get_quadrant_mood(row):
    """
    Creates the 4-quadrant mood label from valence/energy.
    This ensures consistency for all 90k+ tracks.
    """
    try:
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

# Re-create the 'app_mood' column for ALL tracks to be 100% consistent
df['app_mood'] = df.progress_apply(get_quadrant_mood, axis=1)

# --- 4. Predict Missing SUPER-GENRES ---
genre_missing_mask = df['super_genre'].isna()
tracks_to_predict_genre = df[genre_missing_mask]

if not tracks_to_predict_genre.empty:
    print(f"Predicting super-genre for {len(tracks_to_predict_genre)} missing tracks...")
    
    # Ensure all required features are present
    if not all(col in tracks_to_predict_genre.columns for col in genre_model_features):
        print("FATAL ERROR: Dataset is missing features required by the GENRE model.")
        exit()

    # Scale features
    X_genre = tracks_to_predict_genre[genre_model_features]
    X_genre_scaled = genre_scaler.transform(X_genre)
    
    # Predict
    genre_preds = genre_model.predict(X_genre_scaled)
    genre_labels = genre_encoder.inverse_transform(genre_preds)
    
    # Fill in the blanks
    df.loc[genre_missing_mask, 'super_genre'] = genre_labels
    print("Super-genre prediction complete.")
else:
    print("No missing super-genre labels to predict.")

# --- 5. Save the Final Database ---
# We only need the identifiers and the final predicted labels
final_columns = ['track_id', 'track_name', 'artists', 'app_mood', 'super_genre']

df_final = df[final_columns]
# Drop any rows that still have nulls in our key labels
df_final = df_final.dropna(subset=['app_mood', 'super_genre'])

print(f"\nFinal database has {len(df_final)} tracks.")
print("\nFinal App Mood Distribution:")
print(df_final['app_mood'].value_counts())
print("\nFinal Super-Genre Distribution:")
print(df_final['super_genre'].value_counts())

print(f"\nSaving final database to '{OUTPUT_FILE}'...")
try:
    df_final.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ Successfully saved final database to '{OUTPUT_FILE}'.")
    print("Lets Build This Yankee Ass System!")
except Exception as e:
    print(f"\nFATAL ERROR: Could not save final file. Error: {e}")

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