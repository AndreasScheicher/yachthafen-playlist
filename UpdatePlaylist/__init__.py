import os
import datetime
import logging

import azure.functions as func
from dotenv import load_dotenv

from . import utils

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)

    # load .env if running locally
    if os.getenv('WEBSITE_SITE_NAME')  != "YachthafenPlaylistUpdate":
        logging.info('developing locally')
        load_dotenv()

    # load spotify secrets from key vault
    CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    REFRESH_TOKEN = os.getenv('SPOTIFY_REFRESH_TOKEN')

    # generate new spotify access token
    access_token = utils.refresh_spotify_access_token(
        client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
        refresh_token=REFRESH_TOKEN)
    
    # get all new tracks from website
    radio_tracks = utils.get_superfly_playlist()
    # get spotify ids of radio tracks
    track_ids = utils.get_new_track_ids(radio_tracks, access_token=access_token)
    # get spotify ids of current spotify playlist
    playlist_tracks = utils.get_current_playlist(access_token=access_token)
    # filter all tracks that are already in playlist
    tracks_to_add = [track for track in track_ids if track not in playlist_tracks]
    # add new tracks to playlist if there are any
    if len(tracks_to_add):
        utils.add_tracks_to_playlist(tracks_to_add, access_token=access_token)
    else:
        logging.info('no new tracks to add')
