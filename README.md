# YouTube · Twitter 데이터 크롤링 스크립트

YouTube Data API v3와 Tweepy를 사용하여 동영상·채널 메타데이터와 트윗을 수집하는 스크립트 모음입니다. API 키/토큰은 코드에 하드코딩하지 않고 `.env` 환경변수로 관리합니다.

## 요구 사항

- Python 3.9 이상 권장
- 의존성: `google-api-python-client`, `python-dotenv`, `tweepy`, `requests`, `openpyxl`, `Unidecode`

설치:

```powershell
pip install -r requirements.txt
```

## 설정 (.env)

루트에 `.env` 파일을 생성하고 다음 값을 채웁니다. 템플릿은 `.env.example`에 있습니다.

```env
# YouTube Data API v3
YOUTUBE_API_KEY=your_youtube_api_key_here

# Twitter API (OAuth 1.0a)
TWITTER_API_KEY=your_twitter_api_key_here
TWITTER_API_SECRET=your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN=your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_twitter_access_token_secret_here
```

`.env`는 `.gitignore`에 포함되어 Git에 커밋되지 않습니다.

## 프로젝트 구성

- `config.py`: 공통 설정 모듈. `.env` 로드 및 필수 환경변수 검증
- `youtube_statisrics.py`: YouTube 데이터 수집용 클래스 `YTstats`
- `youtubesearch.py`: 검색어 기반 동영상 검색 + 통계 수집 → CSV 출력
- `get_channel_video_data.py`: 채널 전체 동영상 메타데이터 수집 → Excel 출력
- `get_single_video_data.py`: 지정한 비디오(들)의 메타데이터 수집 → Excel 출력
- `get_serch_data.py`: 키워드 기반 동영상 ID 수집(빠른 목록 생성)
- `twittersearch.py`: 트위터 검색 → CSV 출력

## 스크립트별 사용법

### 1) youtubesearch.py (검색 + 통계 → CSV)

YouTube에서 검색어로 동영상을 찾고, 각 동영상의 통계를 배치로 조회하여 CSV로 저장합니다.

```powershell
python youtubesearch.py --q "로블록스" --max-results 50 --out video_result.csv
```

옵션
- `--q, --query`: 검색어(기본값: `Google`)
- `--max-results`: 검색 결과 상한(1~500)
- `--out`: 출력 CSV 파일명(기본값: `video_result.csv`)

출력 컬럼
- `title, videoId, viewCount, likeCount, dislikeCount, commentCount, favoriteCount`

구현 포인트
- 검색 페이지네이션 처리, 비디오 ID 모음에 대해 `videos().list(..., part=statistics)` 배치 조회 (최대 50개/호출)
- 타이틀은 `Unidecode`로 ASCII 정규화

### 2) get_channel_video_data.py (채널 → Excel)

지정한 채널의 업로드 동영상 목록을 가져오고, 각 동영상의 메타데이터와 통계를 Excel로 저장합니다.

```powershell
python get_channel_video_data.py
```

설정
- 파일 상단의 `channel_id` 값을 원하는 채널 ID로 변경
- YouTube API 키는 자동으로 `config.get_youtube_api_key()`에서 로드

출력
- `Channel_video_data.xlsx`의 `result` 시트에 다음 컬럼을 기록합니다.
	- `view, like, comment, length(초), caption, postingperiod, subcount, video_id, channel_id, tags, categoryId, gold, silver, shortvideo, channel_title, video_title`

구현 포인트
- `YTstats._get_channel_content()`로 채널의 동영상 ID 수집(최대 50/페이지, 최대 10페이지 순회)
- 각 동영상에 대해 `snippet/statistics/contentDetails` 파트 별도로 조회
- 영상 길이 ISO8601 포맷을 파싱해 초 단위로 변환
- 구독자 수에 따라 `gold/silver` 플래그 산출, 120초 이하 `shortvideo=1`

### 3) get_single_video_data.py (비디오 목록 → Excel)

하드코딩된 `videolist`의 각 비디오에 대해 메타데이터/통계를 수집하고 Excel로 저장합니다.

```powershell
python get_single_video_data.py
```

출력
- `video_data.xlsx`의 `Test` 시트에 확장 컬럼 기록
	- `... channel_title, video_title, postingdate(YYYY-MM-DD), postingday(요일)`

### 4) get_serch_data.py (키워드 → 비디오 ID 목록)

검색어로 동영상 ID를 빠르게 수집합니다. 내부적으로 `YTstats.get_serch_data(search_query, ...)`를 호출합니다.

```powershell
python get_serch_data.py
```

출력
- 콘솔에 수집된 `video_id` 리스트를 출력

비고
- `youtube_statisrics.py`의 메서드명은 `get_serch_data`로 구현되어 있습니다(오탈자 유지).

### 5) youtube_statisrics.py (YTstats 클래스)

주요 메서드
- `get_channel_statistics()`: 채널 통계(`subscriberCount` 등) 조회
- `get_channel_video_data()`: 채널 업로드 동영상 ID 목록 수집
- `_get_single_video_data(video_id, part)`: 특정 비디오의 `snippet/statistics/contentDetails` 파트 조회
- `get_playlist_content(playlistid, ...)`: 재생목록의 비디오 ID 수집
- `get_serch_data(search_query, video_category_id=None, order="viewcount", limit=50, check_all_pages=True)`:
	- 검색어 기반으로 비디오 ID 컬렉션을 반환(dict: `video_id -> {}`)
	- 페이지네이션 최대 20페이지 순회

### 6) twittersearch.py (트위터 검색 → CSV)

트위터에서 쿼리로 트윗을 검색하고 CSV로 저장합니다. 인증은 `.env`의 키/토큰을 사용합니다.

```powershell
python twittersearch.py "검색어"
```

옵션(간단 설명)
- `-g`: 위치 프리셋(예: `lo`, `nyl`, `nym`, `nyu`, `dc`, `sf`, `nb`)
- `-l`: 언어(`en`, `fr`, `es`, `po`, `ko`, `ar` 등, 기본 `en`)
- `-t`: 타입(`mixed`, `recent`, `popular`, 기본 `recent`)
- `-c`: 개수 상한(기본 1, 최대 150)

출력 컬럼
- `created, text, retwc, hashtag, followers, friends` → `result.csv`

구현 포인트
- 인증: `.env` → `config.get_twitter_credentials()` → `tweepy.OAuthHandler`
- URL 정규화 헬퍼 `url_fix`는 Python 3 표준 라이브러리(`urllib.parse`) 기반으로 개선

## 에러/제한 사항

- YouTube API 쿼터: 검색/비디오 조회에 할당량이 있으며 초과 시 `HttpError`가 발생할 수 있습니다.
- `youtubesearch.py`는 API 오류를 포착하여 상태코드와 메시지를 출력합니다.
- 환경변수 누락 시 `config.require_env()`에서 명확한 메시지와 함께 중단합니다.

## 보안 수칙

- API 키/토큰은 `.env`에만 저장하고, 코드/커밋에 포함하지 않습니다.
- `.env`, 생성된 데이터 파일(csv/xlsx/json), 개인 키 파일(`auth.k`)은 `.gitignore`로 커밋 제외됩니다.
- 과거 히스토리에 키가 노출되었다면 키를 즉시 회수/재발급하세요.

---

이 문서는 저장소 내 소스코드를 기반으로 작성되었습니다. 기능 확장이나 추가 예제가 필요하면 이슈로 제안하세요.