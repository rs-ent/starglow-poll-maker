from ytmusicapi import YTMusic
import random
import re
from math import ceil

CHANNEL_PATTERN = re.compile(r'/channel/([^/?]+)')
USER_PATTERN = re.compile(r'/user/([^/?]+)')
CUSTOM_PATTERN = re.compile(r'/c/([^/?]+)')
HANDLE_PATTERN = re.compile(r'/@([^/?]+)')

def process_batch_requests(youtube, requests):
    if not requests:
        return {}
    
    results = {}
    
    def callback(request_id, response, exception):
        if exception:
            results[request_id] = {'exception': exception}
        else:
            results[request_id] = response

    batch = youtube.new_batch_http_request(callback=callback)
    for req_id, request in requests.items():
        batch.add(request, request_id=req_id)
    batch.execute()
    return results

def get_youtube_channel_ids_optimized(youtube, youtube_links):
    channel_ids = {}
    api_links = []

    # 먼저 직접 처리 가능한 링크와 API 요청이 필요한 링크로 분리합니다.
    for link in youtube_links:
        if link is None:
            continue
        m = CHANNEL_PATTERN.search(link)
        if m:
            channel_ids[link] = m.group(1)
        else:
            api_links.append(link)
    
    # API 호출이 필요한 링크에 대해서만 기존 함수 활용
    if api_links:
        api_results = get_youtube_channel_ids(youtube, api_links)
        channel_ids.update(api_results)
    
    return channel_ids

def get_youtube_channel_ids(youtube, youtube_links):
    channel_ids = {}
    batch_requests = {}
    # 요청과 링크 인덱스를 매핑할 딕셔너리 (req_id -> 링크 인덱스)
    link_map = {}

    for idx, link in enumerate(youtube_links):
        # 패턴 1: /channel/ 형태 -> 바로 처리
        m = CHANNEL_PATTERN.search(link)
        if m:
            channel_ids[link] = m.group(1)
            continue

        req_id = f"req_{idx}"
        link_map[req_id] = link

        # 패턴 2: /user/ 형태
        m = USER_PATTERN.search(link)
        if m:
            username = m.group(1)
            batch_requests[req_id] = youtube.channels().list(forUsername=username, part="id")
            continue

        # 패턴 3: /c/ 형태 (커스텀 URL)
        m = CUSTOM_PATTERN.search(link)
        if m:
            custom_name = m.group(1)
            batch_requests[req_id] = youtube.search().list(q=custom_name, type="channel", part="snippet", maxResults=1)
            continue

        # 패턴 4: /@ 형태 (채널 핸들 URL)
        m = HANDLE_PATTERN.search(link)
        if m:
            handle = m.group(1)
            batch_requests[req_id] = youtube.search().list(q=handle, type="channel", part="snippet", maxResults=1)
            continue

        # 어떤 패턴에도 해당하지 않으면 None 처리
        channel_ids[link] = None

    # 배치 요청 실행
    if batch_requests:
        batch_results = process_batch_requests(youtube, batch_requests)
        for req_id, result in batch_results.items():
            link = link_map.get(req_id)
            if not link:
                continue
            if "exception" in result:
                channel_ids[link] = None
            else:
                items = result.get("items", [])
                if items:
                    # /user/ 패턴: 응답 아이템에 "id" 필드가 있음
                    if "id" in items[0]:
                        channel_ids[link] = items[0]["id"]
                    # /c/ 또는 /@ 패턴: snippet 내에 channelId가 있음
                    elif "snippet" in items[0] and "channelId" in items[0]["snippet"]:
                        channel_ids[link] = items[0]["snippet"]["channelId"]
                    else:
                        channel_ids[link] = None
                else:
                    channel_ids[link] = None

    return channel_ids


def get_youtube_stats_batch(youtube, channel_ids):
    from math import ceil
    stats_results = {}
    if not channel_ids:
        return stats_results

    # None이 아니면서 문자열인 채널 ID만 필터링
    valid_ids = [cid for cid in channel_ids if cid and isinstance(cid, str)]
    if not valid_ids:
        return stats_results

    batch_size = 50
    num_batches = ceil(len(valid_ids) / batch_size)
    
    for i in range(num_batches):
        batch_ids = valid_ids[i * batch_size:(i + 1) * batch_size]
        request = youtube.channels().list(id=",".join(batch_ids), part="statistics")
        response = request.execute()
        for item in response.get("items", []):
            cid = item.get("id")
            stats = item.get("statistics", {})
            data = {}
            for key in ["subscriberCount", "viewCount", "videoCount"]:
                try:
                    data[key] = int(stats.get(key, 0))
                except (ValueError, TypeError):
                    data[key] = 0
            stats_results[cid] = data
    return stats_results


def get_playlist(playlist_id):
    ytm = YTMusic()
    playlist_info = ytm.get_playlist(playlist_id)

    tracks = playlist_info.get('tracks', [])
    if not tracks:
        raise ValueError("No tracks found in playlist.")
    
    return tracks

import random

def get_random_track_from_playlist(data, tracks, max_attempts=20):
    attempt = 0
    while attempt < max_attempts:
        selected_track = random.choice(tracks)
        track_artist = [artist.get('name') for artist in selected_track.get('artists', [])][0]
        print(f"Selected track: {selected_track.get('title')} by {track_artist}")

        matched_groups = data[data['group_name'].str.lower().str.contains(track_artist.lower(), case=False, na=False)]

        if not matched_groups.empty:
            matched_group_info = matched_groups.iloc[0].to_dict()
            matched_group_info["song_title"] = selected_track.get('title')
            matched_group_info["videoId"] = selected_track.get('videoId')
            matched_group_info["artists"] = track_artist
            matched_group_info["song_thumbnail"] = selected_track.get('thumbnails', [{}])[0].get('url', '').split("/sddefault.jpg")[0] + "/maxresdefault.jpg"
            return matched_group_info
        
        attempt += 1

    return None

