# In train_svm_genre.py
import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- Configuration ---
INPUT_FILE = 'combined_processed.csv'
MODELS_DIR = 'models'

# These are the 11 features we will use for training
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

# --- 2. Load the SCALER and ENCODER from the RF Genre training ---
print("Loading 'final_genre_scaler.joblib' and 'final_genre_encoder.joblib'...")
try:
    scaler_genre = joblib.load(os.path.join(MODELS_DIR, 'final_genre_scaler.joblib'))
    le_genre = joblib.load(os.path.join(MODELS_DIR, 'final_genre_encoder.joblib'))
except FileNotFoundError:
    print("FATAL ERROR: Could not find 'final_genre_scaler.joblib' or 'final_genre_encoder.joblib'.")
    print("Please run 'train_rf_genre.py' first to create these files.")
    exit()
    
# --- 3. Prepare Data for Training ---
df_trainable = df.dropna(subset=['super_genre'])
if df_trainable.empty:
    print("FATAL ERROR: No data with 'super_genre' labels found.")
    exit()

print(f"Found {len(df_trainable)} tracks with super-genre labels.")

# --- 4. Create Target (y) and Features (X) ---
y = le_genre.transform(df_trainable['super_genre']) 
X = df_trainable[TRAINING_FEATURES]
print(f"Target super-genres: {le_genre.classes_}")

# --- 5. Scale Features ---
X_scaled = scaler_genre.transform(X)

# --- 6. Split Data ---
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

# --- 7. Train SVM Model ---
print("\n--- Training SVM Super-Genre Model (for comparison) ---")
subset_size = 20000 
if len(X_train) > subset_size:
    print(f"Using a subset of {subset_size} samples for SVM training (for speed)...")
    indices = np.random.choice(len(X_train), subset_size, replace=False)
    X_train_sub = X_train[indices]
    y_train_sub = y_train[indices]
else:
    X_train_sub, y_train_sub = X_train, y_train

svm_genre_model = SVC(random_state=42) # Model is named svm_genre_model
svm_genre_model.fit(X_train_sub, y_train_sub)
print("SVM training complete.")

# --- 8. Evaluate Model ---
# ***** FIX #1: Use the correct variable name *****
svm_preds = svm_genre_model.predict(X_test) 
svm_accuracy = accuracy_score(y_test, svm_preds)
print(f"SVM Super-Genre Accuracy: {svm_accuracy:.4f}")

print("\nClassification Report:")
print(classification_report(y_test, svm_preds, target_names=le_genre.classes_))

# --- 9. Generate and Save Confusion Matrix ---
print("Generating SVM Confusion Matrix...")
cm = confusion_matrix(y_test, svm_preds)
plt.figure(figsize=(12, 8))
# ***** FIX #2: Use the correct variable name *****
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=le_genre.classes_, yticklabels=le_genre.classes_)
plt.xlabel('Predicted Label')
plt.ylabel('True Label')
plt.title('SVM Super-Genre Confusion Matrix')
plt.tight_layout()

plot_path = os.path.join(MODELS_DIR, 'svm_super_genre_confusion_matrix.png')
plt.savefig(plot_path)
print(f"✅ Confusion Matrix saved to '{plot_path}'")

# --- 10. Save the Model ---
print(f"\nSaving SVM Super-Genre model (Accuracy: {svm_accuracy:.4f})...")
# ***** FIX #3: Use the correct variable name *****
joblib.dump(svm_genre_model, os.path.join(MODELS_DIR, 'final_svm_genre_model.joblib'))
print("✅ SVM GENRE model saved successfully.")