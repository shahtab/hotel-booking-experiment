
__author__ = 'Shahtab Khandakar'

"""
Desc: Query Travelopro Hotel Booking API to search hotels by City Name and GET MORE HOTEL CONTENTS for the searched hotels
      ITEM:  - 'GET HOTEL CONTENTS' - from Travelopro website FOR MORE RECENT STATIC CONTENT
             - This is in addition to 'HOTEL STATIC CONTENTS'
             
      Can query ONLY the hotels and cities that Travelocity has in their inventory
Usage:   
        First need to set the OS environment variables as below and export them:
        
        travelopro_user_id=
        travelopro_user_password=
        mongodb_host=my.mongodb.net
        mongodb_database=
        mongodb_user_id=
        mongodb_user_password=

        hotel_room_rates_by_city_insert_mongo.py -c 'CITY_NAME' -C 'COUNTRY_NAME' -s true -l true
        hotel_room_rates_by_city_insert_mongo.py -c 'London' -C 'United Kingdom' -s true -l true
        
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

    """ This is required as Travelopro send status code of 200 even though when access is denied This is a Hack :-("""
    print(response.json().get('status'))
    if response.json().get('status'):
      if not 'sessionId' in response.json().get('status'):
        #if response.json().get('status')['errors'][0]['errorMessage'] == 'Access Denied':
        sys.exit(f"*** ERROR ***  {response.json().get('status')}" )

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

    """ This is required as Travelopro send status code of 200 even though when access is denied This is a Hack :-("""
    print(response.json().get('status'))
    if response.json().get('status'):
      if not 'sessionId' in response.json().get('status'):
          #if response.json().get('status')['errors'][0]['errorMessage'] == 'Access Denied':
          sys.exit(f"*** ERROR *** {response.json().get('status')}" )
       
    return response.json()

def parse_args():
    try:
        import argparse
    except:
        raise

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--cityname', required=False, help="Specify the cityname")
    parser.add_argument('-C', '--countryname', required=False,help="Specify the country name")
    parser.add_argument('-s', '--status', required=False,help="Specify the status")    
    parser.add_argument('-l', '--list', required=False,help="Specify the listing")    

    args = parser.parse_args()
    return parser.parse_args()    

def _get_hotel_room_rates_for_each_hotel(hotel_dict):
    """ POST	https://travelnext.works/api/hotel_trawexv6/get_room_rates
        I need to capture ratebasisId from the response of this function and do POST 
        to https://travelnext.works/api/hotel_trawexv6/get_rate_rules
        {  --- RESPONSE
             "sessionId": "TVRVNE1qSTJOVEExTlY4ek1URmZNVEkxTGprNUxqSTBNUzR5TkE9PV8w",
             "hotelId": "882885",
             "tokenId": "IP8Z2AeBKGrnVvi6Hdbq",
             "roomRates": {
                  "perBookingRates": [  ----- list of dict
                                       { ---- dicts
                                          "productId": "trx101",  
    """
    rate_query = {
               'sessionId': hotel_dict['sessionId'],
               'hotelId': hotel_dict['hotelId'],
               'productId': hotel_dict['productId'],
               'tokenId': hotel_dict['tokenId']
               }
    try:
        response = requests.post(
                      _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT+"/api/hotel_trawexv6/get_room_rates", 
                      data=json.dumps(rate_query), 
                      verify=False, 
                      timeout=20
                    )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print (err.response.text)  
        raise SystemExit(err)

    return response.json()


def _check_hotel_room_rates_for_each_hotel(hotel_rates_dict):
    """ POST	https://travelnext.works/api/hotel_trawexv6/get_rate_rules
        to https://travelnext.works/api/hotel_trawexv6/get_rate_rules
        ITEM in travelopro website 'CHECK ROOM RATES'
        parameter is moreResults is true

        CAPTURE:  {'status': {'error': 'Selected Room Not Available.'}} when calling this function
    """
    #Here inside each dict 'ratebasisId' exist ... get that
    print ('--------------------------')
    print(hotel_rates_dict)
    #for per_booking_rate in hotel_rates_dict:
    rate_rules_query = {
               'sessionId': hotel_rates_dict['sessionId'],
               'tokenId':   hotel_rates_dict['tokenId'],
               'productId': hotel_rates_dict['productId'],
               'rateBasisId': hotel_rates_dict['rateBasisId']
               }
    try:
        response = requests.post(
                      _TRAVELOPRO_HOTEL_SEARCH_ENDPOINT+"/api/hotel_trawexv6/get_rate_rules", 
                      data=json.dumps(rate_rules_query), 
                      verify=False, 
                      timeout=20
                    )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print (err.response.text)  
        raise SystemExit(err)

    return response.json()


def _process_list_of_hotels_in_dict(list_of_hotel_dicts):
    for each_hotel in list_of_hotel_dicts:
        yield each_hotel

   
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

  city_search_obj = TraveloproHotelSearchByCity(user_id, user_password, 'Test', args.cityname, args.countryname)
  hotel_listing_initial = city_search_obj._get_initial_numof_hotels_by_city()
  search_initial_status_dict = hotel_listing_initial.get('status')

  print(search_initial_status_dict)

  hotel_count = 0
  status_sessionId = search_initial_status_dict['sessionId']

  #itineraries hold hotel info in dict... loop over these and do other queries for "Get Hotel Content"
  # GET https://travelnext.works/api/hotel_trawexv6/hotelDetails?sessionId=<sessionId> &hotelId=<hotelId>&productId=trx104&tokenId=<tokenId>
  # for each hotel we query
  
with MongoDBConnectionManager(mongodb_host, mongodb_user_id, mongodb_user_password, mongodb_database) as mongo:
  collection = mongo.connection.travelopro.hotelRoomRatesByCity
  """ hotel_listing_initial.get('itineraries') is a list of dicts each with hotel info """

  if args.list:
    for each_hotel in _process_list_of_hotels_in_dict(hotel_listing_initial.get('itineraries')):
        hotel_count += 1
        print(f"-------------------  {hotel_count} -----------------")
        each_hotel['sessionId'] = status_sessionId
        print(each_hotel)

        room_rates_for_each_hotel = _get_hotel_room_rates_for_each_hotel(each_hotel)
        print(room_rates_for_each_hotel)
        if 'roomRates' in room_rates_for_each_hotel:
          for per_booking_rate in room_rates_for_each_hotel['roomRates']['perBookingRates']:
              per_booking_rate['sessionId'] = room_rates_for_each_hotel['sessionId']
              per_booking_rate['hotelId'] = room_rates_for_each_hotel['hotelId']
              per_booking_rate['tokenId'] = room_rates_for_each_hotel['tokenId']

          print(per_booking_rate)
          insert_response = collection.insert_one(per_booking_rate)
          print(f"--- {insert_response} ---")
  
  status_token = search_initial_status_dict['nextToken']
  status_sessionId = search_initial_status_dict['sessionId']

  while status_token:
    hotel_listing_more = city_search_obj._get_remaining_hotels_by_city(status_sessionId, status_token)
    more_status_dict = hotel_listing_more.get('status')
    
    if more_status_dict.get('sessionId'):
      status_sessionId = more_status_dict['sessionId'] 
      status_token = more_status_dict['nextToken'] 

      if args.list:
        for each_hotel in _process_list_of_hotels_in_dict(hotel_listing_more.get('itineraries')):
            hotel_count += 1
            print(f"-------------------  {hotel_count} -----------------")
            each_hotel['sessionId'] = status_sessionId
            print(each_hotel)

            room_rates_for_each_hotel = _get_hotel_room_rates_for_each_hotel(each_hotel)
            if 'roomRates' in room_rates_for_each_hotel:
                for per_booking_rate in room_rates_for_each_hotel['roomRates']['perBookingRates']:
                    per_booking_rate['sessionId'] = room_rates_for_each_hotel['sessionId']
                    per_booking_rate['hotelId'] = room_rates_for_each_hotel['hotelId']
                    per_booking_rate['tokenId'] = room_rates_for_each_hotel['tokenId']

                    print(per_booking_rate)
                    insert_response = collection.insert_one(per_booking_rate)
                    print(insert_response)
            else:
                  continue
          
      continue
    else :
      print(type(more_status_dict['nextToken']))
      break

 
