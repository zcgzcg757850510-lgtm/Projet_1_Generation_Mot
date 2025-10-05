/**/;(function(){try{if(!window.__suppressLogs){window.__suppressLogs=true;console.log=function(){};console.info=function(){};console.debug=function(){};console.warn=function(){};} }catch(e){}})();

// 网格变形全局状态
let gridTransform = {
  size: 3,
  canvas: null,
  ctx: null,
  controlPoints: [],
  originalPoints: [],
  currentPoints: [],
  gridVisible: true,
  isDragging: false,
  dragIndex: -1,
  backgroundImage: null,
  svgElement: null,
  originalSVG: '',
  deformStrength: 1.0
};

// 确保其他模块（如 grid-state-manager.js）能通过 window 访问到当前网格状态
try { if (typeof window !== 'undefined') { window.gridTransform = gridTransform; } } catch (e) {}

// 将网格状态同步到后端（Phase 1：仅传输数据，不生成文件）
async function syncGridStateToServer(state) {
  try {
    if (!state || !state.controlPoints || state.controlPoints.length === 0) return;
    const charInput = document.querySelector('input[name="char"]');
    const ch = charInput ? (charInput.value || '').trim() : '';
    const dims = {
      width: (gridTransform && gridTransform.canvas && gridTransform.canvas.width) ? gridTransform.canvas.width : 800,
      height: (gridTransform && gridTransform.canvas && gridTransform.canvas.height) ? gridTransform.canvas.height : 600
    };
    const payload = { grid_state: state, canvas_dimensions: dims, char: ch };
    await fetch('/save_grid_state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
  } catch (e) { /* 静默失败，避免打断交互 */ }
}

/**
 * 网格状态管理器
 * 负责网格状态的保存、加载和管理
 */
const GridStateManager = {
  // 获取当前网格状态
  getState() {
    if (!gridTransform.controlPoints || gridTransform.controlPoints.length === 0) {
      return this.getDefaultGridState();
    }
    
    // 如果画布不存在，尝试初始化
    if (!gridTransform.canvas) {
      const canvas = document.getElementById('gridCanvas');
      if (canvas) {
        const container = canvas.parentElement;
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
        gridTransform.canvas = canvas;
        gridTransform.ctx = canvas.getContext('2d');
      } else {
        return this.getDefaultGridState();
      }
    }
    
    if (!gridTransform.controlPoints || gridTransform.controlPoints.length === 0) {
      if (gridTransform.canvas) {
        createGridPoints();
      } else {
        return this.getDefaultGridState();
      }
    }
    
    const state = {
      controlPoints: gridTransform.controlPoints.map(point => ({
        x: point.x,
        y: point.y,
        originalX: point.originalX,
        originalY: point.originalY,
        row: point.row,
        col: point.col
      })),
      size: gridTransform.size,
      deformStrength: gridTransform.deformStrength,
      // 保存背景图像信息，用于状态恢复时的位置计算
      backgroundImage: gridTransform.backgroundImage ? {
        x: gridTransform.backgroundImage.x,
        y: gridTransform.backgroundImage.y,
        width: gridTransform.backgroundImage.width,
        height: gridTransform.backgroundImage.height
      } : null
    };
    
    return state;
  },

  // 获取默认网格状态
  getDefaultGridState() {
    return {
      controlPoints: [],
      size: 3,
      deformStrength: 1.0
    };
  },

  // 从localStorage加载状态
  loadFromStorage() {
    try {
      const savedState = localStorage.getItem('gridTransform_state');
      if (savedState) {
        const state = JSON.parse(savedState);
        return state;
      }
    } catch (e) {
      console.error('加载网格状态失败:', e);
    }
    return null;
  },

  // 保存网格状态到localStorage
  save() {
    // 检查核心数据是否存在
    if (!gridTransform.controlPoints || gridTransform.controlPoints.length === 0) {
      console.warn('GridStateManager: 无法保存，controlPoints不存在或为空');
      return false;
    }
    
    try {
      const state = this.getState();
      localStorage.setItem('gridTransform_state', JSON.stringify(state));
      
      console.log('✅ 网格状态已保存:', state);
      
      // 显示保存提示
      if (typeof showToast === 'function') {
        showToast('网格状态已自动保存', 'success', 1000);
      }
      
      return true;
    } catch (e) {
      console.error('保存网格状态失败:', e);
      return false;
    }
  },

  // 加载网格状态
  load() {
    const savedState = this.loadFromStorage();
    if (!savedState) {
      console.log('没有找到保存的网格状态');
      return false;
    }
    
    try {
      // 首先恢复基本设置
      if (savedState.size) {
        // 兼容旧状态，将4规范为3
        gridTransform.size = savedState.size === 4 ? 3 : savedState.size;
      }
      if (savedState.deformStrength) {
        gridTransform.deformStrength = savedState.deformStrength;
      }
      
      // 如果有保存的控制点，直接恢复（不依赖createGridPoints）
      if (savedState.controlPoints && savedState.controlPoints.length > 0) {
        gridTransform.controlPoints = savedState.controlPoints.map(point => ({
          x: point.x,
          y: point.y,
          originalX: point.originalX,
          originalY: point.originalY,
          row: point.row || 0,
          col: point.col || 0
        }));
        
        // 更新当前点和原始点数组
        updatePointArrays();
        
        // 立即绘制网格，显示恢复的控制点
        if (gridTransform.canvas && gridTransform.ctx) {
          drawGrid();
        }
        
        console.log('✅ 网格状态已恢复:', savedState);
        console.log('🎯 恢复的控制点数量:', gridTransform.controlPoints.length);
        
        // 如果SVG已存在，立即应用变形
        if (gridTransform.svgElement) {
          applyGridDeformation();
        }
        
        return true;
      } else {
        // 没有保存的控制点，创建默认网格
        createGridPoints();
        console.log('ℹ️ 创建默认网格控制点');
        return false;
      }
    } catch (e) {
      console.error('恢复网格状态失败:', e);
    }
    
    return false;
  },

  // 更新UI显示
  updateUI() {
    // 更新网格大小选择器
    const sizeSelect = document.getElementById('gridSize');
    if (sizeSelect) {
      sizeSelect.value = gridTransform.size;
    }
    
    // 更新变形强度滑块
    const strengthSlider = document.getElementById('deformStrength');
    if (strengthSlider) {
      strengthSlider.value = gridTransform.deformStrength;
    }
    
    // 重绘网格
    drawGrid();
  }
};

/**
 * 初始化网格变形系统（优化版，减少闪动）
 */
function initializeGridTransform() {
  console.log('🔄 初始化网格变形系统（优化版）');
  
  // 1. 预设画布尺寸，避免后续调整导致闪动
  const canvas = document.getElementById('gridCanvas');
  const container = canvas.parentElement;
  if (canvas && container) {
    // 立即设置画布尺寸，避免后续变化
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    gridTransform.canvas = canvas;
    gridTransform.ctx = canvas.getContext('2d');
    // 整图变形：创建覆盖画布
    (function ensureWarpCanvas() {
      let warpCanvas = document.getElementById('gridWarpCanvas');
      if (!warpCanvas) {
        warpCanvas = document.createElement('canvas');
        warpCanvas.id = 'gridWarpCanvas';
        warpCanvas.style.position = 'absolute';
        warpCanvas.style.top = '50px';
        warpCanvas.style.left = '0';
        warpCanvas.style.right = '0';
        warpCanvas.style.bottom = '0';
        warpCanvas.style.zIndex = '4';
        warpCanvas.style.pointerEvents = 'none';
        const parent = canvas.parentElement;
        if (parent) parent.appendChild(warpCanvas);
      }
      warpCanvas.width = canvas.width;
      warpCanvas.height = canvas.height;
      gridTransform.warpCanvas = warpCanvas;
      gridTransform.warpCtx = warpCanvas.getContext('2d');
    })();
    
    // 添加事件监听器
    canvas.addEventListener('mousedown', handleGridMouseDown);
    canvas.addEventListener('mousemove', handleGridMouseMove);
    canvas.addEventListener('mouseup', handleGridMouseUp);
    canvas.addEventListener('dblclick', handleGridDoubleClick);
  }
  
  // 2. 立即尝试加载保存的网格状态
  const stateLoaded = GridStateManager.load();
  console.log('📥 状态加载结果:', stateLoaded);
  
  // 3. 如果没有加载到状态，使用默认值并创建网格
  if (!stateLoaded) {
    console.log('📝 使用默认网格设置');
    gridTransform.size = 3;
    gridTransform.deformStrength = 1.0;
    createGridPoints();
  }
  
  // 4. 立即更新UI状态和绘制网格
  GridStateManager.updateUI();
  updateGridStatus(`网格变换初始化完成 (${gridTransform.size}×${gridTransform.size})`);
  
  // 5. 立即开始加载图片，不等待延迟
  autoLoadD1ToGrid();
}

/**
 * 自动加载D1图片到网格画布 -> 修改为自动加载C（原始中轴SVG）
 */
async function autoLoadD1ToGrid() {
  console.log('🔄 开始自动加载C图片');
  
  // 获取当前字符
  const charInput = document.querySelector('input[name="char"]');
  let currentChar = charInput ? charInput.value.trim() : '';
  
  console.log('📝 当前字符:', currentChar);
  
  if (!currentChar) {
    console.log('❌ 没有输入字符，无法加载C图片');
    updateGridStatus('请先输入字符', 'warning');
    return;
  }
  
  updateGridStatus('正在加载C图片...', 'loading');
  console.log('🔍 开始查找C图片文件...');
  
  // 方法1: 优先检查预览区域的C图片
  try {
    const imgC = document.getElementById('imgC');
    console.log('🖼️ 检查预览区域C图片:', imgC ? '找到' : '未找到');
    
    if (imgC && imgC.src && !imgC.src.includes('placeholder') && !imgC.src.includes('data:')) {
      const currentSrc = imgC.src;
      const latestPath = currentSrc.split('?')[0]; // 移除时间戳参数
      // 仅当预览区域的C指向 C_processed_centerline 时才采用
      if (latestPath.includes('/C_processed_centerline/')) {
        console.log('✅ 预览区域指向C_processed_centerline，采用该路径:', latestPath);
      // 验证路径是否有效
      const response = await fetch(latestPath);
      if (response.ok) {
        const newSrc = latestPath + '?t=' + Date.now();
          if (imgC.src !== newSrc) {
            imgC.src = newSrc;
        }
        loadImageToGridCanvas(latestPath + '?t=' + Date.now());
        return;
      } else {
          console.log('❌ C图片路径无效:', latestPath);
        }
      } else {
        console.log('⚠️ 预览区域imgC不是C_processed_centerline，跳过该来源');
      }
    }
  } catch (e) {
    console.log('❌ 预览区域方法失败:', e);
  }

  // 方法2: 直接从状态接口获取最新文件
  try {
    const statusResp = await fetch(`/status?ch=${encodeURIComponent(currentChar)}`);
    if (statusResp.ok) {
      const statusData = await statusResp.json();
      const files = statusData.files || statusData; // 兼容不同结构
      const cInfo = files && (files.C || files.c);
      let cUrl = '';
      if (typeof cInfo === 'string' && cInfo) {
        cUrl = cInfo.startsWith('/') ? cInfo : `/compare/C_processed_centerline/${cInfo}`;
      } else if (cInfo && (cInfo.path || cInfo.url || cInfo.file)) {
        const raw = cInfo.path || cInfo.url || cInfo.file;
        cUrl = raw.startsWith('/') ? raw : `/compare/C_processed_centerline/${raw}`;
      }
      if (cUrl) {
        console.log('✅ /status 返回C文件URL:', cUrl);
        loadImageToGridCanvas(cUrl + (cUrl.includes('?') ? '&' : '?') + 't=' + Date.now());
        return;
      }
    }
  } catch (e) {
    console.log('❌ /status 方法失败:', e);
  }

  // 方法3: 回退到目录列表搜索（原始中轴B_raw_centerline中包含字符的最新SVG）
  try {
    const listResp = await fetch('/compare/C_processed_centerline/');
    if (listResp.ok) {
      const text = await listResp.text();
      // 简单解析包含链接的HTML，筛选包含当前字符的文件
      const re = new RegExp(`>(\\d{8}-\\d{6}-\\d{3})_${currentChar}_[^<]+<`, 'g');
      let m, files = [];
      while ((m = re.exec(text)) !== null) {
        files.push(m[1]);
      }
      if (files.length > 0) {
        // 由于只提取了时间戳，这里不可靠；改为直接使用预览路径回退
      }
    }
  } catch (e) {
    console.log('❌ 目录列表方法失败:', e);
  }
  
  console.log('❌ 未找到C图片文件');
  updateGridStatus('未找到C图片文件，请先生成C', 'error');
}

/**
 * 将图片加载到网格画布中
 */
function loadImageToGridCanvas(imageUrl) {
  const canvas = gridTransform.canvas;
  const ctx = gridTransform.ctx;
  
  if (!canvas || !ctx) {
    console.error('❌ 网格画布未初始化');
    updateGridStatus('网格画布未初始化', 'error');
    return;
  }
  
  console.log('🖼️ 开始加载图片到网格画布:', imageUrl);
  updateGridStatus('正在加载图片...', 'loading');
  
  const img = new Image();
  img.crossOrigin = 'anonymous';
  
  img.onload = function() {
    console.log('✅ 图片加载成功，原始尺寸:', img.width, 'x', img.height);
    
    // 新规则：SVG完全填满主要区域（排除50px标题栏）
    const container = canvas.parentElement;
    const containerWidth = container.clientWidth;
    const containerHeight = container.clientHeight - 50; // 减去header高度
    
    // Canvas填满主要区域（不包括header）
    const canvasWidth = containerWidth;
    const canvasHeight = containerHeight;
    
    // 只在尺寸确实需要调整时才修改canvas，避免不必要的闪动
    if (canvas.width !== canvasWidth || canvas.height !== canvasHeight) {
      canvas.width = canvasWidth;
      canvas.height = canvasHeight;
      console.log('🎯 Canvas尺寸已调整:', canvasWidth, 'x', canvasHeight);
      // 同步变形画布尺寸
      if (gridTransform.warpCanvas) {
        gridTransform.warpCanvas.width = canvasWidth;
        gridTransform.warpCanvas.height = canvasHeight;
      }
    }
    
    // SVG保持原始比例，居中显示，为网格控制点留出边距
    const margin = 60; // 为网格控制点预留边距
    const availableWidth = canvasWidth - margin;
    const availableHeight = canvasHeight - margin;
    
    // 计算SVG显示尺寸，保持原始比例
    const imgAspect = img.width / img.height;
    let displayWidth, displayHeight;
    
    if (availableWidth / availableHeight > imgAspect) {
      // 容器更宽，以高度为准
      displayHeight = availableHeight;
      displayWidth = displayHeight * imgAspect;
    } else {
      // 容器更高，以宽度为准
      displayWidth = availableWidth;
      displayHeight = displayWidth / imgAspect;
    }
    
    // SVG居中定位
    const drawX = (canvasWidth - displayWidth) / 2;
    const drawY = (canvasHeight - displayHeight) / 2;
    
    console.log('📏 SVG保持比例居中显示:', displayWidth, 'x', displayHeight, '边距:', margin + 'px');
    
    // 清除画布并绘制图片（注释掉实际绘制，只保存位置信息）
    ctx.clearRect(0, 0, canvasWidth, canvasHeight);
    // ctx.drawImage(img, drawX, drawY, drawWidth, drawHeight);
    
    // 保存图片信息到gridTransform对象
    gridTransform.backgroundImage = {
      img: img,
      x: drawX,
      y: drawY,
      width: displayWidth,
      height: displayHeight
    };
    
    // 如果图片是SVG，尝试获取SVG文本内容并显示在SVG容器中
    if (imageUrl.toLowerCase().includes('.svg')) {
      fetch(imageUrl)
        .then(response => response.text())
        .then(svgText => {
        const container = document.getElementById('gridSvgContainer');
        container.innerHTML = svgText;
        
        gridTransform.svgElement = container.querySelector('svg');
        gridTransform.originalSVG = svgText;
        
        if (gridTransform.svgElement) {
          // 重置SVG容器的定位，让SVG完全居中
          const container = document.getElementById('gridSvgContainer');
          container.style.position = 'absolute';
          container.style.left = '0';
          container.style.top = '0';
          container.style.width = '100%';
          container.style.height = '100%';
          container.style.pointerEvents = 'none';
          container.style.zIndex = '1';
          container.style.margin = '0';
          container.style.padding = '0';
          container.style.opacity = '0'; // 初始隐藏，避免闪动
          container.style.transition = 'opacity 0.2s ease';
          
          // 设置SVG样式以填满显示区域，位置在标题栏下方
          gridTransform.svgElement.style.position = 'absolute';
          gridTransform.svgElement.style.left = drawX + 'px';
          gridTransform.svgElement.style.top = (drawY + 50) + 'px'; // 加上50px标题栏高度
          gridTransform.svgElement.style.width = displayWidth + 'px';
          gridTransform.svgElement.style.height = displayHeight + 'px';
          gridTransform.svgElement.style.pointerEvents = 'none';
          
          // 立即显示SVG，减少延迟
          setTimeout(() => {
            container.style.opacity = '1';
          }, 20);
          
          console.log('🎯 SVG居中显示，网格精确覆盖:', {
            left: drawX + 'px',
            top: (drawY + 50) + 'px', 
            width: displayWidth + 'px',
            height: displayHeight + 'px',
            '位置': '标题栏下方',
            '网格覆盖': 'SVG文字区域'
          });
          
          // 立即尝试恢复保存的网格状态，减少延迟
          const stateLoaded = GridStateManager.load();
          
          if (stateLoaded) {
            console.log('🔄 立即恢复网格状态');
            // 立即重绘网格以显示恢复的控制点
            drawGrid();
            
            // 使用整图变形渲染
            setTimeout(() => {
              applyWholeImageWarp();
            }, 50);
          } else {
            // 没有保存状态，创建默认网格
            createGridPoints();
            drawGrid();
            setTimeout(() => {
              applyWholeImageWarp();
            }, 30);
          }
          
          console.log('✅ SVG已加载到网格容器');
          updateGridStatus('SVG已加载并定位（整图变形）', 'success');
        }
      })
      .catch(err => {
        console.error('❌ 获取SVG内容失败:', err);
        updateGridStatus('SVG内容获取失败', 'error');
      });
    }
    
    // 重绘网格（在图片上方）
    drawGrid();
    
    console.log('✅ 图片已加载到网格画布，位置:', drawX, drawY, '尺寸:', displayWidth, displayHeight);
    updateGridStatus('C图片已加载到网格画布', 'success');
  };
  
  img.onerror = function() {
    console.error('❌ 图片加载失败:', imageUrl);
    updateGridStatus('C图片加载失败', 'error');
  };
  
  img.src = imageUrl;
}

/**
 * 创建网格控制点
 */
function createGridPoints() {
  const size = gridTransform.size;
  const canvas = gridTransform.canvas;
  
  // 新规则：如果有背景图像，使用其尺寸和位置创建网格
  let gridWidth, gridHeight, startX, startY;
  
  if (gridTransform.backgroundImage) {
    // 网格完全覆盖SVG显示区域（填满整个主要区域）
    const img = gridTransform.backgroundImage;
    gridWidth = img.width;
    gridHeight = img.height;
    startX = img.x;
    startY = img.y;
    console.log('🎯 网格覆盖完整SVG区域:', {
      width: gridWidth,
      height: gridHeight,
      startX: startX,
      startY: startY,
      '覆盖比例': '100%'
    });
  } else {
    // 回退到原有逻辑：网格填满整个canvas
    gridWidth = canvas.width;
    gridHeight = canvas.height;
    startX = 0;
    startY = 0;
    console.log('🎯 网格填满整个canvas');
  }
  
  gridTransform.controlPoints = [];
  gridTransform.originalPoints = [];
  gridTransform.currentPoints = [];
  
  for (let row = 0; row < size; row++) {
    for (let col = 0; col < size; col++) {
      const x = startX + (col / (size - 1)) * gridWidth;
      const y = startY + (row / (size - 1)) * gridHeight;
      
      gridTransform.controlPoints.push({
        x: x,
        y: y,
        originalX: x,
        originalY: y,
        row: row,
        col: col
      });
      
      gridTransform.originalPoints.push([x, y]);
      gridTransform.currentPoints.push([x, y]);
    }
  }
  
  console.log(`创建 ${size}×${size} 网格控制点`);
}

/**
 * 绘制网格
 */
function drawGrid() {
  if (!gridTransform.ctx || !gridTransform.gridVisible) return;
  
  const ctx = gridTransform.ctx;
  const canvas = gridTransform.canvas;
  const size = gridTransform.size;
  
  // 清除画布
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  if (!gridTransform.controlPoints || gridTransform.controlPoints.length === 0) {
    return;
  }
  
  // 绘制网格线（已移除背景网格线，只保留控制点）
  ctx.setLineDash([]);
  ctx.lineWidth = 0;
  
  // 绘制水平线
  for (let row = 0; row < size; row++) {
    ctx.beginPath();
    for (let col = 0; col < size; col++) {
      const point = gridTransform.controlPoints[row * size + col];
      if (col === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        ctx.lineTo(point.x, point.y);
      }
    }
    // 不绘制线
  }
  
  // 绘制垂直线
  for (let col = 0; col < size; col++) {
    ctx.beginPath();
    for (let row = 0; row < size; row++) {
      const point = gridTransform.controlPoints[row * size + col];
      if (row === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        ctx.lineTo(point.x, point.y);
      }
    }
    // 不绘制线
  }
  
  // 绘制控制点（绿色圆点）
  ctx.setLineDash([]);
  gridTransform.controlPoints.forEach((point, index) => {
    ctx.beginPath();
    ctx.arc(point.x, point.y, 6, 0, 2 * Math.PI);
    ctx.fillStyle = '#00ff00';
    ctx.fill();
    ctx.strokeStyle = '#0b3d0b';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  });
}

/**
 * 处理鼠标按下事件
 */
function handleGridMouseDown(e) {
  const rect = gridTransform.canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  
  // 查找最近的控制点
  let minDistance = Infinity;
  let closestIndex = -1;
  
  gridTransform.controlPoints.forEach((point, index) => {
    const distance = Math.sqrt((mouseX - point.x) ** 2 + (mouseY - point.y) ** 2);
    if (distance < minDistance && distance < 15) { // 15像素的点击范围
      minDistance = distance;
      closestIndex = index;
    }
  });
  
  if (closestIndex !== -1) {
    gridTransform.isDragging = true;
    gridTransform.dragIndex = closestIndex;
    gridTransform.canvas.style.cursor = 'grabbing';
  }
}

/**
 * 处理双击事件 - 重置控制点
 */
function handleGridDoubleClick(e) {
  const rect = gridTransform.canvas.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  
  // 查找最近的控制点并重置
  gridTransform.controlPoints.forEach((point, index) => {
    const distance = Math.sqrt((x - point.x) ** 2 + (y - point.y) ** 2);
    if (distance < 15) {
      point.x = point.originalX;
      point.y = point.originalY;
      updatePointArrays();
      drawGrid();
      applyGridDeformation();
      GridStateManager.save();
      try { syncGridStateToServer(GridStateManager.getState()); } catch(e) {}
    }
  });
}

/**
 * 处理鼠标移动事件
 */
function handleGridMouseMove(e) {
  if (!gridTransform.isDragging || gridTransform.dragIndex === -1) return;
  
  const rect = gridTransform.canvas.getBoundingClientRect();
  const mouseX = e.clientX - rect.left;
  const mouseY = e.clientY - rect.top;
  
  // 更新控制点位置
  gridTransform.controlPoints[gridTransform.dragIndex].x = mouseX;
  gridTransform.controlPoints[gridTransform.dragIndex].y = mouseY;
  
  // 更新点数组
  updatePointArrays();
  
  // 重绘网格
  drawGrid();
  
  // 应用整图变形
  applyWholeImageWarp();
  
  // 立即保存状态（移除节流限制）
  GridStateManager.save();
  try { syncGridStateToServer(GridStateManager.getState()); } catch(e) {}
}

/**
 * 处理鼠标释放事件
 */
function handleGridMouseUp(e) {
  if (gridTransform.isDragging) {
    gridTransform.isDragging = false;
    gridTransform.dragIndex = -1;
    gridTransform.canvas.style.cursor = 'default';
    
    // 拖拽结束，确保最终状态已保存
    console.log('🔄 拖拽结束，确认状态已保存');
    GridStateManager.save();
    try { syncGridStateToServer(GridStateManager.getState()); } catch(e) {}
    // 拖拽结束后进行无缝高质量重渲染
    applySeamlessImageWarp();
  }
}

/**
 * 更新点数组
 */
function updatePointArrays() {
  gridTransform.currentPoints = gridTransform.controlPoints.map(point => [point.x, point.y]);
}

/**
 * 应用网格变形
 */
function applyGridDeformation() {
  // 新策略：整图变形替代逐路径变形
  applyWholeImageWarp();
}

// —— 整图变形实现 ——
let _warpRenderRAF = null;
function applyWholeImageWarp() {
  if (!gridTransform.warpCanvas || !gridTransform.warpCtx || !gridTransform.backgroundImage) return;
  if (!gridTransform.controlPoints || gridTransform.controlPoints.length === 0) return;
  // 节流：每帧最多渲染一次
  if (_warpRenderRAF) return;
  _warpRenderRAF = requestAnimationFrame(() => {
    _warpRenderRAF = null;
    const outCtx = gridTransform.warpCtx;
    const outCanvas = gridTransform.warpCanvas;
    outCtx.clearRect(0, 0, outCanvas.width, outCanvas.height);

    const bg = gridTransform.backgroundImage;
    const size = gridTransform.size;

    // 将原SVG半透明显示，仅显示整图变形结果在上层
    const container = document.getElementById('gridSvgContainer');
    if (container) container.style.opacity = '0';

    // 源图尺寸（使用自然尺寸用于裁剪源块）
    const source = bg.img;
    const sW = source.naturalWidth || source.width;
    const sH = source.naturalHeight || source.height;

    // 画质优化（交互阶段不做超采样）
    const SS = 1;
    const ctx = outCtx;
    ctx.clearRect(0, 0, outCanvas.width, outCanvas.height);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';

    // Photoshop风格：基于Catmull-Rom边界曲线与Coons Patch的无缝变形
    function clampIndex(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
    function getCP(r, c) { return gridTransform.controlPoints[r * size + c]; }
    // Catmull-Rom 到 Bezier（段 p1->p2）
    function catmullRomToBezier(p0, p1, p2, p3) {
      const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 };
      const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 };
      return [ { x: p1.x, y: p1.y }, c1, c2, { x: p2.x, y: p2.y } ];
    }
    function bezierEval(bz, t) {
      const it = 1 - t;
      const b0 = it * it * it;
      const b1 = 3 * it * it * t;
      const b2 = 3 * it * t * t;
      const b3 = t * t * t;
      return {
        x: bz[0].x * b0 + bz[1].x * b1 + bz[2].x * b2 + bz[3].x * b3,
        y: bz[0].y * b0 + bz[1].y * b1 + bz[2].y * b2 + bz[3].y * b3
      };
    }

    // 将图像区域划分为(size-1)x(size-1)小网格，使用网格内进一步细分，近似无缝双线性形变
    const cells = Math.max(1, size - 1);
    const SUBDIV = 8; // 交互时使用8×8细分，兼顾性能

    for (let gy = 0; gy < cells; gy++) {
      for (let gx = 0; gx < cells; gx++) {
        // 源块矩形坐标（在源图坐标系中）
        const srcX1 = (gx    / cells) * sW;
        const srcY1 = (gy    / cells) * sH;
        const srcX2 = ((gx+1)/ cells) * sW;
        const srcY2 = ((gy+1)/ cells) * sH;

        // 目标四角控制点（画布坐标）
        const p00 = getCP(gy, gx);
        const p10 = getCP(gy, gx+1);
        const p01 = getCP(gy+1, gx);
        const p11 = getCP(gy+1, gx+1);
        if (!p00 || !p10 || !p01 || !p11) continue;

        // 构建四条边界Bezier（Catmull-Rom -> Bezier），共享边界确保无缝
        // 顶边（行 gy，列 gx->gx+1）
        const ta = getCP(gy, clampIndex(gx-1, 0, size-1));
        const tb = p00;
        const tc = p10;
        const td = getCP(gy, clampIndex(gx+2, 0, size-1));
        const topBz = catmullRomToBezier(ta, tb, tc, td);

        // 底边（行 gy+1，列 gx->gx+1）
        const ba = getCP(gy+1, clampIndex(gx-1, 0, size-1));
        const bb = p01;
        const bc = p11;
        const bd = getCP(gy+1, clampIndex(gx+2, 0, size-1));
        const bottomBz = catmullRomToBezier(ba, bb, bc, bd);

        // 左边（列 gx，行 gy->gy+1）
        const la = getCP(clampIndex(gy-1, 0, size-1), gx);
        const lb = p00;
        const lc = p01;
        const ld = getCP(clampIndex(gy+2, 0, size-1), gx);
        const leftBz = catmullRomToBezier(la, lb, lc, ld);

        // 右边（列 gx+1，行 gy->gy+1）
        const ra = getCP(clampIndex(gy-1, 0, size-1), gx+1);
        const rb = p10;
        const rc = p11;
        const rd = getCP(clampIndex(gy+2, 0, size-1), gx+1);
        const rightBz = catmullRomToBezier(ra, rb, rc, rd);

        function coons(u, v) {
          const top = bezierEval(topBz, u);
          const bottom = bezierEval(bottomBz, u);
          const left = bezierEval(leftBz, v);
          const right = bezierEval(rightBz, v);
          const blendUV = {
            x: p00.x * (1 - u) * (1 - v) + p10.x * u * (1 - v) + p01.x * (1 - u) * v + p11.x * u * v,
            y: p00.y * (1 - u) * (1 - v) + p10.y * u * (1 - v) + p01.y * (1 - u) * v + p11.y * u * v
          };
          return {
            x: top.x * (1 - v) + bottom.x * v + left.x * (1 - u) + right.x * u - blendUV.x,
            y: top.y * (1 - v) + bottom.y * v + left.y * (1 - u) + right.y * u - blendUV.y
          };
        }

        // 对该单元格进行细分绘制
        for (let vstep = 0; vstep < SUBDIV; vstep++) {
          const v0 = vstep / SUBDIV;
          const v1 = (vstep + 1) / SUBDIV;
          const sy0 = srcY1 + (srcY2 - srcY1) * v0;
          const sy1 = srcY1 + (srcY2 - srcY1) * v1;

          for (let ustep = 0; ustep < SUBDIV; ustep++) {
            const u0 = ustep / SUBDIV;
            const u1 = (ustep + 1) / SUBDIV;
            const sx0 = srcX1 + (srcX2 - srcX1) * u0;
            const sx1 = srcX1 + (srcX2 - srcX1) * u1;

            // 目标四角（Photoshop风格Coons曲面）
            const d00 = coons(u0, v0);
            const d10 = coons(u1, v0);
            const d01 = coons(u0, v1);
            const d11 = coons(u1, v1);

            // 源四角
            const s00x = sx0, s00y = sy0;
            const s10x = sx1, s10y = sy0;
            const s01x = sx0, s01y = sy1;
            const s11x = sx1, s11y = sy1;

            // 使用两个三角形绘制微单元（缝隙极小）
            drawImageTriangleAffine(ctx, source,
              s00x, s00y, s10x, s10y, s01x, s01y,
              d00.x * SS, d00.y * SS, d10.x * SS, d10.y * SS, d01.x * SS, d01.y * SS
            );

            drawImageTriangleAffine(ctx, source,
              s11x, s11y, s01x, s01y, s10x, s10y,
              d11.x * SS, d11.y * SS, d01.x * SS, d01.y * SS, d10.x * SS, d10.y * SS
            );
          }
        }
      }
    }

    // 交互阶段直接输出（不改变网格密度与分辨率）
  });
}

