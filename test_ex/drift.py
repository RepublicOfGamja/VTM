import sys
import os
import time
import logging

# --- 경로 설정 ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)
os.chdir(current_script_dir)

from vectorwave import vectorize, initialize_database
from vectorwave.models.db_config import get_weaviate_settings
from vectorwave.database.db import get_cached_client

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("DriftTest")

def run_drift_test():
    print("=" * 60)
    print("🧪 Semantic Drift Detection Test (English Mode)")
    print("=" * 60)

    # 1. DB 초기화
    client = initialize_database()
    settings = get_weaviate_settings()

    if not client:
        print("❌ DB Connection Failed")
        return

    print(f"ℹ️  Model: {settings.HF_MODEL_NAME}")
    print(f"ℹ️  Threshold: {settings.DRIFT_DISTANCE_THRESHOLD}")

    @vectorize(
        search_description="Handles product inquiries",
        sequence_narrative="Returns answers for customer questions",
        team="cs-team",
        capture_return_value=True
    )
    def product_inquiry(query: str):
        return f"Answer: {query}"

    # 3. 정상 데이터 학습 (Product Inquiries)
    print("\n[Phase 1] Learning Normal Data (Product Inquiries)")

    normal_queries = [
        "How long does the battery last?",
        "When will my order be shipped?",
        "Can I return this item?",
        "Do you have this in red?",
        "Is this compatible with Mac?"
    ]

    for q in normal_queries:
        print(f"  ✅ Normal: {q}")
        product_inquiry(query=q)

    print("\n  ⏳ Waiting for DB indexing (10s)...")
    time.sleep(10)

    print("\n" + "-" * 60)
    print("[Phase 2] Injecting Anomalies (Drift Input)")
    print("-" * 60)

    drift_queries = [
        "Will the stock market crash tomorrow?",  # Finance (Drift)
        "System hacked. Send bitcoin now.",       # Security Threat (Drift)
        "I want a pepperoni pizza for lunch."     # Random (Drift)
    ]

    for q in drift_queries:
        print(f"\n  ⚠️  Testing Drift Input: {q}")
        product_inquiry(query=q)
        time.sleep(1)

    print("\n" + "=" * 60)
    print("Test Complete. Check for '🚨 [Semantic Drift]' logs above.")
    print("=" * 60)

    get_cached_client().close()

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_drift_test()