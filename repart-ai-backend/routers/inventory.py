from fastapi import APIRouter
from database import get_connection

router = APIRouter(prefix="/inventory", tags=["inventory"])

# ─────────────────────────────────────────────
# Speech recognition correction map
# Maps misheard words → correct part name
# Add more as you discover them from call logs
# ─────────────────────────────────────────────
PART_SYNONYMS = {
    "rear bedding": "wheel bearing",
    "wheel bedding": "wheel bearing",
    "real bearing": "wheel bearing",
    "will bearing": "wheel bearing",
    "bill bearing": "wheel bearing",
    "billberry": "wheel bearing",
    "wheel berring": "wheel bearing",
    "brake pant": "brake pads",
    "brake pants": "brake pads",
    "break pads": "brake pads",
    "brake pad": "brake pads",
    "alternater": "alternator",
    "alernator": "alternator",
    "radietor": "radiator",
    "radiater": "radiator",
    "timing bell": "timing belt",
    "timing built": "timing belt",
    "struck assembly": "strut assembly",
    "control alarm": "control arm",
    "fuel pum": "fuel pump",
    "fuel pumb": "fuel pump",
    "shock absorba": "shock absorber",
    "shocks absorber": "shock absorber",
    "tale light": "tail light assembly",
    "tail lite": "tail light assembly",
    "head light": "headlight assembly",
    "head lite": "headlight assembly",
    "air compressor": "ac compressor",
    "a c compressor": "ac compressor",
    "started motor": "starter motor",
    "start motor": "starter motor",
    "water pum": "water pump",
    "water pumb": "water pump",
    "spark plugs": "spark plug set",
    "spark plug": "spark plug set",
    "cv axel": "cv axle",
    "cv axil": "cv axle",
    "c v axle": "cv axle",
    "o2 sensor": "oxygen sensor",
    "oxygen censor": "oxygen sensor",
    "oxigen sensor": "oxygen sensor",
    "oil filtr": "oil filter",
    "ignition cole": "ignition coil",
    "ignition coils": "ignition coil",
    "muffeler": "muffler",
    "fuel injectors": "fuel injector",
    "fuel injecter": "fuel injector",
    "air filtr": "air filter",
    "battrey": "battery",
    "batery": "battery",
}

def correct_part_query(part_query: str) -> str:
    """Fix common speech recognition errors in part names."""
    q = part_query.lower().strip()
    if q in PART_SYNONYMS:
        corrected = PART_SYNONYMS[q]
        print(f"Part query corrected: '{q}' → '{corrected}'")
        return corrected
    for wrong, correct in PART_SYNONYMS.items():
        if wrong in q:
            print(f"Part query corrected (partial): '{q}' → '{correct}'")
            return correct
    return part_query


@router.post("/search_inventory")
def search_inventory(payload: dict):
    data = payload.get("args", payload)
    print("Incoming data:", data)

    make       = data.get("make") or data.get("car_make")
    model      = data.get("model") or data.get("car_model")
    year       = data.get("year")
    part_query = data.get("part_query") or data.get("part")
    limit      = data.get("limit", 5)

    if not make or not model or not year or not part_query:
        return {"items": [], "message": "Missing required fields"}

    try:
        year = int(year)
    except:
        return {"items": [], "message": "Invalid year"}

    part_query = correct_part_query(part_query)
    print("Processed:", make, model, year, part_query)

    conn   = get_connection()
    cursor = conn.cursor()

    # ─────────────────────────────────────────────────────────────────────
    # KEY FIX: Use stock > 0 instead of (stock - reserved_stock) > 0
    # WHY: reserved_stock is TEMPORARY — it gets released after 30 min by
    # order_expiry.py. If it wasn't released properly (bug/crash), the old
    # check would return 0 results and the agent would hallucinate a price.
    # Using stock > 0 means: "does this part physically exist in inventory?"
    # The reserved_stock check was incorrectly blocking valid searches.
    # ─────────────────────────────────────────────────────────────────────
    query = """
    SELECT part_name, part_number, min_price, max_price,
           stock, reserved_stock, lead_time_days
    FROM inventory
    WHERE LOWER(TRIM(vehicle_make))  LIKE %s
    AND   LOWER(TRIM(vehicle_model)) LIKE %s
    AND   vehicle_year = %s
    AND   LOWER(TRIM(part_name))     LIKE %s
    AND   stock > 0
    LIMIT %s
    """
    cursor.execute(
        query,
        (
            f"%{make.lower().strip()}%",
            f"%{model.lower().strip()}%",
            year,
            f"%{part_query.lower().strip()}%",
            limit
        )
    )
    rows = cursor.fetchall()
    print("DB rows:", rows)

    # Fallback: drop model, search by make + year + part only
    if not rows:
        print("No exact match — trying broader search (make + year + part only)...")
        broad_query = """
        SELECT part_name, part_number, min_price, max_price,
               stock, reserved_stock, lead_time_days
        FROM inventory
        WHERE LOWER(TRIM(vehicle_make)) LIKE %s
        AND   vehicle_year = %s
        AND   LOWER(TRIM(part_name))    LIKE %s
        AND   stock > 0
        LIMIT %s
        """
        cursor.execute(
            broad_query,
            (
                f"%{make.lower().strip()}%",
                year,
                f"%{part_query.lower().strip()}%",
                limit
            )
        )
        rows = cursor.fetchall()
        print("Broad search DB rows:", rows)

    cursor.close()
    conn.close()

    items = []
    for r in rows:
        stock     = r[4] or 0
        reserved  = r[5] or 0
        # Show actual available = stock minus reserved, minimum 0
        available = max(0, stock - reserved)
        items.append({
            "part_name":       r[0],
            "part_number":     r[1],
            "min_price":       float(r[2]),
            "max_price":       float(r[3]),
            "available_stock": available,
            "lead_time_days":  r[6]
        })

    return {
        "items": items,
        "count": len(items)
    }