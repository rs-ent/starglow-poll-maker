##### sns\youtube.py #####

from googleapiclient.errors import HttpError
import isodate

def get_youtube_channel_id(youtube, youtube_link):
    """
    youtube: build()를 통해 생성한 YouTube API 클라이언트 객체
    youtube_link: YouTube 채널 링크 ("/channel/" 또는 "/@" 형식)
    """
    if "/channel/" in youtube_link:
        # "/channel/" URL 형식의 경우: 채널 ID 바로 추출
        return youtube_link.split("/channel/")[1].split("/")[0]
    elif "/@" in youtube_link:
        # "/@" URL 형식의 경우: handle을 추출하여 search API로 채널 ID 확인
        handle = youtube_link.split("/@")[1].split("/")[0]
        # handle을 검색어로 사용 (앞에 @ 기호 포함)
        response = youtube.search().list(
            q="@" + handle,
            type="channel",
            part="snippet",
            maxResults=1
        ).execute()
        if response.get("items"):
            return response["items"][0]["snippet"]["channelId"]
        else:
            return None
    else:
        return None

def get_youtube_stats(youtube, channel_id):
    # 채널 구독자 수 가져오기
    response = youtube.channels().list(
        part="statistics",
        id=channel_id
    ).execute()
    
    print(response)
    
    if "items" not in response:
        print(f"Error fetching statistics for channel_id {channel_id}: {response}")
        return 0
      
    if response["items"]:
        stats = response["items"][0]["statistics"]
        subscribers = int(stats.get("subscriberCount", 0))
    else:
        subscribers = 0
    return subscribers

def get_top_videos(youtube, channel_id, top_n=10):
    # 업로드 플레이리스트 ID 가져오기
    try:
        channel_response = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()
    except HttpError as e:
        print(f"Error fetching contentDetails for channel_id {channel_id}: {e}")
        return []
    
    if "items" not in channel_response or not channel_response["items"]:
        print(f"Error: No items in contentDetails response for channel_id {channel_id}: {channel_response}")
        return []
    
    uploads_playlist = channel_response["items"][0]["contentDetails"]["relatedPlaylists"].get("uploads")
    if not uploads_playlist:
        print(f"No uploads playlist found for channel_id {channel_id}")
        return []

    # 플레이리스트에서 동영상 ID 가져오기 (최대 50개씩, 전체 리스트 가져옴)
    video_ids = []
    next_page_token = None
    while True:
        try:
            playlist_response = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist,
                maxResults=50,
                pageToken=next_page_token
            ).execute()
        except HttpError as e:
            print(f"Error fetching playlist items for playlist_id {uploads_playlist}: {e}")
            return []  # 에러 발생 시 빈 리스트 반환
        for item in playlist_response.get("items", []):
            video_ids.append(item["snippet"]["resourceId"]["videoId"])
        next_page_token = playlist_response.get("nextPageToken")
        if not next_page_token:
            break

    # 각 동영상의 조회수와 duration 가져오기
    stats = {}
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        try:
            videos_response = youtube.videos().list(
                part="statistics,snippet,contentDetails",
                id=",".join(batch_ids)
            ).execute()
        except HttpError as e:
            print(f"Error fetching video stats for batch {batch_ids}: {e}")
            continue
        for item in videos_response.get("items", []):
            # duration 필드를 파싱하여 120초 미만이면 제외 (Shorts)
            duration_str = item["contentDetails"].get("duration", "")
            try:
                duration = isodate.parse_duration(duration_str).total_seconds()
            except Exception as ex:
                duration = None
            if duration is not None and duration < 120:
                continue  # 짧은 동영상(Shorts)는 건너뜁니다.
            vid = item["id"]
            view_count = int(item["statistics"].get("viewCount", 0))
            title = item["snippet"]["title"]
            stats[vid] = {"title": title, "view_count": view_count}

    # 조회수 기준 내림차순 정렬하여 상위 top_n 선택
    sorted_videos = sorted(stats.items(), key=lambda x: x[1]["view_count"], reverse=True)
    return sorted_videos[:top_n]