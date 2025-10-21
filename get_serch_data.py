from youtube_statisrics import YTstats
from config import get_youtube_api_key

API_KEY = get_youtube_api_key()
channel_id = "UClf0nMufbyc7QE3PaPO7SRg" # 채널 ID를 입력합니다.
search_query = "밤하늘의별" # 검색어를 입력합니다.

yt = YTstats(API_KEY, channel_id)
search_data = yt.get_serch_data(search_query)
video_ids = list(search_data.keys())
print(video_ids if video_ids else "No video found.")


# youtube_statisrics파일에서 get_serch_data 함수에 설정된 URL의 q값을 원하는 검색어로 수정
# https://developers.google.com/youtube/v3/docs/search/list -> 참고하여 URL 변수를 수정
# https://console.cloud.google.com/iam-admin/quotas?project=spatial-subject-348610  -> api 할당량 확인