// 无缝高质量整图变形（拖拽结束或生成前调用）
function applySeamlessImageWarp() {
  if (!gridTransform.warpCanvas || !gridTransform.warpCtx || !gridTransform.backgroundImage) return;
  if (!gridTransform.controlPoints || gridTransform.controlPoints.length === 0) return;
  const outCtx = gridTransform.warpCtx;
  const outCanvas = gridTransform.warpCanvas;
  outCtx.clearRect(0, 0, outCanvas.width, outCanvas.height);

  const bg = gridTransform.backgroundImage;
  const size = gridTransform.size;

  const container = document.getElementById('gridSvgContainer');
  if (container) container.style.opacity = '0';

  const source = bg.img;
  const sW = source.naturalWidth || source.width;
  const sH = source.naturalHeight || source.height;

  // 高质量超采样
  const SS = 3;
  const off = document.createElement('canvas');
  off.width = Math.max(1, Math.round(outCanvas.width * SS));
  off.height = Math.max(1, Math.round(outCanvas.height * SS));
  const ctx = off.getContext('2d');
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';

  // Photoshop风格：基于Catmull-Rom边界曲线与Coons Patch的无缝变形
  function clampIndex(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }
  function getCP(r, c) { return gridTransform.controlPoints[r * size + c]; }
  function catmullRomToBezier(p0, p1, p2, p3) {
    const c1 = { x: p1.x + (p2.x - p0.x) / 6, y: p1.y + (p2.y - p0.y) / 6 };
    const c2 = { x: p2.x - (p3.x - p1.x) / 6, y: p2.y - (p3.y - p1.y) / 6 };
    return [ { x: p1.x, y: p1.y }, c1, c2, { x: p2.x, y: p2.y } ];
  }
  function bezierEval(bz, t) {
    const it = 1 - t;
    const b0 = it * it * it;
    const b1 = 3 * it * it * t;
    const b2 = 3 * it * t * t;
    const b3 = t * t * t;
        return {
      x: bz[0].x * b0 + bz[1].x * b1 + bz[2].x * b2 + bz[3].x * b3,
      y: bz[0].y * b0 + bz[1].y * b1 + bz[2].y * b2 + bz[3].y * b3
    };
  }

  const cells = Math.max(1, size - 1);
  const SUBDIV = 20; // 更高细分，显著降低接缝

  for (let gy = 0; gy < cells; gy++) {
    for (let gx = 0; gx < cells; gx++) {
      const srcX1 = (gx    / cells) * sW;
      const srcY1 = (gy    / cells) * sH;
      const srcX2 = ((gx+1)/ cells) * sW;
      const srcY2 = ((gy+1)/ cells) * sH;

      const p00 = getCP(gy, gx);
      const p10 = getCP(gy, gx+1);
      const p01 = getCP(gy+1, gx);
      const p11 = getCP(gy+1, gx+1);
      if (!p00 || !p10 || !p01 || !p11) continue;

      const ta = getCP(gy, clampIndex(gx-1, 0, size-1));
      const tb = p00;
      const tc = p10;
      const td = getCP(gy, clampIndex(gx+2, 0, size-1));
      const topBz = catmullRomToBezier(ta, tb, tc, td);

      const ba = getCP(gy+1, clampIndex(gx-1, 0, size-1));
      const bb = p01;
      const bc = p11;
      const bd = getCP(gy+1, clampIndex(gx+2, 0, size-1));
      const bottomBz = catmullRomToBezier(ba, bb, bc, bd);

      const la = getCP(clampIndex(gy-1, 0, size-1), gx);
      const lb = p00;
      const lc = p01;
      const ld = getCP(clampIndex(gy+2, 0, size-1), gx);
      const leftBz = catmullRomToBezier(la, lb, lc, ld);

      const ra = getCP(clampIndex(gy-1, 0, size-1), gx+1);
      const rb = p10;
      const rc = p11;
      const rd = getCP(clampIndex(gy+2, 0, size-1), gx+1);
      const rightBz = catmullRomToBezier(ra, rb, rc, rd);

      function coons(u, v) {
        const top = bezierEval(topBz, u);
        const bottom = bezierEval(bottomBz, u);
        const left = bezierEval(leftBz, v);
        const right = bezierEval(rightBz, v);
        const blendUV = {
          x: p00.x * (1 - u) * (1 - v) + p10.x * u * (1 - v) + p01.x * (1 - u) * v + p11.x * u * v,
          y: p00.y * (1 - u) * (1 - v) + p10.y * u * (1 - v) + p01.y * (1 - u) * v + p11.y * u * v
        };
        return {
          x: top.x * (1 - v) + bottom.x * v + left.x * (1 - u) + right.x * u - blendUV.x,
          y: top.y * (1 - v) + bottom.y * v + left.y * (1 - u) + right.y * u - blendUV.y
        };
      }

      for (let vstep = 0; vstep < SUBDIV; vstep++) {
        const v0 = vstep / SUBDIV;
        const v1 = (vstep + 1) / SUBDIV;
        const sy0 = srcY1 + (srcY2 - srcY1) * v0;
        const sy1 = srcY1 + (srcY2 - srcY1) * v1;

        for (let ustep = 0; ustep < SUBDIV; ustep++) {
          const u0 = ustep / SUBDIV;
          const u1 = (ustep + 1) / SUBDIV;
          const sx0 = srcX1 + (srcX2 - srcX1) * u0;
          const sx1 = srcX1 + (srcX2 - srcX1) * u1;

          const d00 = coons(u0, v0);
          const d10 = coons(u1, v0);
          const d01 = coons(u0, v1);
          const d11 = coons(u1, v1);

          drawImageTriangleAffine(ctx, source,
            sx0, sy0, sx1, sy0, sx0, sy1,
            d00.x * SS, d00.y * SS, d10.x * SS, d10.y * SS, d01.x * SS, d01.y * SS
          );

          drawImageTriangleAffine(ctx, source,
            sx1, sy1, sx0, sy1, sx1, sy0,
            d11.x * SS, d11.y * SS, d01.x * SS, d01.y * SS, d10.x * SS, d10.y * SS
          );
        }
      }
    }
  }

  // 输出到目标画布（降采样抗锯齿，消除背景斜线）
  outCtx.imageSmoothingEnabled = true;
  outCtx.imageSmoothingQuality = 'high';
  outCtx.drawImage(off, 0, 0, off.width, off.height, 0, 0, outCanvas.width, outCanvas.height);
}

