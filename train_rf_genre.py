# In train_rf_genre.py
import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
INPUT_FILE = 'combined_processed.csv'
MODELS_DIR = 'models'

# We'll use the same 11 features we used for the mood model
TRAINING_FEATURES = [
    'danceability', 'energy', 'key', 'loudness', 'speechiness', 
    'acousticness', 'instrumentalness', 'liveness', 'valence', 'tempo',
    'time_signature'
]



# --- 1. Load Data ---
print(f"Loading dataset: {INPUT_FILE}...")
try:
    df = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    print(f"FATAL ERROR: Could not find '{INPUT_FILE}'.")
    print("Please run 'dataprocessing.py' first.")
    exit()

# --- 2. Prepare Data for Training ---
# This is the key difference: We now train on rows that have a 'track_genre' label.
df_trainable = df.dropna(subset=['super_genre'])

if df_trainable.empty:
    # This error message is now updated
    print("FATAL ERROR: No data with 'super_genre' labels found in the processed file.")
    exit()

print(f"Found {len(df_trainable)} tracks with SUPER-GENRE labels to use for training.")

# --- 3. Create Target (y) and Features (X) ---
le_genre = LabelEncoder()
y = le_genre.fit_transform(df_trainable['super_genre'])
X = df_trainable[TRAINING_FEATURES]
print(f"Found {len(le_genre.classes_)} target SUPER-GENRES to train: {le_genre.classes_}")

# --- 4. Scale Features ---
# We create a NEW scaler specifically for this training data
scaler_genre = StandardScaler()
X_scaled = scaler_genre.fit_transform(X)

# --- 5. Split Data ---
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

# --- 6. Train Random Forest Model ---
print("\n--- Training Random Forest GENRE Model (Size Optimized) ---")
# ADJUSTMENTS FOR MAXIMUM SIZE REDUCTION:
# 1. n_estimators=100: Back to 100. It's stable enough and saves 33% space vs 150.
# 2. max_depth=15: Prevents trees from becoming too "tall" and complex.
# 3. min_samples_leaf=5: The Aggressive Pruner. This ensures leaves are "thick", 
#    drastically reducing the number of nodes stored. This is the key to small files.
# 4. class_weight='balanced': Still crucial for accuracy.
rf_genre_model = RandomForestClassifier(
    n_estimators=100, 
    max_depth=15, 
    min_samples_leaf=5, 
    class_weight='balanced',
    random_state=42, 
    n_jobs=-1
)
rf_genre_model.fit(X_train, y_train)

# --- 7. Evaluate Model ---
rf_preds = rf_genre_model.predict(X_test)
rf_accuracy = accuracy_score(y_test, rf_preds)
print(f"Random Forest Genre Accuracy: {rf_accuracy:.4f}")

# Note: The full classification report will be very long, so we'll save it to a file
print("Saving full classification report to 'models/genre_report.txt'...")
report = classification_report(y_test, rf_preds, target_names=le_genre.classes_)
os.makedirs(MODELS_DIR, exist_ok=True)
with open(os.path.join(MODELS_DIR, 'genre_report.txt'), 'w', encoding='utf-8') as f:
    f.write(report)

# --- 8. Generate and Save Confusion Matrix ---
print("Generating Confusion Matrix (this may take a moment)...")
cm = confusion_matrix(y_test, rf_preds)
plt.figure(figsize=(20, 15)) # Make it large to fit all genres
sns.heatmap(cm, annot=False, cmap='Blues', 
            xticklabels=le_genre.classes_, yticklabels=le_genre.classes_)
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title('Random Forest Genre Confusion Matrix')
plt.tight_layout() # Fit labels

plot_path = os.path.join(MODELS_DIR, 'rf_genre_confusion_matrix.png')
plt.savefig(plot_path)
print(f"✅ Confusion Matrix saved to '{plot_path}'")

# --- 9. Save the Model and Processors ---
print(f"\nSaving Random Forest Genre model (Accuracy: {rf_accuracy:.4f})...")
# Keep compression at 9
joblib.dump(rf_genre_model, os.path.join(MODELS_DIR, 'final_genre_model.joblib'), compress=9)
joblib.dump(scaler_genre, os.path.join(MODELS_DIR, 'final_genre_scaler.joblib'), compress=9)
joblib.dump(le_genre, os.path.join(MODELS_DIR, 'final_genre_encoder.joblib'), compress=9)

print("✅ Random Forest GENRE model, scaler, and encoder saved successfully.")