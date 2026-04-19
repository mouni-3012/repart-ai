from fastapi import APIRouter, HTTPException
from typing import Any, Dict

router = APIRouter(tags=["Shipping"])

def extract_args(payload): return payload.get("args", payload)
def ensure_fields(data, fields):
    missing = [f for f in fields if not data.get(f)]
    if missing: raise HTTPException(status_code=422, detail=f"Missing required fields: {missing}")

@router.post("/get_shipping_estimate")
def get_shipping_estimate(payload: Dict[str, Any]):
    req = extract_args(payload)
    ensure_fields(req, ["zip", "lead_time_days"])
    try:
        lead_time = int(req.get("lead_time_days", 5))
    except Exception:
        raise HTTPException(status_code=422, detail="lead_time_days must be a number")
    speed          = str(req.get("shipping_speed", "standard")).lower()
    base_ship_cost = 15.0
    if speed == "express":
        ship_cost     = base_ship_cost + 25.0
        delivery_days = max(2, lead_time - 1)
    else:
        ship_cost     = base_ship_cost
        delivery_days = lead_time + 2
    return {
        "shipping_cost":    round(ship_cost, 2),
        "delivery_days":    int(delivery_days),
        "customer_message": f"Estimated shipping is ${ship_cost:.2f} with delivery in about {delivery_days} days."
    }