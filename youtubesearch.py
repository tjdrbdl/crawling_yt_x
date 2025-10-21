"""YouTube search utility.

Refactored to remove hardcoded API keys and improve robustness.
Reads API key from environment variable YOUTUBE_API_KEY (optionally via .env).
"""

from __future__ import annotations

import argparse
import csv
import os
from typing import Dict, Iterable, List, Tuple

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import unidecode
from config import get_youtube_api_key


YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def _get_api_key() -> str:
    # config 모듈에서 .env 로딩 및 검증을 수행합니다.
    return get_youtube_api_key()


def _chunked(iterable: Iterable[str], size: int) -> Iterable[List[str]]:
    chunk: List[str] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def _fetch_video_stats(youtube, video_ids: List[str]) -> Dict[str, Dict[str, str]]:
    """Fetch statistics for a list of video IDs in batches.

    Returns a mapping video_id -> statistics dict.
    """
    stats: Dict[str, Dict[str, str]] = {}
    # API allows up to 50 IDs per call
    for batch in _chunked(video_ids, 50):
        response = youtube.videos().list(id=",".join(batch), part="statistics").execute()
        for item in response.get("items", []):
            vid = item.get("id")
            stats[vid] = item.get("statistics", {})
    return stats


def youtube_search(query: str, max_results: int = 25, output_csv: str = "video_result.csv") -> Tuple[int, str]:
    """Search YouTube and write basic video stats to CSV.

    Returns a tuple: (row_count, output_csv_path)
    """
    api_key = _get_api_key()
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=api_key)

    # Prepare CSV writer (Windows-friendly newline handling)
    with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "title",
            "videoId",
            "viewCount",
            "likeCount",
            "dislikeCount",
            "commentCount",
            "favoriteCount",
        ])

        total_written = 0
        next_page_token = None

        while total_written < max_results:
            page_size = min(50, max_results - total_written)  # API page size up to 50
            search_request = youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=page_size,
                pageToken=next_page_token,
            )
            search_response = search_request.execute()

            items = search_response.get("items", [])
            if not items:
                break

            video_ids: List[str] = []
            titles: Dict[str, str] = {}
            for item in items:
                if item.get("id", {}).get("kind") == "youtube#video":
                    vid = item.get("id", {}).get("videoId")
                    if not vid:
                        continue
                    title = unidecode.unidecode(item.get("snippet", {}).get("title", ""))
                    video_ids.append(vid)
                    titles[vid] = title

            if video_ids:
                stats_map = _fetch_video_stats(youtube, video_ids)
                for vid in video_ids:
                    st = stats_map.get(vid, {})
                    view_count = st.get("viewCount", 0)
                    like_count = st.get("likeCount", 0)
                    dislike_count = st.get("dislikeCount", 0)  # field retained for legacy; may be absent
                    comment_count = st.get("commentCount", 0)
                    favorite_count = st.get("favoriteCount", 0)
                    writer.writerow([
                        titles.get(vid, ""),
                        vid,
                        view_count,
                        like_count,
                        dislike_count,
                        comment_count,
                        favorite_count,
                    ])
                    total_written += 1

            next_page_token = search_response.get("nextPageToken")
            if not next_page_token:
                break

    return total_written, os.path.abspath(output_csv)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search YouTube and export basic video stats to CSV")
    parser.add_argument("--q", "--query", dest="query", help="Search term", default="Google")
    parser.add_argument("--max-results", dest="max_results", type=int, help="Max results (1-500)", default=25)
    parser.add_argument("--out", dest="output", help="Output CSV filename", default="video_result.csv")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    # Bound the max results to a reasonable range
    max_results = max(1, min(int(args.max_results), 500))
    try:
        count, path = youtube_search(query=args.query, max_results=max_results, output_csv=args.output)
        print(f"Wrote {count} rows to {path}")
    except HttpError as e:
        # Provide a concise error message helpful for API quota/key issues
        status = getattr(e, "resp", {}).status if hasattr(e, "resp") else "?"
        print(f"YouTube API error (status {status}): {getattr(e, 'error_details', str(e))}")
        raise
    except RuntimeError as e:
        print(str(e))
        raise


if __name__ == "__main__":
    main()