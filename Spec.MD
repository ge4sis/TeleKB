TeleKB(Telegram Knowledge Base)앱 개발 요구사항을 한 문서로 정리한 **Spec(개발 명세서)** 입니다.

---

# Telegram Channel Collector → Gemini 번역 → Markdown Exporter (Local GUI) Spec

## 1. 목적

사용자가 **구독 중인 텔레그램 채널(기본) 및 옵션으로 그룹/슈퍼그룹**에서 새 메시지를 수집하여, **한국어가 아닌 메시지만 Gemini로 한국어 번역**하고, **채널별/일자별 1개의 Markdown 파일**을 **단일 디렉토리**에 저장하는 로컬 앱을 만든다.

앱은 **스케줄링 없이** 사용자가 실행 버튼을 눌렀을 때 **1회 실행(배치 처리)**로 동작한다.

---

## 2. 타겟 환경

* OS: **Windows 우선**, **macOS도 고려**
* 실행 형태: 로컬 GUI 앱
* GUI 프레임워크: **Tkinter**
* 데이터 저장: 로컬 **SQLite**
* 텔레그램 접근: **MTProto 기반 클라이언트(예: Telethon 또는 Pyrogram)**

  * Bot API 사용하지 않음(구독 채널 다수 대상 요구사항 충족 목적)

---

## 3. 핵심 기능 요구사항

### 3.1 채널 관리(초기 1회 지정 + 이후 자동)

* 앱 최초 실행 시, 수집 대상 채널이 DB에 없으면 **채널 추가(가입 목록 선택)** 플로우를 수행한다.
* 이후부터는 **선택 UI 없이** DB에 저장된 수집 대상만으로 즉시 동작한다.
* 사용자는 필요 시 **채널 관리 화면**에서 채널을 **추가 또는 제외**할 수 있어야 한다.

### 3.2 채널 추가 정책(중요)

* 채널을 추가하는 경우, **추가한 시점 이후의 메시지부터** 수집 대상이 된다.
* 이를 위해 채널 추가 시:

  * 해당 채널의 **현재 최신 메시지 ID(latest_message_id)**를 조회하고,
  * DB에 `last_message_id = latest_message_id`로 저장한다.
* 과거 백필(과거 메시지 파일 생성)은 **하지 않는다(MUST NOT)**.

### 3.3 채널 제외(구독 해지 아님)

* “채널 제외”는 텔레그램 구독을 변경하지 않고, **향후 수집 대상에서만 배제**한다.
* 구현은 기본적으로 **Soft delete**:

  * DB의 `channels.is_enabled = 0`
* (선택 기능) “완전 삭제” 버튼을 제공할 수 있다(SHOULD).

  * 완전 삭제는 DB에서 row 제거이며, 제거 후 재추가 시에도 “추가 시점 이후만 수집” 정책으로 과거 재생성은 발생하지 않아야 한다.

### 3.4 수집 실행(배치, 1회)

* 메인 화면에서 **[실행]** 클릭 시:

  * `is_enabled=1`인 채널만 대상으로,
  * 각 채널에서 `last_message_id` 이후의 메시지를 모두 수집한다.
* 메시지마다:

  * 한국어 메시지는 번역을 **건너뛴다(MUST)**.
  * 한국어가 아니면 Gemini로 한국어 번역한다.
  * 이미지가 포함된 경우 `images` 서브 디렉토리에 다운로드한다(MUST).
  * 해당 일자의 Markdown 파일에 내용을 추가(Append)한다(이미지 링크 포함).
  * 중복 방지 기록을 DB에 남긴다.
* 처리 완료 후:

  * 성공적으로 저장된 메시지 중 최대 `message_id`로 해당 채널의 `last_message_id`를 갱신한다.

---

## 4. GUI 요구사항 (Tkinter)

### 4.1 메인 창

구성 요소(MUST):

* Output Directory 표시 + **[폴더 변경]** 버튼(폴더 선택 다이얼로그)
* **[실행]** 버튼
* **[채널 관리]** 버튼
* 진행 상태 표시(현재 채널명, 처리/생성/실패 카운트)
* 로그 텍스트 영역(스크롤)

동작(MUST):