// 将源三角形映射到目标三角形的仿射绘制
function drawImageTriangleAffine(ctx, image,
  sx0, sy0, sx1, sy1, sx2, sy2,
  dx0, dy0, dx1, dy1, dx2, dy2) {
  // 计算源矩阵A（2x2）和位移s0
  const ax = sx1 - sx0; const bx = sx2 - sx0;
  const ay = sy1 - sy0; const by = sy2 - sy0;
  const det = ax * by - bx * ay;
  if (!det) return;
  const invDet = 1.0 / det;
  // A^{-1}
  const a11 =  by * invDet;   // (sy2 - sy0)/det
  const a12 = -bx * invDet;   // -(sx2 - sx0)/det
  const a21 = -ay * invDet;   // -(sy1 - sy0)/det
  const a22 =  ax * invDet;   // (sx1 - sx0)/det

  // 目标矩阵B（2x2）和位移d0
  const ux = dx1 - dx0; const vx = dx2 - dx0;
  const uy = dy1 - dy0; const vy = dy2 - dy0;

  // M = B * A^{-1}
  const m11 = ux * a11 + vx * a21;
  const m12 = ux * a12 + vx * a22;
  const m21 = uy * a11 + vy * a21;
  const m22 = uy * a12 + vy * a22;

  // e = d0 - M * s0
  const e  = dx0 - (m11 * sx0 + m12 * sy0);
  const f  = dy0 - (m21 * sx0 + m22 * sy0);

  ctx.save();
  // 裁剪到目标三角形
  ctx.beginPath();
  ctx.moveTo(dx0, dy0);
  ctx.lineTo(dx1, dy1);
  ctx.lineTo(dx2, dy2);
  ctx.closePath();
  ctx.clip();

  // 设置从源像素到目标的仿射变换
  ctx.setTransform(m11, m21, m12, m22, e, f);
  // 绘制整张源图（只显示裁剪区域）
  ctx.drawImage(image, 0, 0);
  ctx.restore();
}

