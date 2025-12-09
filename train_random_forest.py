import pandas as pd
import joblib
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
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

# --- 2. Prepare Data for Training ---
# We can now train on ALL rows, as they all have a 'mood' label
df_trainable = df.dropna(subset=['mood'] + TRAINING_FEATURES)
print(f"Using {len(df_trainable)} tracks to train the mood model.")

# --- 3. Create Target (y) and Features (X) ---
le = LabelEncoder()
y = le.fit_transform(df_trainable['mood'])
X = df_trainable[TRAINING_FEATURES]
print(f"Target moods to train: {le.classes_}") # Should be all 4 quadrants

# --- 4. Scale Features ---
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# --- 5. Split Data ---
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
print(f"Training on {len(X_train)} samples, testing on {len(X_test)} samples.")

# --- 6. Train Random Forest Model ---
print("\n--- Training Random Forest Mood Model (Optimized High-Acc) ---")
# ADJUSTMENTS FOR <100MB SIZE:
# 1. n_estimators=150: Good middle ground. 200 is too heavy for GitHub.
# 2. max_depth=25: Allows very deep learning, but prevents infinite growth.
# 3. min_samples_leaf=2: The "Magic Bullet". Prevents the model from creating 
#    a branch for just ONE song. This cuts file size by ~40% with almost no accuracy loss.
# 4. class_weight='balanced': KEY for your accuracy on 'Calm' songs.
rf_model = RandomForestClassifier(
    n_estimators=150, 
    max_depth=25,       
    min_samples_leaf=2,  
    class_weight='balanced', 
    random_state=42, 
    n_jobs=-1
)
rf_model.fit(X_train, y_train)

# --- 7. Evaluate Model ---
rf_preds = rf_model.predict(X_test)
print("Random Forest Mood Accuracy:", accuracy_score(y_test, rf_preds))
print("\nClassification Report:")
print(classification_report(y_test, rf_preds, target_names=le.classes_))

# --- 8. Generate and Save Confusion Matrix ---
print("Generating Confusion Matrix...")
cm = confusion_matrix(y_test, rf_preds)
plt.figure(figsize=(10, 7))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
            xticklabels=le.classes_, yticklabels=le.classes_)
plt.xlabel('Predicted Label'); plt.ylabel('True Label')
plt.title('Random Forest Mood Confusion Matrix')
plot_path = os.path.join(MODELS_DIR, 'final_mood_confusion_matrix.png')
plt.savefig(plot_path)
print(f"✅ Confusion Matrix saved to '{plot_path}'")

# --- 9. Save the Model and Processors ---
print("\nSaving Random Forest MOOD model...")
os.makedirs(MODELS_DIR, exist_ok=True)

# CRITICAL: Keep compression at 9 (Maximum)
joblib.dump(rf_model, os.path.join(MODELS_DIR, 'final_mood_model.joblib'), compress=9)
joblib.dump(scaler, os.path.join(MODELS_DIR, 'final_mood_scaler.joblib'), compress=9)
joblib.dump(le, os.path.join(MODELS_DIR, 'final_mood_encoder.joblib'), compress=9)
print("✅ MOOD model saved (Max Compressed).")