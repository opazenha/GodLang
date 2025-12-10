from pydantic import BaseModel

class Message(BaseModel):
    transcripT: str
    translation: str