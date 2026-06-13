import json
import os
import re
import sys

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))

# ---Feature extraction---

TIER1_KEYWORDS = [
    "what is", "what are", "what does", "what was", "who is", "who was",
    "when was", "where is", "how many", "convert", "translate", "extract",
    "list", "define", "format", "calculate", "spell"
]

TIER2_KEYWORDS = [
    "summarize", "summary", "explain", "describe", "compare", "difference",
    "classify", "write a function", "write a script", "write a query",
    "write a test", "write an email", "pros and cons", "how does", "implement"
]

TIER3_KEYWORDS = [
    "design", "architect", "analyze", "tradeoff", "tradeoffs", "evaluate",
    "propose", "strategy", "multi-step", "at scale", "production", "migrate",
    "migration", "deep dive", "comprehensive", "detailed", "system design",
    "compare and", "justify", "recommend", "research", "audit", "pipeline",
    "distributed", "rate limiter", "rfc", "zero downtime", "fault tolerance",
    "scalable", "high availability", "disaster recovery", "capacity planning",
    "technical proposal", "technical design", "post-mortem", "root cause",
    "10,000", "1 million", "10 million", "100 million", "50,000", "500,000"
]

OUTPUT_FORMAT_WORDS = [
    "json", "table", "bullet", "numbered", "markdown", "diagram",
    "document", "report", "checklist", "rfc", "post-mortem"
]


def extract_features(prompt: str) -> list[float]:
    text = prompt.lower()
    tokens = text.split()

    token_count = len(tokens)
    char_count = len(prompt)

    tier1_hits = sum(1 for kw in TIER1_KEYWORDS if kw in text)
    tier2_hits = sum(1 for kw in TIER2_KEYWORDS if kw in text)
    tier3_hits = sum(1 for kw in TIER3_KEYWORDS if kw in text)

    constraint_words = ["must", "should", "ensure", "without", "constraint",
                        "require", "only", "exactly", "at least", "no more"]
    constraint_count = sum(1 for w in constraint_words if w in text)

    format_hits = sum(1 for w in OUTPUT_FORMAT_WORDS if w in text)

    sentence_count = len(re.split(r'[.!?]+', prompt))

    question_marks = prompt.count("?")

    numbers_in_prompt = len(re.findall(r'\b\d+\b', prompt))
    has_scale_number = 1 if re.search(r'\b\d{4,}\b', prompt) else 0

    instruction_verbs = ["write", "design", "build", "implement", "create",
                         "analyze", "compare", "explain", "describe", "evaluate",
                         "summarize", "classify", "propose", "migrate", "audit"]
    verb_count = sum(1 for v in instruction_verbs if v in text)

    return [
        token_count,
        char_count,
        tier1_hits,
        tier2_hits,
        tier3_hits,
        constraint_count,
        format_hits,
        sentence_count,
        question_marks,
        numbers_in_prompt,
        verb_count,
        has_scale_number,
    ]


# ---Training---

def load_training_data(path: str) -> tuple[list, list]:
    with open(path, "r") as f:
        data = json.load(f)
    X = [extract_features(item["prompt"]) for item in data]
    y = [item["tier"] for item in data]
    return X, y


def train(data_path: str, output_path: str) -> dict:
    X, y = load_training_data(data_path)
    X = np.array(X)
    y = np.array(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    lr_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])

    rf_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=100, random_state=42)),
    ])

    lr_pipeline.fit(X_train, y_train)
    rf_pipeline.fit(X_train, y_train)

    lr_score = lr_pipeline.score(X_test, y_test)
    rf_score = rf_pipeline.score(X_test, y_test)

    best_model = rf_pipeline if rf_score >= lr_score else lr_pipeline
    best_name = "RandomForest" if rf_score >= lr_score else "LogisticRegression"
    best_score = max(lr_score, rf_score)

    joblib.dump(best_model, output_path)

    y_pred = best_model.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=["Tier1", "Tier2", "Tier3"])

    return {
        "best_model": best_name,
        "lr_accuracy": round(lr_score, 4),
        "rf_accuracy": round(rf_score, 4),
        "best_accuracy": round(best_score, 4),
        "report": report,
    }


# ---Inference---

_model_cache = None


def load_model(path: str):
    global _model_cache
    if _model_cache is None:
        _model_cache = joblib.load(path)
    return _model_cache


def predict_tier(prompt: str, model_path: str) -> dict:
    model = load_model(model_path)
    features = np.array([extract_features(prompt)])
    tier = int(model.predict(features)[0])
    proba = model.predict_proba(features)[0]
    confidence = round(float(max(proba)), 4)

    tier_labels = {1: "Simple", 2: "Moderate", 3: "Complex"}
    return {
        "tier": tier,
        "label": tier_labels[tier],
        "confidence": confidence,
        "probabilities": {
            "tier_1": round(float(proba[0]), 4),
            "tier_2": round(float(proba[1]), 4),
            "tier_3": round(float(proba[2]), 4),
        },
    }


# ---Entry point---
if __name__ == "__main__":
    base = os.path.dirname(__file__)
    data_path = os.path.join(base, "data", "training_prompts.json")
    output_path = os.path.join(base, "data", "classifier.pkl")

    print("Training classifier...")
    results = train(data_path, output_path)

    print(f"\nBest model:       {results['best_model']}")
    print(f"LR accuracy:      {results['lr_accuracy']}")
    print(f"RF accuracy:      {results['rf_accuracy']}")
    print(f"Best accuracy:    {results['best_accuracy']}")
    print(f"\n{results['report']}")
    print(f"Model saved to:   {output_path}")