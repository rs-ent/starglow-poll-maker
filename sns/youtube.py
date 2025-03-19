from ytmusicapi import YTMusic
import random
import re
from math import ceil
import requests
from bs4 import BeautifulSoup
import re

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

CHANNEL_PATTERN = re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/channel/([^/?]+)')
CUSTOM_PATTERN = re.compile(r'/c/([^/?]+)')
USER_PATTERN = re.compile(r'/user/([^/?]+)')
HANDLE_PATTERN = re.compile(r'youtube\.com/@([^/?]+)')
def is_valid_youtube_url(url):
    return bool(re.match(
        r'(https?://)?(www\.)?(youtube\.com)/(channel/UC[\w-]{22,}|user/[\w-]+|c/[\w-]+|@[\w-]+)', 
        url
    ))

def get_youtube_channel_id(url, timeout=10):
    headers = {"User-Agent": "Mozilla/5.0"}
    CHANNEL_PATTERN = re.compile(r'/channel/([^/?]+)')

    if not url or not is_valid_youtube_url(url):
        print(f"Invalid URL format: {url}")
        return None

    try:
        match = CHANNEL_PATTERN.search(url)
        if match:
            return match.group(1)

        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        canonical_link = soup.find("link", rel="canonical")
        if canonical_link and 'href' in canonical_link.attrs:
            match = CHANNEL_PATTERN.search(canonical_link['href'])
            if match:
                return match.group(1)
    except requests.RequestException as e:
        print(f"Request error ({url}): {e}")
    except Exception as e:
        print(f"Parsing error ({url}): {e}")
    
    return None

def get_youtube_channel_ids(youtube_links):
    channel_ids_mapping = {}
    for url in youtube_links:
        if not url:
            channel_ids_mapping[url] = None
            continue

        channel_id = get_youtube_channel_id(url)
        channel_ids_mapping[url] = channel_id

    return channel_ids_mapping

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


def get_playlist(playlist_url):
    def extract_playlist_id(url):
        match = re.search(r"[?&]list=([a-zA-Z0-9_-]+)", url)
        return match.group(1) if match else None

    ytm = YTMusic()
    playlist_id = extract_playlist_id(playlist_url)
    if not playlist_id:
        raise ValueError("Invalid playlist URL.")
    
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

    