/**
 * 解析SVG路径数据，提取坐标点
 */
function parsePathData(pathData) {
  const points = [];
  const commands = pathData.match(/[MmLlHhVvCcSsQqTtAaZz][^MmLlHhVvCcSsQqTtAaZz]*/g);
  
  if (!commands) return points;
  
  commands.forEach(command => {
    const type = command[0];
    const coords = command.slice(1).trim().split(/[\s,]+/).filter(n => n !== '');
    
    // 添加命令标记
    points.push({ type: 'command', command: type });
    
    // 提取坐标点
    for (let i = 0; i < coords.length; i += 2) {
      if (i + 1 < coords.length) {
        const x = parseFloat(coords[i]);
        const y = parseFloat(coords[i + 1]);
        if (!isNaN(x) && !isNaN(y)) {
          points.push({ type: 'point', x, y, originalX: x, originalY: y });
        }
      }
    }
  });
  
  return points;
}

/**
 * 重构SVG路径数据
 */
function reconstructPathData(points) {
  let pathData = '';
  let currentCommand = '';
  let coordBuffer = [];
  
  points.forEach(point => {
    if (point.type === 'command') {
      // 输出之前的命令和坐标
      if (currentCommand && coordBuffer.length > 0) {
        pathData += currentCommand + coordBuffer.join(' ');
      }
      
      // 开始新命令
      currentCommand = point.command;
      coordBuffer = [];
    } else if (point.type === 'point') {
      // 添加坐标到缓冲区
      coordBuffer.push(point.x.toFixed(2), point.y.toFixed(2));
    }
  });
  
  // 输出最后的命令
  if (currentCommand && coordBuffer.length > 0) {
    pathData += currentCommand + coordBuffer.join(' ');
  }
  
  return pathData;
}

