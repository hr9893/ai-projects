import os
from dotenv import load_dotenv

load_dotenv()

class Settings:

    TYPESAFE_API_KEY: str = os.getenv("JEV_API_KEY", "")
    DEEP_SEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL","")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    def __init__(self):
        if self.TYPESAFE_API_KEY:
            os.environ["TYPESAFE_API_KEY"] = self.TYPESAFE_API_KEY
        if self.DEEP_SEEK_MODEL:
            os.environ["DEEP_SEEK_MODEL"] = self.DEEP_SEEK_MODEL
        if self.GROQ_API_KEY:
            os.environ["GROQ_API_KEY"] = self.GROQ_API_KEY

settings = Settings()
