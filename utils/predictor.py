"""
utils/predictor.py — MediSense AI
Replaces the old JSON-based predictor with a real ML model.

Public functions used by app.py:
    predict_diseases(symptoms)  →  [(disease_name, confidence_pct), ...]
    get_all_symptoms()          →  [symptom_string, ...]
    get_recommendation(disease) →  {"care_level": "...", "recommendation": "..."}
"""

import os, logging, csv, joblib
import pandas as pd

# Path to trained model file
_BASE        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODEL_PATH  = os.path.join(_BASE, "model",   "medisense_model.pkl")
_REC_PATH    = os.path.join(_BASE, "dataset", "recommendation.csv")

# Load model once when Flask starts (not on every request)
_bundle = None

def _load():
    global _bundle
    if _bundle is None:
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"\n\nModel not found: {_MODEL_PATH}\n"
                "Fix: run  python model/train_model.py  then restart Flask.\n"
            )
        _bundle = joblib.load(_MODEL_PATH)
        logging.info("MediSense model loaded.")
    return _bundle


def predict_diseases(symptoms: list, top_n: int = 5) -> list:
    """
    Args:
        symptoms  : list of strings e.g. ['fever', 'headache', 'chills']
        top_n     : how many results to return (default 5)
    Returns:
        list of (disease_name, confidence_percent) tuples
        e.g. [('Malaria', 72), ('Dengue', 18), ('Typhoid', 6)]
    """
    bundle       = _load()
    model        = bundle["model"]
    encoder      = bundle["encoder"]
    symptom_list = bundle["symptoms"]

    # Normalise: lowercase and strip
    user_syms = {s.strip().lower() for s in symptoms if s.strip()}

    # Build binary feature row — must match training columns exactly
    X = pd.DataFrame(0, index=[0], columns=symptom_list)
    matched = []
    for s in symptom_list:
        if s in user_syms:
            X.at[0, s] = 1
            matched.append(s)

    if not matched:
        return []   # no recognised symptoms → result.html shows the helpful message

    proba   = model.predict_proba(X)[0]
    top_idx = proba.argsort()[::-1][:top_n]

    results = []
    for idx in top_idx:
        confidence = int(round(proba[idx] * 100))
        if confidence == 0:
            break
        disease = encoder.inverse_transform([idx])[0]
        results.append((disease, confidence))

    return results


def get_all_symptoms() -> list:
    """Returns list of all recognised symptom strings (for autocomplete)."""
    return _load()["symptoms"]


def get_recommendation(disease_name: str) -> dict:
    """
    Looks up recommendation.csv for care advice for a given disease.
    Returns {"care_level": "...", "recommendation": "..."} or {}
    """
    if not os.path.exists(_REC_PATH):
        return {}
    with open(_REC_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["disease"].strip().lower() == disease_name.strip().lower():
                return {
                    "care_level"    : row["care_level"],
                    "recommendation": row["recommendation"],
                }
    return {}