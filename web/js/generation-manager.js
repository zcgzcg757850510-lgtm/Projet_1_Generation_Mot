// 生成管理模块
// 处理字符生成、对比功能、图像模态框等核心生成相关功能

// 模态框缩放相关变量
let _modalZoom = 1;
let _modalZoomMin = 0.1;
let _modalZoomMax = 5;

// 画布绘制相关变量
let _penEnabled = false;
let _isDrawing = false;
let _ctx = null; 
let _cnv = null; 
let _img = null; 
let _zoomWrap = null; 
let _wrapRect = null;

// 应用模态框缩放
function _applyModalZoom() {
  const img = document.getElementById('modalImg');
  const img1 = document.getElementById('modalImg1');
  if (img) img.style.transform = `scale(${_modalZoom})`;
  if (img1) img1.style.transform = `scale(${_modalZoom})`;
  _syncCanvasSize();
}

// 打开缩放模态框
function openZoomModal(url) {
  const m = document.getElementById('zoomModal');
  const img = document.getElementById('modalImg');
  const zWrap = document.getElementById('zCmpWrap');
  const vp = document.getElementById('zoomContent');
  if (!m || !img || !zWrap) return;
  img.style.display = 'block';
  zWrap.style.display = 'none';
  img.src = url;
  _modalZoom = 1; 
  _applyModalZoom();
  if (vp) { vp.scrollTo(0, 0); }
  m.classList.remove('hidden');
  _setupCanvas();
}

// 简单的图片对比模态框函数
function openImageCompareModal(primaryImg, compareImg) {
  const modal = document.getElementById('zoomModal');
  const singleImg = document.getElementById('modalImg');
  const compareWrap = document.getElementById('zCmpWrap');
  const baseImg = document.getElementById('modalImg0');
  const overlayImg = document.getElementById('modalImg1');
  const handle = document.getElementById('zCmpHandle');
  
  if (!modal || !singleImg || !compareWrap || !baseImg || !overlayImg || !handle) return;
  
  // 重置缩放
  _modalZoom = 1;
  _applyModalZoom();
  
  // 设置对比模式
  singleImg.style.display = 'none';
  compareWrap.style.display = 'block';
  
  // 直接设置图片
  baseImg.src = primaryImg;
  baseImg.style.display = 'block';
  overlayImg.src = compareImg;
  overlayImg.style.display = 'block';
  handle.style.display = 'block';
  
  // 显示模态框
  modal.classList.remove('hidden');
  _setupCanvas();
  
  // 立即设置分割位置到左侧
  setComparePosition(0.2);
  bindCompareEvents();
}

// 设置对比分割位置
function setComparePosition(percentage) {
  const overlayImg = document.getElementById('modalImg1');
  const handle = document.getElementById('zCmpHandle');
  
  if (!overlayImg || !handle) return;
  
  handle.style.display = 'block';
  handle.style.left = `${percentage * 100}%`;
  overlayImg.style.clipPath = `inset(0 ${100 - percentage * 100}% 0 0)`;
}

// 绑定对比拖拽事件
function bindCompareEvents() {
  const wrap = document.getElementById('zCmpWrap');
  const handle = document.getElementById('zCmpHandle');
  
  if (!wrap || !handle) return;
  
  let isDragging = false;
  
  const handleMouseDown = (e) => {
    isDragging = true;
    e.preventDefault();
  };
  
  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    const rect = wrap.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    
    setComparePosition(percentage);
  };
  
  const handleMouseUp = () => {
    isDragging = false;
  };
  
  // 移除旧的事件监听器
  handle.removeEventListener('mousedown', handleMouseDown);
  wrap.removeEventListener('mousedown', handleMouseDown);
  document.removeEventListener('mousemove', handleMouseMove);
  document.removeEventListener('mouseup', handleMouseUp);
  
  // 添加新的事件监听器
  handle.addEventListener('mousedown', handleMouseDown);
  wrap.addEventListener('mousedown', (e) => {
    const rect = wrap.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = Math.max(0, Math.min(1, x / rect.width));
    setComparePosition(percentage);
    isDragging = true;
    e.preventDefault();
  });
  document.addEventListener('mousemove', handleMouseMove);
  document.addEventListener('mouseup', handleMouseUp);
}

// 关闭缩放模态框
function closeZoomModal() { 
  const m = document.getElementById('zoomModal'); 
  if (m) { m.classList.add('hidden'); } 
}