/**
 * 路径级变形实现（回退方案）
 */
function applyPathLevelDeformation() {
  const paths = gridTransform.svgElement.querySelectorAll('path, circle, rect, line, polygon, polyline');
  console.log(`🎨 路径级变形：处理 ${paths.length} 个元素`);
  
  paths.forEach((element, index) => {
    try {
      // 获取路径数据
      if (element.tagName === 'path') {
        const pathData = element.getAttribute('d');
        if (pathData) {
          const deformedPath = deformPathData(pathData);
          element.setAttribute('d', deformedPath);
        }
      } else {
        // 对其他元素应用变形
        const bbox = element.getBBox();
        const centerX = bbox.x + bbox.width / 2;
        const centerY = bbox.y + bbox.height / 2;
        
        const deformed = applyBilinearInterpolation(centerX, centerY);
        const dx = deformed[0] - centerX;
        const dy = deformed[1] - centerY;
        
        if (Math.abs(dx) > 0.1 || Math.abs(dy) > 0.1) {
          element.style.transform = `translate(${dx}px, ${dy}px)`;
        }
      }
    } catch (e) {
      console.warn(`路径 ${index} 变形失败:`, e);
    }
  });
  
  console.log('✅ 路径级变形已应用');
}

/**
 * 双线性插值变形算法
 */
