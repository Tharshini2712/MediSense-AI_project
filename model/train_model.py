"""
MediSense AI — train_model.py
Place this file inside:  MediSense-AI/model/train_model.py

Run it ONCE from the VS Code terminal:
    python model/train_model.py

Creates:
    model/medisense_model.pkl   ← trained ML model loaded by predictor.py
    model/model_meta.json       ← accuracy info and disease list
"""

import os, json, joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Paths — relative to MediSense-AI root folder
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, "dataset", "disease_dataset.csv")
MODEL_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "medisense_model.pkl")
META_PATH  = os.path.join(MODEL_DIR, "model_meta.json")


def train():
    print("=" * 55)
    print("  MediSense AI — Training ML Model")
    print("=" * 55)

    # Step 1: Load dataset
    print("\n[1/4] Loading dataset/disease_dataset.csv ...")
    if not os.path.exists(DATA_PATH):
        print(f"\n  ERROR: Cannot find {DATA_PATH}")
        print("  Did you paste the data into dataset/disease_dataset.csv?\n")
        return

    df = pd.read_csv(DATA_PATH, on_bad_lines="skip")
    symptom_cols = [c for c in df.columns if c.startswith("Symptom_")]
    for col in symptom_cols:
        df[col] = df[col].apply(
            lambda x: x.strip().lower() if isinstance(x, str) else x
        )
    print(f"  Rows loaded    : {len(df)}")
    print(f"  Diseases found : {df['Disease'].nunique()}")

    # Step 2: Build binary feature matrix
    print("\n[2/4] Building symptom feature matrix ...")
    all_symptoms = sorted(set(
        v.strip() for col in symptom_cols
        for v in df[col].dropna() if str(v).strip()
    ))
    print(f"  Unique symptoms: {len(all_symptoms)}")

    X = pd.DataFrame(0, index=df.index, columns=all_symptoms)
    for col in symptom_cols:
        for s in all_symptoms:
            X.loc[df[col] == s, s] = 1

    le = LabelEncoder()
    y  = le.fit_transform(df["Disease"])

    # Step 3: Train Random Forest
    print("\n[3/4] Training Random Forest (200 trees) ...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    clf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)
    acc = accuracy_score(y_test, clf.predict(X_test))
    print(f"  Test accuracy  : {acc:.2%}")

    # Step 4: Save model + metadata
    print("\n[4/4] Saving model files ...")
    joblib.dump({"model": clf, "encoder": le, "symptoms": all_symptoms}, MODEL_PATH)
    meta = {
        "accuracy"  : round(float(acc), 4),
        "n_diseases": int(df["Disease"].nunique()),
        "n_symptoms": len(all_symptoms),
        "diseases"  : list(le.classes_),
        "symptoms"  : all_symptoms,
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  model/medisense_model.pkl  saved")
    print(f"  model/model_meta.json      saved")
    print("\n" + "=" * 55)
    print("  Done! Now run:  python app.py")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    train()