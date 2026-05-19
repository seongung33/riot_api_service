# Riot API Insight Service

League of Legends Riot API 데이터를 수집하고 최근 경기 기반 인사이트를 제공하는 MVP 프로젝트입니다.

## Frontend MVP

Vue 프론트엔드는 `frontend/`에 있습니다.

```bash
cd frontend
npm install
npm run dev
```

개발 서버 기본 주소는 `http://127.0.0.1:5173`입니다.

프론트엔드는 Vite dev proxy를 통해 Django 백엔드의 `http://127.0.0.1:8000/api`로 요청을 전달합니다. 검색 기능을 사용하려면 백엔드 서버도 함께 실행되어 있어야 합니다.

현재 구현된 화면:

- Riot ID 검색 폼
- `POST /api/accounts/search/` 호출
- 최근 경기 summary 카드
- rule-based feedback 카드
- champion performance 테이블
- 최근 match 리스트
