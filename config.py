import os
from pymongo import MongoClient
from groq import Groq
import ffmpeg

def init_clients():
    # Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    # Initialize MongoDB Client
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        # Check connection immediately
        mongo_client.admin.command('ping')
        print("Connected to MongoDB")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        mongo_client = None
    
    # Initialize Groq Client
    groq_client = Groq(api_key=GROQ_API_KEY)
    
    return mongo_client, groq_client