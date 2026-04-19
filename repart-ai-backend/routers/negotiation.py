from fastapi import APIRouter, HTTPException
from database import get_connection
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Negotiation"])


# ─────────────────────────────────────────────────────────────────────────────
# PRICING LOGIC:
#   - Agent starts at max_price (from inventory table)
#   - Counter-offers step down over up to 3 rounds
#   - Floor = 25% below max_price (i.e. 75% of max_price) — never go below this
#   - If customer's offer is at or above floor → accept it
#   - After round 3 → quote the floor as the absolute final offer
#
# Example: max_price = $200
#   Floor   = $200 * 0.75 = $150
#   Round 1 → $200  (starting offer)
#   Round 2 → ~$183 (step down ~8-9%)
#   Round 3 → $150  (final floor, no further negotiation)
# ─────────────────────────────────────────────────────────────────────────────

STEP_PERCENTS = [0.0, 0.08, 0.17]
# Round 1: 0%   off max  → max_price
# Round 2: 8%   off max  → 92% of max
# Round 3: 25%  off max  → floor (75% of max) — this is the final


def get_part_pricing(part_number: str) -> dict:
    """Fetch min_price and max_price from inventory by part_number."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT part_name, min_price, max_price
        FROM inventory
        WHERE part_number = %s
        LIMIT 1
        """,
        (part_number,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if not row:
        return None

    return {
        "part_name": row[0],
        "min_price": float(row[1]),
        "max_price": float(row[2]),
    }


def calculate_floor(max_price: float) -> float:
    """Floor is 75% of max_price (i.e. max discount = 25%)."""
    return round(max_price * 0.75, 2)


def calculate_counter(max_price: float, round_number: int) -> float:
    """
    Calculate the agent's counter offer for a given round.
    Round 1 → max_price (0% off)
    Round 2 → 92% of max_price (8% off)
    Round 3 → 75% of max_price (25% off = floor, final offer)
    """
    idx = min(round_number - 1, len(STEP_PERCENTS) - 1)
    discount = STEP_PERCENTS[idx]
    offer = max_price * (1.0 - discount)
    return round(offer, 2)


@router.post("/negotiate_offer")
def negotiate_offer(payload: dict):
    """
    Negotiation endpoint called by the Retell agent during a call.

    Required payload fields:
        item_id        — part_number from inventory (e.g. "WHE-BM2012-5")
        round_number   — which round this is (1, 2, or 3)

    Optional payload fields:
        customer_offer — the price the customer offered (float)

    Response fields:
        decision       — "counter" | "accept" | "final"
        counter_offer  — the agent's new offer (if decision=counter or final)
        final_price    — the agreed price (if decision=accept)
        stop           — True if negotiation should end
        script         — what the agent should say
        floor_price    — for agent reference (never reveal to customer)
        max_price      — for agent reference
    """
    # Handle Retell's "args" wrapper
    data = payload.get("args", payload)

    item_id = str(data.get("item_id", "")).strip()
    if not item_id:
        raise HTTPException(status_code=400, detail="item_id (part_number) is required")

    round_number = int(data.get("round_number", 1) or 1)
    round_number = max(1, min(round_number, 3))  # clamp between 1 and 3

    customer_offer = data.get("customer_offer", None)
    if customer_offer is not None:
        try:
            customer_offer = float(customer_offer)
        except (ValueError, TypeError):
            customer_offer = None

    # ── Fetch pricing from PostgreSQL inventory ───────────────────────────────
    pricing = get_part_pricing(item_id)
    if not pricing:
        raise HTTPException(
            status_code=404,
            detail=f"Part '{item_id}' not found in inventory. Make sure the agent passes the exact part_number."
        )

    max_price   = pricing["max_price"]
    part_name   = pricing["part_name"]
    floor_price = calculate_floor(max_price)

    logger.info(
        "negotiate_offer | part=%s | max=$%.2f | floor=$%.2f | round=%d | customer_offer=%s",
        item_id, max_price, floor_price, round_number, customer_offer
    )

    # ── Check if customer offer is acceptable ────────────────────────────────
    if customer_offer is not None:
        if customer_offer >= floor_price:
            # Customer's offer is at or above our floor — accept it
            final_price = round(customer_offer, 2)
            logger.info("Accepting customer offer $%.2f (above floor $%.2f)", final_price, floor_price)
            return {
                "decision":     "accept",
                "final_price":  final_price,
                "counter_offer": None,
                "stop":         True,
                "floor_price":  floor_price,
                "max_price":    max_price,
                "script": (
                    f"Alright, I can do ${final_price:.2f} for you today. "
                    f"I'll lock that in right now and send you the payment link."
                )
            }

        # Customer offered below floor — we cannot accept
        if round_number >= 3:
            # We've already been through 3 rounds — quote the floor as final
            logger.info("Round 3 reached, quoting floor $%.2f as final", floor_price)
            return {
                "decision":     "final",
                "final_price":  floor_price,
                "counter_offer": floor_price,
                "stop":         True,
                "floor_price":  floor_price,
                "max_price":    max_price,
                "script": (
                    f"I appreciate your patience — ${floor_price:.2f} is honestly the absolute "
                    f"lowest I can go on this one. If you can do that today, I'll send the payment link right now."
                )
            }

    # ── No customer offer yet, or customer offered below floor and rounds remain
    agent_counter = calculate_counter(max_price, round_number)

    # If we've hit floor naturally — mark as final
    if agent_counter <= floor_price or round_number >= 3:
        agent_counter = floor_price
        logger.info("Quoting floor $%.2f as final (round %d)", floor_price, round_number)
        return {
            "decision":     "final",
            "counter_offer": agent_counter,
            "final_price":  None,
            "stop":         True,
            "floor_price":  floor_price,
            "max_price":    max_price,
            "script": (
                f"I'll be straight with you — ${agent_counter:.2f} is the best I can do. "
                f"That's my final number. Want me to lock that in and send you the payment link?"
            )
        }

    # Normal counter offer
    logger.info("Counter offer: $%.2f (round %d)", agent_counter, round_number)

    if round_number == 1:
        script = (
            f"For the {part_name}, I can offer you ${agent_counter:.2f}. "
            f"That's our best price for a quality part. Does that work for you?"
        )
    else:
        script = (
            f"Let me see what I can do… I can come down to ${agent_counter:.2f}. "
            f"That's a solid deal — want to lock that in today?"
        )

    return {
        "decision":     "counter",
        "counter_offer": agent_counter,
        "final_price":  None,
        "stop":         False,
        "floor_price":  floor_price,
        "max_price":    max_price,
        "script":       script
    }