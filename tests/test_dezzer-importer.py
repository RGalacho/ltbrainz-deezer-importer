#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 R. Galacho
# License GPLv3

import logging
import configparser
from pathlib import Path
import pylistenbrainz
from requests.exceptions import ConnectionError

import pytest
from unittest import TestCase
from unittest.mock import patch


import deezer_importer

# Dummy configuration data
DUMMY_CONFIG = """
[BRAINZ]
auth_token = wewewe
"""

class DeezeerImporterTests (TestCase):
    #@pytest.fixture(autouse=True)
    def mock_config(self):
        config = configparser.ConfigParser()
        config.read_string(DUMMY_CONFIG)
        config.add_section('FILES')
        return config

    def test_config_loaded(self):
        config_parser = configparser.ConfigParser()
        with patch('configparser.ConfigParser.read', return_value = config_parser.read_string(DUMMY_CONFIG)):
            config = deezer_importer.setup_config()
        assert config.has_section('FILES')

    def test_parse_and_submit_without_errors(self):
        mock_config = self.mock_config()
        logger = logging.getLogger('deezer_importer')
        with patch("deezer_importer.MAX_LISTENS_PER_REQUEST", 2):
            with patch('deezer_importer.logger', logger):
                with patch('deezer_importer.submit_listens', return_value={'status': 'ok'}):
                    deezer_importer.parse_and_submit(config=mock_config, csv_file=str(Path('deezer-listeningHistory.csv').resolve()),client=pylistenbrainz.ListenBrainz())

                    assert mock_config.has_section('FILES')
                    assert mock_config.get('FILES', 'deezer-listeningHistory.csv') == '4'

    def test_parse_and_submit_with_error(self):
        mock_config = self.mock_config()
        logger = logging.getLogger('deezer_importer')
        with patch("deezer_importer.MAX_LISTENS_PER_REQUEST", 2):
            with patch('deezer_importer.logger', logger):
                with patch('deezer_importer.submit_listens', side_effect=ConnectionError('Mock Connection exception')) as excinfo:
                    #with pytest.raises(ConnectionError) as excinfo:
                    try:
                        deezer_importer.parse_and_submit(config=mock_config, csv_file=str(Path('deezer-listeningHistory.csv').resolve()),client=pylistenbrainz.ListenBrainz())
                    # skipping sys.exit event
                    except SystemExit:
                        pass
                    assert excinfo.side_effect.args[0] == 'Mock Connection exception'
                    assert mock_config.has_section('FILES')
                    assert mock_config.get('FILES', 'deezer-listeningHistory.csv') == '2'
