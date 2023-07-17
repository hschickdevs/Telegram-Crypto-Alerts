from dotenv import find_dotenv, load_dotenv
from os import getenv

from pymongo import MongoClient


class MongoDBConnection(MongoClient):
    """LOADS CONNECTION VARIABLES FROM .ENV FILE - STORE CREDENTIALS THERE"""
    def __init__(self):
        envpath = find_dotenv(raise_error_if_not_found=True, usecwd=True)
        load_dotenv(dotenv_path=envpath)

        cxn_string = getenv("MONGODB_CONNECTION_STRING")
        if cxn_string is None:
            raise ValueError(f"Missing MongoDB connection string environment variable (MONGODB_CONNECTION_STRING)")
        database = getenv("MONGODB_DATABASE")
        if database is None:
            raise ValueError(f"Missing MongoDB database environment variable (MONGODB_DATABASE)")
        collection = getenv("MONGODB_COLLECTION")
        if collection is None:
            raise ValueError(f"Missing MongoDB database collection environment variable (MONGODB_COLLECTION)")

        super().__init__(cxn_string)
        self.uri = cxn_string
        self.database = self[database]
        self.collection = self.database[collection]

    def ping(self):
        self.admin.command('ping')
        print(f"Pinged your deployment. You successfully connected to MongoDB at {self.uri}!")
