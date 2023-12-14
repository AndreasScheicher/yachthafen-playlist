"""
Functions for updating the yachthafen playlist. 
Includes API calls to superfly.fm and spotify.
"""


import logging
import time
import base64
from urllib import parse
from difflib import SequenceMatcher
import requests

from bs4 import BeautifulSoup


def get_superfly_playlist():
    """
    Get current Superfly Yachthafen Playlist
    """
    superfly_url = "https://superfly.fm/shows/superfly-yachthafen"
    # get page content
    response = requests.request("GET", superfly_url, timeout=10)
    assert response.status_code == 200, "Playlist Request Error"

    # parse page content
    soup = BeautifulSoup(response.content, 'html.parser')

    # extract and clean tracks
    items = soup.find(class_="itemFullText").find_all('li')
    radio_tracks = [item.text.strip('\n').lower().replace(
        "`", "'").replace("–", "-") for item in items]

    if len(radio_tracks):
        logging.info('accessed superfly playlist')
    return radio_tracks


# def get_spotify_token(client_id, client_secret):
#    url = "https://accounts.spotify.com/api/token"

#    payload = f'grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}'
#    headers = {
#    'Content-Type': 'application/x-www-form-urlencoded'
#    }

#    response = requests.request("POST", url, headers=headers, data=payload)

#    return response


def encode_credentials(client_id, client_secret):
    """
    Encode client id and client secret Base 64.
    Used for refreshing Spotify Access Token
    """
    combined = f"{client_id}:{client_secret}"
    combined_bytes = combined.encode('utf-8')
    base64_bytes = base64.b64encode(combined_bytes)
    base64_string = base64_bytes.decode('utf-8')
    return base64_string


def refresh_spotify_access_token(client_id, client_secret, refresh_token):
    """
    Generate a new Spotify Access Token, using the Refresh Token.
    """
    url = "https://accounts.spotify.com/api/token"

    authorization = encode_credentials(client_id, client_secret)

    payload = f'grant_type=refresh_token&refresh_token={refresh_token}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': f'Basic {authorization}',
    }

    response = requests.request(
        "POST", url, headers=headers, data=payload, timeout=10)

    if response.status_code == 200:
        logging.info('refreshed access_token')

    return response.json()['access_token']


def get_current_playlist(access_token, playlist_id='7jNg10gzkESHZ0SiX8FtlG'):
    """
    Get all tracks that were already added to the playlist.
    """
    offset = 0
    limit = 100
    max_requests = 1000
    requests_counter = 0

    playlist_tracks_ids = []
    playlist_tracks_names = []

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?offset={offset}&limit={limit}"

    payload = {}
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    while url and requests_counter < max_requests:

        response = requests.request(
            "GET", url, headers=headers, data=payload, timeout=10)

        if response.status_code == 200:

            data = response.json()

            for item in data.get('items'):
                track = item.get('track')
                playlist_tracks_ids.append(track.get('id'))
                playlist_tracks_names.append((track.get('artists')[0].get('name').lower(), track.get('name').lower()))

            url = data.get('next')

        else:
            url = None
            break

        time.sleep(1)

    return playlist_tracks_ids, playlist_tracks_names


def get_spotify_search_response(artist, track, access_token):
    """
    Get the 10 most likely matches from Spotify.
    """
    url_base = "https://api.spotify.com/v1/search?q="
    # format the url containing the track info
    quoted_space = parse.quote(' ')
    query_unquoted = f"remaster{quoted_space}track:{track.title()}{quoted_space}artist:{artist.title()}"
    query = parse.quote(query_unquoted)
    end = "&type=track&limit=10"

    url = url_base + query + end

    payload = {}
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }

    response = requests.request(
        "GET", url, headers=headers, data=payload, timeout=10)

    return response.json()


def get_matching_id_from_search(response, artist, track):
    """
    Returns id of the first track where artist and track match at least 80%.
    """
    for item in response['tracks']['items']:
        spotify_name = item['name'].lower()
        for item_artist in item['artists']:
            spotify_artist = item_artist['name'].lower()
            if (SequenceMatcher(None, a=spotify_artist, b=artist).ratio() >= 0.8 and
                    SequenceMatcher(None, a=spotify_name, b=track).ratio() >= 0.8):
                return item['id'], spotify_artist, spotify_name
    return None, None, None


def get_new_track_ids(radio_tracks, access_token):
    """
    Takes Superfly playlist and returns the Spotify matches.
    """
    track_ids = []
    track_names = []

    for radio_track in radio_tracks:
        # extract artist and track from format "artist - track"
        splitted = radio_track.split('-')
        if len(splitted) == 2:
            artist = splitted[0].strip()
            song = splitted[1].strip()

            # get list of spotify search results
            response = get_spotify_search_response(
                artist, song, access_token=access_token)

            # get first matching item of search result list
            track_id, spotify_artist, spotify_name = get_matching_id_from_search(response, artist, song)
            if track_id is not None:
                track_ids.append(track_id)
                track_names.append((spotify_artist, spotify_name))

            # wait 1 second between api calls
            time.sleep(1)

    return track_ids, track_names


def filter_existing_tracks(track_ids, track_names, playlist_tracks_ids, playlist_tracks_names):
    tracks_to_add = []
    for track_id, track_name in zip(track_ids, track_names):
        if track_id in playlist_tracks_ids:
            continue
        elif track_name in playlist_tracks_names:
            continue
        else:
            tracks_to_add.append(track_id)
    return tracks_to_add


def add_tracks_to_playlist(tracks_to_add, access_token, playlist_id='7jNg10gzkESHZ0SiX8FtlG'):

    url_base = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?uris="
    url_tracks = parse.quote(
        ','.join(['spotify:track:' + id_ for id_ in tracks_to_add]))
    url = url_base + url_tracks

    payload = {}
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.request(
        "POST", url, headers=headers, data=payload, timeout=10)

    if response.status_code == 201:
        logging.info('added tracks to playlist, snapshot: %s',
                     response.json()['snapshot_id'])
