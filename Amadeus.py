
__author__ = 'Shahtab Khandakar'

"""
 DO RESEARCH or ASK VENDOR
        For PROD setup:
            - Must pass x.509 certificate
            - Need to check if mTLS is required or available. If/when available then mTLS should be used.
IMPORTANT:
    - Most of the API endpoint that developers have free access to are RESTful, but some which are Enterprise grade use SOAP.
      So the mechanisms will change a bit as SOAP uses XML.  SOAP is a protocol
    - SOAP API uses services interfaces like @WebService

"""

import base64
import json
import requests
import warnings
import logging
import re
import sys
from string import Template

"""Let's filter all warnings for now"""
warnings.filterwarnings("ignore")

global DEBUG
DEBUG = False

if DEBUG: logging.basicConfig(level=logging.DEBUG) 
else: logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

class AmadeusBadInputParameterOrEndpointRequest(Exception):
    def __init__(self, message):
        super().__init__(message)

class AmadeusInterfaceFileNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)

class AmadeusOAuth2TokenNotFoundException(Exception):
    pass

class AmadeusClient(object):
    def __init__(self, auth_endpoint, username, secret):
        self.auth_endpoint = auth_endpoint
        self.username = username
        self.secret = secret 

        self.oauth_json_response = self.request_oauth_token() 
        self.oauth2_access_token = self.oauth_json_response.json().get('access_token')
        logger.debug(f"DEBUG: oauth2_access_token: {self.oauth2_access_token}")

    def __repr__(self):
        return str(self.__dict__)

    def request_oauth_token(self):
        """
          Requests a response through basic authentication.
          Returns json object with keys "access_token", "token_type","expires_in" etc ...
        """

        auth_header_basic = {'Content-Type': 'application/x-www-form-urlencoded' }

        #currently not using grant_data dict and may be needed for similar cases when JSON payload is needed to be sent
        grant_data = {
            'grant_type': 'client_credentials',
            'client_id' : self.username,
            'client_secret' : self.secret
        }

        grant_data_str = 'grant_type=client_credentials&client_id=$username&client_secret=$secret'
        grant_data_obj = Template(grant_data_str)
        grant_query_data = grant_data_obj.substitute(username=self.username, secret=self.secret)

        try:
            response = requests.post(
                self.auth_endpoint+"/v1/security/oauth2/token",
                data=grant_query_data,
                headers=auth_header_basic, 
                verify=False,
                timeout=10
                )
        except IOError as e:   
          raise AmadeusBadInputParameterOrEndpointRequest("Either Endpoint or params is incorrect")
          print(e)

        #try:
        #    response.raise_for_status()
        #except requests.HTTPError:
        #    print(response.content.decode("utf-8"), file=sys.stderr)
        #    raise

        logger.debug(f"response -> {response}")
        logger.debug(f"response.status_code: {response.status_code}")

        if response.status_code != 200 or response.status_code != 201:
            logger.debug(f"response.content: {response.content}")
            logger.debug(f"access_token: {response.json().get('access_token')}")
            pass # For Now - need better validation checks

        return response

    @property
    def _get_access_token(self) -> str:
        return self.oauth2_access_token

    @property
    def _get_full_response(self) -> str:
        return self.oauth_json_response.content


class AmadeusHotelSearch(object):
    def __init__(self, search_endpoint, access_token):
        self.search_endpoint = search_endpoint
        self.access_token = access_token

    def __repr__(self):
        return str(self.__dict__)

    def search_hotels_by_citycode(self, cityCode) -> str:

        header = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
             }

        response = requests.get(
            self.search_endpoint+"/v2/shopping/hotel-offers", 
            params={'cityCode': cityCode}, 
            headers=header, 
            verify=False, 
            timeout=20
            )
    
        logger.debug(f"response from GET: {response}")
        logger.debug(f"response.status_code: {response.status_code}") 

        if response.status_code != 200 or response.status_code != 201:
            logger.debug(f"DEBUG: response.content: {response.content}")
            logger.debug(f"DEBUG: access_token: {response.json().get('access_token')}")
            pass 

        return response.content


def set_requests_retries(num_retry):
    """ We need to set some retry mechanisms for REST calls to Remote API endpoints """
    try:
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
    except ImportError as e:
        raise e

    retry_strategy = Retry(
        total=num_retry,
        status_forcelist=[429, 500, 502, 503, 504],
        method_whitelist=["HEAD", "GET", "POST", "PUT", "OPTIONS"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)



class Config(object):      
    """
      Read key/val from a config file
      conf = Config("amadeus.conf", overwrite_keys=False)
      conf.get('amadeus_username')
      conf.get('amadeus_secret')
      conf.get('amadeus_endpoint')
    """
    def __init__(self, filename, overwrite_keys):
        """ overwrite_keys will be required once I get the 'set' method done (TO-DO). Has no impact for 'get' """
        self.filename = filename
        self.overwrite_keys = overwrite_keys

    def get(self,k) -> str:
        self.k = k
        mydict = {}
        with open(self.filename) as fh:
            for line in fh.readlines():
                (k,v) = line.split('=',1)
                mydict[k] = v

        return mydict[self.k].rstrip()


if __name__ == '__main__':
   pass 
