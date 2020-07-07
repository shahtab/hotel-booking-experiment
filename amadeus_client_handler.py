#!/usr/bin/env python3

__author__ = 'Shahtab Khandakar'

"""
Desc:  This just retrieves the access_token and prints it out .. A helper script
"""

import sys
import re
import os
import logging

try:
    from Amadeus import *
    from endpoint import *
except ImportError as e:
    raise AmadeusInterfaceFileNotFound('Amadeus.py Library file is missing in the current context')
    print(e)

global DEBUG
DEBUG = False

global _AMADEUS_AUTH_ENDPOINT
global _AMADEUS_DEV_AUTH_ENDPOINT
_AMADEUS_DEV_AUTH_ENDPOINT = "https://test.api.amadeus.com"
_AMADEUS_AUTH_ENDPOINT = _AMADEUS_DEV_AUTH_ENDPOINT

if DEBUG: logging.basicConfig(level=logging.DEBUG) 
else: logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def parse_args():
    try:
        import argparse
    except:
        raise

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=False, help="Specify the username")
    parser.add_argument('-p', '--password', required=False,help="Specify the password")
    args = parser.parse_args()
    return parser.parse_args()

if __name__ == '__main__':

    try:
        from  Amadeus import Config
    except ImportError as error:
        print(f"error.__class__.__name__ : {error}")
    except Exception as exception:
        print(f"exception.__class__.__name__: {exception}")

    amadeus_config_file = 'amadeus.conf'
    if os.path.exists(amadeus_config_file):
        conf = Config(amadeus_config_file, overwrite_keys=False) 
    else:
        print(f"ERROR: Unable to locate config file {amadeus_config_file}")
        sys.exit(-1)


    args = parse_args()

    if not args.password:
        secret = conf.get('amadeus_secret')
        """ TO-DO:  validate data from the config file """
        #secret = 'Pr-----!'
    else:
        secret = args.password
    
    if not args.username:
        username = conf.get('amadeus_username')
    else:
        username = 'shahtab'  """ Placeholder """

    print(f"client_id: {username}  client_secret: {secret}")

    amadeus_auth_obj = AmadeusClient(_AMADEUS_AUTH_ENDPOINT, username, secret)
    print(amadeus_auth_obj._get_full_response.decode('utf-8'))
    amadeus_access_token = amadeus_auth_obj._get_access_token

    logger.debug(f"amadeus_access_token: {amadeus_access_token}")


