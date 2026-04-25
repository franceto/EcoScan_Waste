from PIL import Image
import torch
from torchvision import transforms
import io

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def process_image(file_bytes):
    image = Image.open(io.BytesIO(file_bytes)).convert('RGB')
    return transform(image).unsqueeze(0)