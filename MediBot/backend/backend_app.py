from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from api.auth_router import router as auth_router
from api.chat_router import router as chat_router

app = FastAPI(title="Modular MediAssist Backend")

# Enable CORS so if you DO run the UI locally later, it can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the modular routers
app.include_router(auth_router)
app.include_router(chat_router)

@app.get("/")
def health_check():
    return {"status": "ok", "message": "MediAssist Modular Backend is running."}