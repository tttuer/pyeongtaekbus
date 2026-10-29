# 평택버스

FastAPI와 MySQL로 만든 평택여객 웹사이트입니다. 버스 시간표, 공지사항, 고객 문의, 분실물 및 관리자 화면을 제공합니다.

## 실행 흐름

**Python 준비 → 설정 파일 작성 → MySQL 실행 → 테이블 생성 → 웹 서버 실행** 순서로 진행합니다.

아래 명령어는 Windows PowerShell 기준입니다. 모든 명령은 `main.py`가 있는 프로젝트 폴더에서 실행하세요.

## 1. 준비물

- Python 3.12 (`Dockerfile` 기준)
- Docker Desktop: 실행해 두고 사용합니다. MySQL을 띄우는 데 필요합니다.

이미 MySQL 8을 사용 중이라면 Docker 단계는 건너뛰고, `pyeongtaek` 데이터베이스와 해당 DB에 접근할 계정을 준비하세요. 현재 코드는 DB 이름 `pyeongtaek`과 포트 `3306`을 사용합니다.

## 2. Python 환경 만들기

가상환경은 이 프로젝트에서 쓸 라이브러리만 따로 담는 폴더입니다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

이후에도 가상환경의 Python을 직접 사용하므로 별도의 활성화 명령은 필요 없습니다.

## 3. `.env` 설정하기

프로젝트 폴더에 `.env` 파일을 만들고 아래 내용을 넣으세요. 이미 파일이 있다면 필요한 값만 수정합니다.

```dotenv
KAKAO_API_KEY=여기에_카카오_지도_JavaScript_키
DB_USER=test_user
DB_PASSWORD=test_password
DB_HOST=127.0.0.1
```

- `DB_USER`, `DB_PASSWORD`: 아래 Docker 설정에 들어 있는 로컬 개발용 계정입니다.
- `DB_HOST`: MySQL이 실행되는 컴퓨터 주소입니다. 내 컴퓨터에서 실행하면 `127.0.0.1`입니다. 반드시 입력하세요.
- `KAKAO_API_KEY`: 오시는 길 화면의 지도에서 사용합니다. 지도 없이 먼저 실행하려면 `KAKAO_API_KEY=`로 비워 둘 수 있지만 지도는 표시되지 않습니다.

설정 파일은 `routes/pages.py`에서 읽습니다. 변수 이름은 위 예시를 사용하세요. `.env`에는 비밀번호가 있으므로 Git에 올리지 않습니다.

## 4. MySQL 실행하기

```powershell
docker compose up -d db
docker compose logs -f db
```

로그에 `ready for connections`가 나오면 준비된 것입니다. `Ctrl+C`로 로그 보기만 종료하세요. MySQL은 계속 실행됩니다.

현재 `docker-compose.yml`은 **DB만 실행**합니다. 웹 서버는 6단계에서 따로 켭니다.

## 5. 처음 한 번, 테이블 만들기

데이터베이스가 큰 서랍장이라면 테이블은 종류별로 자료를 넣는 작은 서랍입니다. 현재 앱은 이 서랍을 자동으로 만들지 않으므로 아래 명령을 실행해야 합니다.

```powershell
.\.venv\Scripts\python.exe -c "import main; from sqlmodel import SQLModel; from database.connection import engine_url; SQLModel.metadata.create_all(engine_url)"
```

이 명령은 앱에서 사용하는 모델을 불러와 없는 테이블을 만듭니다. 기존 테이블의 구조를 바꾸거나 운영 데이터를 가져오지는 않습니다. 새 DB에는 시간표나 공지사항이 없는 것이 정상입니다.

참고로 `init.sql`은 별도 `test_db`와 권한만 준비합니다. 앱에서 쓰는 `pyeongtaek` DB는 Docker 설정이 만들며, 앱 테이블은 위 명령으로 만듭니다.

## 6. 웹 서버 실행하기

```powershell
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

`Uvicorn running on http://127.0.0.1:8000` 메시지가 나오면 브라우저에서 접속합니다.

| 화면 | 주소 |
| --- | --- |
| 홈페이지 | http://127.0.0.1:8000 |
| 관리자 로그인 | http://127.0.0.1:8000/adm/login |
| API 문서 | http://127.0.0.1:8000/api/docs |