function applyBilinearInterpolation(x, y) {
  if (!gridTransform.backgroundImage) {
    return [x, y];
  }
  
  const img = gridTransform.backgroundImage;
  const size = gridTransform.size;
  
  // 转换为相对坐标
  const relX = (x - img.x) / img.width;
  const relY = (y - img.y) / img.height;
  
  // 边界检查
  if (relX < 0 || relX > 1 || relY < 0 || relY > 1) {
    return [x, y];
  }
  
  // 网格位置
  const gridX = relX * (size - 1);
  const gridY = relY * (size - 1);
  
  // 四个角点索引
  const x1 = Math.floor(gridX);
  const y1 = Math.floor(gridY);
  const x2 = Math.min(x1 + 1, size - 1);
  const y2 = Math.min(y1 + 1, size - 1);
  
  // 获取四个控制点
  const p1 = gridTransform.controlPoints[y1 * size + x1];
  const p2 = gridTransform.controlPoints[y1 * size + x2];
  const p3 = gridTransform.controlPoints[y2 * size + x1];
  const p4 = gridTransform.controlPoints[y2 * size + x2];
  
  if (!p1 || !p2 || !p3 || !p4) {
    return [x, y];
  }
  
  // 插值权重
  const wx = gridX - x1;
  const wy = gridY - y1;
  
  // 计算位移
  const dx1 = p1.x - p1.originalX;
  const dy1 = p1.y - p1.originalY;
  const dx2 = p2.x - p2.originalX;
  const dy2 = p2.y - p2.originalY;
  const dx3 = p3.x - p3.originalX;
  const dy3 = p3.y - p3.originalY;
  const dx4 = p4.x - p4.originalX;
  const dy4 = p4.y - p4.originalY;
  
  // 双线性插值
  const dx = dx1 * (1 - wx) * (1 - wy) + 
            dx2 * wx * (1 - wy) + 
            dx3 * (1 - wx) * wy + 
            dx4 * wx * wy;
            
  const dy = dy1 * (1 - wx) * (1 - wy) + 
            dy2 * wx * (1 - wy) + 
            dy3 * (1 - wx) * wy + 
            dy4 * wx * wy;
  
  // 应用变形强度
  const strength = gridTransform.deformStrength || 1.0;
  
  return [x + dx * strength, y + dy * strength];
}

