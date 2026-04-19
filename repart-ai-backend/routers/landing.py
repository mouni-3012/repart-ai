from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator
from typing import Optional, Any
import time
import json
import re
import os
from pathlib import Path
from datetime import datetime
import logging

import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Config — all values that used to come from core.config are defined here
# directly from environment variables and path definitions.
# ---------------------------------------------------------------------------
RETELL_API_KEY    = os.getenv("RETELL_API_KEY", "")
RETELL_AGENT_ID   = os.getenv("RETELL_AGENT_ID", "")
RETELL_FROM_NUMBER = os.getenv("RETELL_FROM_NUMBER", "")
RETELL_API_BASE   = os.getenv("RETELL_API_BASE", "https://api.retellai.com")

# Log files — stored in a "logs" folder next to your project root
_BASE_DIR       = Path(__file__).resolve().parent.parent
LOG_FILE        = _BASE_DIR / "logs" / "leads.jsonl"
RETELL_DEBUG_FILE = _BASE_DIR / "logs" / "retell_debug.json"

# ---------------------------------------------------------------------------
# DB import — graceful fallback if postgres isn't available during local dev
# ---------------------------------------------------------------------------
try:
    from database import get_connection
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter(tags=["landing"])


# ---------------------------------------------------------------------------
# Phone helpers
# ---------------------------------------------------------------------------

def _normalize_phone(phone: str) -> str:
    s = re.sub(r"[\s\-\(\)\.]", "", phone.strip())
    digits = re.sub(r"\D", "", s)
    if not digits:
        return ""
    if s.startswith("+"):
        return "+" + digits
    if len(digits) == 10 and digits[0] not in "01":
        return "+1" + digits
    if len(digits) == 11 and digits[0] == "1":
        return "+" + digits
    if len(digits) >= 10:
        return "+" + digits
    return "+" + digits


def _e164_to_display_us(e164: str) -> str:
    digits = re.sub(r"\D", "", e164)
    if len(digits) == 11 and digits[0] == "1":
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[0:3]}) {digits[3:6]}-{digits[6:]}"
    return e164


# ---------------------------------------------------------------------------
# Retell outbound call
# ---------------------------------------------------------------------------

def trigger_retell_outbound_call(phone: str, lead_id: str, metadata: dict) -> dict:
    out = {"ok": False, "detail": ""}
    if not RETELL_API_KEY or not RETELL_AGENT_ID:
        out["detail"] = "RETELL_API_KEY or RETELL_AGENT_ID not set"
        logger.warning("Retell: %s", out["detail"])
        return out
    if not RETELL_FROM_NUMBER:
        out["detail"] = "RETELL_FROM_NUMBER not set in .env"
        logger.warning("Retell: %s", out["detail"])
        return out

    to_number = _normalize_phone(phone)
    if not to_number:
        out["detail"] = f"Invalid phone number: {phone!r}"
        logger.warning("Retell: %s", out["detail"])
        return out

    from_number = _normalize_phone(RETELL_FROM_NUMBER)
    if not from_number:
        out["detail"] = "RETELL_FROM_NUMBER must be a valid number"
        logger.warning("Retell: %s", out["detail"])
        return out

    url = f"https://api.retellai.com/v2/create-phone-call"
    headers = {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "from_number": from_number,
        "to_number": to_number,
        "override_agent_id": RETELL_AGENT_ID,
        "metadata": {"lead_id": lead_id, **metadata},
        "retell_llm_dynamic_variables": {"lead_id": lead_id, **metadata},
    }

    try:
        r = requests.post(url, json=body, headers=headers, timeout=15)
        try:
            data = r.json() if r.text else {}
        except Exception:
            data = {"raw_text": r.text[:500] if r.text else ""}

        # If 404 "not found from phone-number", retry with display format
        if r.status_code == 404 and "not found from phone-number" in str(data.get("message", "")):
            from_number = _e164_to_display_us(from_number)
            body["from_number"] = from_number
            r = requests.post(url, json=body, headers=headers, timeout=15)
            data = r.json() if r.text else {}

        debug = {
            "ts": datetime.utcnow().isoformat(),
            "from_number": from_number,
            "to_number": to_number,
            "status_code": r.status_code,
            "response": data,
        }
        try:
            RETELL_DEBUG_FILE.parent.mkdir(parents=True, exist_ok=True)
            RETELL_DEBUG_FILE.write_text(json.dumps(debug, indent=2), encoding="utf-8")
        except Exception:
            pass

        if r.status_code in (200, 201):
            call_id = data.get("call_id") or data.get("id") or "ok"
            out["ok"] = True
            out["detail"] = f"Call created: {call_id}"
            out["call_id"] = call_id
            logger.info("Retell outbound call created: %s -> %s (call_id=%s)", from_number, to_number, call_id)
            return out

        out["detail"] = f"Retell API error {r.status_code}: {data}"
        logger.error("Retell API error: status=%s body=%s", r.status_code, data)
        out["status_code"] = r.status_code
        out["response"] = data
        return out

    except Exception as e:
        out["detail"] = str(e)
        logger.exception("Retell request failed: %s", e)
        return out