// 初始化图像模态框
function initImageModal() {
  const imgs = document.querySelectorAll('#four img');
  
  imgs.forEach(img => {
    img.style.cursor = 'zoom-in';
    
    // 移除旧的事件监听器
    img.removeEventListener('click', img._clickHandler);
    
    // 创建新的点击处理器
    img._clickHandler = () => {
      if (!img.src) return;
      
      // 寻找对比图片
      const allImages = ['imgA', 'imgB', 'imgC', 'imgD0', 'imgD1', 'imgD2'];
      let compareImg = '';
      
      for (let imgId of allImages) {
        if (imgId !== img.id) {
          const element = document.getElementById(imgId);
          if (element && element.src && element.src.trim() !== '') {
            compareImg = element.src;
            break;
          }
        }
      }
      
      if (compareImg) {
        openImageCompareModal(img.src, compareImg);
      }
    };
    
    // 绑定新的事件监听器
    img.addEventListener('click', img._clickHandler);
  });
  
  _setupCanvas();
  const wrap = document.getElementById('zoomContent');
  const ro2 = new ResizeObserver(() => _syncCanvasSize()); 
  if (wrap) { ro2.observe(wrap); }
}

// 设置画布
function _setupCanvas() {
  _cnv = document.getElementById('modalCanvas');
  _img = document.getElementById('modalImg');
  _zoomWrap = document.getElementById('zoomContent');
  if (!_cnv || !_img || !_zoomWrap) return;
  const resize = () => { _syncCanvasSize(); };
  // 每次打开/缩放后更新一次
  const ro = new ResizeObserver(resize);
  ro.observe(_img);
  // 将 canvas 放到 img 之上对齐
  _cnv.style.left = '0px';
  _cnv.style.top = '0px';
  _ctx = _cnv.getContext('2d');
  _ctx.lineCap = 'round'; 
  _ctx.lineJoin = 'round'; 
  _ctx.lineWidth = 3; 
  _ctx.strokeStyle = '#ff0066';
  // 事件
  const toLocal = (e) => {
    // 将鼠标位置映射到未缩放的画布坐标系
    const wrap = document.getElementById('zoomContent');
    const rect = wrap ? wrap.getBoundingClientRect() : _cnv.getBoundingClientRect();
    const x = (e.clientX - rect.left) / _modalZoom; 
    const y = (e.clientY - rect.top) / _modalZoom; 
    return { x, y };
  };
  const down = (e) => { if (!_penEnabled) return; _isDrawing = true; const p = toLocal(e); _ctx.beginPath(); _ctx.moveTo(p.x, p.y); e.preventDefault(); };
  const move = (e) => { if (!_penEnabled || !_isDrawing) return; const p = toLocal(e); _ctx.lineTo(p.x, p.y); _ctx.stroke(); e.preventDefault(); };
  const up = () => { if (!_penEnabled) return; _isDrawing = false; };
  _cnv.addEventListener('mousedown', down);
  _cnv.addEventListener('mousemove', move);
  window.addEventListener('mouseup', up);
}

// 清除画布
function _clearCanvas() { 
  if (_ctx && _cnv) { _ctx.clearRect(0, 0, _cnv.width, _cnv.height); } 
}

// 同步画布大小
function _syncCanvasSize() {
  if (!_cnv || !_img) return;
  const r = _img.getBoundingClientRect();
  const w = Math.max(1, Math.round(r.width));
  const h = Math.max(1, Math.round(r.height));
  if (_cnv.width !== w) _cnv.width = w;
  if (_cnv.height !== h) _cnv.height = h;
  _cnv.style.width = w + 'px';
  _cnv.style.height = h + 'px';
}

// 注意：genOnce函数已移至generation-service.js中统一管理
// 此处不再重复定义，避免函数覆盖导致的问题

// 对比分割功能
function cmpSetSplit(t) {
  const img = document.getElementById('imgD1');
  const wrap = document.getElementById('cmpWrap');
  const bar = document.getElementById('cmpHandle');
  if (!img || !wrap || !bar) return;
  const w = wrap.clientWidth || 1;
  const x = Math.max(0, Math.min(1, t)) * w;
  img.style.clipPath = `inset(0 ${Math.max(0, w - x)}px 0 0)`;
  bar.style.left = x + 'px';
}

