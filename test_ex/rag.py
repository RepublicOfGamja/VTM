import sys
import os
from dotenv import load_dotenv

# --- 1. 경로 설정 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# --- 2. 모듈 임포트 ---
try:
    from vectorwave import initialize_database, search_executions
    # [신규] RAG 기능 임포트 (src/vectorwave/__init__.py에 추가되었다고 가정)
    from vectorwave import search_and_answer, analyze_trace_log
    from vectorwave.database.db import get_cached_client
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    print("   src/vectorwave/__init__.py 파일에 search_and_answer, analyze_trace_log가 추가되었는지 확인해주세요.")
    sys.exit(1)

def run_rag_test():
    # DB 초기화
    print("🔌 데이터베이스 연결 중...")
    client = initialize_database()
    if not client:
        print("❌ DB 연결 실패. Weaviate가 실행 중인지 확인하세요.")
        return

    print("\n" + "="*60)
    print("🤖 [Test 1] Code RAG: 함수 검색 및 질문 (다국어 테스트)")
    print("="*60)

    query_kr = "결제 처리 로직이 어떻게 되는지 설명해줘."
    query_en = "How is the payment processed?"

    # 1-1. 한국어 질문 테스트
    print(f"\n🇰🇷 [Korean Query]: {query_kr}")
    answer_kr = search_and_answer(query=query_kr, language='ko')
    print(f"[AI Answer]:\n{answer_kr}\n")

    # 1-2. 영어 질문 테스트
    print(f"🇺🇸 [English Query]: {query_en}")
    answer_en = search_and_answer(query=query_en, language='en')
    print(f"[AI Answer]:\n{answer_en}")


    print("\n" + "="*60)
    print("🕵️ [Test 2] Trace RAG: 실행 로그 분석 (다국어 테스트)")
    print("="*60)

    # 최신 실행 로그(Trace ID) 가져오기
    recent_logs = search_executions(limit=1, sort_by="timestamp_utc", sort_ascending=False)

    if recent_logs:
        target_trace_id = recent_logs[0]['trace_id']
        print(f"target_trace_id: {target_trace_id}")

        # 2-1. 한국어 분석 테스트
        print(f"\n🇰🇷 [Korean Analysis Request]")
        analysis_kr = analyze_trace_log(trace_id=target_trace_id, language='ko')
        print(f"[AI Analysis]:\n{analysis_kr}\n")

        # 2-2. 영어 분석 테스트
        print(f"🇺🇸 [English Analysis Request]")
        analysis_en = analyze_trace_log(trace_id=target_trace_id, language='en')
        print(f"[AI Analysis]:\n{analysis_en}")

    else:
        print("⚠️ 분석할 실행 로그가 없습니다.")
        print("   -> 'python test_ex/example.py'를 먼저 실행하여 로그를 생성해주세요.")

    # 연결 종료
    get_cached_client().close()
    print("\n✅ 테스트 완료.")

if __name__ == "__main__":
    load_dotenv() # .env 파일 로드 (OPENAI_API_KEY 필수)
    run_rag_test()