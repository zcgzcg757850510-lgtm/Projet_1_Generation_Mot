/**
 * 生成服务模块 - Generation Service Module
 * 提供D1/D2生成、文章生成等核心生成功能
 */

/**
 * 生成服务类
 */
class GenerationService {
  constructor() {
    this.currentChar = '';
  }

  /**
   * 更新当前字符
   */
  updateCurrentChar() {
    const charInput = document.querySelector('input[name="char"]');
    this.currentChar = charInput ? charInput.value.trim() : '';
    return this.currentChar;
  }

  /**
   * 生成D2
   */
  async generateD2() {
    updateTestWindow('开始生成D2');
    
    // 更新当前字符
    this.updateCurrentChar();
    
    if (!this.currentChar) {
      updateTestWindow('❌ 请先输入字符');
      return;
    }

    updateTestWindow(`正在为字符 "${this.currentChar}" 生成D2...`);

    try {
      // 在调用前保存网格状态到后端可访问的位置
      if (typeof window.gridStateManager !== 'undefined' && window.gridStateManager.hasDeformation()) {
        const gridState = window.gridStateManager.getState();
        let canvasDimensions = { width: 800, height: 600 };
        
        if (typeof gridTransform !== 'undefined' && gridTransform.canvas) {
          canvasDimensions = {
            width: gridTransform.canvas.width,
            height: gridTransform.canvas.height
          };
        }
        
        // 保存网格状态到后端可访问的临时存储
        const gridData = {
          gridState: gridState,
          canvasDimensions: canvasDimensions,
          character: this.currentChar
        };
        
        // 发送POST请求，包含网格状态
        const response = await fetch('/gen', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            char: this.currentChar,
            type: 'D2',
            gridState: gridData
          })
        });
        
        const result = await response.json();
        
