
__author__ = 'Shahtab Khandakar'

"""
Desc:  A library containing classes and methods to work with Elasticsearch
       Started with a Context Manager for Elasticsearch connection
       Then *** add methods ***  to tailor our data ingestion/processing needs

       IMPORTANT:
       - In PROD, we may not directly ingest into elasticsearch rather use one/more of the below
         - Kafka
         - Redis
         - Logstash
         - FluentD
         - Beats ( for now file beats)
"""

#from elasticsearch_xpack import XPackClient
from elasticsearch import Elasticsearch, helpers
import urllib3
import warnings
import contextlib

class ElasticsearchConnectionManager(object):
    """ This is only a context manager for elasticsearch connection"""
    def __init__(self, fqdn):
        #self.user = user
        #self.password = password
        self.fqdn = fqdn
        self.connection = None      

    def __enter__(self):
        _es_host = {"host": self.fqdn, "port": 9200}
        self.connection = Elasticsearch(hosts=[_es_host], use_ssl=False, verify_certs=False, timeout=600)
        return self.connection

    def __exit__(self, exc_type, exc_value, exc_traceback):
        del(self)

    def connectToElasticsearch( self, fqdn, port):
        connection_string = 'https://' + fqdn + ':' + str(port)
        #connection_string = 'https://' + user + ':' + password + '@' + fqdn + ':' + str(port)
        # Below with conn_string with http_auth will also work ...
        #conn_string = 'https://' + fqdn + ':' + str(port)
        #self.connection = Elasticsearch([conn_string], http_auth=(user, password))
        self.connection = Elasticsearch([connection_string], use_ssl=False, verify_certs=False, timeout=600)
        #elasticsearch_xpack.XPackClient.infect_client(self.connection)

        return self.connection

def default_template_settings(index_pattern):
    """ set default index pattern for indices """
    return {
        #"index_patterns": ["hotel-booking-*"],
        "index_patterns": [index_pattern],
        "order": 1, 
        "settings": {
            "index": {
                "mapping": {
                    "total_fields": {
                        "limit": 1000
                    }
                },
                "refresh_interval": "5s"
            }
        },
        "mappings": {}
    }


def connect_es():
    _es = None
    host = ''
    id = ''
    password = ''
    
    _es = Elasticsearch([{"host": host, "hhtp_auth": (id, password), "port": 9200}])
    response = _es_search(index="myindex-*", doc_type=not_needed, body={"query": {"match_all": {} }})

    if _es.ping():
        print('connected')
    else:
        print("failed to connect ...")


    print(f"Number of hits : {response['hits']['total']['value']}")
    print(_es.indices.get_alias().keys())
    print(response)
    return _es

    

"""
context
connecting with a localhost 
with ElasticsearchConnectionManager(fqdn) as es:
    es.indices.create(index=index_name)
"""


if __name__ == '__main__':
   pass 
