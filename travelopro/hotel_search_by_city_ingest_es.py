__author__ = 'Shahtab Khandakar'

"""
Desc: Query Travelopro Hotel Booking API to search hotels by City Name
      And ingest the data into Elasticsearch Index
      ITEM: - 'HOTEL AVAILABILITY SEARCH' + CHECK MORE HOTEL RESULTS' from travelopro website
               also get 'HOTEL AVAILABILITY RESPONSE'
      Can query ONLY the hotels and cities that Travelocity has in their inventory
Usage:   
        First need to set the OS environment variables as below and export them:
        
        travelopro_user_id=
        travelopro_user_password=

        hotel_search_by_city_ingest_es.py -c 'CITY_NAME' -C 'COUNTRY_NAME'
        hotel_search_by_city_ingest_es.py -c 'London' -C 'United Kingdom'
        hotel_search_by_city_ingest_es.py -c 'Barcelona' -C 'Spain'
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

from elastic import *

global _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT
_TRAVELOPRO_HOTEL_SEARCH_ENDPOINT = "https://travelnext.works"

template_file_path = jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates"))
jinja2_environment = jinja2.Environment(loader=template_file_path)

class TraveloproHotelSearch:
  def __init__(self, user_id, user_password, access='Test'):
    self.user_id = user_id
    self.user_password = user_password
    self.access = access
  
  def __repr__(self):
    return f"self.user_id, self.access"


class TraveloproHotelSearchByCity(TraveloproHotelSearch):
  def __init__(self, user_id, user_password, access, city_name, country_name):
    super().__init__(user_id, user_password, access)
    self.city_name = city_name
    self.country_name = country_name

  def _get_initial_numof_hotels_by_city(self):
    template_search_by_city = jinja2_environment.get_template("hotel_search_by_city.json")

    config = {
      "user_id": self.user_id,
      "user_password": self.user_password,
      "city_name": self.city_name,
      "country_name": self.country_name,
      "access": self.access
    }

    search_query = template_search_by_city.render(config)

    try:
      response = requests.post(
        _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT+"/api/hotel_trawexv6/hotel_search",
        data=search_query,
        verify=False,
        timeout=20
        )
      response.raise_for_status()
    except requests.exceptions.HTTPError as err:
      print (err.response.text)  
      raise SystemExit(err)

    """ This is required as Travelopro send status code of 200 even though when access is denied ... This is a Hack :-("""
    if response.json().get('status'):
      if not response.json().get('status')['sessionId']:
        if response.json().get('status')['errors'][0]['errorMessage'] == 'Access Denied':
          sys.exit(f"*** ERROR *** Access is denied to travelopro endpoint for user id: {user_id}" )

    return response.json()
  
  def _get_remaining_hotels_by_city(self, sessionId, nextToken):
    """ https://travelnext.works/api/hotel_trawexv6/moreResults?sessionId=<sessionId>&nextToken=<nextToken>&maxResult=20> """

    params = {"sessionId": sessionId, "nextToken": nextToken, "maxResult": 100}
    try:
      response = requests.get(
         _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT+"/api/hotel_trawexv6/moreResults", 
         params=params, 
         verify=False, 
         timeout=20
      )
      response.raise_for_status()
    except requests.exceptions.HTTPError as err:
      print (err.response.text)
      raise SystemExit(err)
       
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
  try:
      user_id = os.environ.get('travelopro_user_id') 
      user_password = os.environ.get('travelopro_user_password')
  except Exception as e:
      print(e)
      sys.exit("Required OS environment variables need to be set. Exiting ...")

  city_search_obj = TraveloproHotelSearchByCity(user_id, user_password, 'Test', args.cityname, args.countryname)
  hotel_listing_initial  = city_search_obj._get_initial_numof_hotels_by_city()

  search_initial_status_dict = hotel_listing_initial.get('status')
  status_sessionId = search_initial_status_dict['sessionId']

with ElasticsearchConnectionManager('127.0.0.1') as _es:
  """ First/initial paginated data"""
  for each_hotel in hotel_listing_initial.get('itineraries'):
      each_hotel['sessionId'] = status_sessionId
      ingest_response = _es.index(index='travelopro-hotels-by-city', doc_type='_doc', body=each_hotel)
      print(ingest_response)


  status_sessionId = search_initial_status_dict['sessionId']
  status_token = search_initial_status_dict['nextToken']

  """ Second and until last paginated data"""
  while status_token:
    hotel_listing_more = city_search_obj._get_remaining_hotels_by_city(status_sessionId, status_token)
    
    print(hotel_listing_more)
    more_status_dict = hotel_listing_more.get('status')
    
    """ hotel_listing_more.get('itineraries') is a LIST of DICTS"""

    if more_status_dict.get('sessionId'):
      status_sessionId = more_status_dict['sessionId'] 
      status_token = more_status_dict['nextToken'] 

      for each_hotel in hotel_listing_more.get('itineraries'):
          each_hotel['sessionId'] = status_sessionId
          ingest_response = _es.index(index='travelopro-hotels-by-city', doc_type='_doc', body=each_hotel)
          print(ingest_response)
      continue
    else:
      break

 
