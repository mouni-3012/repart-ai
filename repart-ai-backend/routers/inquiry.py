from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter(tags=["General"])

def extract_args(payload): return payload.get("args", payload)

@router.post("/general_inquiry")
def general_inquiry(payload: Dict[str, Any]):
    req      = extract_args(payload)
    question = str(req.get("question", "")).lower().strip()
    if "shipping" in question or "delivery" in question:
        msg = "We ship nationwide with tracking. Delivery depends on your ZIP and part availability."
    elif "refund" in question or "return" in question:
        msg = "If anything arrives incorrect or damaged, we'll help right away with replacement or return options."
    elif "warranty" in question:
        msg = "Most parts come with a limited warranty depending on condition and availability."
    else:
        msg = "RePart AI helps you find compatible used or refurbished parts, confirm fitment, and ship with tracking."
    return {"customer_message": msg}