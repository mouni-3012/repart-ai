import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

from routers.vin import router as vin_router
from routers.inventory import router as inventory_router
from routers.negotiation import router as negotiation_router
from routers.shipping import router as shipping_router
from routers.landing import router as landing_router
from routers.orders import router as orders_router
from routers.inquiry import router as inquiry_router
from routers.payments import router as payments_router
from routers.retell_webhook import router as retell_webhook_router

# Import the expiry scheduler
from order_expiry import start_expiry_scheduler

app = FastAPI(title="RePart AI Tools (Retell Safe)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vin_router)
app.include_router(inventory_router)
app.include_router(negotiation_router)
app.include_router(shipping_router)
app.include_router(landing_router)
app.include_router(orders_router)
app.include_router(inquiry_router)
app.include_router(payments_router)
app.include_router(retell_webhook_router)


@app.on_event("startup")
def startup_event():
    """Start the order expiry background scheduler when the server starts."""
    start_expiry_scheduler()


@app.get("/")
def home():
    return {"message": "RePart AI backend running"}