* 네트워크 작업(채널 로딩/수집/번역)은 UI 프리징 방지를 위해 **백그라운드 작업 스레드**에서 수행하고, UI는 Queue/after로 업데이트한다.

### 4.2 채널 관리 창

구성 요소(MUST):

* “수집 대상 채널” 리스트(테이블 느낌)

  * 채널명, username(있으면), enabled 상태, last_message_id
* 버튼:

  * **[채널 추가]**
  * **[채널 제외]** (Soft delete: is_enabled=0)
  * (선택) **[완전 삭제]**
  * **[닫기]**

### 4.3 가입 목록 팝업(채널 추가용)

구성 요소(MUST):

* 체크박스: **[ ] 그룹 포함** (기본 OFF)

  * OFF: 채널만 표시
  * ON: 채널 + 그룹/슈퍼그룹도 표시
* (선택) 검색창
* 체크박스 다중 선택 리스트
* 버튼: **[추가] [취소]**

동작(MUST):

* “그룹 포함” 토글 변경 시 목록이 즉시 갱신된다.
* [추가] 클릭 시 선택 항목 각각에 대해:

  * latest_message_id를 조회
  * channels에 저장/활성화(`is_enabled=1`)
  * `last_message_id = latest_message_id`로 세팅

---

## 5. 한국어 감지(번역 스킵) 요구사항

### 5.1 is_korean(text) 휴리스틱 (MUST)

* 입력: `text: str | None`
* 규칙:

  1. `text`가 `None` 또는 공백뿐이면 → 한국어 아님(False)
  2. URL 제거 후, 기호/공백 제거 등으로 “유의미 글자”만 남김
  3. 유의미 글자 수 `< 5`면 → False (판별 불가로 보고 번역 시도)
  4. 한글로 카운트하는 유니코드 범위:

     * `가-힣`, `ㄱ-ㅎ`, `ㅏ-ㅣ`
  5. `korean_ratio = 한글 글자 수 / 유의미 글자 수`
  6. `korean_ratio >= 0.30` 이면 True(한국어로 간주) → 번역 스킵

     * else False → 번역 수행

### 5.2 한국어 메시지의 Markdown 표기 (SHOULD)

* 번역 섹션에 아래 문구 1줄 남김을 권장:

  * `> 번역 생략: 원문이 한국어로 판단됨`

---

## 6. 파일 저장 요구사항

### 6.1 저장 위치

* 모든 Markdown 파일은 **OUTPUT_DIR 하위의 `YYYY-MM` (예: `2026-02`) 디렉토리**에 저장한다(MUST).
* **폴더명의 기준은 메시지 생성 시간(Local Time)을 따른다.**
* 해당 디렉토리가 없다면 자동으로 생성해서 저장해야 한다.

### 6.2 파일명 규칙 (MUST)

* 포맷: `채널명_YYYYMMDD.md`
* 일자(YYYYMMDD)의 기준은 **메시지 수신 일자(Local Time)**를 따른다.

### 6.3 파일명 정제(sanitize) (MUST)

* Windows/macOS 공통으로 안전하게 저장되도록:

  * 금지 문자 제거/치환: `\/:*?"<>|`
  * 개행/탭 제거
  * 공백 정리
  * 길이 제한(권장, MUST로 구현해도 됨):

    * 채널명 최대 30자

### 6.5 이미지 처리 (MUST)

### 6.5 이미지 처리 (MUST)

* 메시지에 포함된 이미지는 **Markdown 파일이 저장된 `YYYY-MM` 디렉토리 하위의 `images` 디렉토리**에 저장한다.
  * 즉, `OUTPUT_DIR/YYYY-MM/images` 위치에 저장된다.
* 이미지 파일명은 중복 방지를 위해 `{channel_id}_{message_id}.jpg` 형식을 권장한다.
* Markdown 파일 내에 해당 이미지에 대한 링크를 포함시켜야 한다.
  * 예: `![Image](images/12345_67890.jpg)` (같은 폴더 내의 images 폴더이므로 상대 경로 사용)

### 6.4 파일 내용 (SHOULD)

* 각 메시지는 구분선(---) 등으로 구별되도록 추가한다.
* 메시지 헤더 (메시지 ID, 시간 등)
* 원문 텍스트
* 번역 텍스트(또는 번역 생략 문구)
* (이미지 존재 시) 이미지 섹션 및 로컬 이미지 링크

