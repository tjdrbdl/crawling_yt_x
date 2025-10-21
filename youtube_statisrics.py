import json
import requests
import datetime


class YTstats:

    def __init__(self, api_key, channel_id):
        self.api_key = api_key
        self.channel_id = channel_id
        self.channel_statistics = None
        self.video_data = None

    def extract_all(self):
        self.get_channel_statistics()
        self.get_channel_video_data()

    def get_channel_statistics(self):
        url = f'https://www.googleapis.com/youtube/v3/channels?part=statistics&id={self.channel_id}&key={self.api_key}'
        # print(url)
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        # print(data)
        try:
            data = data["items"][0]["statistics"]
        except:
            data = None
        
        self.channel_statistics = data
        return data

    def get_channel_video_data(self):
        "Extract all video information of the channel"
        print('get video data...')
        channel_videos, channel_playlists = self._get_channel_content(limit=50)
        # print(channel_videos)

        # parts=["snippet", "statistics","contentDetails", "topicDetails"]
        # for video_id in tqdm(channel_videos):
        #     for part in parts:
        #         data = self._get_single_video_data(video_id, part)
        #         channel_videos[video_id].update(data)

        self.video_data = channel_videos
        return channel_videos

    def _get_single_video_data(self, video_id, part):
        """
        Extract further information for a single video
        parts can be: 'snippet', 'statistics', 'contentDetails', 'topicDetails'
        """

        url = f"https://www.googleapis.com/youtube/v3/videos?part={part}&id={video_id}&key={self.api_key}"
        # print(url)
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        # print(data)
        try:
            data = data['items'][0][part]
        except KeyError as e:
            print(f'Error! Could not get {part} part of data: \n{data}')
            data = dict()
        return data

    def _get_channel_content(self, limit=None, check_all_pages=True):
        """
        Extract all videos and playlists, can check all available search pages
        channel_videos = videoId: title, publishedAt
        channel_playlists = playlistId: title, publishedAt
        return channel_videos, channel_playlists
        """
        url = f"https://www.googleapis.com/youtube/v3/search?key={self.api_key}&channelId={self.channel_id}&part=snippet,id&order=date"
        if limit is not None and isinstance(limit, int):
            url += "&maxResults=" + str(limit)

        vid, pl, npt = self._get_channel_content_per_page(url)
        idx = 0
        while(check_all_pages and npt is not None and idx < 10):
            nexturl = url + "&pageToken=" + npt
            next_vid, next_pl, npt = self._get_channel_content_per_page(nexturl)
            vid.update(next_vid)
            pl.update(next_pl)
            idx += 1

        return vid, pl

    def _get_channel_content_per_page(self, url):
        """
        Extract all videos and playlists per page
        return channel_videos, channel_playlists, nextPageToken
        """
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        channel_videos = dict()
        channel_playlists = dict()
        if 'items' not in data:
            print('Error! Could not get correct channel data!\n', data)
            return channel_videos, channel_videos, None

        nextPageToken = data.get("nextPageToken", None)

        item_data = data['items']
        for item in item_data:
            try:
                kind = item['id']['kind']
                published_at = item['snippet']['publishedAt']
                title = item['snippet']['title']
                if kind == 'youtube#video':
                    video_id = item['id']['videoId']
                    channel_videos[video_id] = dict()
                # elif kind == 'youtube#playlist':
                #     playlist_id = item['id']['playlistId']
                #     channel_playlists[playlist_id] = {'publishedAt': published_at, 'title': title}
            except KeyError as e:
                print('Error! Could not extract data from item:\n', item)

        return channel_videos, channel_playlists, nextPageToken
    def get_playlist_content(self, playlistid, limit=None, check_all_pages=True):
        url = f"https://www.googleapis.com/youtube/v3/playlistItems?part={'contentDetails'}&playlistId={playlistid}&key={self.api_key}"

        if limit is not None and isinstance(limit, int):
            url += "&maxResults=" + str(limit)

        vid, npt = self.get_playlist_data_per_page(url)
        idx = 0
        while(check_all_pages and npt is not None and idx < 10):
            nexturl = url + "&pageToken=" + npt
            next_vid, npt = self.get_playlist_data_per_page(nexturl)
            vid.update(next_vid)
            # pl.update(next_pl)
            idx += 1
        
        return vid
    def get_playlist_data_per_page(self, url):
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        channel_videos = dict()

        nextPageToken = data.get("nextPageToken", None)
        item_data = data['items']
        for item in item_data:
            try:

                video_id = item['contentDetails']['videoId']
                channel_videos[video_id]= dict()
            except KeyError as e:
                print('Error! Could not extract data from item:\n', item)
        
        # print(channel_videos)
        return channel_videos, nextPageToken


    def get_serch_data(self, search_query: str, video_category_id: str | None = None, order: str = "viewcount", limit: int | None = 50, check_all_pages: bool = True):
        """검색어 기반으로 동영상 ID 목록을 수집합니다.

        - search_query: 검색어 문자열
        - video_category_id: 카테고리 ID (선택)
        - order: 정렬 기준 (date, rating, relevance, title, videoCount, viewCount)
        - limit: 페이지당 결과 수 (최대 50)
        """
        max_results = 50 if limit is None else min(50, max(1, int(limit)))
        base = f"https://www.googleapis.com/youtube/v3/search?key={self.api_key}&part=id&type=video&q={search_query}&maxResults={max_results}&order={order}"
        if video_category_id:
            base += f"&videoCategoryId={video_category_id}"

        url = base
        json_url = requests.get(url)
        _ = json.loads(json_url.text)

        vid, npt = self.get_serch_data_per_page(url)
        idx = 0
        # 최대 20 페이지까지 순회
        while(check_all_pages and npt is not None and idx < 20):
            nexturl = base + "&pageToken=" + npt
            next_vid, npt = self.get_serch_data_per_page(nexturl)
            vid.update(next_vid)
            # pl.update(next_pl)
            idx += 1
        return vid
    
    def get_serch_data_per_page(self, url):
        json_url = requests.get(url)
        data = json.loads(json_url.text)
        channel_videos = dict()
        print(url)

        nextPageToken = data.get("nextPageToken", None)
        item_data = data['items']
        for item in item_data:
            try:

                video_id = item['id']['videoId']
                channel_videos[video_id]= dict()
            except KeyError as e:
                print('Error! Could not extract data from item:\n', item)
        
        # print(channel_videos)
        return channel_videos, nextPageToken
    def get_weekday(date):
        y = date[0:4]
        m = date[5:7]
        d = date[8:10]
        if m[0]=='0':
            m = m[1]
        if d[0]=='0':
            d=d[1]

        days = ['월요일','화요일','수요일','목요일','금요일','토요일','일요일']
        a= days[datetime.date(y,m,d).weekday()]
        return a    





    def dump(self):
        """Dumps channel statistics and video data in a single json file"""
        if self.channel_statistics is None or self.video_data is None:
            print('data is missing!\nCall get_channel_statistics() and get_channel_video_data() first!')
            return

        fused_data = {self.channel_id: {"channel_statistics": self.channel_statistics,
                              "video_data": self.video_data}}

        channel_title = self.video_data.popitem()[1].get('channelTitle', self.channel_id)
        channel_title = channel_title.replace(" ", "_").lower()
        filename = channel_title + '.json'
        with open(filename, 'w') as f:
            json.dump(fused_data, f, indent=4)
        
        print('file dumped to', filename)