`--reload`는 코드를 저장하면 서버를 자동으로 다시 켜는 개발용 옵션입니다.

## 7. 관리자 계정 만들기 (필요할 때)

새 DB에는 관리자 계정도 없습니다. 현재 로그인 코드는 아이디가 `bsbus`인 사용자만 허용합니다. 서버를 켜 둔 상태에서 **새 PowerShell 창**을 열고 프로젝트 폴더에서 실행하세요.

```powershell
$adminPassword = Read-Host '로컬 관리자 비밀번호' -AsSecureString
$credential = [System.Net.NetworkCredential]::new('', $adminPassword)
$body = @{ id = 'bsbus'; password = $credential.Password } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/users/signup' -ContentType 'application/json' -Body $body
Remove-Variable adminPassword, credential, body
```

그다음 관리자 로그인 화면에서 `bsbus`와 방금 정한 비밀번호로 로그인하세요. 이미 계정이 있다면 다시 만들 필요가 없습니다. API 문서도 DB에 등록된 계정의 아이디와 비밀번호를 요구합니다.

## 종료와 다음 실행

- 웹 서버 종료: 서버 창에서 `Ctrl+C`
- DB 중지: `docker compose stop db`
- 다음 실행: `docker compose start db` 후 6단계의 웹 서버 명령 실행

현재 Docker 설정에는 DB 데이터를 위한 명시적인 볼륨이 없습니다. 데이터를 유지하며 개발하려면 `stop` / `start`를 사용하고, 컨테이너 삭제나 재생성 전에는 필요한 데이터를 백업하세요.

## 자주 막히는 부분

| 증상 | 확인할 것 |
| --- | --- |
| `py` 명령을 찾지 못함 | Python 3.12 설치 및 Python Launcher 설치 여부를 확인합니다. |
| Docker에 연결할 수 없음 | Docker Desktop이 실행 중인지 확인합니다. |
| `db_host` 관련 `Field required` | `.env`에 `DB_HOST=127.0.0.1`을 추가하고 프로젝트 폴더에서 실행합니다. |
| MySQL 연결 거부 | `docker compose ps`와 DB 로그를 확인하고 MySQL 준비가 끝난 뒤 다시 시도합니다. |
| `Access denied` | `.env`의 계정과 MySQL 계정이 같은지 확인합니다. 기존 컨테이너의 계정은 Compose 파일만 수정해도 바뀌지 않습니다. |
| `Table ... doesn't exist` | 5단계의 테이블 생성 명령을 실행합니다. |
| `3306` 포트 사용 중 | 이미 실행 중인 MySQL 또는 다른 컨테이너가 있는지 확인합니다. |
| `8000` 포트 사용 중 | 웹 서버 명령의 `--port 8000`을 `--port 8001`로 바꾸고 접속 주소도 바꿉니다. |
| `static` 또는 `templates`를 찾지 못함 | `main.py`가 있는 프로젝트 폴더에서 실행합니다. |
| 관리자 로그인 실패 | `bsbus` 계정 생성 여부와 비밀번호를 확인합니다. |

`connection_test.py`는 앱과 다른 `test_db`를 확인하므로 앱 DB 연결 확인용으로 사용하지 마세요. 위 테이블 생성 명령이 성공하는지 확인하는 편이 정확합니다.

## 주요 파일

| 경로 | 역할 |
| --- | --- |
| `main.py` | 웹 서버 진입점과 라우터 연결 |
| `routes/` | 화면 및 API 처리 |
| `models/` | DB 테이블과 요청·응답 형식 |
| `database/connection.py` | MySQL 연결 |
| `templates/`, `static/` | HTML, CSS, JavaScript, 이미지 |
| `requirements.txt` | Python 라이브러리 목록 |
| `docker-compose.yml` | 로컬 MySQL 실행 설정 |
| `Dockerfile` | Python 웹 서버 이미지 빌드 설정 |

이 문서는 로컬 개발 실행 기준입니다. 공개 배포 전에는 코드에 들어 있는 JWT·세션 비밀키와 회원가입 API의 접근 제어를 별도로 정비해야 합니다.
