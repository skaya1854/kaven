# Kaven Web App Scaffold

Kaven을 웹 앱 형태로 포팅하기 위한 최소 구조입니다.

## 구조

- `backend/app.py`: FastAPI 엔드포인트 (`/health`, `/runs/latest`, `/runs/once`)
- `frontend/index.html`: 백엔드 호출용 간단 대시보드

## 백엔드 실행

```bash
pip install fastapi uvicorn
uvicorn webapp.backend.app:app --reload --port 8000
```

## 프론트 실행

정적 파일이므로 아무 정적 서버로 열면 됩니다.

예시:
```bash
python -m http.server 8080 --directory webapp/frontend
```

브라우저에서 `http://127.0.0.1:8080` 접속 후 버튼으로 API 호출.
