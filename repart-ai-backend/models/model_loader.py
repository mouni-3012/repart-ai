from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "acceptance_model.pkl"

try:
    acceptance_model = joblib.load(MODEL_PATH)
    print(f"✅ Acceptance model loaded: {MODEL_PATH}")
except Exception as e:
    print(f"❌ Failed to load acceptance model from {MODEL_PATH}: {e}")
    acceptance_model = None
