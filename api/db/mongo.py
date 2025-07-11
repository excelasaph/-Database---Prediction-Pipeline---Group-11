from pymongo import MongoClient

MONGO_CONN_STR = "mongodb+srv://excel:LNS0e1g0eA8e7xMq@drug-cluster.cut2esi.mongodb.net/?retryWrites=true&w=majority&appName=drug-cluster"

def get_mongo_db():
    client = MongoClient(MONGO_CONN_STR)
    return client["drug-db"]