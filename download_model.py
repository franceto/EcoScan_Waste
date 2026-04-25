import gdown
import os

MODEL_PATH = "backend/models/resnet50_waste_compressed.pth"
GDRIVE_URL = "https://drive.google.com/uc?id=1rArMB9hnJTXCrnKfyNyeQ5fE8ZLh-3i6"

if not os.path.exists(MODEL_PATH):
    os.makedirs("backend/models", exist_ok=True)
    print("Downloading model from Google Drive...")
    gdown.download(GDRIVE_URL, MODEL_PATH, quiet=False)
    print("Model downloaded successfully!")
else:
    print("Model already exists")