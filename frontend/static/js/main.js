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

function showFileError(msg) {
    dropZone.style.display    = 'flex';
    filePreview.style.display = 'none';
    selectedFile = null;

    const hint = dropZone.querySelector('.drop-hint');
    if (hint) {
        const orig = hint.textContent;
        hint.style.color = '#DC2626';
        hint.textContent = msg;
        setTimeout(() => {
            hint.textContent = orig;
            hint.style.color = '';
        }, 3000);
    }
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
    fileInput.value = '';
});

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/gif'];
const MAX_SIZE_MB = 10;

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

        const img = new Image();
        img.onload = () => {
            if (infoDimension) infoDimension.textContent = `${img.naturalWidth} × ${img.naturalHeight} px`;
        };
        img.src = dataURL;

        if (infoName) infoName.textContent = file.name;
        if (infoSize) infoSize.textContent = formatSize(file.size);
        if (infoFormat) infoFormat.textContent = getFormat(file);

        dropZone.style.display = 'none';
        filePreview.style.display = 'flex';
        classifyBtn.disabled = false;
    };

    reader.readAsDataURL(file);
}

removeBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    dropZone.style.display = 'flex';
    filePreview.style.display = 'none';
    classifyBtn.disabled = true;

    resultContent.style.display = 'none';
    if (resultError) resultError.style.display = 'none';
    resultEmpty.style.display = 'flex';

    if (confFill) confFill.style.width = '0%';
    if (bar1Fill) bar1Fill.style.width = '0%';
    if (bar2Fill) bar2Fill.style.width = '0%';
});

if (document.getElementById('retryBtn')) {
    document.getElementById('retryBtn').addEventListener('click', () => removeBtn.click());
}

classifyBtn.addEventListener('click', async () => {
    if (!selectedFile) {
        alert('⚠️ Vui lòng chọn ảnh trước!');
        return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    loadingOverlay.classList.add('active');

    try {
        const response = await fetch('/api/classify', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        loadingOverlay.classList.remove('active');

        if (response.status === 422) {
            alert(`⚠️ ${data.error}\nĐộ tin cậy: ${data.confidence}%\nCần tối thiểu: 58%`);
            return;
        }

        if (response.status !== 200) {
            alert('❌ ' + (data.error || 'Lỗi không xác định'));
            return;
        }

        const emoji = data.class === 'O' ? '+' : '+';
        const conf = data.confidence;

        if (resultImage) resultImage.src = previewImage.src;
        if (resultPrediction) resultPrediction.textContent = `${emoji} ${data.class_name}`;
        
        if (confFill) confFill.style.width = `${conf}%`;
        if (confPct) confPct.textContent = `${conf}%`;

        if (bar1Label) bar1Label.textContent = 'Rác hữu cơ';
        if (bar2Label) bar2Label.textContent = 'Rác tái chế';

        const organicProb = data.class === 'O' ? conf : (100 - conf);
        const recycleProb = data.class === 'R' ? conf : (100 - conf);

        if (bar1Fill) bar1Fill.style.width = `${organicProb}%`;
        if (bar1Pct) bar1Pct.textContent = `${organicProb.toFixed(1)}%`;
        
        if (bar2Fill) bar2Fill.style.width = `${recycleProb}%`;
        if (bar2Pct) bar2Pct.textContent = `${recycleProb.toFixed(1)}%`;

        resultEmpty.style.display = 'none';
        if (resultError) resultError.style.display = 'none';
        resultContent.style.display = 'flex';

    } catch (error) {
        loadingOverlay.classList.remove('active');
        alert('❌ Lỗi kết nối server!\n' + error.message);
        console.error('Classify error:', error);
    }
});

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
    sendChat.disabled = true;

    const botDiv = document.createElement('div');
    botDiv.className = 'message bot streaming';
    chatMessages.appendChild(botDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            const data = await response.json();
            botDiv.textContent = data.error || 'Lỗi kết nối AI!';
            botDiv.classList.remove('streaming');
            sendChat.disabled = false;
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            botDiv.textContent += decoder.decode(value, { stream: true });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }

    } catch (err) {
        botDiv.textContent = 'Lỗi kết nối AI! Vui lòng thử lại.';
    } finally {
        botDiv.classList.remove('streaming');
        sendChat.disabled = false;
    }
}

function addMessage(text, type) {
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = text;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}