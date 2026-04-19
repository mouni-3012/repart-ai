from fastapi import APIRouter, HTTPException
from typing import Any, Dict
import requests

router = APIRouter(tags=["VIN"])

def extract_args(payload): return payload.get("args", payload)
def ensure_fields(data, fields):
    missing = [f for f in fields if not data.get(f)]
    if missing: raise HTTPException(status_code=422, detail=f"Missing required fields: {missing}")

@router.post("/vin_decode")
def vin_decode(payload: Dict[str, Any]):
    req = extract_args(payload)
    ensure_fields(req, ["vin"])
    vin = str(req["vin"]).strip().upper()
    if len(vin) < 11:
        raise HTTPException(status_code=422, detail="VIN too short. Provide at least 11 chars (ideally 17).")
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValuesExtended/{vin}?format=json"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"VIN decode failed: {str(e)}")
    results = data.get("Results", [])
    if not results:
        return {"year": "", "make": "", "model": "", "trim": "", "engine": ""}
    r = results[0]
    return {
        "year":   str(r.get("ModelYear", "") or "").strip(),
        "make":   str(r.get("Make", "") or "").strip(),
        "model":  str(r.get("Model", "") or "").strip(),
        "trim":   str(r.get("Trim", "") or "").strip(),
        "engine": str(r.get("EngineModel", "") or "").strip(),
    }