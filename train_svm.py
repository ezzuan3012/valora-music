# In train_svm_mood.py
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

# These are the features we use to PREDICT mood
# We MUST exclude 'valence' and 'energy' to prevent data leakage!
TRAINING_FEATURES = [
    'danceability', 'key', 'loudness', 'speechiness', 'acousticness', 
    'instrumentalness', 'liveness', 'tempo', 'time_signature'
]

# --- 1. Load Data ---
print(f"Loading dataset: {INPUT_FILE}...")
try:
    df = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    print(f"FATAL ERROR: Could not find '{INPUT_FILE}'. Run dataprocessing.py first.")
    exit()

# --- 2. Load the SCALER and ENCODER from the RF training ---
# We MUST use the same scaler/encoder for a fair comparison
print("Loading 'final_mood_scaler.joblib' and 'final_mood_encoder.joblib'...")
try:
    scaler = joblib.load(os.path.join(MODELS_DIR, 'final_mood_scaler.joblib'))
    le = joblib.load(os.path.join(MODELS_DIR, 'final_mood_encoder.joblib'))
except FileNotFoundError:
    print("FATAL ERROR: Could not find 'final_mood_scaler.joblib' or 'final_mood_encoder.joblib'.")
    print("Please run 'train_rf_mood.py' first to create these files.")
    exit()
    
# --- 3. Prepare Data for Training ---
df_trainable = df.dropna(subset=['mood'] + TRAINING_FEATURES)
print(f"Using {len(df_trainable)} tracks to train the mood model.")

# --- 4. Create Target (y) and Features (X) ---
y = le.transform(df_trainable['mood']) # Use loaded encoder
X = df_trainable[TRAINING_FEATURES]
print(f"Target moods to train: {le.classes_}")

# --- 5. Scale Features ---
X_scaled = scaler.transform(X) # Use loaded scaler

# --- 6. Split Data ---
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

# --- 7. Train SVM Model ---
print("\n--- Training SVM Mood Model (for comparison) ---")
# SVM is slow. We'll use a subset.
subset_size = 20000 
if len(X_train) > subset_size:
    print(f"Using a subset of {subset_size} samples for SVM training (for speed)...")
    indices = np.random.choice(len(X_train), subset_size, replace=False)
    X_train_sub = X_train[indices]
    y_train_sub = y_train[indices]
else:
    X_train_sub, y_train_sub = X_train, y_train

svm_model = SVC(random_state=42)
svm_model.fit(X_train_sub, y_train_sub)
print("SVM training complete.")

# --- 8. Evaluate Model ---
svm_preds = svm_model.predict(X_test)
svm_accuracy = accuracy_score(y_test, svm_preds) # This will work now
print(f"SVM Mood Accuracy: {svm_accuracy:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, svm_preds, target_names=le.classes_))

# --- 9. Generate and Save Confusion Matrix ---
print("Generating SVM Confusion Matrix...")
cm = confusion_matrix(y_test, svm_preds)
plt.figure(figsize=(10, 7))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.xlabel('Predicted Label'); plt.ylabel('True Label')
plt.title('SVM Mood Confusion Matrix')
plot_path = os.path.join(MODELS_DIR, 'final_mood_confusion_matrix_SVM.png')
plt.savefig(plot_path)
print(f"✅ Confusion Matrix saved to '{plot_path}'")

# --- 10. Save the Model ---
print(f"\nSaving SVM MOOD model (Accuracy: {svm_accuracy:.4f})...")
os.makedirs(MODELS_DIR, exist_ok=True)
joblib.dump(svm_model, os.path.join(MODELS_DIR, 'final_svm_mood_model.joblib'))
print("✅ SVM MOOD model saved successfully.")