/**
 * 变形路径数据
 */
function deformPathData(pathData) {
  // 解析路径命令并变形坐标点
  return pathData.replace(/([ML])\s*([\d.-]+)\s*,?\s*([\d.-]+)/g, (match, command, x, y) => {
    const deformed = applyBilinearInterpolation(parseFloat(x), parseFloat(y));
    return `${command}${deformed[0].toFixed(2)},${deformed[1].toFixed(2)}`;
  });
}

/**
 * 变形点函数 - 核心变形算法
 */
function deformPoint(x, y) {
  if (!gridTransform.controlPoints || !gridTransform.backgroundImage) {
    console.log('⚠️ deformPoint: 缺少控制点或背景图像');
    return [x, y];
  }
  
  const img = gridTransform.backgroundImage;
  const size = gridTransform.size;
  
  console.log(`🔍 deformPoint: 输入点(${x}, ${y}), 图像区域(${img.x}, ${img.y}, ${img.width}x${img.height})`);
  
  // 将SVG坐标转换为相对于网格的坐标
  const relX = (x - img.x) / img.width;
  const relY = (y - img.y) / img.height;
  
  console.log(`📐 相对坐标: (${relX.toFixed(3)}, ${relY.toFixed(3)})`);
  
  // 如果点在网格范围外，不进行变形
  if (relX < 0 || relX > 1 || relY < 0 || relY > 1) {
    console.log('🚫 点在网格范围外，不变形');
    return [x, y];
  }
  
  // 计算在网格中的位置
  const gridX = relX * (size - 1);
  const gridY = relY * (size - 1);
  
  // 获取周围的四个控制点
  const x1 = Math.floor(gridX);
  const y1 = Math.floor(gridY);
  const x2 = Math.min(x1 + 1, size - 1);
  const y2 = Math.min(y1 + 1, size - 1);
  
  // 获取四个角点
  const p1 = gridTransform.controlPoints[y1 * size + x1];
  const p2 = gridTransform.controlPoints[y1 * size + x2];
  const p3 = gridTransform.controlPoints[y2 * size + x1];
  const p4 = gridTransform.controlPoints[y2 * size + x2];
  
  if (!p1 || !p2 || !p3 || !p4) {
    console.log('❌ 无法获取四个角点');
    return [x, y];
  }
  
  // 双线性插值权重
  const wx = gridX - x1;
  const wy = gridY - y1;
  
  // 计算四个角点的位移
  const dx1 = p1.x - p1.originalX;
  const dy1 = p1.y - p1.originalY;
  const dx2 = p2.x - p2.originalX;
  const dy2 = p2.y - p2.originalY;
  const dx3 = p3.x - p3.originalX;
  const dy3 = p3.y - p3.originalY;
  const dx4 = p4.x - p4.originalX;
  const dy4 = p4.y - p4.originalY;
  
  console.log(`📊 角点位移: p1(${dx1.toFixed(1)},${dy1.toFixed(1)}) p2(${dx2.toFixed(1)},${dy2.toFixed(1)}) p3(${dx3.toFixed(1)},${dy3.toFixed(1)}) p4(${dx4.toFixed(1)},${dy4.toFixed(1)})`);
  
  // 双线性插值计算位移
  const dx = dx1 * (1 - wx) * (1 - wy) + 
            dx2 * wx * (1 - wy) + 
            dx3 * (1 - wx) * wy + 
            dx4 * wx * wy;
            
  const dy = dy1 * (1 - wx) * (1 - wy) + 
            dy2 * wx * (1 - wy) + 
            dy3 * (1 - wx) * wy + 
            dy4 * wx * wy;
  
  // 应用变形强度
  const strength = gridTransform.deformStrength || 1.0;
  const finalDx = dx * strength;
  const finalDy = dy * strength;
  
  console.log(`🎯 最终位移: (${finalDx.toFixed(1)}, ${finalDy.toFixed(1)})`);
  
  return [x + finalDx, y + finalDy];
}

/**
 * 获取点在网格中的位置
 */
function getGridPosition(x, y) {
  if (!gridTransform.backgroundImage) return null;
  
  const img = gridTransform.backgroundImage;
  const relX = (x - img.x) / img.width;
  const relY = (y - img.y) / img.height;
  
  if (relX < 0 || relX > 1 || relY < 0 || relY > 1) return null;
  
  return { relX, relY };
}

/**
 * 双线性插值变形
 */
function bilinearInterpolation(x, y, gridPos) {
  const size = gridTransform.size;
  const { relX, relY } = gridPos;
  
  // 计算网格索引
  const gridX = relX * (size - 1);
  const gridY = relY * (size - 1);
  
  const x1 = Math.floor(gridX);
  const y1 = Math.floor(gridY);
  const x2 = Math.min(x1 + 1, size - 1);
  const y2 = Math.min(y1 + 1, size - 1);
  
  // 获取四个角点的位移
  const p1 = gridTransform.controlPoints[y1 * size + x1];
  const p2 = gridTransform.controlPoints[y1 * size + x2];
  const p3 = gridTransform.controlPoints[y2 * size + x1];
  const p4 = gridTransform.controlPoints[y2 * size + x2];
  
  if (!p1 || !p2 || !p3 || !p4) return [x, y];
  
  // 计算权重
  const wx = gridX - x1;
  const wy = gridY - y1;
  
  // 双线性插值
  const dx1 = p1.x - p1.originalX;
  const dy1 = p1.y - p1.originalY;
  const dx2 = p2.x - p2.originalX;
  const dy2 = p2.y - p2.originalY;
  const dx3 = p3.x - p3.originalX;
  const dy3 = p3.y - p3.originalY;
  const dx4 = p4.x - p4.originalX;
  const dy4 = p4.y - p4.originalY;
  
  const dx = dx1 * (1 - wx) * (1 - wy) + dx2 * wx * (1 - wy) + dx3 * (1 - wx) * wy + dx4 * wx * wy;
  const dy = dy1 * (1 - wx) * (1 - wy) + dy2 * wx * (1 - wy) + dy3 * (1 - wx) * wy + dy4 * wx * wy;
  
  return [x + dx, y + dy];
}

