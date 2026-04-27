@"
# 📥 Hướng dẫn tải Model ResNet50

## Bước 1: Tải file model

Model đã được train sẵn với độ chính xác 97%.

**Link tải:** [Google Drive - ResNet50 Waste Model](https://drive.google.com/file/d/1rArMB9hnJTXCrnKfyNyeQ5fE8ZLh-3i6/view)

**File:** \`resnet50_waste.pth\` (~94MB)

## Bước 2: Đặt file vào đúng vị trí

Sau khi tải xong, đặt file vào thư mục:

\`\`\`
backend/models/resnet50_waste.pth
\`\`\`

## Bước 3: Kiểm tra

Chạy lệnh sau để kiểm tra model đã load thành công:

\`\`\`bash
python -c \"from backend.utils.model_loader import classifier; print('Model loaded successfully!')\"
\`\`\`

## Thông tin Model

- **Architecture:** ResNet50
- **Input Size:** 224x224
- **Classes:** 2 (Organic, Recyclable)
- **Accuracy:** 97%
- **File Size:** ~94MB
- **Format:** PyTorch (.pth)

## Nếu gặp lỗi

1. Đảm bảo đã cài đặt PyTorch: \`pip install torch torchvision\`
2. Kiểm tra đường dẫn file chính xác
3. Kiểm tra file không bị corrupt (download lại nếu cần)
"@ | Out-File -FilePath MODEL_DOWNLOAD.md -Encoding utf8