        if (result.success) {
          const fillResult = {
            success: true,
            filename: result.filename,
            filepath: result.file_path || result.filepath
          };
          showD2Result(fillResult);
        } else {
          updateTestWindow(`❌ D2生成失败: ${result.error}`);
        }
      } else {
        // 没有网格变形，使用普通GET请求
        const response = await fetch(`/gen?char=${encodeURIComponent(this.currentChar)}&type=D2`);
        const result = await response.json();
        
        if (result.success) {
          showD2Result(result);
        } else {
          updateTestWindow(`❌ D2生成失败: ${result.error}`);
        }
      }
    } catch (error) {
      console.error('D2生成错误:', error);
      updateTestWindow(`❌ D2生成失败: ${error.message}`);
    }
  }

  /**
   * 生成文章
   */
  async generateArticle() {
    const text = document.getElementById('articleText').value.trim();
    if (!text) {
      alert('请输入要生成的文章内容');
      return;
    }

    // 获取当前字符作为参考字符
    const charInput = document.querySelector('input[name="char"]');
    const currentChar = charInput ? charInput.value.trim() : '';

    // Show progress bar
    const progressBar = document.getElementById('articleProgress');
    const progressFill = progressBar.querySelector('.progress-fill');
    progressBar.classList.remove('hidden');
    progressFill.style.width = '0%';

    // Animate progress bar
    let progress = 0;
    const progressInterval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress > 90) progress = 90;
      progressFill.style.width = progress + '%';
    }, 200);

    try {
      const params = {
        text: text,
        fontSize: document.getElementById('fontSize').value,
        lineSpacing: document.getElementById('lineSpacing').value,
        charSpacing: document.getElementById('charSpacing').value,
        backgroundType: document.querySelector('input[name="backgroundType"]:checked').value,
        referenceChar: currentChar
      };
      
      // Send request to backend
      const response = await fetch('/generate_article', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(params)
      });

      const result = await response.json();
      
      // Complete progress bar
      clearInterval(progressInterval);
      progressFill.style.width = '100%';
      
      if (result.success) {
        // Display preview
        const preview = document.getElementById('articlePreview');
        preview.innerHTML = `<img src="${result.svg_url}?t=${Date.now()}" alt="Generated Article" style="max-width: 100%; height: auto;">`;
        
        // Add download functionality
        const downloadBtn = document.getElementById('btnDownloadArticle');
        downloadBtn.onclick = function() {
          const link = document.createElement('a');
          link.href = result.svg_url;
          link.download = 'article_' + Date.now() + '.svg';
          link.click();
        };
      } else if (result.imageUrl) {
        // 兼容旧的PNG格式
        preview.style.backgroundImage = 'none';
        preview.innerHTML = `<img src="${result.imageUrl}?t=${Date.now()}" alt="Generated Article" style="max-width: 100%; height: auto;">`;
        
        // Add download functionality for PNG
        const downloadBtn = document.getElementById('btnDownloadArticle');
        downloadBtn.onclick = function() {
          const link = document.createElement('a');
          link.href = result.imageUrl;
          link.download = 'article_' + Date.now() + '.png';
          link.click();
        };
      }
      
      // Hide progress bar after a delay
      setTimeout(() => {
        progressBar.classList.add('hidden');
      }, 1000);

    } catch (error) {
      clearInterval(progressInterval);
      progressBar.classList.add('hidden');
      console.error('Article generation error:', error);
      alert('文章生成失败: ' + error.message);
    }
  }

  /**
   * 从网格变形工具生成D2 (保持向后兼容)
   */
  generateD2FromGrid() {
    // 确保使用主界面最新字符
    const charInput = document.querySelector('input[name="char"]');
    const currentChar = charInput?.value?.trim();
    
    if (!currentChar) {
      updateTestWindow('❌ 请先在主界面输入字符');
      return;
    }
    
    this.currentChar = currentChar;
    updateTestWindow(`使用主界面字符: ${currentChar}`);
    
    this.generateD2();
  }

  /**
   * 新的D2生成按钮功能
   */
  generateNewD2() {
    console.log('🚀 新D2按钮被点击');
    
    // 获取当前字符
    const charInput = document.querySelector('input[name="char"]');
    const currentChar = charInput?.value?.trim();
    
    if (!currentChar) {
      updateTestWindow('❌ 请先输入字符');
      if (typeof showToast !== 'undefined') {
        showToast('请先输入字符', 'warning');
      }
      return;
    }
    
    updateTestWindow(`🎯 新D2生成: ${currentChar}`);
    
    // 可以在这里实现新的D2生成逻辑
    // 目前复用现有的D2生成逻辑
    this.currentChar = currentChar;
    this.generateD2();
  }

  /**
   * 生成D1 - 主要生成函数
   */
  async generateD1() {
    console.log('🚀 D1按钮被点击');
    
    // 获取当前字符
    const charInput = document.querySelector('input[name="char"]');
    const currentChar = charInput ? charInput.value.trim() : '';
    
    if (!currentChar || currentChar.length !== 1) {
      alert('请输入单个汉字');
      return;
    }
    
    console.log(`🎯 目标字符: ${currentChar}`);
    
    try {
      // 保存表单参数
      const form = document.querySelector('form');
      if (form) {
        form.querySelectorAll('input').forEach((el) => {
          if (!el.name) return;
          let val = '';
          if (el.type === 'checkbox') { 
            val = el.checked ? '1' : '0'; 
          } else { 
            val = el.value || ''; 
          }
          if (typeof setPref !== 'undefined') {
            setPref(el.name, val);
          }
        });
      }
      
      // 检查网格变形状态
      let gridState = null;
      if (typeof window.gridStateManager !== 'undefined' && window.gridStateManager.hasDeformation()) {
        gridState = window.gridStateManager.getState();
        console.log('🔄 检测到网格变形状态');
        if (gridState && (!gridState.canvas_dimensions || !gridState.canvas_dimensions.width)) {
          try {
            const dims = {
              width: (window.gridTransform && window.gridTransform.canvas && window.gridTransform.canvas.width) ? window.gridTransform.canvas.width : 800,
              height: (window.gridTransform && window.gridTransform.canvas && window.gridTransform.canvas.height) ? window.gridTransform.canvas.height : 600
            };
            gridState.canvas_dimensions = dims;
          } catch (e) {
            console.warn('⚠️ 计算画布尺寸失败:', e);
          }
        }
      }
      
      const requestBody = { char: currentChar, type: 'D1' };
      if (gridState) {
        requestBody.grid_state = gridState;
      }
      
      // 发送请求
      const response = await fetch('/api/gen_single', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody),
        cache: 'no-store'
      });
      
      if (!response.ok) {
        const txt = await response.text();
        console.error('生成失败', txt);
        console.error('生成失败：' + txt);
        return;
      }
      
      const data = await response.json();
      console.log('📥 服务器响应:', data);
      
      // 更新预览卡片
      if (window.previewCardManager) {
        const withTs = (u) => u ? (u + (u.includes('?') ? '&' : '?') + 'ts=' + Date.now()) : u;
        if (data.url) {
          window.previewCardManager.updateCard('D1', withTs(data.url));
        }
        if (data.base_url) {
          console.log('📁 D1基础版本:', data.base_url);
        }
      }
      
      console.log('✅ D1生成完成');
      
      // 确保所有现有SVG文件都已加载到预览窗口
      if (window.previewManager) {
        setTimeout(() => {
          window.previewManager.loadExistingSVGs();
        }, 500);
      }
      
      // 显示成功提示
      if (typeof showToast !== 'undefined') {
        showToast('生成完成', 'success');
      }
      
    } catch (error) {
      console.error('D1生成错误:', error);
      console.error('生成出错：' + error.message);
    }
  }

  /**
   * 纯调用D2按钮 - 只有调用接口和显示结果两个功能
   */
  async generateD2WithNewInterface() {
    updateTestWindow('🚀 D2按钮被点击，开始执行...');
    console.log('🚀 D2按钮被点击');
    
    // 获取当前字符
    const charInput = document.querySelector('input[name="char"]');
    const currentChar = charInput ? charInput.value.trim() : '';
    
    if (!currentChar) {
      updateTestWindow('❌ 请先输入字符');
      return;
    }
    
    updateTestWindow(`🎯 目标字符: ${currentChar}`);
    
    try {
      // 检查是否有网格变形
      let hasGridDeformation = false;
      let gridStateData = null;
      
      if (typeof window.gridStateManager !== 'undefined') {
        hasGridDeformation = window.gridStateManager.hasDeformation();
        if (hasGridDeformation) {
          gridStateData = window.gridStateManager.getState();
          updateTestWindow('🔄 检测到网格变形，将应用到D2生成');
        }
      }
      
      let response;
      
      if (hasGridDeformation && gridStateData) {
        // 有网格变形，使用POST请求
        updateTestWindow('📤 发送POST请求（包含网格变形数据）...');
        
        response = await fetch('/gen', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            char: currentChar,
            type: 'D2',
            gridState: gridStateData
          })
        });
      } else {
        // 无网格变形，使用GET请求
        updateTestWindow('📤 发送GET请求...');
        
        response = await fetch(`/gen?char=${encodeURIComponent(currentChar)}&type=D2`);
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      updateTestWindow(`📥 服务器响应: ${JSON.stringify(result, null, 2)}`);
      
      if (result.success) {
        updateTestWindow('✅ D2生成成功！');
        
        // 显示结果
        showD2Result({
          success: true,
          filename: result.filename,
          filepath: result.file_path || result.filepath || result.file
        });
        
      } else {
        updateTestWindow(`❌ D2生成失败: ${result.error || '未知错误'}`);
      }
      
    } catch (error) {
      console.error('D2生成错误:', error);
      updateTestWindow(`❌ D2生成异常: ${error.message}`);
    }
  }
}