/**
 * 重置网格变形
 */
function resetGridTransform() {
  console.log('🔄 开始重置网格变形');
  
  if (!gridTransform.controlPoints) {
    console.warn('❌ 无法重置：控制点不存在');
    return;
  }
  
  // 重置所有控制点到原始位置
  gridTransform.controlPoints.forEach(point => {
    point.x = point.originalX;
    point.y = point.originalY;
  });
  
  // 更新点数组
  updatePointArrays();
  
  // 完全重置SVG变形
  if (gridTransform.svgElement && gridTransform.originalSVG) {
    try {
      // 恢复原始SVG内容
      const container = document.getElementById('gridSvgContainer');
      if (container) {
        container.innerHTML = gridTransform.originalSVG;
        
        // 重新获取SVG元素
        gridTransform.svgElement = container.querySelector('svg');
        
        if (gridTransform.svgElement && gridTransform.backgroundImage) {
          // 重新设置SVG样式和位置
          gridTransform.svgElement.style.position = 'absolute';
          gridTransform.svgElement.style.left = gridTransform.backgroundImage.x + 'px';
          gridTransform.svgElement.style.top = (gridTransform.backgroundImage.y + 50) + 'px';
          gridTransform.svgElement.style.width = gridTransform.backgroundImage.width + 'px';
          gridTransform.svgElement.style.height = gridTransform.backgroundImage.height + 'px';
          gridTransform.svgElement.style.pointerEvents = 'none';
          
          console.log('✅ SVG已重置到原始状态');
        }
      }
    } catch (e) {
      console.error('❌ SVG重置失败:', e);
    }
  }
  
  // 重绘网格
  drawGrid();
  
  // 保存重置后的状态
  GridStateManager.save();
  try { syncGridStateToServer(GridStateManager.getState()); } catch(e) {}
  
  // 重新渲染整图变形
  applyWholeImageWarp();
  
  updateGridStatus('网格已重置到原始状态', 'success');
  console.log('✅ 网格重置完成');
  
  // 显示重置提示
  if (typeof showToast === 'function') {
    showToast('网格已重置', 'success', 1500);
  }
}

/**
 * 更新网格状态显示
 */
function updateGridStatus(message, type = 'info') {
  const statusElement = document.getElementById('gridStatus');
  if (statusElement) {
    statusElement.textContent = message;
    statusElement.className = `grid-status ${type}`;
  }
  
  console.log(`[Grid] ${message}`);
}

/**
 * 保持向后兼容的函数
 */
function loadGridTransformSettings() {
  return GridStateManager.load();
}

// 导出主要函数供外部使用
window.GridTransform = {
  initialize: initializeGridTransform,
  reset: resetGridTransform,
  getState: () => GridStateManager.getState(),
  loadImage: loadImageToGridCanvas,
  autoLoad: autoLoadD1ToGrid
};

// 初始化函数
function initGridTransform() {
    // 确保状态管理器已初始化
    if (typeof window.initStateManager === 'function') {
        window.initStateManager();
    }
    
    // 如果已经初始化过，直接返回
    if (gridTransform.initialized) {
        return;
    }
    
    // 标记为已初始化
    gridTransform.initialized = true;
    
    console.log('✅ 网格变形模块已初始化');
}

// DOM加载完成后自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGridTransform);
} else {
    initGridTransform();
}

// 导出初始化函数、状态管理器和核心对象
window.initGridTransform = initGridTransform;
window.GridStateManager = GridStateManager;
window.gridTransform = gridTransform;

// 导出关键函数供全局使用
window.openGridTransformModal = openGridTransformModal;
window.closeGridTransformModal = closeGridTransformModal;
window.resetGridTransform = resetGridTransform;
window.createGridPoints = createGridPoints;
window.drawGrid = drawGrid;
window.loadImageToGridCanvas = loadImageToGridCanvas;
window.updateGridSize = updateGridSize;
window.updateDeformStrength = updateDeformStrength;

// 已移除“生成D1”按钮；使用主界面D1按钮触发

// 生成D1：将当前网格变形保存为新的D1版本（覆盖处理后的中轴）
window.generateD1FromGrid = async function() {
  try {
    console.log('[GRID] Début génération D1 (warp de C)');
    const state = GridStateManager.getState();
    const charInput = document.querySelector('input[name="char"]');
    const ch = charInput ? charInput.value.trim() : '';
    if (!ch) {
      console.error('[GRID] Aucun caractère saisi');
      if (typeof showToast === 'function') showToast('请先输入字符', 'error');
      return;
    }
    // 保存网格状态
    GridStateManager.save();
    // 仅生成D1，携带网格状态
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    console.log('[GRID] POST /api/gen_single', { char: ch, type: 'D1' });
    const resp = await fetch('/api/gen_single', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ char: ch, type: 'D1', grid_state: state }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    console.log('[GRID] Réponse /api/gen_single status=', resp.status);
    if (resp.ok) {
      const data = await resp.json();
      console.log('[GRID] D1 URL:', data && data.url);
      if (typeof showToast === 'function') showToast('D1生成完成', 'success');
      // 刷新预览
      if (window.previewCardManager && data.url) {
        const ts = Date.now();
        // D1生成的文件显示在“网格变形 (D1)”窗口
        window.previewCardManager.setCardImage('D2', data.url + '?ts=' + ts);
      }
    } else {
      const text = await resp.text().catch(() => '');
      throw new Error('生成失败, status=' + resp.status + ' ' + text);
    }
  } catch (e) {
    console.error('生成D1失败:', e);
    if (typeof showToast === 'function') showToast('生成D1失败: ' + e.message, 'error');
  }
}

/**
 * 更新网格大小
 */
function updateGridSize() {
  const sizeSelect = document.getElementById('gridSize');
  if (!sizeSelect) return;
  
  const newSize = parseInt(sizeSelect.value);
  if (newSize && newSize !== gridTransform.size) {
    console.log('[GRID_TRANSFORM] 网格大小从', gridTransform.size, '更新为', newSize);
    gridTransform.size = newSize;
    
    // 重新创建控制点
    createGridPoints();
    
    // 重绘网格
    if (gridTransform.gridVisible) {
      drawGrid();
    }
    
    // 立即保存状态（包括新的网格大小）
    if (window.gridStateManager) {
      window.gridStateManager.save();
      console.log('[GRID_TRANSFORM] 网格大小已保存到localStorage');
    }
    
    updateGridStatus(`网格大小已更新为 ${newSize}×${newSize}`);
    
    // 显示保存提示
    if (window.toastManager) {
      window.toastManager.show('grid.size.updated', `网格大小已更新为 ${newSize}×${newSize}`);
    }
    
    // 应用整图变形
    applyWholeImageWarp();
  }
}

/**
 * 更新变形强度
 */
function updateDeformStrength() {
  const strengthSlider = document.getElementById('deformStrength');
  const strengthValue = document.getElementById('strengthValue');
  
  if (!strengthSlider) return;
  // 强制锁定为1.0，忽略任何修改
  strengthSlider.value = '1.0';
  if (strengthValue) strengthValue.textContent = '1.0';
  gridTransform.deformStrength = 1.0;
  return;
}

console.log('✅ 网格变形模块已加载');
