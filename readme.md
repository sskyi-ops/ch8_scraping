# Python Project Template

FastAPI 기반의 웹 API 및 데이터 처리를 위한 파이썬 프로젝트입니다.

## 주요 기능

* **RESTful API 서버**: `FastAPI`와 `Uvicorn`을 활용한 고성능 비동기 웹 서버
* **데이터 처리 및 분석**: `Pandas` 및 `NumPy`를 이용한 데이터 조작
* **환경 변수 및 데이터 검증**: `python-dotenv`와 `Pydantic`을 통한 설정 관리 및 스키마 검증
* **코드 품질 및 테스트**: `Pytest`, `Black`, `Flake8`을 활용한 테스트 자동화 및 코드 포맷팅

## 시작하기

### 사전 요구 사항

* Python 3.9 이상 권장

### 설치 방법

1. 저장소를 클론합니다.
   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. 가상 환경을 생성하고 활성화합니다.
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. 필요한 패키지를 설치합니다.
   ```bash
   pip install -r requirements.txt
   ```

4. 환경 변수 설정을 위해 루트 디렉토리에 `.env` 파일을 생성합니다.
   ```env
   APP_ENV=development
   PORT=8000
   ```

## 실행 방법

### 로컬 서버 실행
```bash
uvicorn main:app --reload
```
서버가 실행되면 브라우저에서 `http://127.0.0.1:8000/docs`로 접속하여 Swagger API 문서를 확인할 수 있습니다.

### 테스트 및 코드 포맷팅
```bash
# 테스트 실행
pytest

# 코드 포맷팅 (Black)
black .

# 린트 검사 (Flake8)
flake8
```

## 프로젝트 구조

```text
├── main.py              # 애플리케이션 진입점
├── requirements.txt     # 프로젝트 의존성 목록
├── .env                 # 환경 변수 설정 파일
└── tests/               # 테스트 코드 디렉토리
```