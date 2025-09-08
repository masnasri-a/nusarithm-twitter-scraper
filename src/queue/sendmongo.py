import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Configuration for MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://nasri:UtyCantik12t@192.168.8.187:27017/')
DATABASE_NAME = 'tweeter'
COLLECTION_NAME = 'annotation'

def send_to_mongo(data, collection_name=COLLECTION_NAME):
    """
    Function to send data to MongoDB.
    
    :param data: Dictionary or list of dictionaries to insert
    :param collection_name: Name of the collection (default: scraped_tweets)
    """
    try:
        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[collection_name]
        
        if isinstance(data, list):
            result = collection.insert_many(data)
            print(f"Inserted {len(result.inserted_ids)} documents")
        else:
            result = collection.insert_one(data)
            print(f"Inserted document with ID: {result.inserted_id}")
        
        client.close()
    except ConnectionFailure as e:
        print(f"Failed to connect to MongoDB: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")