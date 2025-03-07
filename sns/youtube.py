from ytmusicapi import YTMusic
import random

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