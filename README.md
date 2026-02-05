# ListenBrainz Deezer listening history importer
This is a small utility for uploading historical listenings data from Deezer 
to ListenBrainz's user data.
Based on derat script's (see@https://community.metabrainz.org/t/pylistenbrainz-import-lastfm-csv-with-this-csv-format/663565/2)

## How to use
Get your Deezer account's data, extract the listening history sheet to 
a single and indpendent CSV file.
Download or clone this repo. Edit the _deezer_importer.ini_ and complete 
the auth_token entry with your ListenBrainz personal auth token. Save the file.
From the shell (or from the Python virtual environment if you created one):
./deezer-importer <path to CSV file with Deezer's personal data>

To prevent random ListenBrainz server outages, the utility keeps a count of the
entries it was able to upload before the connection error, so subsequent runs 
will be incremental.
