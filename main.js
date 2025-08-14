function copyText(btn){
  const text = btn.getAttribute("data-text");
  navigator.clipboard.writeText(text).then(()=>{
    showToast("E-Mail-Text kopiert ✅");
  });
}
function showToast(msg){
  const toastEl = document.getElementById('appToast');
  const toastBody = document.getElementById('toastBody');
  toastBody.textContent = msg;
  const toast = new bootstrap.Toast(toastEl);
  toast.show();
}
