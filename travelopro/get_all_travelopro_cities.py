__author__ = 'Shahtab Khandakar'

"""
Desc: Get all the CITIES and Country Names from the Travelopro Invemntory
      And Insert the records into Elasticsearch and MongoDB
      ITEM: - 'CITIES' from travelopro website

Usage: 
       get_all_travelopro_cities.py [-e/--elastic] true [-m/--mongo] true   -> for both Elastic & MongoDB
       get_all_travelopro_cities.py [-e/--elastic] true  -> Only ELASTICSEARCH 
       get_all_travelopro_cities.py [-m/--mongodb] true  -> Only MONGODB 
""" 

import os
import sys
import requests
import json
import urllib3
urllib3.disable_warnings()

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from elastic import *
from connections import *

global _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT
_TRAVELOPRO_HOTEL_SEARCH_ENDPOINT = "https://travelnext.works"

class TraveloproAllCities:
   def __init__(self, user_id, user_password):
      self.user_id = user_id
      self.user_password = user_password
  
   def __repr__(self):
      return f"self.user_id"

   def _get_all_travelopro_cities(self):
      """ https://travelnext.works/api/hotel_trawexv6/cities?user_id=<user_id>&user_password=<user_password>&ip_address=<p_address>&access=Test"""

      params = {'user_id': self.user_id , 'user_password': self.user_password , 'ip_address': '10.10.10.11', 'access': 'Test'}
      try:
         response = requests.get(
                      _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT+"/api/hotel_trawexv6/cities", 
                      params=params, 
                      verify=False, 
                      timeout=20
                    )
         response.raise_for_status()
      except requests.exceptions.HTTPError as err:
         print (err.response.text)  
         raise SystemExit(err)

      """ This is required as Travelopro send status code of 200 even though when access is denied. This is a Hack :-("""
      if response.json().get('status'):
        if response.json().get('status')['errors'][0]['errorMessage'] == 'Access Denied':
           sys.exit(f"*** ERROR *** Access is denied to travelopro endpoint for user id: {user_id}" )
      
      return response.json()


def parse_args():
    try:
        import argparse
    except:
        raise

    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--elastic', required=False, help="true for ingesting into elastic")
    parser.add_argument('-m', '--mongodb', required=False,help="true for inserting into MongoDB")
    args = parser.parse_args()
    return parser.parse_args()    


if __name__ == '__main__':
       
   args = parse_args()

   try:
      user_id = os.environ.get('travelopro_user_id') 
      user_password = os.environ.get('travelopro_user_password')
      mongodb_host = os.environ.get('mongodb_host')
      mongodb_database = os.environ.get('mongodb_database')
      mongodb_user_id = os.environ.get('mongodb_user_id')
      mongodb_user_password = os.environ.get('mongodb_user_password')
   except Exception as e:
      print(e)
      sys.exit("Required OS environment variables need to be set. Exiting ...")

   all_cities_obj = TraveloproAllCities(user_id, user_password)

   all_cities = all_cities_obj._get_all_travelopro_cities()

   for each_city in all_cities['cities']:
      print(f"{each_city['id']} - {each_city['city_name']} - {each_city['country_name']}")

   if args.elastic:
     with ElasticsearchConnectionManager('127.0.0.1') as _es:
        for each_city in all_cities['cities']:
            ingest_response = _es.index(index='travelopro-all-cities', doc_type='_doc', body=each_city)
            print(ingest_response)
   
   if args.mongodb:
     with MongoDBConnectionManager(mongodb_host, mongodb_user_id, mongodb_user_password, mongodb_database) as mongo:
        collection = mongo.connection.travelopro.allCities
        for each_city in all_cities['cities']:
            try:
                insert_response = collection.insert_one(each_city)
                print(f"--- {insert_response} ---")
                print(each_city)
            except Exception as e:
                print(e)