---

## 7. 중복 방지 및 상태 관리

### 7.1 SQLite 스키마 (MUST)

* `channels`

  * `channel_id` INTEGER/TEXT (PK; 라이브러리 타입에 맞춤)
  * `title` TEXT
  * `username` TEXT NULL
  * `last_message_id` INTEGER DEFAULT 0
  * `is_enabled` INTEGER DEFAULT 1
  * `created_at`, `updated_at` (선택)
  * `last_run_at` (선택)

* `messages`

  * `channel_id`
  * `message_id`
  * `file_path`
  * `created_at`
  * UNIQUE(`channel_id`, `message_id`)

### 7.2 상태 갱신 규칙 (MUST)

* 메시지 파일 생성이 성공하고 `messages`에 기록된 후에만

  * 채널의 `last_message_id` 갱신 대상에 포함
* 실행 종료 시 채널별로 `last_message_id`를 “이번 실행에서 성공 저장된 최대 message_id”로 업데이트

### 7.3 기기 간 동기화 (Sync State) (NEW)

* **목적**: 여러 기기에서 동일한 `OUTPUT_DIR`을 공유(예: GitHub Sync)할 때, 수집 대상 채널과 마지막 수집 시점을 동기화한다.
* **메커니즘**: `OUTPUT_DIR/sync_state.json` 파일을 매개체로 사용한다.
* **동작 정책**:
  * **불러오기(Import)**: 앱 시작 시 또는 출력 폴더 변경 시, `sync_state.json`이 존재하면 로컬 DB의 `channels` 테이블을 업데이트한다.
    * JSON에만 있는 채널은 로컬 DB에 추가한다.
    * 이미 존재하는 채널은 `last_message_id`를 `MAX(로컬, JSON)`으로 갱신하고, `is_enabled` 상태를 JSON 값으로 동기화한다.
  * **저장하기(Export)**: 수집 작업이 성공적으로 종료되면, 최신 `channels` 테이블 상태를 `sync_state.json`으로 덮어쓴다.
* **주의**: `telekb.db` 및 `.session` 파일은 기기별로 로컬에 유지하여 Git 충돌을 방지한다.

---

## 8. Gemini 번역 요구사항

* Gemini API Key 기반 사용 (환경변수 또는 설정 파일; 키 하드코딩 금지)
* 번역 실패 시 정책(MUST):

  * 번역이 실패해도 **원문으로 Markdown 파일은 생성**
  * 로그에 실패 기록
* 번역 대상 텍스트가 비어 있으면 번역 호출하지 않음(MUST)

---

## 9. 에러 처리/로그 요구사항

* 네트워크 오류(텔레그램/Gemini), 권한 문제, 파일 쓰기 오류 등은:

  * 앱이 전체 중단하지 말고 가능한 범위에서 계속 진행(SHOULD)
  * 실패 건수 및 사유를 로그에 남김(MUST)
* 최종 요약 로그:

  * 처리 채널 수, 새 메시지 수(처리 시도), 생성 파일 수, 실패 수

---

## 10. 비기능 요구사항

* 로컬에서 안전하게 동작:

  * 텔레그램 세션 파일 및 SQLite는 로컬 디스크에 저장
  * API Key는 환경변수/설정으로 관리(로그에 노출 금지)
* Windows/macOS에서 파일명/경로 호환성 확보(MUST)

---

## 11. 구현 범위 외(명시)

* 스케줄링/백그라운드 상시 실행: **하지 않음**
* 과거 백필/대량 아카이빙: **하지 않음**
* 텔레그램 클라이언트 캐시/로컬 DB를 직접 파싱해서 가져오기: **하지 않음**

---

## 12. 산출물(Deliverables)

* 소스코드(모듈 분리 권장):

  * telegram client wrapper
  * state store(SQLite)
  * korean detector
  * gemini translator
  * markdown writer
  * tkinter UI
* 실행 방법 문서(README):

  * 의존성 설치
  * 텔레그램 로그인/세션 생성
  * Gemini API Key 설정
  * 빌드/패키징(우선 Windows, 이후 macOS)