function cmpBind() {
  const wrap = document.getElementById('cmpWrap');
  const bar = document.getElementById('cmpHandle');
  if (!wrap || !bar) return;
  let dragging = false;
  const onDown = (e) => { dragging = true; e.preventDefault(); };
  const onMove = (e) => { if (!dragging) return; const rect = wrap.getBoundingClientRect(); const x = (e.clientX - rect.left); cmpSetSplit(x / Math.max(1, rect.width)); };
  const onUp = () => { dragging = false; };
  bar.addEventListener('mousedown', onDown);
  window.addEventListener('mousemove', onMove);
  window.addEventListener('mouseup', onUp);
  // 响应式
  const ro = new ResizeObserver(() => cmpSetSplit(parseFloat((bar.style.left || '0').replace('px', '')) / Math.max(1, wrap.clientWidth))); 
  ro.observe(wrap);
}

// 渲染角度面板
function renderAnglesPanel(arr) {
  const box = document.getElementById('anglesBox'); 
  if (!box) return;
  // 临时用于显示D2生成结果
  box.innerHTML = '<div style="color: var(--muted); font-size: 12px;">等待D2生成结果...</div>';
  return;
}

// 导出全局函数
window.openZoomModal = openZoomModal;
window.closeZoomModal = closeZoomModal;
window.initImageModal = initImageModal;
// window.genOnce = genOnce; // 已移至generation-service.js统一管理
// 移除已删除的函数导出
window.renderAnglesPanel = renderAnglesPanel;

// 初始化剩余功能
function initRemainingFunctionality() {
  if (typeof bindAutoSave !== 'undefined') {
    bindAutoSave();
  }
  initImageModal();
}

// 在DOM加载完成后初始化图像模态框
document.addEventListener('DOMContentLoaded', () => {
  initImageModal();
});

// 在窗口加载完成后初始化剩余功能
window.addEventListener('load', function() {
  initRemainingFunctionality();
});

// 尝试直接文件路径加载功能
async function tryDirectFileLoad(char) {
  console.log('🔍 尝试直接文件路径加载:', char);
  
  const imgA = document.getElementById('imgA');
  const imgB = document.getElementById('imgB');
  const imgC = document.getElementById('imgC');
  const imgD1 = document.getElementById('imgD1');
  
  const withTs = (u) => u + '?ts=' + Date.now();
  
  // Try different paths for each image type
  const testPaths = {
    A: [
      `/A_outlines/${char}.svg`,
      `/A_outlines/${char}_outline.svg`,
      `/output/A_outlines/${char}.svg`
    ],
    B: [
      `/D2_median_fill/${char}.svg`,
      `/D2_median_fill/${char}_filled.svg`,
      `/output/D2_median_fill/${char}.svg`
    ],
    C: [
      `/B_raw_centerline/${char}.svg`,
      `/B_raw_centerline/${char}_raw.svg`,
      `/output/B_raw_centerline/${char}.svg`
    ],
    D: [
      `/C_processed_centerline/${char}.svg`,
      `/C_processed_centerline/${char}_processed.svg`,
      `/output/C_processed_centerline/${char}.svg`
    ]
  };
  
  // Test each image type
  for (const [type, paths] of Object.entries(testPaths)) {
    const img = type === 'A' ? imgA : type === 'B' ? imgB : type === 'C' ? imgC : imgD1;
    if (!img) continue;
    
    for (const path of paths) {
      try {
        console.log(`🔍 测试路径 ${type}:`, path);
        const response = await fetch(withTs(path));
        if (response.ok) {
          console.log(`✅ 找到文件 ${type}:`, path);
          img.src = withTs(path);
          img.style.display = 'block';
          img.style.opacity = '1';
          break;
        }
      } catch (e) {
        // Silent fail, continue to next path
      }
    }
  }
}

// 初始化测试加载
async function initTestLoad() {
  console.log('🔍 尝试直接加载文件...');
  await tryDirectFileLoad('的');
}

// 创建生成管理器对象
const generationManager = {
  tryDirectFileLoad,
  initTestLoad,
  initImageModal,
  initRemainingFunctionality
};

// 导出测试加载函数和管理器对象
window.tryDirectFileLoad = tryDirectFileLoad;
window.initTestLoad = initTestLoad;
window.generationManager = generationManager;

console.log('✅ 生成管理模块已加载');
