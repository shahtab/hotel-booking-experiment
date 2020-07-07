
__author__ = 'Shahtab Khandakar'

"""
Desc:  Library to construct API endpoints
"""

import os
import sys
import copy
from urllib.parse import quote_plus

class EndPointConfig:
    """ Construct endpoints with simple hostname, username/password, with ports"""
    def __init__(self, host: str = None, ignore_urls: [str] = None, **kwargs):
        self.host = host

        kwargs = copy.deepcopy(kwargs)
        kwargs.setdefault('username', None)
        kwargs.setdefault('password', None)
        kwargs.setdefault('port', None)

        _acceptable_keys_list = ['username', 'password','port']

        _ignore_urls = ['127.0.0.1', 'localhost']
        self.ignore_urls = ignore_urls if ignore_urls is not None else _ignore_urls
        if self.host in _ignore_urls:
            print(f"Invalid host: {self.host}")
            sys.exit(1)
        
        #Create self.[var] from dict items from kwargs for all acceptable keys
        [self.__setattr__(key, kwargs.get(key)) for key in _acceptable_keys_list]

    @property
    def http_endpoint(self) -> str:
        return self._create_url()

    @property
    def https_endpoint(self) -> str:
        return self._create_url('https://')

    @property
    def no_url(self) -> str:
        return ','.join(self.ignore_urls)


    def _create_url(self, proto: str = None) -> str:
        """
           Construct an endpoint URL/HOST urllib.parse.quote_plus builds query string
        """
        url = proto if proto else "http://"

        if self.username and self.password:
            user = quote_plus(self.username)
            password = quote_plus(self.password)
            url += f'{user}:{password}@{self.host}'
        else:
            url += self.host


        if self.port is not None:
            url += f':{self.port}'

        return url


class GetEndpoint(EndPointConfig):
    """ TODO:  Add more methods/functions to manage endpoints"""
    def __init__(self, host, **kwargs):
        super().__init__(host, **kwargs)




