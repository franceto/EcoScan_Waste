import torch
import torch.nn as nn
import torchvision.models as models
from backend.config import MODEL_PATH

class WasteClassifier:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        checkpoint = torch.load(MODEL_PATH, map_location=self.device)
        
        self.model = models.resnet50(weights=None)
        
        in_features = self.model.fc.in_features
        self.model.fc = nn.Sequential(
            nn.Identity(),
            nn.Linear(in_features, 2)
        )
        
        state_dict = checkpoint["model_state_dict"]
        filtered_state_dict = {k: v for k, v in state_dict.items() 
                              if not any(x in k for x in ['scale', 'zero_point', '_packed_params'])}
        
        self.model.load_state_dict(filtered_state_dict, strict=False)
        self.model.to(self.device)
        self.model.eval()
        
        self.class_to_idx = checkpoint["class_to_idx"]
        self.idx_to_class = {v: k for k, v in self.class_to_idx.items()}
        
    def predict(self, image_tensor):
        with torch.no_grad():
            image_tensor = image_tensor.to(self.device)
            outputs = self.model(image_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)
            confidence, predicted = torch.max(probabilities, 1)
            
            pred_idx = predicted.item()
            pred_class = self.idx_to_class[pred_idx]
            
            return pred_class, round(confidence.item() * 100, 2)

classifier = WasteClassifier()