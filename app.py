import os
import re

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import HashingVectorizer
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app, origins=["*"])

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
CROP_MODEL_PATH = os.path.join(MODELS_DIR, "crop_model.pkl")
DIABETES_MODEL_PATH = os.path.join(MODELS_DIR, "diabetes_model.pkl")
MENTAL_BURN_MODEL_PATH = os.path.join(MODELS_DIR, "mental_burn_model.pkl")
MENTAL_DEP_MODEL_PATH = os.path.join(MODELS_DIR, "mental_dep_model.pkl")
MENTAL_ANX_MODEL_PATH = os.path.join(MODELS_DIR, "mental_anx_model.pkl")
SPAM_MODEL_PATH = os.path.join(MODELS_DIR, "spam_model.pkl")

CROP_FEATURE_ORDER = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
DIABETES_FEATURE_ORDER = [
    "Age",
    "Gender",
    "Polyuria",
    "Polydipsia",
    "sudden weight loss",
    "weakness",
    "Polyphagia",
    "Genital thrush",
    "visual blurring",
    "Itching",
    "Irritability",
    "delayed healing",
    "partial paresis",
    "muscle stiffness",
    "Alopecia",
    "Obesity"
]
MENTAL_FEATURE_ORDER = [
    "Age",
    "Gender",
    "Occupation",
    "Daily_Screen_Time",
    "Social_Media_Usage",
    "Night_Usage",
    "Sleep_Hours",
    "Stress_Level",
    "Work_Study_Hours",
    "Physical_Activity",
    "Social_Interaction_Score",
    "Caffeine_Intake",
    "Smoking",
    "Alcohol"
]
SPAM_THRESHOLD = 0.4
SPAM_KEYWORD_BOOST = 0.2
SPAM_HINT_KEYWORDS = {
    "win",
    "winner",
    "prize",
    "free",
    "offer",
    "limited",
    "discount",
    "cash",
    "urgent",
    "verify",
    "click",
    "buy now",
    "claim",
    "iphone",
    "suspended"
}

GENDER_MAP = {"Female": 0, "Male": 1}
YES_NO_MAP = {"No": 0, "Yes": 1}
PHYSICAL_ACTIVITY_MAP = {"Low": 0, "Medium": 1, "Moderate": 1, "High": 2}


def load_model(path):
    if not os.path.exists(path):
        return None, f"Model file not found: {path}"
    try:
        return joblib.load(path), None
    except Exception as exc:
        return None, f"Failed to load model: {exc}"


crop_model, crop_model_error = load_model(CROP_MODEL_PATH)
diabetes_model, diabetes_model_error = load_model(DIABETES_MODEL_PATH)
mental_burn_model, mental_burn_model_error = load_model(MENTAL_BURN_MODEL_PATH)
mental_dep_model, mental_dep_model_error = load_model(MENTAL_DEP_MODEL_PATH)
mental_anx_model, mental_anx_model_error = load_model(MENTAL_ANX_MODEL_PATH)
spam_model, spam_model_error = load_model(SPAM_MODEL_PATH)

expected_features = getattr(spam_model, "n_features_in_", None)
spam_vectorizer = None
if spam_model is not None and expected_features:
    spam_vectorizer = HashingVectorizer(
        n_features=int(expected_features),
        ngram_range=(1, 2),
        alternate_sign=False
    )


def predict_numeric(model, values):
    row = np.array(values, dtype=float).reshape(1, -1)
    try:
        return model.predict(row)[0]
    except Exception:
        frame = pd.DataFrame([values])
        return model.predict(frame)[0]


def spam_keyword_hits(text):
    lower = text.lower()
    score = 0
    for keyword in SPAM_HINT_KEYWORDS:
        if keyword in lower:
            score += 1
    return score


def build_mental_frame(payload, model):
    expected_columns = list(getattr(model, "feature_names_in_", []))
    if not expected_columns:
        return pd.DataFrame([payload])

    row = {}
    for column in expected_columns:
        if column.startswith("Occupation_"):
            row[column] = 0.0
        else:
            row[column] = payload.get(column)

    if "Gender" in row:
        row["Gender"] = float(GENDER_MAP.get(str(payload.get("Gender", "")).strip(), 0))

    if "Physical_Activity" in row:
        activity_value = str(payload.get("Physical_Activity", "")).strip()
        row["Physical_Activity"] = float(PHYSICAL_ACTIVITY_MAP.get(activity_value, 0))

    occupation_value = str(payload.get("Occupation", "")).strip()
    occupation_column = f"Occupation_{occupation_value}"
    if occupation_value and occupation_column in row:
        row[occupation_column] = 1.0

    return pd.DataFrame([row], columns=expected_columns)


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.post("/api/predict")
def predict_crop():
    if crop_model is None:
        return jsonify({"error": crop_model_error}), 500

    payload = request.get_json(silent=True) or {}

    try:
        values = [float(payload[key]) for key in CROP_FEATURE_ORDER]
    except KeyError as exc:
        return jsonify({"error": f"Missing input field: {exc.args[0]}"}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "All fields must be numeric."}), 400

    try:
        input_frame = pd.DataFrame([values], columns=CROP_FEATURE_ORDER)
        prediction = crop_model.predict(input_frame)[0]
        probabilities = crop_model.predict_proba(input_frame)[0]
        classes = crop_model.classes_
        top3_indices = probabilities.argsort()[-3:][::-1]
        top3 = [
            {
                "crop": str(classes[i]),
                "confidence": round(float(probabilities[i]) * 100, 1)
            }
            for i in top3_indices
        ]
    except Exception as exc:
        return jsonify({"error": f"Model prediction failed: {str(exc)}"}), 500

    return jsonify({"label": str(prediction), "results": top3})