# ---------------------------------------------------------------------------
# Retell phone number listing (debug helper)
# ---------------------------------------------------------------------------

@router.get("/retell-numbers")
def list_retell_phone_numbers():
    if not RETELL_API_KEY:
        return {"error": "RETELL_API_KEY not set", "numbers": []}
    url = "https://api.retellai.com/list-phone-numbers"
    headers = {"Authorization": f"Bearer {RETELL_API_KEY}", "Content-Type": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json() if r.text else []
        if r.status_code != 200:
            return {"error": f"Retell API {r.status_code}", "body": data, "numbers": []}
        if not isinstance(data, list):
            data = [data] if data else []
        numbers = [
            {
                "phone_number": n.get("phone_number"),
                "phone_number_pretty": n.get("phone_number_pretty"),
                "phone_number_type": n.get("phone_number_type"),
            }
            for n in data
        ]
        return {"ok": True, "count": len(numbers), "numbers": numbers, "current_from_in_env": RETELL_FROM_NUMBER}
    except Exception as e:
        return {"error": str(e), "numbers": []}


# ---------------------------------------------------------------------------
# Form payload model
# ---------------------------------------------------------------------------

class SubmitFormPayload(BaseModel):
    fullName: Optional[str] = None
    phoneNumber: Optional[str] = None
    email: Optional[str] = None
    vehicleMake: Optional[str] = None
    year: Optional[str] = None
    vinNumber: Optional[str] = None
    partNeeded: Optional[str] = None
    additionalNotes: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    vin: Optional[str] = None
    make: Optional[str] = None
    model: Optional[str] = None
    part_name: Optional[str] = None
    part_number: Optional[str] = None
    notes: Optional[str] = None
    source: Optional[str] = "landing_page"

    @model_validator(mode="before")
    @classmethod
    def accept_any_keys(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        return data

    def get_phone(self) -> str:
        return (self.phoneNumber or self.phone or "").strip()

    def get_name(self) -> str:
        return (self.fullName or self.name or "").strip()

    def get_email(self) -> Optional[str]:
        return (self.email or "").strip() or None

    def get_vin(self) -> Optional[str]:
        return (self.vinNumber or self.vin or "").strip() or None

    def get_part(self) -> Optional[str]:
        return (self.partNeeded or self.part_name or "").strip() or None

    def get_notes(self) -> Optional[str]:
        return (self.additionalNotes or self.notes or "").strip() or None


# ---------------------------------------------------------------------------
# /submit-form
# ---------------------------------------------------------------------------

@router.post("/submit-form")
def submit_form(payload: SubmitFormPayload):
    lead_id = f"L-{int(time.time())}"
    phone = payload.get_phone()

    if not phone:
        raise HTTPException(status_code=422, detail="Phone number is required")

    # 1. Save to PostgreSQL
    db_status = "skipped"
    if DB_AVAILABLE:
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO leads
                    (full_name, phone, email, vehicle_make, year, vin, part_needed, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    payload.get_name(),
                    phone,
                    payload.get_email(),
                    payload.vehicleMake or payload.make,
                    payload.year,
                    payload.get_vin(),
                    payload.get_part(),
                    payload.get_notes(),
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()
            db_status = "saved"
            logger.info("Lead %s saved to DB", lead_id)
        except Exception as e:
            logger.error("DB insert failed for lead %s: %s", lead_id, e)
            db_status = f"error: {e}"

    # 2. Write to log file (always, as a backup)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps({
                "ts": datetime.utcnow().isoformat(),
                "type": "landing_submit",
                "lead_id": lead_id,
                "phone": phone,
                "name": payload.get_name(),
                "email": payload.get_email(),
                "vin": payload.get_vin(),
                "year": payload.year,
                "vehicle_make": payload.vehicleMake or payload.make,
                "part_needed": payload.get_part(),
                "notes": payload.get_notes(),
                "source": payload.source or "landing_page",
            }) + "\n"
        )

    # 3. Trigger Retell outbound call
    call_metadata = {
        "name": payload.get_name(),
        "part_needed": payload.get_part() or "",
        "vehicle": payload.vehicleMake or payload.make or "",
        "vin": payload.get_vin() or "",
        "notes": payload.get_notes() or "",
    }
    retell_result = trigger_retell_outbound_call(phone, lead_id, call_metadata)

    return {
        "ok": True,
        "lead_id": lead_id,
        "message": "Submitted successfully",
        "db": db_status,
        "retell": retell_result,
    }