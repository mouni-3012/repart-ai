from __future__ import annotations
from typing import Dict, Any, List, Optional
from pathlib import Path
import math
import numpy as np

try:
    import joblib
except Exception:
    joblib = None

MODEL_PATH = Path("acceptance_model.pkl")
ACCEPT_MODEL = None

def load_acceptance_model() -> None:
    """
    Loads a sklearn-style model that supports predict_proba.
    
    Safe to call multiple times.
    """
    global ACCEPT_MODEL
    if ACCEPT_MODEL is not None:
        return
    if joblib is None:
        ACCEPT_MODEL = None
        return
    if MODEL_PATH.exists():
        try:
            ACCEPT_MODEL = joblib.load(str(MODEL_PATH))
        except Exception:
            ACCEPT_MODEL = None

def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def make_floor_price(cost: float, min_margin_pct: float = 0.12, min_margin_abs: float = 15.0) -> float:
    """
    Example internal floor: at least +12% margin or +$15, whichever is higher.
    Tune for your business.
    """
    return max(cost * (1.0 + min_margin_pct), cost + min_margin_abs)

def _nice_price(p: float) -> float:
    # round to nearest 5 dollars for human-friendly pricing
    return float(round(p / 5.0) * 5.0)

def generate_candidates(
    last_agent_offer: Optional[float],
    floor: float,
    ceiling: float,
    urgency: str = "medium",
    customer_offer: Optional[float] = None,
    round_number: int = 1
) -> List[float]:
    """
    Candidate set for counteroffers.

    - Uses customer_offer (if provided) to avoid countering at the ceiling when the customer is far lower.
    - Uses round_number to make larger concessions in later rounds.
    - Respects [floor, ceiling] and rounds to "nice" prices.
    """
    urgency = (urgency or "medium").lower()
    round_number = int(round_number or 1)

    if customer_offer is not None:
        customer_offer = float(customer_offer)
        start = 0.65 * float(ceiling) + 0.35 * customer_offer
    else:
        start = float(ceiling if last_agent_offer is None else last_agent_offer)

    start = clamp(start, floor, ceiling)

    gap_ratio = 0.0
    if customer_offer is not None and ceiling > 0:
        gap_ratio = clamp((float(ceiling) - float(customer_offer)) / max(float(ceiling), 1.0), 0.0, 1.0)

    base_step = 10.0 if urgency == "low" else (6.0 if urgency == "medium" else 4.0)
    step = base_step * (1.0 + 0.35 * (round_number - 1) + 0.9 * gap_ratio)

    max_step = max(5.0, 0.12 * (ceiling - floor))
    step = min(step, max_step)

    multiples = [0, 1, 2, 3, 4, 5]
    cands = []
    for m in multiples:
        p = start - (m * step)
        p = clamp(p, floor, ceiling)
        cands.append(_nice_price(p))

    cands.append(_nice_price(floor))
    return sorted(set(cands), reverse=True)

def features_with_price(state: Dict[str, Any], offer_price: float) -> np.ndarray:
    """
    IMPORTANT: Must match training feature order.
    This baseline uses 7 numeric features.
    """
    cost = float(state.get("cost", 0.0))
    list_price = float(state.get("list_price", offer_price))
    customer_offer = float(state.get("customer_offer", state.get("last_offer_by_customer", offer_price)) or offer_price)
    round_number = float(state.get("round_number", state.get("turn_count", 1)) or 1)
    urgency = str(state.get("urgency", "medium")).lower()

    urgency_high = 1.0 if urgency == "high" else 0.0
    urgency_low = 1.0 if urgency == "low" else 0.0

    margin = offer_price - cost
    offer_ratio = offer_price / max(list_price, 1.0)
    delta_vs_customer = offer_price - customer_offer

    x = np.array([
        offer_price,
        cost,
        list_price,
        margin,
        offer_ratio,
        delta_vs_customer,
        round_number,
        urgency_high,
        urgency_low
    ], dtype=float)

    return x.reshape(1, -1)

def predict_accept_prob(state: Dict[str, Any], offer_price: float) -> Optional[float]:
    load_acceptance_model()
    if ACCEPT_MODEL is None:
        return None
    if not hasattr(ACCEPT_MODEL, "predict_proba"):
        return None
    x = features_with_price(state, offer_price)
    prob = float(ACCEPT_MODEL.predict_proba(x)[0][1])
    return clamp(prob, 0.0, 1.0)

def pick_next_offer(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Uses acceptance model (if available) + expected profit objective.
    Falls back to rule-based ladder if model missing.
    """
    cost = float(state.get("cost", 0.0))

    ceiling = float(state.get("ceiling_price") or state.get("list_price") or state.get("anchor") or (cost * 2.0))
    floor = float(state.get('floor_price') or make_floor_price(cost, min_margin_pct=float(state.get('min_margin_pct', 0.12) or 0.12), min_margin_abs=float(state.get('min_profit_abs', 15.0) or 15.0)))

    urgency = str(state.get("urgency", "medium")).lower()
    last_agent_offer = state.get("last_offer_by_agent", ceiling)

    # Candidate prices
    candidates = generate_candidates(last_agent_offer, floor, ceiling, urgency=urgency, customer_offer=state.get('customer_offer', state.get('last_offer_by_customer')), round_number=int(state.get('round_number', state.get('turn_count', 1)) or 1))

    best_price = candidates[0]
    best_prob = None
    best_score = -1e18

    for p in candidates:
        prob = predict_accept_prob(state, p)
        if prob is None:
            # fallback heuristic: acceptance rises as we approach customer offer / lower price
            customer_offer = float(state.get("customer_offer", state.get("last_offer_by_customer", 0.0)) or 0.0)
            # If customer_offer unknown, assume medium
            if customer_offer <= 0:
                prob = 0.55 - 0.15 * ((p - floor) / max(ceiling - floor, 1.0))
            else:
                # closer to customer_offer => higher acceptance
                prob = 0.25 + 0.70 * clamp(customer_offer / max(p, 1.0), 0.0, 1.0)
            prob = clamp(prob, 0.05, 0.95)

        expected_profit = (p - cost) * prob
        if expected_profit > best_score:
            best_score = expected_profit
            best_price = p
            best_prob = prob

    return {
        "next_offer": float(best_price),
        "floor_price": float(floor),
        "ceiling_price": float(ceiling),
        "p_accept": None if best_prob is None else float(best_prob),
        "expected_profit_score": float(best_score),
        "engine": "acceptance_model + constrained_optimizer" if ACCEPT_MODEL is not None else "heuristic + constrained_optimizer"
    }