@app.post("/api/predict/diabetes")
def predict_diabetes():
    if diabetes_model is None:
        return jsonify({"error": diabetes_model_error}), 500

    payload = request.get_json(silent=True) or {}
    missing_fields = [name for name in DIABETES_FEATURE_ORDER if name not in payload]
    if missing_fields:
        return jsonify({"error": f"Missing input field: {missing_fields[0]}"}), 400

    row = {name: payload.get(name) for name in DIABETES_FEATURE_ORDER}
    try:
        row["Age"] = float(row["Age"])
    except (TypeError, ValueError):
        return jsonify({"error": "Age must be numeric."}), 400

    for feature in DIABETES_FEATURE_ORDER:
        if feature in {"Age", "Gender"}:
            continue
        value = str(row[feature]).strip()
        if value not in YES_NO_MAP:
            return jsonify({"error": f"{feature} must be Yes or No."}), 400
        row[feature] = YES_NO_MAP[value]

    gender_value = str(row["Gender"]).strip() if "Gender" in row else ""
    if gender_value not in GENDER_MAP:
        return jsonify({"error": "Gender must be Male or Female."}), 400
    row["Gender"] = GENDER_MAP[gender_value]

    try:
        frame = pd.DataFrame([row], columns=DIABETES_FEATURE_ORDER)
        prediction = diabetes_model.predict(frame)[0]
    except Exception as exc:
        return jsonify({"error": f"Model prediction failed: {str(exc)}"}), 500

    if str(prediction) in {"1", "Positive", "positive", "True", "true"}:
        label = "Positive"
    else:
        label = "Negative"
    return jsonify({"label": label})


@app.post("/api/predict/mental")
def predict_mental():
    model_errors = [
        mental_burn_model_error,
        mental_dep_model_error,
        mental_anx_model_error
    ]
    if any(err for err in model_errors):
        return jsonify({"error": next(err for err in model_errors if err)}), 500

    payload = request.get_json(silent=True) or {}
    missing_fields = [name for name in MENTAL_FEATURE_ORDER if name not in payload]
    if missing_fields:
        return jsonify({"error": f"Missing input field: {missing_fields[0]}"}), 400

    row = {name: payload.get(name) for name in MENTAL_FEATURE_ORDER}
    numeric_fields = [
        "Age",
        "Daily_Screen_Time",
        "Social_Media_Usage",
        "Night_Usage",
        "Sleep_Hours",
        "Stress_Level",
        "Work_Study_Hours",
        "Social_Interaction_Score",
        "Caffeine_Intake",
        "Smoking",
        "Alcohol"
    ]
    try:
        for field in numeric_fields:
            row[field] = float(row[field])
    except (TypeError, ValueError):
        return jsonify({"error": "One or more numeric mental health fields are invalid."}), 400

    try:
        frame = build_mental_frame(row, mental_burn_model)
        burnout = mental_burn_model.predict(frame)[0]
        depression = mental_dep_model.predict(frame)[0]
        anxiety = mental_anx_model.predict(frame)[0]
    except Exception as exc:
        return jsonify({"error": f"Model prediction failed: {str(exc)}"}), 500

    return jsonify(
        {
            "burnout": str(burnout),
            "depression": str(depression),
            "anxiety": str(anxiety)
        }
    )


@app.post("/api/predict/spam")
def predict_spam():
    if spam_model is None:
        return jsonify({"error": spam_model_error}), 500

    payload = request.get_json(silent=True) or {}
    message = (payload.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is required."}), 400

    try:
        if spam_vectorizer is not None:
            model_input = spam_vectorizer.transform([message])
        else:
            model_input = [message]

        spam_score = None
        if hasattr(spam_model, "predict_proba"):
            probs = spam_model.predict_proba(model_input)[0]
            model_spam_score = float(probs[1]) if len(probs) > 1 else float(probs[0])
            keyword_count = spam_keyword_hits(message)
            boosted_score = min(1.0, model_spam_score + keyword_count * SPAM_KEYWORD_BOOST)
            spam_score = boosted_score
            prediction = "spam" if boosted_score >= SPAM_THRESHOLD else "ham"
        else:
            prediction = spam_model.predict(model_input)[0]
    except Exception as exc:
        return jsonify({"error": f"Model prediction failed: {str(exc)}"}), 500

    result = {"label": str(prediction)}
    if spam_score is not None:
        result["spam_score"] = round(spam_score, 4)
        result["threshold"] = SPAM_THRESHOLD
        result["keyword_hits"] = spam_keyword_hits(message)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