/**
 * 显示D2生成结果
 */
function showD2Result(result) {
  if (!result.success) {
    updateTestWindow('❌ D2生成失败');
    return;
  }

  const filename = result.filename;
  const filepath = result.filepath;
  
  updateTestWindow(`✅ D2生成完成: ${filename}`);
  updateTestWindow(`📁 文件路径: ${filepath}`);
  
  // 自动加载到主界面的imgD2元素
  const imgD2 = document.getElementById('imgD2');
  if (imgD2 && filepath) {
    const url = filepath.startsWith('/') ? filepath : '/' + filepath;
    const timestampedUrl = url + '?t=' + Date.now();
    
    updateTestWindow(`🔄 正在加载D2到主界面: ${timestampedUrl}`);
    
    imgD2.onerror = function() {
      updateTestWindow(`❌ D2文件加载失败: ${filename || 'unknown'}`);
      updateTestWindow(`失败的URL: ${url}`);
      imgD2.style.opacity = '0.5'; 
    }; 
    
    imgD2.onload = () => {      
      imgD2.style.opacity = '1'; 
      console.log('✅ D2文件已成功加载到主界面');
      updateTestWindow(`✅ D2文件已成功加载到主界面: ${filename || 'D2文件'}`);
    }; 
    
    imgD2.src = timestampedUrl; 
    imgD2.style.display = 'block';
  }
  
  // 同时尝试加载到网格变形的D2窗口
  const gridD2Element = document.querySelector('#dragTransformModal .d2-preview img');
  if (gridD2Element && filepath) {
    const url = filepath.startsWith('/') ? filepath : '/' + filepath;
    const timestampedUrl = url + '?t=' + Date.now();
    
    const setImg = (el, url, filename) => {
      el.onerror = function() {
        updateTestWindow(`❌ D2文件加载失败: ${filename || 'unknown'}`);
        updateTestWindow(`失败的URL: ${url}`);
        el.style.opacity = '0.5'; 
      }; 
      
      el.onload = () => {      
        el.style.opacity = '1'; 
        console.log('✅ D2文件已成功加载到网格变形(D2)窗口');
        updateTestWindow(`✅ D2文件已自动填充到网格变形(D2)窗口: ${filename || 'D2文件'}`);
      }; 
      
      el.src = url; 
      el.style.display = 'block';
    };
    
    // 使用setImg函数加载D2图片
    updateTestWindow(`正在加载D2文件: ${filename || 'D2文件'}`);
    setImg(gridD2Element, timestampedUrl, filename);
  }
}

