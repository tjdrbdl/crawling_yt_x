"""공통 환경설정 모듈.

-.env 파일을 자동으로 로드하고 필요한 환경 변수를 안전하게 읽습니다.
"""

from __future__ import annotations

import os
from typing import Dict

from dotenv import load_dotenv


def load_env() -> None:
    """현재 디렉터리의 .env를(있다면) 로드합니다."""
    # override=False: 이미 설정된 OS 환경변수를 .env가 덮어쓰지 않도록 함
    load_dotenv(override=False)


def require_env(name: str) -> str:
    """필수 환경변수를 읽고 없으면 명확한 에러를 발생시킵니다."""
    load_env()
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"환경변수 {name} 가(이) 설정되지 않았습니다. 루트 폴더에 .env 파일을 만들거나 OS 환경변수로 설정하세요."
        )
    return value


def get_youtube_api_key() -> str:
    return require_env("YOUTUBE_API_KEY")


def get_twitter_credentials() -> Dict[str, str]:
    """트위터 API 자격증명을 읽어 dict로 반환합니다.

    필요한 키가 일부라도 없으면 RuntimeError를 발생시킵니다.
    """
    keys = {
        "TWITTER_API_KEY": require_env("TWITTER_API_KEY"),
        "TWITTER_API_SECRET": require_env("TWITTER_API_SECRET"),
        "TWITTER_ACCESS_TOKEN": require_env("TWITTER_ACCESS_TOKEN"),
        "TWITTER_ACCESS_TOKEN_SECRET": require_env("TWITTER_ACCESS_TOKEN_SECRET"),
    }
    return keys
