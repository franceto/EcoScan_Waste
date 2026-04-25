// ── DOM References ──
const dropZone      = document.getElementById('dropZone');
const fileInput     = document.getElementById('fileInput');
const filePreview   = document.getElementById('filePreview');
const previewImage  = document.getElementById('previewImage');
const removeBtn     = document.getElementById('removeBtn');
const infoName      = document.getElementById('infoName');
const infoSize      = document.getElementById('infoSize');
const infoFormat    = document.getElementById('infoFormat');
const infoDimension = document.getElementById('infoDimension');
const classifyBtn   = document.getElementById('classifyBtn');
const batchBtn      = document.getElementById('batchBtn');

const resultEmpty   = document.getElementById('resultEmpty');
const resultError   = document.getElementById('resultError');
const resultContent = document.getElementById('resultContent');
const resultImage   = document.getElementById('resultImage');
const resultPrediction = document.getElementById('resultPrediction');
const confFill      = document.getElementById('confFill');
const confPct       = document.getElementById('confPct');
const bar1Label     = document.getElementById('bar1Label');
const bar1Pct       = document.getElementById('bar1Pct');
const bar1Fill      = document.getElementById('bar1Fill');
const bar2Label     = document.getElementById('bar2Label');
const bar2Pct       = document.getElementById('bar2Pct');
const bar2Fill      = document.getElementById('bar2Fill');

const loadingOverlay = document.getElementById('loadingOverlay');
const chatFab        = document.getElementById('chatFab');
const chatModal      = document.getElementById('chatModal');
const closeChat      = document.getElementById('closeChat');
const chatInput      = document.getElementById('chatInput');
const sendChat       = document.getElementById('sendChat');
const chatMessages   = document.getElementById('chatMessages');

let selectedFile = null;

// ── File helpers ──
function showFileError(msg) {
    dropZone.style.display    = 'flex';
    filePreview.style.display = 'none';
    selectedFile = null;

    // Hiện thông báo lỗi trong drop zone rồi tự biến mất sau 3s
    const hint = dropZone.querySelector('.drop-hint');
    const orig  = hint.textContent;
    hint.style.color  = '#DC2626';
    hint.textContent  = msg;
    setTimeout(() => {
        hint.textContent = orig;
        hint.style.color = '';
    }, 3000);
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
}

function getFormat(file) {
    const ext = file.name.split('.').pop().toUpperCase();
    return ext || file.type.split('/')[1].toUpperCase();
}

// ── Drag & Drop ──
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file) handleFileSelect(file);
});

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFileSelect(file);
    fileInput.value = '';   // reset để chọn lại cùng file vẫn trigger change
});

// ── Handle file selection ──
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/gif'];
const MAX_SIZE_MB   = 10;

function handleFileSelect(file) {
    if (!ALLOWED_TYPES.includes(file.type)) {
        showFileError(`Chỉ chấp nhận ảnh (JPG, PNG, WEBP, BMP).\nFile "${file.name}" không hợp lệ.`);
        return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
        showFileError(`Ảnh vượt quá ${MAX_SIZE_MB}MB.\nFile "${file.name}" có dung lượng ${formatSize(file.size)}.`);
        return;
    }
    selectedFile = file;
    const reader = new FileReader();

    reader.onload = (e) => {
        const dataURL = e.target.result;
        previewImage.src = dataURL;

        // Extract pixel dimensions
        const img = new Image();
        img.onload = () => {
            infoDimension.textContent = `${img.naturalWidth} × ${img.naturalHeight} px`;
        };
        img.src = dataURL;

        infoName.textContent   = file.name;
        infoSize.textContent   = formatSize(file.size);
        infoFormat.textContent = getFormat(file);

        dropZone.style.display  = 'none';
        filePreview.style.display = 'flex';
        classifyBtn.disabled = false;
    };

    reader.readAsDataURL(file);
}

// ── Remove file ──
removeBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    dropZone.style.display    = 'flex';
    filePreview.style.display = 'none';
    classifyBtn.disabled = true;

    resultContent.style.display = 'none';
    resultError.style.display   = 'none';
    resultEmpty.style.display   = 'flex';

    // Reset bars
    confFill.style.width  = '0%';
    bar1Fill.style.width  = '0%';
    bar2Fill.style.width  = '0%';
});

