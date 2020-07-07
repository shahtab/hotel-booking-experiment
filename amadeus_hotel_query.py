#!/usr/bin/env python3

__author__ = 'Shahtab Khandakar'

"""
Desc: testing Amadeus APIs to get information about various hotels in the world for booking
"""

import sys
import re
import os
import datetime
import logging
from Amadeus import *
from datetime import datetime
from elasticsearch import Elasticsearch
from elastic import *

global DEBUG
DEBUG = False

global _AMADEUS_AUTH_ENDPOINT
global _AMADEUS_DEV_AUTH_ENDPOINT
_AMADEUS_DEV_AUTH_ENDPOINT = "https://test.api.amadeus.com"
_AMADEUS_AUTH_ENDPOINT = _AMADEUS_DEV_AUTH_ENDPOINT
global _AMADEUS_HOTEL_SEARCH_ENDPOINT
_AMADEUS_HOTEL_SEARCH_ENDPOINT = "https://test.api.amadeus.com"


if DEBUG: 
    logging.basicConfig(level=logging.DEBUG) 
else: 
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


def parse_args():
    try:
        import argparse
    except:
        raise

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--username', required=False, help="Specify the username")
    parser.add_argument('-p', '--password', required=False,help="Specify the password")
    parser.add_argument('-c', '--citycode', required=False, help="Specify the search citycode")
    parser.add_argument('-e', '--elastic', required=False,help="Specify the option to ingest into elastic index")
    #parser.set_defaults(username='elastic', password='changeme')  --> change this in code as 'username' and 'password is used for something else
    args = parser.parse_args()
    return parser.parse_args()

if __name__ == '__main__':

    try:
        from  Amadeus import *
    except ImportError as error:
        print(f"error.__class__.__name__ : {error}")
    except Exception as exception:
        print(f"exception.__class__.__name__: {exception}")

    now = datetime.now()
    amadeus_config_file = 'amadeus.conf'

    if os.path.exists(amadeus_config_file):
        conf = Config(amadeus_config_file, overwrite_keys=False) 
    else:
        print(f"ERROR: Unable to locate config file {amadeus_config_file}")
        sys.exit(-1)

    args = parse_args()
    if not args.password:
        secret = conf.get('amadeus_secret')
    else:
        secret = args.password
    
    if not args.username:
        username = conf.get('amadeus_username')
    else:
        username = 'invalid_shahtab'

    logger.debug(f"DEBUG: client_id: {username}  client_secret: {secret}")
    
    try:
        from Redis import *
    except ImportError as e: 
        raise RedisInterfaceFileNotFound('Redis.py Interface file not found in the current context of the runniong program')
        print(e)
    
    #TODO: Check connection to Redis and if doesn't exist do something .. as Redis might not be available/up
    redis_conn_str = RedisConnection('localhost', 6379)
    redis_conn_obj = redis_conn_str._connect()
    amadeus_access_token = redis_conn_obj.get('amadeus_access_token')

    if amadeus_access_token is None:
        """ token doesn't exist"""
        amadeus_auth_obj = AmadeusClient(_AMADEUS_AUTH_ENDPOINT, username, secret)
        amadeus_access_token = amadeus_auth_obj._get_access_token
        redis_conn_obj.set('amadeus_access_token', amadeus_access_token)
        redis_conn_obj.expire('amadeus_access_token', 1799)
        amadeus_access_token = redis_conn_obj.get('amadeus_access_token')
        set_requests_retries(3)
        amadeus_hotel_search_obj = AmadeusHotelSearch(_AMADEUS_HOTEL_SEARCH_ENDPOINT, amadeus_access_token.decode('utf-8'))
    else:
        """ token exists .. token is in bytes so decode it into 'str' for test in isinstance"""
        amadeus_access_token = redis_conn_obj.get('amadeus_access_token')
        if isinstance(amadeus_access_token.decode('utf-8'), str):
            set_requests_retries(3)
            amadeus_hotel_search_obj = AmadeusHotelSearch(_AMADEUS_HOTEL_SEARCH_ENDPOINT, amadeus_access_token.decode('utf-8'))

    # 'message' with data:  is a list of dicts [{},{}...]
    message = amadeus_hotel_search_obj.search_hotels_by_citycode(args.citycode)
    msg_dict = json.loads(message)
    
    if DEBUG:
      logger.debug(f"DEBUG: message -> {message}")
      logger.debug(f"DEBUG: type -> {type(message)}")
      for k in msg_dict.keys():
          if k == 'data':
            logger.debug(f"DEBUG: {msg_dict['data']}")


    def add_timestamp_to_message_dict(mdict):
        """ A GENERATOR function to timestamp each item/doc in the dictionary and pass the message dictionary msg_dict """
        mdict['timestamp'] = now.strftime("%Y/%m/%d, %H:%M:%s")
        yield mdict

    """ Ingest data into an index in Elasticsearch """
    if args.elastic:
       """ 
        FYI: message has multiple keys like 'data', 'meta' etc ... we may need to find out what we need
       """

       with ElasticsearchConnectionManager('127.0.0.1') as _es:
           for each_item in msg_dict['data']:
               for item in add_timestamp_to_message_dict(each_item):
                   ingest_response = _es.index(index='hotels-by-city', doc_type='_doc', body=item)
                   print(ingest_response)


