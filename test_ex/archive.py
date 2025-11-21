import sys
import os
import time
from dotenv import load_dotenv

# --- 1. 경로 설정 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

try:
    from vectorwave import vectorize, initialize_database
    from vectorwave.database.db import get_cached_client
    # Archiver 임포트 (아직 __init__.py에 추가 안 했을 경우를 대비해 직접 경로 지정)
    from vectorwave.database.archiver import VectorWaveArchiver
except ImportError as e:
    print(f"모듈 임포트 실패: {e}")
    sys.exit(1)

# --- 2. 테스트용 함수 정의 ---
@vectorize(
    search_description="Archive Test Function",
    sequence_narrative="Function to generate logs for archiving tests.",
    team="data-eng"
)
def archive_test_func(idx: int):
    print(f"  [Exec] archive_test_func({idx}) executed.")
    return {"result": idx * 10, "status": "ok"}

def run_archiving_demo():
    # DB 초기화
    print("🔌 데이터베이스 연결 중...")
    client = initialize_database()
    if not client:
        print("❌ DB 연결 실패.")
        return

    archiver = VectorWaveArchiver()
    target_func = "archive_test_func"

    print("\n" + "="*60)
    print("🛠️  [Step 1] 테스트 데이터 생성")
    print("="*60)

    # 로그 10개 생성
    for i in range(10):
        archive_test_func(i)

    # Weaviate가 비동기로 데이터를 저장할 시간을 줌 (Batch flush)
    print("  ⏳ 데이터 저장 대기 중 (3초)...")
    time.sleep(3)

    print("\n" + "="*60)
    print("📂 [Step 2] 백업 (Snapshot) - 내보내기만 수행")
    print("="*60)
    # 데이터는 유지하고 파일만 생성
    res_backup = archiver.export_and_clear(
        function_name=target_func,
        output_file="data/backup_snapshot.jsonl",
        clear_after_export=False
    )
    print(f"  -> 결과: {res_backup}")

    print("\n" + "="*60)
    print("📦 [Step 3] 아카이빙 (Archive) - 내보내고 DB에서 삭제")
    print("="*60)
    # 10개 중 일부가 이미 백업되었지만, 이번엔 삭제까지 수행
    # (실제로는 UUID로 중복 체크를 하거나 쿼리 시점에 따라 다를 수 있음)
    res_archive = archiver.export_and_clear(
        function_name=target_func,
        output_file="data/archive_data.jsonl",
        clear_after_export=True
    )
    print(f"  -> 결과: {res_archive}")

    print("\n" + "="*60)
    print("🗑️  [Step 4] 청소 (Purge) - 남은 데이터 삭제")
    print("="*60)
    # 테스트를 위해 데이터 5개 추가 생성
    print("  -> 삭제 테스트용 데이터 5개 추가 생성 중...")
    for i in range(100, 105):
        archive_test_func(i)
    time.sleep(3)

    # 파일 저장 없이 삭제만 수행
    res_purge = archiver.export_and_clear(
        function_name=target_func,
        output_file="",
        delete_only=True
    )
    print(f"  -> 결과: {res_purge}")

    # 연결 종료
    get_cached_client().close()
    print("\n✅ 모든 테스트 완료.")

if __name__ == "__main__":
    load_dotenv()
    run_archiving_demo()