document.getElementById('retryBtn').addEventListener('click', () => removeBtn.click());

// ── Classify ──
classifyBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    const formData = new FormData();
    formData.append('file', selectedFile);

    loadingOverlay.classList.add('active');

    try {
        const response = await fetch('/api/classify', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.error) {
            loadingOverlay.classList.remove('active');
            if (data.type === 'not_waste') {
                resultEmpty.style.display   = 'none';
                resultContent.style.display = 'none';
                resultError.style.display   = 'flex';
            } else {
                alert(data.error);
            }
            return;
        }

        const isOrganic = data.class === 'O';
        const predName  = isOrganic ? 'Rác hữu cơ' : 'Rác tái chế';
        const otherName = isOrganic ? 'Rác tái chế' : 'Rác hữu cơ';
        const conf1 = parseFloat(data.confidence).toFixed(1);
        const conf2 = (100 - parseFloat(data.confidence)).toFixed(1);

        // Show result image (same as uploaded)
        resultImage.src = previewImage.src;

        // Prediction label
        resultPrediction.textContent = predName;

        // Confidence bar
        confPct.textContent = `${conf1}%`;

        // Bar chart
        bar1Label.textContent = predName;
        bar1Pct.textContent   = `${conf1}%`;
        bar2Label.textContent = otherName;
        bar2Pct.textContent   = `${conf2}%`;

        bar1Fill.className = `bar-fill ${isOrganic ? 'organic' : 'recycle'}`;
        bar2Fill.className = `bar-fill ${isOrganic ? 'recycle' : 'organic'}`;

        // Description

        // Show results, hide empty state
        resultEmpty.style.display   = 'none';
        resultContent.style.display = 'flex';
        loadingOverlay.classList.remove('active');

        // Reset bar widths then animate (double RAF for reliable transition)
        confFill.style.width = '0%';
        bar1Fill.style.width = '0%';
        bar2Fill.style.width = '0%';

        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                confFill.style.width  = `${conf1}%`;
                bar1Fill.style.width  = `${conf1}%`;
                bar2Fill.style.width  = `${conf2}%`;
            });
        });

    } catch (err) {
        alert('Lỗi kết nối server!');
        loadingOverlay.classList.remove('active');
    }
});

// ── Batch classify ──
const batchInput = document.getElementById('batchInput');

batchBtn.addEventListener('click', () => batchInput.click());

batchInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    // Reuse loading overlay with custom text
    const loadingText = loadingOverlay.querySelector('p');
    const loadingSub  = loadingOverlay.querySelector('span');
    const origText    = loadingText.textContent;
    const origSub     = loadingSub.textContent;

    loadingText.textContent = 'Đang phân loại hàng loạt...';
    loadingSub.textContent  = 'Vui lòng chờ, đang xử lý từng ảnh';
    loadingOverlay.classList.add('active');

    try {
        const response = await fetch('/api/batch-classify', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            try {
                const err = await response.json();
                alert(err.error || err.detail || `Lỗi server (${response.status})`);
            } catch {
                alert(`Lỗi server (${response.status})`);
            }
            return;
        }

        // Trigger PDF download
        const blob = await response.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        const ts   = new Date().toISOString().slice(0,19).replace(/[-:T]/g, (c) => c === 'T' ? '_' : c);
        a.href     = url;
        a.download = `EcoScan_Report_${ts}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (err) {
        alert('Lỗi kết nối server!');
    } finally {
        loadingOverlay.classList.remove('active');
        loadingText.textContent = origText;
        loadingSub.textContent  = origSub;
        batchInput.value = '';
    }
});

// ── Chat ──
chatFab.addEventListener('click', () => {
    chatModal.classList.add('active');
    if (chatMessages.children.length === 0) {
        addMessage('Xin chào! Tôi là EcoScan AI Assistant. Tôi có thể giúp bạn tìm hiểu về phân loại rác thải. Bạn cần hỏi gì?', 'bot');
    }
});

closeChat.addEventListener('click', () => {
    chatModal.classList.remove('active');
});

sendChat.addEventListener('click', sendMessage);
chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
});

async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    chatInput.value = '';
    chatInput.style.height = 'auto';

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        addMessage(data.response, 'bot');

    } catch (err) {
        addMessage('Lỗi kết nối AI! Vui lòng thử lại.', 'bot');
    }
}

function addMessage(text, type) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
