"""
retell_webhook.py
-----------------
Receives post-call events from Retell (call_started, call_ended, call_analyzed).

IMPORTANT — WHY THIS WEBHOOK DOES NOT SEND EMAILS:
===================================================
Payment emails are already sent by orders.py (/orders/deal_closed) which is
called by the Retell agent tool DURING the call the moment the customer agrees.

orders.py:
  - Validates price against inventory min_price/max_price  ✅
  - Saves order to DB                                      ✅
  - Sends payment email with correct price                 ✅

This webhook fires AFTER the call ends. If we sent another email here,
the customer would receive TWO emails — one with the correct validated price
from orders.py, and one with whatever raw price the agent memorized ($150).

This webhook is now used ONLY for:
  - Logging call outcomes
  - Monitoring / debugging
  - Future features (follow-up scheduling, CRM sync, etc.)
"""

from fastapi import APIRouter, Request
from database import get_connection
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Retell Webhook"])


def log_call_outcome(call_id: str, call_status: str, duration_ms: int,
                     customer_name: str, deal_closed: bool,
                     part_name: str, dynamic_vars: dict):
    """
    Optionally save call outcome to DB for analytics.
    Silently skips if DB write fails — never block the webhook response.
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # Check if a call_logs table exists — if not, skip gracefully
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'call_logs'
            )
        """)
        exists = cursor.fetchone()[0]

        if exists:
            cursor.execute("""
                INSERT INTO call_logs
                    (call_id, call_status, duration_ms, customer_name,
                     deal_closed, part_name, raw_dynamic_vars)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (call_id) DO NOTHING
            """, (
                call_id, call_status, duration_ms, customer_name,
                deal_closed, part_name, str(dynamic_vars)
            ))
            conn.commit()
            logger.info("Call outcome logged: call_id=%s deal_closed=%s", call_id, deal_closed)

        cursor.close()
        conn.close()
    except Exception as e:
        logger.warning("Could not log call outcome (non-fatal): %s", e)


@router.post("/retell-webhook")
async def retell_webhook(request: Request):
    """
    Retell posts here for call_started, call_ended, and call_analyzed events.

    This endpoint does NOT send payment emails.
    Payment emails are handled by /orders/deal_closed which the agent
    calls as a tool DURING the call with the validated price.
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.error("retell_webhook: could not parse JSON body: %s", e)
        return {"ok": False, "error": "Invalid JSON"}

    event = body.get("event", "unknown")
    call  = body.get("call", body)

    call_id     = call.get("call_id", "")
    call_status = call.get("call_status", "")
    duration_ms = call.get("duration_ms", 0)

    dynamic_vars  = call.get("retell_llm_dynamic_variables", {}) or {}
    metadata      = call.get("metadata", {}) or {}
    call_analysis = call.get("call_analysis", {}) or {}

    customer_name = dynamic_vars.get("customer_name") or metadata.get("name", "")
    part_name     = dynamic_vars.get("part_name") or metadata.get("part_needed", "")

    # Detect if deal was closed — for logging only
    deal_closed = (
        str(dynamic_vars.get("deal_closed", "")).lower() == "true"
        or str(call_analysis.get("custom_analysis_data", {})
               .get("deal_closed", "")).lower() == "true"
    )

    logger.info(
        "retell_webhook: event=%s | call_id=%s | status=%s | deal_closed=%s | customer=%s",
        event, call_id, call_status, deal_closed, customer_name
    )

    # ── call_started: just acknowledge ───────────────────────────────────────
    if event == "call_started":
        return {"ok": True, "action": "call_started_acknowledged"}

    # ── call_ended / call_analyzed: log the outcome ───────────────────────────
    if event in ("call_ended", "call_analyzed"):

        if deal_closed:
            logger.info(
                "retell_webhook: deal was closed during call for '%s' | part='%s' | "
                "Payment email was already sent by /orders/deal_closed during the call.",
                customer_name, part_name
            )
            # Log to DB for analytics (non-blocking)
            log_call_outcome(
                call_id, call_status, duration_ms,
                customer_name, True, part_name, dynamic_vars
            )
            return {
                "ok":     True,
                "action": "deal_logged",
                "note":   "Payment email was already sent during the call by /orders/deal_closed"
            }

        else:
            logger.info(
                "retell_webhook: call ended without deal | customer='%s' | status=%s",
                customer_name, call_status
            )
            log_call_outcome(
                call_id, call_status, duration_ms,
                customer_name, False, part_name, dynamic_vars
            )
            return {
                "ok":     True,
                "action": "no_deal_logged",
                "call_status": call_status
            }

    # ── Any other event ───────────────────────────────────────────────────────
    return {"ok": True, "action": "event_acknowledged", "event": event}