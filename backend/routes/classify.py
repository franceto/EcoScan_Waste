from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse
from backend.utils.model_loader import classifier
from backend.utils.image_processor import process_image
from backend.config import CLASS_DESCRIPTIONS, CLASS_NAMES

router = APIRouter()

# Ngưỡng tối thiểu để chấp nhận kết quả phân loại
CONFIDENCE_THRESHOLD = 70.0


@router.post("/classify")
async def classify_image(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        image_tensor = process_image(contents)

        predicted_class, confidence = classifier.predict(image_tensor)

        if confidence < CONFIDENCE_THRESHOLD:
            return JSONResponse({
                "type":    "not_waste",
                "error":   "Không nhận diện được rác thải",
                "confidence": confidence
            }, status_code=422)

        return JSONResponse({
            "class":       predicted_class,
            "class_name":  CLASS_NAMES.get(predicted_class, predicted_class),
            "confidence":  confidence,
            "description": CLASS_DESCRIPTIONS.get(predicted_class, "")
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)