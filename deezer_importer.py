#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 R. Galacho
# Based on derat script's (see@https://community.metabrainz.org/t/pylistenbrainz-import-lastfm-csv-with-this-csv-format/663565/2)
# License GPLv3

"""
    Submit to MusicBrainz listening historing from Deezer.
    Usage: Usage: %s <csv-file>

    IMPORTANT: Before first-time run, open and edit deezer_importer.ini and set your MusicBrainz auth-token
"""
import csv
import configparser
import os
import sys
import time
import logging
import pylistenbrainz
from requests.exceptions import ConnectionError
from pylistenbrainz.errors import InvalidAuthTokenException
from pathlib import Path

MAX_LISTENS_PER_REQUEST = 1000
logger = None


def setup_config():
    config = configparser.ConfigParser()
    config.read('deezer_importer.ini')
    if not config.has_section('FILES'):
        config.add_section('FILES')
    return config


def get_listenbrainz_token(config: configparser.ConfigParser):
    return config['BRAINZ']['auth_token']


def previously_processed_entries(config: configparser.ConfigParser, csv_filename: str):
    try:
        return int(config.get('FILES', csv_filename))
    except configparser.NoOptionError:
        return 0


def update_processed_files_config(config: configparser.ConfigParser, csv_filename: str, total_processed: str):
    config.set('FILES', csv_filename, total_processed)
    with open('deezer_importer.ini', 'w') as f:
        config.write(f)


def submit_listens(client: pylistenbrainz.ListenBrainz, listens):
    logger.info("Submitting %d listen(s)..." % len(listens))
    response = client.submit_multiple_listens(listens)
    assert response['status'] == 'ok'


def submit_safely(config: configparser.ConfigParser, csv_filename, client, listens, total_processed):
    try:
        submit_listens(client, listens)
    except ConnectionError:
        # Handling random Connection reset
        update_processed_files_config(config, csv_filename, str(total_processed))
        sys.stderr.write("\nConnection error or reset submitting listens. Saving processed entries\n")
        sys.exit(2)


def parse_and_submit(config: configparser.ConfigParser, csv_file: str, client: pylistenbrainz.ListenBrainz):
    logger.info("Parsing listening history...")
    csv_filename=os.path.basename(csv_file)
    total_entries = 0
    previous_entries = previously_processed_entries(config, csv_filename)
    processed_entries = previous_entries
    listens = []
    with open(csv_file, newline='') as f:
        reader = csv.reader(f, dialect='unix')
        next(reader, None)  # skip header row
        # skipping previous processed entries
        while previous_entries > 0:
            next(reader, None)
            previous_entries -=1

        for row in reader:
            # Row: [Trackname, Artist_name, ISRC, Release_name, IP_address, listening_time, plafform, model, date(yyyy-mm-dd hh:mm:ss)]
            tm = time.strptime(row[8], '%Y-%m-%d %H:%M:%S')
            listens.append(pylistenbrainz.Listen(
                track_name=row[0],
                artist_name=row[1],
                isrc=row[2],
                release_name=row[3],
                listened_at=int(time.mktime(tm)),
            ))
            processed_entries += 1
            total_entries +=1
            if len(listens) >= MAX_LISTENS_PER_REQUEST:
                logger.debug("Splitting %d listen(s)..." % len(listens))
                submit_safely(config, csv_filename, client, listens, processed_entries)
                listens = []

    if len(listens) > 0:
        submit_safely(config, csv_filename, client, listens, processed_entries)

    update_processed_files_config(config, csv_filename, str(processed_entries))
    logger.info("Process completed. Parsed and submitted %d listen(s)..." % total_entries)


def setup_logging():
    console = logging.StreamHandler(sys.stderr)
    console.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)-5s] %(name)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"))
    logging.addLevelName(logging.WARNING, "WARN")
    logging.getLogger().addHandler(console)
    #logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().setLevel(logging.ERROR)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: %s <csv-file>" % sys.argv[0], file=sys.stderr)
        sys.exit(2)

    try:
        setup_logging()
        logger = logging.getLogger('deezer_importer')
        config = setup_config()

        csv_file = str(Path(sys.argv[1]).resolve())

        client = pylistenbrainz.ListenBrainz()
        client.set_auth_token(get_listenbrainz_token(config))

        parse_and_submit(config, csv_file, client)
    except InvalidAuthTokenException:
        sys.stderr.write("\nInvalid ListenBrainz auth_token error. Please, check your 'deezer_importer.ini' configuration file.\n")
        sys.exit(2)
    except KeyError:
        sys.stderr.write("\nCan't read ListenBrainz auth_token. Please, check your 'deezer_importer.ini' configuration file.\n")
        sys.exit(2)
    except KeyboardInterrupt:
        sys.stderr.write("\nCtrl+c received, shutting down...\n")

