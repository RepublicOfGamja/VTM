


# VectorWave: Seamless Auto-Vectorization Framework

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 🌟 프로젝트 소개 (Overview)

**VectorWave**는 파이썬 함수/메서드의 출력을 **데코레이터**를 사용하여 자동으로 **벡터 데이터베이스(Vector DB)**에 저장하고 관리하는 혁신적인 프레임워크입니다. 개발자는 데이터 수집, 임베딩 생성, 벡터 DB 저장의 복잡한 과정을 신경 쓸 필요 없이, 단 한 줄의 코드(`@vectorize`)로 함수 출력을 지능적인 벡터 데이터로 변환할 수 있습니다.

## ✨ 주요 특징 (Features)

* **`@vectorize` 데코레이터:** 함수 호출 시 반환되는 데이터를 지정된 Vector DB에 자동으로 임베딩하고 저장합니다.
* **간결한 검색 인터페이스:** 저장된 벡터 데이터에 대한 유의미한 검색(Similarity Search) 기능을 제공하여 RAG(Retrieval-Augmented Generation) 시스템 구축을 용이하게 합니다.

## ⚙️ 설정 (Configuration)

VectorWave는 Weaviate 데이터베이스 연결 정보를 **환경 변수** 또는 `.env` 파일을 통해 자동으로 읽어옵니다.

라이브러리를 사용하는 당신의 프로젝트 루트 디렉터리(예: `main.py`가 있는 곳)에 `.env` 파일을 생성하고 필요한 값들을 설정하세요.

### .env 파일 예시

```ini
# .env
# VectorWave가 연결할 Weaviate 서버의 주소입니다.
WEAVIATE_HOST=localhost

# Weaviate 서버의 REST API 포트입니다. (기본값 8080)
WEAVIATE_PORT=8080

# Weaviate 서버의 gRPC 포트입니다. (기본값 50051)
WEAVIATE_GRPC_PORT=50051

# text2vec-openai 모듈 등을 사용할 경우 OpenAI API 키가 필요합니다.
# OPENAI_API_KEY=sk-your-key-here
```

## 🤝 기여 (Contributing)

버그 보고, 기능 요청, 코드 기여 등 모든 형태의 기여를 환영합니다. 자세한 내용은 [CONTRIBUTING.md](https://www.google.com/search?q=CONTRIBUTING.md)를 참고해 주세요.

## 📜 라이선스 (License)

이 프로젝트는 MIT 라이선스에 따라 배포됩니다. 자세한 내용은 [LICENSE](https://www.google.com/search?q=LICENSE) 파일을 확인하세요.