// 延迟初始化生成服务
let generationService = null;

// 初始化函数
function initGenerationService() {
    if (!generationService) {
        // 确保状态管理器已初始化
        if (typeof window.initStateManager === 'function') {
            window.initStateManager();
        }
        
        generationService = new GenerationService();
        
        // 更新全局导出
        window.GenerationService = {
            generateD1: () => generationService.generateD1(),
            generateD2: () => generationService.generateD2(),
            generateD2FromGrid: () => generationService.generateD2FromGrid(),
            generateNewD2: () => generationService.generateNewD2(),
            generateD2WithNewInterface: () => generationService.generateD2WithNewInterface(),
            generateArticle: () => generationService.generateArticle(),
            showD2Result: showD2Result
        };
        
        // 保持向后兼容的全局函数
        window.genOnce = () => generationService.generateD1();
        window.generateD2FromGrid = () => generationService.generateD2FromGrid();
        window.generateNewD2 = () => generationService.generateNewD2();
        window.generateD2WithNewInterface = () => generationService.generateD2WithNewInterface();
        window.generateArticle = () => generationService.generateArticle();
        window.showD2Result = showD2Result;
        
        console.log('✅ 生成服务模块已初始化');
    }
    return generationService;
}

// DOM加载完成后自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGenerationService);
} else {
    initGenerationService();
}

// 导出初始化函数
window.initGenerationService = initGenerationService;

console.log('✅ 生成服务模块已加载');
