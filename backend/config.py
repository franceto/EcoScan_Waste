import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL_PATH = "backend/models/resnet50_waste_compressed.pth"
UPLOAD_FOLDER = "uploads"

CLASS_DESCRIPTIONS = {
    "O": "Rác hữu cơ bao gồm thực phẩm thừa, vỏ trái cây, rau củ, lá cây. Nên phân hủy sinh học hoặc làm phân compost.",
    "R": "Rác tái chế bao gồm giấy, nhựa, kim loại, thủy tinh. Có thể tái chế để giảm thiểu rác thải và bảo vệ môi trường."
}

CLASS_NAMES = {
    "O": "Rác hữu cơ",
    "R": "Rác tái chế"
}