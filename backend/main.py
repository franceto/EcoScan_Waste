from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.routes import classify, chat
import uvicorn
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

app = FastAPI()

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(classify.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

@app.get("/")
async def read_root():
    return FileResponse("frontend/templates/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)