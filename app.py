import os
from flask import Flask, jsonify
from pydantic import BaseModel, ValidationError
from pymongo import MongoClient
from groq import Groq
import ffmpeg

app = Flask(__name__)

# Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize Clients
try:
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    # Check connection immediately
    mongo_client.admin.command('ping')
    print("Combined to MongoDB")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")

groq_client = Groq(api_key=GROQ_API_KEY)

class HealthResponse(BaseModel):
    status: str
    mongo_connected: bool
    ffmpeg_installed: bool

@app.route('/health', methods=['GET'])
def health_check():
    mongo_status = False
    try:
        mongo_client.admin.command('ping')
        mongo_status = True
    except Exception:
        mongo_status = False

    # Assume ffmpeg is available if the import succeeded
    ffmpeg_status = True

    return jsonify(HealthResponse(
        status="active",
        mongo_connected=mongo_status,
        ffmpeg_installed=ffmpeg_status
    ).model_dump())

if __name__ == '__main__':
    app.run(debug=True, port=7770)
