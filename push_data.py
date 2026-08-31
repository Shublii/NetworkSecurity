# # 



# import os
# import sys
# import json

# from dotenv import load_dotenv

# load_dotenv()

# MONGO_DB_URL = os.getenv("MONGO_DB_URL")
# print(MONGO_DB_URL)

# ## Certifi is a Python package that provides up-to-date CA (Certificate Authority)
# ## certificates so HTTPS connections can be verified securely.
# import certifi
# ca = certifi.where()

# import pandas as pd
# import numpy as np
# import pymongo
# from networksecurity.exception.exception import NetworkSecurityException
# from networksecurity.logging.logger import logging


# class NetworkDataExtract():
#     def __init__(self):
#         try:
#             pass
#         except Exception as e:
#             raise NetworkSecurityException(e, sys)

#     def csv_to_json_convertor(self, file_path) -> json:  # Csv to Json converter function
#         try:
#             data = pd.read_csv(file_path)
#             data.reset_index(drop=True, inplace=True)
#             records = list(json.loads(data.T.to_json()).values())
#             return records
#         except Exception as e:
#             raise NetworkSecurityException(e, sys)

#     ##udemy
#     def insert_data_to_mongodb(self, records, database, collection):
#         try:
#             self.records = records

#             # Create the Mongo client first, then derive database/collection from it
#             self.mongo_client = pymongo.MongoClient(MONGO_DB_URL, tlsCAFile=ca)
#             self.database = self.mongo_client[database]
#             self.collection = self.database[collection]

#             self.collection.insert_many(self.records)
#             return len(self.records)
#         except Exception as e:
#             raise NetworkSecurityException(e, sys)

    


# if __name__ == "__main__":
#     FILE_PATH = os.path.join("Network_Data", "phisingData.csv")
#     DATABASE = "SHUBHAMAI"
#     Collection = "NetworkData"

#     networkobj = NetworkDataExtract()
#     records = networkobj.csv_to_json_convertor(file_path=FILE_PATH)
#     print(records)

#     no_of_records = networkobj.insert_data_to_mongodb(
#         records=records, database=DATABASE, collection=Collection
#     )
#     print(no_of_records)





import os
import sys
import json

from dotenv import load_dotenv

load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")

# Certifi provides CA certificates for secure SSL/TLS connections
import certifi

ca = certifi.where()

import pandas as pd
import pymongo

from networksecurity.exception.exception import NetworkSecurityException
from networksecurity.logging.logger import logging


class NetworkDataExtract():

    def __init__(self):
        try:
            pass

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # CSV to JSON converter
    def csv_to_json_convertor(self, file_path) -> json:

        try:
            data = pd.read_csv(file_path)

            data.reset_index(drop=True, inplace=True)

            records = list(
                json.loads(data.T.to_json()).values()
            )

            return records

        except Exception as e:
            raise NetworkSecurityException(e, sys)

    # Insert data into MongoDB
    def insert_data_to_mongodb(self, records, database, collection):

        try:

            self.records = records

            # Create MongoDB client
            self.mongo_client = pymongo.MongoClient(
                MONGO_DB_URL,
                tls=True,
                tlsCAFile=ca,
                serverSelectionTimeoutMS=30000
            )

            # Test MongoDB connection
            self.mongo_client.admin.command("ping")

            print("MongoDB connection successful!")

            # Select database
            self.database = self.mongo_client[database]

            # Select collection
            self.collection = self.database[collection]

            # Insert records
            self.collection.insert_many(self.records)

            print("Data inserted successfully!")

            return len(self.records)

        except Exception as e:
            raise NetworkSecurityException(e, sys)


if __name__ == "__main__":

    FILE_PATH = os.path.join(
        "Network_Data",
        "phisingData.csv"
    )

    DATABASE = "SHUBHAMAI"

    Collection = "NetworkData"

    networkobj = NetworkDataExtract()

    # Convert CSV to JSON
    records = networkobj.csv_to_json_convertor(
        file_path=FILE_PATH
    )

    print("CSV converted to JSON successfully!")

    # Insert data into MongoDB
    no_of_records = networkobj.insert_data_to_mongodb(
        records=records,
        database=DATABASE,
        collection=Collection
    )

    print("Number of records inserted:", no_of_records)

