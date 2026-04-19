from fastapi import HTTPException
from typing import Any, Dict, List

def extract_args(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Supports both formats:
      1) {"args": {...}}  (Swagger/Postman)
      2) {...}            (Retell 'Payload: args only')
    """
    if isinstance(payload, dict) and isinstance(payload.get("args"), dict):
        return payload["args"]
    return payload if isinstance(payload, dict) else {}

def ensure_fields(req: Dict[str, Any], required: List[str]):
    missing = [k for k in required if k not in req or req.get(k) in [None, ""]]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing field(s): {', '.join(missing)}")
