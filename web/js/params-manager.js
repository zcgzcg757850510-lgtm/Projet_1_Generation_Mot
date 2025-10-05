// 参数管理和预览效果模块
// 处理参数重置、预览卡片悬停效果等功能

// 参数重置功能
function resetParams() {
  // 清空所有与参数相关的 cookie，并重置表单显示为默认值
  const names = ['disable_start','start_ori','start_angle','start_frac','start_trim_on','start_trim','end_trim_on','end_trim','keep_start','keep_end','chaikin','smooth','resample','tilt','tilt_k','tilt_range','scale','scale_range','pcv','pcjitter'];
  names.forEach(n=>{ document.cookie = n+'=; Max-Age=0; path=/'; });
  const form=document.querySelector('form');
  if(form){
    form.reset();
    // 针对自定义控件：手动还原默认（与后端默认一致）
    const setVal=(sel,v)=>{ const el=form.querySelector(sel); if(el){ if(el.type==='checkbox'){ el.checked=!!v; } else { el.value = v; } } };
    setVal('input[name="disable_start"]', '0');
    setVal('input[name="start_ori"]', '0');
    setVal('input[name="start_angle"]', '0');
    setVal('input[name="start_frac"]', '0');
    setVal('input[name="start_trim_on"]', '0');
    setVal('input[name="start_trim"]', '0');
    setVal('input[name="end_trim_on"]', '0');
    setVal('input[name="end_trim"]', '0');
    setVal('input[name="keep_start"]', '0');
    setVal('input[name="keep_end"]', '0');
    setVal('input[name="chaikin"]', '0');
    setVal('input[name="smooth"]', '0');
    setVal('input[name="resample"]', '0');
    setVal('input[name="tilt"]', '0');
    setVal('input[name="tilt_k"]', '0');
    setVal('input[name="tilt_range"]', '0');
    setVal('input[name="scale"]', '0');
    setVal('input[name="scale_range"]', '0');
    setVal('input[name="pcv"]', '0');
    setVal('input[name="pcjitter"]', '0');
  }
  
  // 使用toast提示而不是alert
  if (typeof toastManager !== 'undefined') {
    toastManager.show('params.reset.success');
  } else {
    alert('参数已重置为默认。');
  }
}

// Preview cards hover effect - following reference implementation
let previewCardsInitialized = false;

function initPreviewCardsEffect() {
  const previewContainer = document.querySelector('.preview-cards');
  const cardsInner = document.querySelector('.cards__inner');
  const previewCards = Array.from(document.querySelectorAll('.preview-card'));
  const overlay = document.querySelector('.preview-overlay');
  
  if (!previewContainer || !overlay || previewCardsInitialized) return;
  
  // Clear existing overlay content
  overlay.innerHTML = '';
  
  // Apply overlay mask on mouse move
  const applyOverlayMask = (e) => {
    const rect = previewContainer.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    overlay.style.setProperty('--opacity', '1');
    overlay.style.setProperty('--x', x + 'px');
    overlay.style.setProperty('--y', y + 'px');
  };
  
  // Create overlay card - only structure, no content
  const initOverlayCard = (cardEl) => {
    const overlayCard = document.createElement('div');
    overlayCard.classList.add('cell');
    // Copy only the structure classes, not the content
    if (cardEl.classList.contains('preview-card-a')) overlayCard.classList.add('preview-card-a');
    if (cardEl.classList.contains('preview-card-b')) overlayCard.classList.add('preview-card-b');
    if (cardEl.classList.contains('preview-card-c')) overlayCard.classList.add('preview-card-c');
    if (cardEl.classList.contains('preview-card-d1')) overlayCard.classList.add('preview-card-d1');
    if (cardEl.classList.contains('preview-card-d2')) overlayCard.classList.add('preview-card-d2');
    overlay.appendChild(overlayCard);
  };
  
  // Initialize overlay cards
  previewCards.forEach(initOverlayCard);
  
  // Add global mouse move listener
  previewContainer.addEventListener('pointermove', applyOverlayMask);
  
  // Hide overlay when mouse leaves
  previewContainer.addEventListener('mouseleave', () => {
    overlay.style.setProperty('--opacity', '0');
  });
  
  previewCardsInitialized = true;
}

// 创建参数管理器对象
const paramsManager = {
  resetParams,
  initPreviewCardsEffect
};

// 导出全局函数和对象
window.resetParams = resetParams;
window.initPreviewCardsEffect = initPreviewCardsEffect;
window.paramsManager = paramsManager;

// 在DOM加载完成后初始化预览效果
document.addEventListener('DOMContentLoaded', () => {
  initPreviewCardsEffect();
});

console.log('✅ 参数管理模块已加载');
