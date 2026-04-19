from fastapi import APIRouter, HTTPException
from database import get_connection
from routers.payments import send_payment_email
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


def get_inventory_pricing(cursor, part_number: str):
    """Fetch min_price and max_price from inventory for a given part_number."""
    cursor.execute(
        "SELECT min_price, max_price, part_name FROM inventory WHERE part_number = %s LIMIT 1",
        (part_number,)
    )
    return cursor.fetchone()  # returns (min_price, max_price, part_name) or None


def validate_price(price: float, min_price: float, max_price: float) -> float:
    """
    Validate the agreed price is within inventory range.
    - If price is below min_price → use min_price (agent went too low)
    - If price is above max_price → use max_price (agent started too high, shouldn't happen but guard anyway)
    - If price is within range → use as-is
    Returns the corrected valid price.
    """
    if price < min_price:
        logger.warning(
            "Price $%.2f is BELOW min_price $%.2f — correcting to min_price",
            price, min_price
        )
        return float(min_price)
    if price > max_price:
        logger.warning(
            "Price $%.2f is ABOVE max_price $%.2f — correcting to max_price",
            price, max_price
        )
        return float(max_price)
    return price


@router.post("/deal_closed")
def deal_closed(payload: dict):
    # Retell wraps args inside "args" key — handle both formats
    data = payload.get("args", payload)
    logger.info("DEAL CLOSED PAYLOAD: %s", data)

    customer_name = data.get("customer_name", "").strip()
    part_name     = data.get("part_name", "").strip()
    part_number   = data.get("part_number", "").strip()
    price         = data.get("price")

    # Validate required fields
    missing = []
    if not customer_name: missing.append("customer_name")
    if not part_name:     missing.append("part_name")
    if price is None:     missing.append("price")
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {missing}")

    try:
        price = float(price)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="price must be a number")

    order_id       = str(uuid.uuid4())[:8].upper()
    customer_email = None

    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # ── 1. Fetch customer email from leads table ──────────────────────────
        cursor.execute(
            "SELECT email FROM leads WHERE LOWER(full_name) = LOWER(%s) ORDER BY id DESC LIMIT 1",
            (customer_name,)
        )
        row = cursor.fetchone()
        if row:
            customer_email = row[0]
            logger.info("Email fetched for '%s': %s", customer_name, customer_email)

        if not customer_email:
            raise HTTPException(
                status_code=404,
                detail=f"No email found for customer '{customer_name}'. Make sure the form was submitted."
            )

        # ── 2. Resolve part_number ────────────────────────────────────────────
        # Priority: use part_number from agent if valid, else search by part_name
        if part_number:
            logger.info("Using part_number from agent: %s", part_number)
            cursor.execute(
                "SELECT part_number FROM inventory WHERE part_number = %s LIMIT 1",
                (part_number,)
            )
            if not cursor.fetchone():
                logger.warning("part_number %s not found in inventory, falling back to name search", part_number)
                part_number = None

        if not part_number:
            logger.info("Searching inventory by part_name: %s", part_name)
            cursor.execute(
                "SELECT part_number FROM inventory WHERE LOWER(part_name) = LOWER(%s) LIMIT 1",
                (part_name,)
            )
            result = cursor.fetchone()
            if not result:
                # Try LIKE search as last resort
                cursor.execute(
                    "SELECT part_number FROM inventory WHERE LOWER(part_name) LIKE LOWER(%s) LIMIT 1",
                    (f"%{part_name}%",)
                )
                result = cursor.fetchone()
            part_number = result[0] if result else None

        logger.info("Final part_number resolved: %s", part_number)

        # ── 3. Validate and correct price against inventory ───────────────────
        if part_number:
            pricing = get_inventory_pricing(cursor, part_number)
            if pricing:
                db_min_price, db_max_price, db_part_name = pricing
                logger.info(
                    "Inventory pricing for %s: min=$%.2f, max=$%.2f | Agent sent: $%.2f",
                    part_number, db_min_price, db_max_price, price
                )
                corrected_price = validate_price(price, float(db_min_price), float(db_max_price))
                if corrected_price != price:
                    logger.warning(
                        "Price corrected from $%.2f to $%.2f for part %s",
                        price, corrected_price, part_number
                    )
                price = corrected_price
            else:
                logger.warning("Could not fetch pricing for part_number %s — using agent price $%.2f", part_number, price)
        else:
            logger.warning("part_number not resolved for '%s' — using agent price $%.2f as-is", part_name, price)

        # ── 4. Reserve stock ──────────────────────────────────────────────────
        if part_number:
            cursor.execute(
                """
                UPDATE inventory
                SET reserved_stock = COALESCE(reserved_stock, 0) + 1
                WHERE part_number = %s AND stock > COALESCE(reserved_stock, 0)
                """,
                (part_number,)
            )
            logger.info("Stock reserved for part_number=%s", part_number)
        else:
            logger.warning("part_number not found for '%s' — stock not reserved", part_name)

        # ── 5. Save order ─────────────────────────────────────────────────────
        cursor.execute(
            """
            INSERT INTO orders
                (order_id, customer_name, customer_email, part_number, price, status)
            VALUES (%s, %s, %s, %s, %s, 'pending')
            """,
            (order_id, customer_name, customer_email, part_number, price)
        )

        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Order %s saved — customer: %s, part: %s, price: $%.2f",
                    order_id, customer_email, part_number, price)

    except HTTPException:
        raise
    except Exception as e:
        logger.error("DB error in deal_closed: %s", e)
        if not customer_email:
            raise HTTPException(status_code=500, detail=f"DB error, no email found: {e}")
        logger.warning("DB partially failed but email will still be sent to %s", customer_email)

    # ── 6. Send payment email ─────────────────────────────────────────────────
    try:
        send_payment_email({
            "customer_name":  customer_name,
            "customer_email": customer_email,
            "part_name":      part_name,
            "part_number":    part_number or "",
            "price":          price,
            "order_id":       order_id,
        })
        logger.info("Payment email sent to %s for order %s at $%.2f", customer_email, order_id, price)
    except Exception as e:
        logger.error("Email failed for order %s: %s", order_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"Order saved but email failed: {str(e)}"
        )

    return {
        "status":   "success",
        "order_id": order_id,
        "price":    price,
        "message":  f"Payment link sent to {customer_email}"
    }