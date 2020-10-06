__author__ = 'Shahtab Khandakar'

"""
Desc: Query Travelopro Hotel Booking API to search hotels by City Name and get all the static contents
      And insert the data into MongoDB into 'hotelsStaticContentsByCity' collection
      Can query ONLY the hotels and cities that Travelocity has in their inventory
Usage:   
        First need to set the OS environment variables as below and export them:
        
        travelopro_user_id=
        travelopro_user_password=

        hotel_query_static_contents_insert_mongo.py -c 'CITY_NAME' -C 'COUNTRY_NAME'
        hotel_query_static_contents_insert_mongo.py -c 'London' -C 'United Kingdom'
        hotel_query_static_contents_insert_mongo.py -c 'Barcelona' -C 'Spain'
"""

import json
import requests
import jinja2
import os
import sys
import urllib3
urllib3.disable_warnings()

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from connections import *

global _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT
_TRAVELOPRO_HOTEL_SEARCH_ENDPOINT = "https://travelnext.works"

template_file_path = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates"))
jinja2_environment = jinja2.Environment(loader=template_file_path)

class TraveloproHotelSearch:
  def __init__(self, user_id, user_password):
    self.user_id = user_id
    self.user_password = user_password
  
  def __repr__(self):
    return f"self.user_id, self.access"


class TraveloproHotelSearchByCity(TraveloproHotelSearch):
  def __init__(self, user_id, user_password, city_name, country_name):
    super().__init__(user_id, user_password)
    self.city_name = city_name
    self.country_name = country_name
  
  def _get_static_contents_hotels_by_city(self):

    """ https://travelnext.works/api/hotel_trawexv6/static_content?from=1&to=100&user_id=<user_id>
    &user_password=<user_password>&ip_address=<ip_address>&access=Test&city_name=<city_name>&country_name=<country_name> """

    params = {
              "from": 1,
              "to": 1000,
              "user_id": self.user_id, 
              "user_password": self.user_password, 
              "ip_address": '10.10.10.11', 
              "access": 'Test',
              "city_name": self.city_name, 
              "country_name": self.country_name
              }
    try:
      response = requests.get(
         _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT+"/api/hotel_trawexv6/static_content", 
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
    parser.add_argument('-c', '--cityname', required=False, help="Specify the cityname")
    parser.add_argument('-C', '--countryname', required=False,help="Specify the country name")
    args = parser.parse_args()
    return parser.parse_args()    


if __name__ == '__main__':
  
  args = parse_args()
  
  """ these are environment variables set in OS for the user"""
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

  city_search_obj = TraveloproHotelSearchByCity(user_id, user_password, args.cityname, args.countryname)
  hotel_static_contents_listing  = city_search_obj._get_static_contents_hotels_by_city()

  hotel_static_contents_list_of_dict = hotel_static_contents_listing.get('hotels')
  total_hotel_static_contents_total = hotel_static_contents_listing.get('total')
  """ hotel_contents_list_of_dict is a list of hotel dicts"""

  with MongoDBConnectionManager(mongodb_host, mongodb_user_id, mongodb_user_password, mongodb_database) as mongo:
    collection = mongo.connection.travelopro.hotelsStaticContentsByCity
    for each_hotel in hotel_static_contents_list_of_dict:
      try:
        insert_response = collection.insert_one(each_hotel)
        print(f"--- {insert_response} ---")
        print(each_hotel)
      except Exception as e:
        print(e)
    
 

 
