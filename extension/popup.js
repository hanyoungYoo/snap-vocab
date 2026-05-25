const $ = (id) => document.getElementById(id);

(async () => {
  const { apiUrl = '', apiKey = '' } = await chrome.storage.local.get(['apiUrl', 'apiKey']);
  $('apiUrl').value = apiUrl;
  $('apiKey').value = apiKey;
})();

$('save').addEventListener('click', async () => {
  await chrome.storage.local.set({
    apiUrl: $('apiUrl').value.trim(),
    apiKey: $('apiKey').value.trim(),
  });
  $('status').textContent = '저장됨';
  setTimeout(() => ($('status').textContent = ''), 1500);
});
