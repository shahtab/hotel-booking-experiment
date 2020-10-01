from pymongo import MongoClient 
  
class MongoDBConnectionManager(): 
    def __init__(self, hostname, user, password, dbname): 
        self.hostname = hostname 
        #self.port = port 
        self.user = user
        self.password = password
        self.dbname = dbname
        self.connection = None
  
    def __enter__(self): 
        conn_string = f"mongodb+srv://{self.user}:{self.password}@{self.hostname}/{self.dbname}?retryWrites=true&w=majority"
        self.connection = MongoClient(conn_string)
        return self
  
    def __exit__(self, exc_type, exc_value, exc_traceback): 
        self.connection.close() 


if __name__ == '__main__':
   pass 
