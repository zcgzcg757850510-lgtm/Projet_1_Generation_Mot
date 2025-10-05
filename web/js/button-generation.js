/**
 * 按钮生成模块 - Button Generation Module
 * 处理A、B、C、D1、D2、全部按钮的生成功能
 */

/**
 * 按钮生成管理器
 */
class ButtonGenerationManager {
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
   * 验证字符输入
   */
  validateChar() {
    this.updateCurrentChar();
    if (!this.currentChar) {
      console.error('❌ 请先输入一个字符');
      if (typeof showToast !== 'undefined') {
        showToast('请先输入一个字符', 'error');
      }
      return false;
    }
    return true;
  }

  /**
   * 生成单个图像类型
   * @param {string} type - 图像类型 (A, B, C, D1, D2)
   * @param {string} description - 图像描述
   */
  async generateSingle(type, description) {
    if (!this.validateChar()) return;

    console.log(`🔄 开始生成${type}图（${description}）`);
    if (typeof showToast !== 'undefined') {
      showToast(`正在生成${type}图...`, 'info');
    }

    try {
      const response = await fetch('/api/gen_single', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          char: this.currentChar,
          type: type
        })
      });

      if (response.ok) {
        const result = await response.json();
        console.log(`✅ ${type}图生成成功:`, result);

        // 更新预览 - 根据按钮类型映射到正确的窗口ID
        if (window.previewCardManager && result.url) {
          const timestamp = Date.now();
          // 生成类型到窗口ID的映射 - 与generateAll保持一致！
          const buttonToWindowMap = {
            'A': 'A',   // 后端A(轮廓) -> A窗口(轮廓)
            'B': 'C',   // 后端B(原始中轴) -> C窗口(原始中轴 B)
            'C': 'D1',  // 后端C(处理中轴) -> D1窗口(处理中轴 C)
            'D1': 'D2', // 后端D1(网格变形) -> D2窗口(网格变形 D1)
            'D2': 'B'   // 后端D2(中轴填充) -> B窗口(中轴填充 D2)
          };
          const windowId = buttonToWindowMap[type] || type;
          const finalUrl = result.url + '?ts=' + timestamp;
          console.log(`🔍 [DEBUG] Individual generation - Type: ${type}, WindowId: ${windowId}, URL: ${finalUrl}`);
          window.previewCardManager.setCardImage(windowId, finalUrl);
        }

        if (typeof showToast !== 'undefined') {
          showToast(`${type}图生成完成`, 'success');
        }
      } else {
        throw new Error(`${type}图生成失败`);
      }
    } catch (error) {
      console.error(`❌ ${type}图生成错误:`, error);
      if (typeof showToast !== 'undefined') {
        showToast(`${type}图生成失败: ${error.message}`, 'error');
      }
    }
  }

  /**
   * 生成A图（轮廓）
   */
  async generateA() {
    await this.generateSingle('A', '轮廓');  // A按钮生成A类型
  }

  /**
   * 生成B图（原始中轴线的有色渲染）
   */
  async generateB() {
    await this.generateSingle('B', '原始中轴');  // B按钮生成B类型
  }

  /**
   * 生成C图（原始中轴线）
   */
  async generateC() {
    await this.generateSingle('C', '处理中轴线');  // C按钮生成C类型
  }

  /**
   * 生成D1图（网格变形）
   */
  async generateD1() {
    // 附带当前网格状态（若存在）
    const opts = { type: 'D1' };
    try {
      let gridState = null;
      // 1) 优先通过全局 gridStateManager 获取（标准路径）
      if (window.gridStateManager && typeof window.gridStateManager.getState === 'function') {
        gridState = window.gridStateManager.getState();
      }
      // 2) 若为空，尝试从 localStorage 回退读取
      if ((!gridState || !gridState.controlPoints || gridState.controlPoints.length === 0) && typeof localStorage !== 'undefined') {
        const saved = localStorage.getItem('gridTransform_state');
        if (saved) {
          try { gridState = JSON.parse(saved); } catch (e) {}
        }
      }
      // 3) 若仍为空，直接从 window.gridTransform 读取当前内存状态构造
      if ((!gridState || !gridState.controlPoints || gridState.controlPoints.length === 0) && window.gridTransform && Array.isArray(window.gridTransform.controlPoints) && window.gridTransform.controlPoints.length > 0) {
        gridState = {
          controlPoints: window.gridTransform.controlPoints.map(p => ({ x: p.x, y: p.y, originalX: p.originalX ?? p.x, originalY: p.originalY ?? p.y })),
          size: window.gridTransform.size,
          deformStrength: window.gridTransform.deformStrength
        };
      }
      // 仅当存在控制点时附带（是否有形变由后端再判定）
      if (gridState && Array.isArray(gridState.controlPoints) && gridState.controlPoints.length > 0) {
        // 附带画布尺寸，便于后端正确映射
        try {
          const dims = {
            width: (window.gridTransform && window.gridTransform.canvas && window.gridTransform.canvas.width) ? window.gridTransform.canvas.width : 800,
            height: (window.gridTransform && window.gridTransform.canvas && window.gridTransform.canvas.height) ? window.gridTransform.canvas.height : 600
          };
          gridState.canvas_dimensions = dims;
        } catch(e) {}
        opts.grid_state = gridState;
      }
      // 调试：打印是否已附带 grid_state
      try {
        const cpLen = gridState?.controlPoints?.length || 0;
        const hasDef = cpLen > 0 && gridState.controlPoints.some(p => Math.abs((p.x||0) - (p.originalX||0)) > 0.1 || Math.abs((p.y||0) - (p.originalY||0)) > 0.1);
        console.log('[D1] grid_state attached:', !!opts.grid_state, 'points:', cpLen, 'hasDeformation:', hasDef);
      } catch {}
    } catch {}

    if (!this.validateChar()) return;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch('/api/gen_single', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ char: this.currentChar, ...opts }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      if (!response.ok) throw new Error('生成失败');
      const result = await response.json();
      if (window.previewCardManager && result.url) {
        window.previewCardManager.setCardImage('D2', this.withTimestamp ? this.withTimestamp(result.url) : (result.url + '?ts=' + Date.now()));
      }
      if (typeof showToast !== 'undefined') showToast('D1图生成完成', 'success');
    } catch (error) {
      if (typeof showToast !== 'undefined') showToast('D1图生成失败: ' + (error.message || error), 'error');
    }
  }

  /**
   * 生成D2图（中轴填充）
   */
  async generateD2() {
    await this.generateSingle('D2', '中轴填充');  // D2按钮生成D2类型
  }

  /**
   * 生成全部图像（A、B、C、D1）
   */
  async generateAll() {
    if (!this.validateChar()) return;

    console.log('🔄 开始生成全部图像（A、B、C、D1）');
    if (typeof showToast !== 'undefined') {
      showToast('正在生成全部图像...', 'info');
    }

    try {
      // 构建请求体 - 添加网格状态处理
      const requestBody = {
        char: this.currentChar
      };

      // 检查并添加网格状态（与generateD1保持一致）
      try {
        let gridState = null;
        // 1) 优先通过全局 gridStateManager 获取（标准路径）
        if (window.gridStateManager && typeof window.gridStateManager.getState === 'function') {
          gridState = window.gridStateManager.getState();
        }
        // 2) 若为空，尝试从 localStorage 回退读取
        if ((!gridState || !gridState.controlPoints || gridState.controlPoints.length === 0) && typeof localStorage !== 'undefined') {
          const saved = localStorage.getItem('gridTransform_state');
          if (saved) {
            try { gridState = JSON.parse(saved); } catch (e) {}
          }
        }
        // 3) 若仍为空，直接从 window.gridTransform 读取当前内存状态构造
        if ((!gridState || !gridState.controlPoints || gridState.controlPoints.length === 0) && window.gridTransform && Array.isArray(window.gridTransform.controlPoints) && window.gridTransform.controlPoints.length > 0) {
          gridState = {
            controlPoints: window.gridTransform.controlPoints.map(p => ({ x: p.x, y: p.y, originalX: p.originalX ?? p.x, originalY: p.originalY ?? p.y })),
            size: window.gridTransform.size,
            deformStrength: window.gridTransform.deformStrength
          };
        }
        // 仅当存在控制点时附带（是否有形变由后端再判定）
        if (gridState && Array.isArray(gridState.controlPoints) && gridState.controlPoints.length > 0) {
          // 附带画布尺寸，便于后端正确映射
          try {
            const dims = {
              width: (window.gridTransform && window.gridTransform.canvas && window.gridTransform.canvas.width) ? window.gridTransform.canvas.width : 800,
              height: (window.gridTransform && window.gridTransform.canvas && window.gridTransform.canvas.height) ? window.gridTransform.canvas.height : 600
            };
            gridState.canvas_dimensions = dims;
          } catch(e) {}
          requestBody.grid_state = gridState;
        }
        // 调试：打印是否已附带 grid_state
        try {
          const cpLen = gridState?.controlPoints?.length || 0;
          const hasDef = cpLen > 0 && gridState.controlPoints.some(p => Math.abs((p.x||0) - (p.originalX||0)) > 0.1 || Math.abs((p.y||0) - (p.originalY||0)) > 0.1);
          console.log('[generateAll] grid_state attached:', !!requestBody.grid_state, 'points:', cpLen, 'hasDeformation:', hasDef);
          if (requestBody.grid_state) {
            console.log('[generateAll] grid_state content:', JSON.stringify(requestBody.grid_state, null, 2));
          }
        } catch {}
      } catch(e) {
        console.warn('⚠️ 获取网格状态失败:', e);
      }

      const response = await fetch('/api/gen', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const result = await response.json();
        console.log('✅ 全部图像生成成功:', result);
        console.log('🔍 调试 - 后端返回的URLs:', Object.keys(result.urls || {}));

        // 更新所有预览
        if (window.previewCardManager && window.previewCardManager.initialized && result.urls) {
          const timestamp = Date.now();
          
          // 映射后端返回的键到前端预览卡片ID（根据窗口标题）
          // 后端生成: A=轮廓, B=原始中轴, C=处理中轴, D1=网格变形, D2=中轴填充
          // 窗口显示: A=轮廓(A), C=原始中轴(B), D1=处理中轴(C), D2=网格变形(D1), B=中轴填充(D2)
          const keyMapping = {
            'A': 'A',
            'B': 'C',
            'C': 'D1',
            'D1': 'D2',
            'D2': 'B'
          };

          Object.entries(result.urls).forEach(([key, url]) => {
            if (url && key !== 'angles' && key !== 'version') {
              const cardId = keyMapping[key] || key;
              console.log(`🔗 映射: ${key} -> ${cardId} (${url})`);
              window.previewCardManager.setCardImage(cardId, url + '?ts=' + timestamp);
            }
          });
          
          // 特殊处理：如果没有D2数据，确保D1窗口保持可见
          if (!result.urls.D2) {
            console.log('⚠️ 后端没有返回D2数据，D1窗口将保持之前的状态');
            // 不调用setCardImage，避免隐藏D1窗口
          }
        } else {
          console.warn('⚠️ PreviewCardManager未就绪或无URLs数据');
          console.log('PreviewCardManager存在:', !!window.previewCardManager);
          console.log('PreviewCardManager已初始化:', window.previewCardManager?.initialized);
          console.log('URLs数据存在:', !!result.urls);
        }

        if (typeof showToast !== 'undefined') {
          showToast('全部图像生成完成', 'success');
        }
      } else {
        throw new Error('全部图像生成失败');
      }
    } catch (error) {
      console.error('❌ 全部图像生成错误:', error);
      if (typeof showToast !== 'undefined') {
        showToast('全部图像生成失败: ' + error.message, 'error');
      }
    }
  }
}

// 创建全局实例
const buttonGenerationManager = new ButtonGenerationManager();

// 导出全局函数供按钮调用
window.generateA = () => buttonGenerationManager.generateA();
window.generateB = () => buttonGenerationManager.generateB();
window.generateC = () => buttonGenerationManager.generateC();
window.generateD1 = () => buttonGenerationManager.generateD1();
window.generateD2 = () => buttonGenerationManager.generateD2();
window.generateAll = () => buttonGenerationManager.generateAll();

// 导出管理器供其他模块使用
window.buttonGenerationManager = buttonGenerationManager;

console.log('✅ 按钮生成模块已加载');
