import os
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY', '')

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routes import classify, chat
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.include_router(classify.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/")
async def read_root():
    return FileResponse("frontend/templates/index.html")