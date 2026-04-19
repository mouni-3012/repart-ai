from fastapi import APIRouter, HTTPException
from email.message import EmailMessage
import smtplib
from datetime import datetime
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_payment_link(order_id: str) -> str:
    return f"https://repart.ai/pay/{order_id}"


def generate_invoice_text(customer_name: str, order_id: str, part_name: str, price: float) -> str:
    """Plain-text invoice (used as fallback and inside the email body)."""
    return f"""
RePart AI — Invoice
=======================================
Date       : {datetime.now().strftime("%Y-%m-%d")}
Order ID   : {order_id}
Customer   : {customer_name}
---------------------------------------
Part       : {part_name}
Total Price: ${price:.2f}
=======================================
Thank you for choosing RePart AI!
"""


def generate_email_html(customer_name: str, order_id: str, part_name: str,
                         price: float, payment_link: str) -> str:
    """
    Clean HTML email with the payment link and invoice table.
    Works in Gmail, Outlook, Apple Mail.
    """
    date_str = datetime.now().strftime("%B %d, %Y")
    return f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Your RePart AI Order</title></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

        <!-- Header -->
        <tr>
          <td style="background:#1a1a2e;padding:28px 40px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;letter-spacing:1px;">RePart AI</h1>
            <p style="margin:4px 0 0;color:#a0a0c0;font-size:13px;">Your auto parts, delivered fast</p>
          </td>
        </tr>

        <!-- Greeting -->
        <tr>
          <td style="padding:32px 40px 0;">
            <p style="margin:0;font-size:16px;color:#333;">Hi <strong>{customer_name}</strong>,</p>
            <p style="margin:12px 0 0;font-size:15px;color:#555;line-height:1.6;">
              Great news — your order has been confirmed! Click the button below to complete your
              payment securely and we'll get your part shipped right away.
            </p>
          </td>
        </tr>

        <!-- Payment Button -->
        <tr>
          <td style="padding:28px 40px;text-align:center;">
            <a href="{payment_link}"
               style="display:inline-block;background:#e63946;color:#ffffff;
                      font-size:16px;font-weight:bold;padding:14px 36px;
                      border-radius:6px;text-decoration:none;letter-spacing:0.5px;">
              Pay Now &rarr;
            </a>
            <p style="margin:10px 0 0;font-size:12px;color:#999;">
              Or copy this link: <a href="{payment_link}" style="color:#555;">{payment_link}</a>
            </p>
          </td>
        </tr>

        <!-- Divider -->
        <tr><td style="padding:0 40px;"><hr style="border:none;border-top:1px solid #eeeeee;"></td></tr>

        <!-- Invoice Table -->
        <tr>
          <td style="padding:24px 40px;">
            <h2 style="margin:0 0 16px;font-size:15px;color:#333;text-transform:uppercase;
                        letter-spacing:1px;border-bottom:2px solid #1a1a2e;padding-bottom:8px;">
              Invoice
            </h2>
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="font-size:14px;color:#444;">
              <tr style="background:#f8f8f8;">
                <td style="padding:10px 12px;border-radius:4px 0 0 4px;"><strong>Order ID</strong></td>
                <td style="padding:10px 12px;text-align:right;border-radius:0 4px 4px 0;">{order_id}</td>
              </tr>
              <tr>
                <td style="padding:10px 12px;"><strong>Date</strong></td>
                <td style="padding:10px 12px;text-align:right;">{date_str}</td>
              </tr>
              <tr style="background:#f8f8f8;">
                <td style="padding:10px 12px;border-radius:4px 0 0 4px;"><strong>Customer</strong></td>
                <td style="padding:10px 12px;text-align:right;border-radius:0 4px 4px 0;">{customer_name}</td>
              </tr>
              <tr>
                <td style="padding:10px 12px;"><strong>Part</strong></td>
                <td style="padding:10px 12px;text-align:right;">{part_name}</td>
              </tr>
              <tr style="background:#1a1a2e;">
                <td style="padding:12px 12px;color:#fff;border-radius:4px 0 0 4px;"><strong>Total</strong></td>
                <td style="padding:12px 12px;color:#fff;text-align:right;
                            font-size:16px;font-weight:bold;border-radius:0 4px 4px 0;">
                  ${price:.2f}
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <!-- Footer note -->
        <tr>
          <td style="padding:0 40px 28px;">
            <p style="margin:16px 0 0;font-size:13px;color:#999;line-height:1.6;">
              After payment is received, we will process and ship your part with tracking.
              If you have any questions reply to this email or contact our support.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#f0f0f0;padding:16px 40px;text-align:center;">
            <p style="margin:0;font-size:12px;color:#aaa;">
              &copy; {datetime.now().year} RePart AI &bull; All rights reserved
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def send_email(to_email: str, subject: str, html_body: str, text_body: str):
    """Send email with both HTML and plain-text fallback."""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        raise Exception("EMAIL_ADDRESS or EMAIL_PASSWORD missing in .env")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    # Plain-text fallback (shown in email clients that block HTML)
    msg.set_content(text_body)

    # HTML version (shown by default in modern clients)
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        logger.info("Payment email sent to %s", to_email)


