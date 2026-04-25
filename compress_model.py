import torch
import torch.nn as nn
from torchvision import models

MODEL_PATH = "backend/models/resnet50_waste.pth"
OUTPUT_PATH = "backend/models/resnet50_waste_compressed.pth"

checkpoint = torch.load(MODEL_PATH, map_location='cpu')

model = models.resnet50(weights=None)
model.fc = nn.Sequential(nn.Dropout(0.5), nn.Linear(model.fc.in_features, 2))
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

model_int8 = torch.quantization.quantize_dynamic(model, {nn.Linear}, dtype=torch.qint8)

torch.save({
    'model_state_dict': model_int8.state_dict(),
    'class_to_idx': checkpoint['class_to_idx']
}, OUTPUT_PATH)

print(f"Model compressed: {OUTPUT_PATH}")