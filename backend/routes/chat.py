from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from groq import Groq
from backend.config import GROQ_API_KEY

router = APIRouter()
client = Groq(api_key=GROQ_API_KEY)

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là trợ lý AI của ứng dụng EcoScan — ứng dụng phân loại rác thải sử dụng mô hình ResNet50.\n\n"

                        "THÔNG TIN CHÍNH XÁC VỀ ECOSCAN:\n"
                        "- Mô hình: ResNet50, huấn luyện trên ~25.100 ảnh\n"
                        "- Độ chính xác: 97% trên tập kiểm thử\n"
                        "- Phân loại 2 nhóm: Rác hữu cơ (O) và Rác tái chế (R)\n"
                        "- Rác hữu cơ: thức ăn thừa, vỏ trái cây, rau củ, xương, lá cây...\n"
                        "- Rác tái chế: nhựa, giấy, kim loại, thủy tinh, hộp carton, lon...\n\n"

                        "NGUYÊN TẮC TRẢ LỜI:\n"
                        "1. Chỉ trả lời các câu hỏi liên quan đến: phân loại rác, cách xử lý rác, tái chế, ứng dụng EcoScan\n"
                        "2. Nếu câu hỏi nằm ngoài phạm vi trên, hãy nói rõ: 'Tôi chỉ hỗ trợ về phân loại rác thải.'\n"
                        "3. KHÔNG bịa đặt thông tin, số liệu, hay sự kiện không chắc chắn\n"
                        "4. Nếu không biết chắc, hãy nói 'Tôi không có thông tin chính xác về điều này.'\n"
                        "5. Trả lời ngắn gọn, rõ ràng, bằng tiếng Việt\n"
                        "6. KHÔNG thêm thông tin ngoài những gì được hỏi"
                    )
                },
                {
                    "role": "user",
                    "content": request.message
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        return JSONResponse({
            "response": completion.choices[0].message.content
        })
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)