"""
order_expiry.py — Background scheduler for payment link expiry

How it works:
- Runs every 5 minutes
- Finds orders with status='pending' that were created more than 30 minutes ago
- For each expired order:
    1. Releases the reserved stock back to available in the inventory table
    2. Marks the order as 'cancelled' in the orders table

To use: import and call start_expiry_scheduler() in your app.py startup
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from database import get_connection

logger = logging.getLogger(__name__)

PAYMENT_TIMEOUT_MINUTES = 30


def release_expired_orders():
    """Find orders pending >30 min, release reserved stock, mark as cancelled."""
    try:
        conn   = get_connection()
        cursor = conn.cursor()

        # Find all orders that are still pending and older than 30 minutes
        cursor.execute("""
            SELECT order_id, part_number
            FROM orders
            WHERE status = 'pending'
            AND created_at < NOW() - INTERVAL '%s minutes'
        """, (PAYMENT_TIMEOUT_MINUTES,))

        expired_orders = cursor.fetchall()

        if not expired_orders:
            logger.info("Expiry check: no expired orders found.")
            cursor.close()
            conn.close()
            return

        logger.info("Expiry check: found %d expired order(s).", len(expired_orders))

        for order_id, part_number in expired_orders:
            try:
                # 1. Release reserved stock back to available in inventory
                if part_number:
                    cursor.execute("""
                        UPDATE inventory
                        SET reserved_stock = GREATEST(COALESCE(reserved_stock, 0) - 1, 0)
                        WHERE part_number = %s
                    """, (part_number,))
                    logger.info("Released reserved stock for part %s (order %s).", part_number, order_id)

                # 2. Mark the order as cancelled
                cursor.execute("""
                    UPDATE orders
                    SET status = 'cancelled'
                    WHERE order_id = %s AND status = 'pending'
                """, (order_id,))
                logger.info("Order %s marked as cancelled.", order_id)

            except Exception as e:
                logger.error("Error processing expired order %s: %s", order_id, e)

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        logger.error("Expiry scheduler error: %s", e)


def start_expiry_scheduler():
    """Start the background scheduler. Call this once when the app starts."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        release_expired_orders,
        trigger="interval",
        minutes=5,
        id="order_expiry",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Order expiry scheduler started (checks every 5 min, timeout=%d min).", PAYMENT_TIMEOUT_MINUTES)
    return scheduler
