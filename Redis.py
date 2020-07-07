#!/usr/bin/env python3

__author__ = 'Shahtab Khandakar'

"""
  Desc:   A library to interact with Redis           
  TODO:  Will need to add more methods to interact with Redis Database so the applications need not to worry about details
"""

import redis

class RedisConnectionFail(Exception):
    def __init__(self, expstring):
        self.expstring = expstring

    def __str__(self):
        print(f"Failed to connect to Redis database: {self.expstring}")
        return repr(self.expstring)

class RedisInterfaceFileNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)


class RedisConnection(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        #self.password = password
    
    def __repr__(self):
        return str(self.__dict__)

    def _connect(self):
        try:
            #Below is for password protected Redis with TLS which will be required for PROD
            # For password protected Redis we also need the DB name
            #conn = redis.StrictRedis(host=self.host, port=self.port, password=self.password, ssl=True, ssl_cert_reqs=None)
            #BETTER to use a connection pool so we can re-use the exiosting connection as opening and closing connections are expensive
            pool = redis.ConnectionPool(host=self.host, port=self.port, db=0)
            conn = redis.Redis(connection_pool=pool)
            #conn = redis.Redis(host=self.host, port=self.port, db=0)
            return conn
        except:
            raise RedisConnectionFail(f'Connection to {self.host} failed. Check if .Redis is up.')


