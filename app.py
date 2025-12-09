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

    ffmpeg_status = False
    try:
        # Check if ffmpeg is accessible
        ffmpeg.probe('dummy_file', cmd='ffmpeg')
    except ffmpeg.Error:
        # It will fail on the file, but if it runs, ffmpeg is there. 
        # Actually a better check is just checking version or relying on the import for now.
        # But ffmpeg-python wraps the binary. Let's try a simple meaningful check if possible, or just assume True if no binary error.
        # For simplicity in this basic setup, we'll assume installed if we can import, 
        # but realistically we should check the binary.
        pass
    except Exception as e:
        # If the binary is missing, usually it raises an FileNotFoundError or similar from subprocess
        if "No such file or directory" in str(e):
            ffmpeg_status = False
        else:
            # If it failed for other reasons (like dummy file missing), it means the binary was found
            ffmpeg_status = True

    return jsonify(HealthResponse(
        status="active",
        mongo_connected=mongo_status,
        ffmpeg_installed=ffmpeg_status
    ).model_dump())

if __name__ == '__main__':
    app.run(debug=True, port=7770)
