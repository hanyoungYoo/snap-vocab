let saveButton = null;

document.addEventListener('mouseup', () => {
  const selection = window.getSelection();
  const text = selection.toString().trim();

  if (text.length < 10) {
    removeSaveButton();
    return;
  }
  showSaveButton(selection, text);
});

document.addEventListener('mousedown', (e) => {
  if (saveButton && !saveButton.contains(e.target)) {
    removeSaveButton();
  }
});

function showSaveButton(selection, text) {
  removeSaveButton();
  const range = selection.getRangeAt(0);
  const rect = range.getBoundingClientRect();

  saveButton = document.createElement('button');
  saveButton.textContent = '📚 저장';
  saveButton.style.cssText = `
    position: fixed;
    top: ${rect.top - 40}px;
    left: ${rect.left}px;
    z-index: 2147483647;
    padding: 6px 12px;
    background: #4F46E5;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font: 13px system-ui, sans-serif;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
  `;
  saveButton.addEventListener('mousedown', (e) => e.stopPropagation());
  saveButton.addEventListener('click', () => saveText(text));
  document.body.appendChild(saveButton);
}

async function saveText(text) {
  saveButton.textContent = '저장 중…';
  saveButton.disabled = true;

  const { apiUrl, apiKey } = await chrome.storage.local.get(['apiUrl', 'apiKey']);
  if (!apiUrl || !apiKey) {
    saveButton.textContent = '⚠ 확장 popup에서 API 설정';
    setTimeout(removeSaveButton, 2500);
    return;
  }

  try {
    const res = await fetch(`${apiUrl.replace(/\/$/, '')}/api/cards`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.saved?.length > 0) {
      saveButton.textContent = `✅ ${data.saved.length}개 저장`;
    } else if (data.duplicates?.length > 0) {
      saveButton.textContent = '이미 학습 중';
    } else {
      saveButton.textContent = '추출된 표현 없음';
    }
  } catch (e) {
    saveButton.textContent = `❌ ${e.message}`;
  }
  setTimeout(removeSaveButton, 2500);
}

function removeSaveButton() {
  if (saveButton) {
    saveButton.remove();
    saveButton = null;
  }
}
