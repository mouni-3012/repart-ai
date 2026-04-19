"""
Train an acceptance model for RePart AI negotiation.

This replaces the old GRU/RNN training and produces:
  - acceptance_model.pkl (sklearn classifier with predict_proba)

You can start with synthetic data (below), then later replace the
data generation with your real negotiation logs.
"""

from __future__ import annotations
import random
from dataclasses import dataclass
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, log_loss
from sklearn.ensemble import HistGradientBoostingClassifier

# ---------------- Synthetic data generator ----------------
def generate_sample():
    """
    Features (must match pricing_engine.features_with_price order):
      [offer_price, cost, list_price, margin, offer_ratio, delta_vs_customer, round_number, urgency_high, urgency_low]
    Label:
      accept (0/1)
    """
    list_price = random.uniform(150, 800)
    cost = list_price * random.uniform(0.60, 0.82)     # internal cost proxy
    round_number = random.randint(1, 4)
    urgency = random.choice(["low", "medium", "high"])

    # customer offer behavior
    customer_offer_ratio = random.uniform(0.55, 1.00)
    customer_offer = list_price * customer_offer_ratio

    # agent offer candidate (we simulate training points around a plausible counter)
    # slightly above customer offer early, closer later
    concession = {1: 0.10, 2: 0.07, 3: 0.05, 4: 0.03}[round_number]
    offer_price = max(cost * 1.05, min(list_price, customer_offer * (1.0 + concession)))

    margin = offer_price - cost
    offer_ratio = offer_price / max(list_price, 1.0)
    delta_vs_customer = offer_price - customer_offer
    urgency_high = 1.0 if urgency == "high" else 0.0
    urgency_low = 1.0 if urgency == "low" else 0.0

    x = np.array([
        offer_price,
        cost,
        list_price,
        margin,
        offer_ratio,
        delta_vs_customer,
        float(round_number),
        urgency_high,
        urgency_low
    ], dtype=float)

    # acceptance probability: higher if offer close to customer_offer and not too high vs list_price
    # urgency high => more likely to accept higher price
    base = 0.15 + (0.20 if urgency_high else 0.0) - (0.05 if urgency_low else 0.0)
    closeness = 1.0 - min(abs(delta_vs_customer) / max(list_price, 1.0), 1.0)  # 0..1
    price_penalty = max(0.0, offer_ratio - 0.95) * 1.2                          # penalize very close to list price
    margin_penalty = max(0.0, (margin / max(list_price, 1.0)) - 0.35)          # too much margin looks unrealistic

    p_accept = base + 0.75 * closeness - 0.35 * price_penalty - 0.15 * margin_penalty
    p_accept = float(np.clip(p_accept, 0.02, 0.98))

    y = 1 if random.random() < p_accept else 0
    return x, y

def build_dataset(n=8000, seed=7):
    random.seed(seed)
    X, y = [], []
    for _ in range(n):
        xi, yi = generate_sample()
        X.append(xi)
        y.append(yi)
    return np.vstack(X), np.array(y, dtype=int)

def main():
    X, y = build_dataset()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # Strong tabular baseline with predict_proba:
    model = HistGradientBoostingClassifier(
        max_depth=4,
        learning_rate=0.08,
        max_iter=400,
        random_state=42
    )
    model.fit(X_train, y_train)

    proba = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, proba)
    ll = log_loss(y_test, proba)

    print("✅ Acceptance model trained")
    print("AUC:", round(auc, 4))
    print("LogLoss:", round(ll, 4))

    joblib.dump(model, "acceptance_model.pkl")
    print("MODEL SAVED AS acceptance_model.pkl")

if __name__ == "__main__":
    main()