# ---------------------------------------------------------------------------
# Stock reduction helper
# ---------------------------------------------------------------------------

def reduce_stock(part_number: str):
    """
    Decrease stock by 1 for the given part_number in PostgreSQL.
    Called after a successful deal close.
    """
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE inventory SET stock = stock - 1 WHERE part_number = %s AND stock > 0",
            (part_number,)
        )
        rows_updated = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        if rows_updated == 0:
            logger.warning("Stock not reduced for part %s — already 0 or not found", part_number)
        else:
            logger.info("Stock reduced by 1 for part %s", part_number)
        return rows_updated > 0
    except Exception as e:
        logger.error("Failed to reduce stock for part %s: %s", part_number, e)
        return False


# ---------------------------------------------------------------------------
# Main function — called by the Retell webhook after deal closes
# ---------------------------------------------------------------------------

def send_payment_email(data: dict):
    """
    Send payment link + invoice to the customer via email.

    Required keys in data:
        customer_name   — e.g. "John Smith"
        customer_email  — e.g. "john@example.com"
        part_name       — e.g. "Alternator"
        price           — e.g. 220.00  (float or string)
        order_id        — e.g. "a1b2c3d4"
        part_number     — e.g. "ALT-ME2010-0"  (optional, used for stock reduction)
    """
    logger.info("send_payment_email called with: %s", data)

    customer_name  = data["customer_name"]
    customer_email = data["customer_email"]
    part_name      = data["part_name"]
    order_id       = data["order_id"]
    part_number    = data.get("part_number", "")

    try:
        price = float(data["price"])
    except (KeyError, ValueError, TypeError):
        raise ValueError("price must be a number")

    payment_link = generate_payment_link(order_id)

    html_body = generate_email_html(customer_name, order_id, part_name, price, payment_link)
    text_body = (
        f"Hi {customer_name},\n\n"
        f"Your order is confirmed. Pay here: {payment_link}\n\n"
        + generate_invoice_text(customer_name, order_id, part_name, price)
    )

    send_email(customer_email, f"RePart AI — Your Payment Link (Order {order_id})", html_body, text_body)

    # Reduce stock in DB after sending the email
    if part_number:
        reduce_stock(part_number)


# ---------------------------------------------------------------------------
# Swagger test endpoint  (POST /payments/send_payment_email)
# ---------------------------------------------------------------------------

@router.post("/send_payment_email")
def send_payment_email_api(payload: dict):
    """Manual test endpoint — call this from Swagger to verify email is working."""
    required = ["customer_name", "customer_email", "part_name", "price", "order_id"]
    missing = [f for f in required if not payload.get(f)]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing fields: {missing}")

    try:
        send_payment_email(payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "message": f"Email sent to {payload['customer_email']}"}
