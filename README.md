# Update Spotify Playlist

Superfly Yachthafen is a radio show airing every Friday 17:00 - 18:00 CET on [Superfly.fm](https://superfly.fm/). The show is hosted by Austrian DJ Legend [Eberhard Forcher](https://www.instagram.com/eberhard_forcher/) and features his personal favourites in the styles of California Westcoast Sounds, Blued Eyed Soul, Smooth Jazz, Brazil, R&B, and Yachtrock.

The show's [website](https://superfly.fm/shows/superfly-yachthafen) regularly updates the playlist of the current week. This project aims to add the weekly playlists to a [Spotify](https://open.spotify.com/) Playlist. To achieve this, we use [Azure Functions](https://azure.microsoft.com/en-us/products/functions), an event-driven, serverless compute platform. 

- The Spotify playlist can be accessed [here](https://open.spotify.com/playlist/7jNg10gzkESHZ0SiX8FtlG)
- The status of the deployed Azure Function can be checked [here](https://yachthafenplaylistupdate.azurewebsites.net)

## Structure

The project runs in [Python](https://www.python.org/). The [requests](https://pypi.org/project/requests/) library is used for API calls and for accessing the radio show's website. The playlist is subsequently obtained by parsing the HTML content using [Beautifulsoup](https://pypi.org/project/beautifulsoup4/).

### Spotify API Authorization

To modify the playlist, we use [Spotify's Authorization Code Flow](https://developer.spotify.com/documentation/web-api/tutorials/code-flow). This flow is suitable for long-running applications and uses a refresh token to generate a new access token at the start of executing the function. The secrets for updating the access token are securely stored in the [Azure Key Vault](https://azure.microsoft.com/en-us/products/key-vault). For developing the project locally, the secrets are stored in a [.env file](https://pypi.org/project/python-dotenv/).

### Find new tracks in Spotify

To find the Spotify IDs of the new tracks, we use the [search](https://developer.spotify.com/documentation/web-api/reference/search) request and pass the artist and track names.
We then iterate the results and check matches using [difflib's Sequencematcher](https://docs.python.org/3/library/difflib.html). The first result that has at least an 80% match for both artist and track is accepted as the track to be added. This way we find the matching tracks despite minor differences, such as special characters (e.g. "e" for "é") or typos.

### Get Current Playlist

To avoid duplicate tracks in our playlist, we get a list of all tracks in our current Spotify playlist using the [get playlist](https://developer.spotify.com/documentation/web-api/reference/get-playlist) request and filter our results.

### Update Playlist

With our filtered list of new tracks, we update the playlist using the [add items to playlist](https://developer.spotify.com/documentation/web-api/reference/add-tracks-to-playlist) request.

### Trigger

The function is triggered once per day, as configured in [functions.json](https://github.com/AndreasScheicher/yachthafen-playlist/blob/main/UpdatePlaylist/function.json). The weekly playlist update doesn't always come on the same day, so this ensures we don't miss a week in case the update is made a different day. We also observed that Spotify doesn't always return the same search results. Sometimes we get a new matching track in the days after the playlist was first published and updated.

### Deployment

The project is automatically built and deployed to Azure using [Github Actions](https://github.com/AndreasScheicher/yachthafen-playlist/actions).
