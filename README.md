# 책이랑 — 학교협동조합 온라인 중고책 서점

## 포함 기능
- 도서 검색/분류, 상태·가격·재고 표시
- 장바구니, 학교 수령 또는 택배 선택, 주문 접수, 내 주문 조회
- 관리자 로그인, 도서 등록/가격·재고·판매 여부 관리, 주문 상태 변경
- SQLite 데이터 저장
- 입점 사업자, 정액제 콘텐츠, 쿠폰, 마일리지 제외

## 로컬 실행
Python 3.10 이상 권장:
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```
관리자 비밀번호 기본값은 `change-this-admin-password`입니다. 운영 전 반드시 `ADMIN_PASSWORD` 환경 변수로 바꾸세요.

## 학교 구성원 접근 제한
환경 변수 `SCHOOL_EMAIL_DOMAIN` 및/또는 `SCHOOL_ACCESS_CODE`를 설정할 수 있습니다. 둘 다 미설정이면 개발 모드로 이메일 형식만 확인합니다. 이메일 도메인 입력만으로 이메일 소유권이 검증되지는 않으므로 실제 운영에서는 학교 SSO/인증 메일/관리자 승인을 추가해야 합니다.

Streamlit Community Cloud의 Settings → Secrets 예시:
```toml
ADMIN_PASSWORD = "강력한-새-비밀번호"
SCHOOL_EMAIL_DOMAIN = "school.ac.kr"
SCHOOL_ACCESS_CODE = "학교에서_배포한_코드"
```

## GitHub/Streamlit 배포
`streamlit_app.py`, `requirements.txt`, `README.md`를 저장소 최상위에 올리고 Streamlit Community Cloud에서 Main file path를 `streamlit_app.py`로 지정합니다.

## 결제 및 운영 한계
이 MVP는 주문 접수 데모이며 **실제 온라인 결제를 처리하지 않습니다**. 실결제에는 PG사 계약 및 결제창/서버 승인 검증/취소·환불 처리가 필요합니다. 결제 비밀키를 GitHub에 올리지 마세요.
SQLite 파일은 Streamlit Cloud 재시작/재배포 시 영속성이 보장되지 않을 수 있습니다. 실제 다중 사용자 운영에는 Supabase/PostgreSQL 같은 영속 DB, 학교 구성원 인증, 권한 강화, 개인정보/환불 정책, 백업이 필요합니다.
