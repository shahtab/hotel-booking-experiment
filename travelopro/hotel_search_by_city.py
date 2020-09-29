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
    except IOError as e:   
      print(e)

    return response.json()
  
  def _get_remaining_hotels_by_city(self, sessionId, nextToken):
    """ https://travelnext.works/api/hotel_trawexv6/moreResults?sessionId=<sessionId>&nextToken=<nextToken>&maxResult=20> """

    params = {"sessionId": sessionId, "nextToken": nextToken, "maxResult": 100}
    response = requests.get(
       _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT+"/api/hotel_trawexv6/moreResults", 
       params=params, 
       verify=False, 
       timeout=20
    )
    return response.json()
        
   
if __name__ == '__main__':
      
  user_id = os.environ.get('travelopro_user_id') 
  user_password = os.environ.get('travelopro_user_password')  

  city_search_obj = TraveloproHotelSearchByCity(user_id, user_password, 'Test', 'London', 'United Kingdom')
  hotel_listing = city_search_obj._get_initial_numof_hotels_by_city()
  search_status_dict = hotel_listing.get('status')

  #print(hotel_listing.get('itineraries'))
  with ElasticsearchConnectionManager('127.0.0.1') as _es:
    for each_hotel in hotel_listing.get('itineraries'):
      ingest_response = _es.index(index='travelopro-hotels-by-city', doc_type='_doc', body=each_hotel)
      print(ingest_response)

  #print(hotel_listing.get('status'))
  #print(search_status_dict['sessionId'])


  """ search_status_dict['nextToken'] is a string """
  while search_status_dict['nextToken']:
    hotel_listing_more = city_search_obj._get_remaining_hotels_by_city(
                                            search_status_dict['sessionId'],
                                            search_status_dict['nextToken'],
                                        )
    
    print(hotel_listing_more)
    more_status_dict = hotel_listing_more.get('status')
    
    """ hotel_listing_more.get('itineraries') is a LIST of DICTS"""

    if len(more_status_dict.get('nextToken')) != 0:
      search_status_dict['nextToken'] = more_status_dict['nextToken'] 
      #print(hotel_listing_more.get('itineraries'))
      print(hotel_listing_more.get('nextToken'))
      #all_hotel_ids = [each_hotel['hotelId'] for each_hotel in hotel_listing_more.get('itineraries')]

      with ElasticsearchConnectionManager('127.0.0.1') as _es:
           for each_hotel in hotel_listing_more.get('itineraries'):
                   ingest_response = _es.index(index='travelopro-hotels-by-city', doc_type='_doc', body=each_hotel)
                   print(ingest_response)
          
      continue

    if not more_status_dict.get('moreResults'):
      break

 
