// 测试工具和ToastManager模块
// 处理测试信息显示、提示管理和调试功能

// ToastManager - 统一的提示管理器
class ToastManager {
  constructor() {
    this.queue = [];
    this.isShowing = false;
    this.messages = {
      // 预设相关消息
      'preset.save.success': '预设保存成功',
      'preset.load.success': '预设加载成功',
      'preset.delete.success': '预设删除成功',
      'preset.rename.success': '预设重命名成功',
      'preset.duplicate.success': '预设复制成功',
      'preset.export.success': '预设导出成功',
      'preset.export.all_success': '批量导出成功',
      'preset.export.no_presets': '没有可导出的预设',
      'preset.import.success': '预设导入成功',
      'preset.import.batch_success': '批量导入完成',
      'preset.import.invalid_format': '无效的预设文件格式',
      'preset.import.parse_error': '预设文件解析失败',
      'preset.name.exists': '预设名称已存在',
      'preset.not_found': '预设不存在',
      'preset.modal.open': '预设管理界面已打开',
      'preset.list.refresh': '预设列表已刷新',
      'preset.search.results': '搜索结果',
      'preset.search.no_results': '未找到匹配的预设',
      'preset.save.error': '预设保存失败',
      'preset.load.error': '预设加载失败',
      
      // 生成相关消息
      'generate.start': '开始生成字符...',
      'generate.success': '字符生成完成',
      'generate.error': '生成失败',
      
      // 网格变形相关
      'grid.save.success': '网格变形保存成功',
      'grid.reset.success': '网格变形重置成功',
      
      // 文章生成相关
      'article.generate.start': '开始生成文章...',
      'article.generate.success': '文章生成完成',
      'article.generate.error': '文章生成失败',
      
      // 参数相关
      'params.reset.success': '参数重置成功',
      'params.save.success': '参数保存成功',
      
      // 文件相关
      'file.save.success': '文件保存成功',
      'file.load.success': '文件加载成功',
      'file.error': '文件操作失败',
      
      // 通用消息
      'success': '操作成功',
      'error': '操作失败',
      'warning': '警告',
      'info': '提示'
    };
  }

  show(messageKey, customText = null, duration = 3000) {
    const message = customText || this.messages[messageKey] || messageKey;
    const type = this.getTypeFromKey(messageKey);
    this.showCustom(message, type, duration);
  }

  showCustom(message, type = 'success', duration = 3000) {
    // 保证唯一：新toast到来时，立刻关闭并移除当前toast与队列，避免多个同时可见
    // 清空队列，仅保留当前这条消息
    this.queue = [{ message, type, duration }];
    // 如果正在显示，立即隐藏当前toast，然后立刻显示新的
    if (this.isShowing && this.currentToast) {
      this.fastHideCurrentToast();
    }
    // 直接处理队列，确保新的toast立即出现
    this.processQueue();
  }

  getTypeFromKey(key) {
    if (key.includes('.error') || key.includes('.parse_error') || key.includes('not_found')) return 'error';
    if (key.includes('.warning') || key.includes('no_presets')) return 'warning';
    if (key.includes('.info') || key.includes('.refresh') || key.includes('.results') || key.includes('.open')) return 'info';
    if (key.includes('.start')) return 'loading';
    return 'success';
  }

  processQueue() {
    if (this.queue.length === 0) {
      this.isShowing = false;
      return;
    }

    this.isShowing = true;
    const { message, type, duration } = this.queue.shift();
    this.displayToast(message, type, duration);
  }

  displayToast(message, type, duration) {
    // 移除已存在的弹窗
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
      existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = `toast-notification ${type}`;
    
    // 添加图标
    const icon = this.getIcon(type);
    toast.innerHTML = `<span class="toast-icon">${icon}</span><span class="toast-message">${message}</span>`;
    
    // 存储当前toast引用
    this.currentToast = toast;
    this.currentToastTimer = null;
    
    document.body.appendChild(toast);

    // 显示动画
    setTimeout(() => {
      toast.classList.add('show');
    }, 100);

    // 自动隐藏（loading类型不自动隐藏）
    if (type !== 'loading') {
      this.currentToastTimer = setTimeout(() => {
        this.hideToast(toast);
      }, duration);
    }
  }

  getIcon(type) {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️',
      loading: '⏳'
    };
    return icons[type] || icons.info;
  }

  hideToast(toast) {
    // 清除定时器
    if (this.currentToastTimer) {
      clearTimeout(this.currentToastTimer);
      this.currentToastTimer = null;
    }
    
    toast.classList.remove('show');
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      // 清除当前toast引用
      if (this.currentToast === toast) {
        this.currentToast = null;
      }
      // 处理队列中的下一个消息
      setTimeout(() => this.processQueue(), 100);
    }, 300);
  }

  fastHideCurrentToast() {
    if (this.currentToast) {
      // 清除定时器
      if (this.currentToastTimer) {
        clearTimeout(this.currentToastTimer);
        this.currentToastTimer = null;
      }
      
      // 立即开始隐藏动画
      this.currentToast.classList.remove('show');
      const toastToHide = this.currentToast;
      this.currentToast = null;
      
      // 快速移除DOM元素
      setTimeout(() => {
        if (toastToHide.parentNode) {
          toastToHide.parentNode.removeChild(toastToHide);
        }
        // 立即处理队列中的下一个消息
        this.processQueue();
      }, 150); // 缩短到150ms
    }
  }

  hideLoading() {
    const loadingToast = document.querySelector('.toast-notification.loading');
    if (loadingToast) {
      this.hideToast(loadingToast);
    }
  }
}

// 创建全局toast管理器实例
const toastManager = new ToastManager();

// 保持向后兼容的showToast函数
function showToast(message, type = 'success') {
  toastManager.showCustom(message, type);
}

// 测试信息显示功能
function showTestInfo() {
  const box = document.getElementById('anglesBox');
  if (!box) return;
  
  const charInput = document.querySelector('input[name="char"]');
  const currentChar = charInput?.value?.trim() || '未设置';
  const imgD1 = document.querySelector('#imgD1');
  
  // 强制初始化网格环境用于测试
  if (typeof gridTransform !== 'undefined' && (!gridTransform.canvas || !gridTransform.controlPoints || gridTransform.controlPoints.length === 0)) {
    console.log('[TEST] 检测到网格未初始化，强制初始化...');
    
    // 创建虚拟画布环境
    gridTransform.canvas = document.createElement('canvas');
    gridTransform.canvas.width = 800;
    gridTransform.canvas.height = 600;
    gridTransform.ctx = gridTransform.canvas.getContext('2d');
    gridTransform.size = 3;
    gridTransform.deformStrength = 0.9;
    
    // 创建控制点网格
    gridTransform.controlPoints = [];
    const size = gridTransform.size;
    const centerX = gridTransform.canvas.width / 2;
    const centerY = gridTransform.canvas.height / 2;
    const gridWidth = 300;
    const gridHeight = 300;
    const gridStartX = centerX - gridWidth / 2;
    const gridStartY = centerY - gridHeight / 2;
    
    for (let row = 0; row < size; row++) {
      for (let col = 0; col < size; col++) {
        const originalX = gridStartX + col * gridWidth / (size - 1);
        const originalY = gridStartY + row * gridHeight / (size - 1);
        
        // 添加随机变形
        const offsetX = (Math.random() - 0.5) * 40;
        const offsetY = (Math.random() - 0.5) * 40;
        
        gridTransform.controlPoints.push({
          x: originalX + offsetX,
          y: originalY + offsetY,
          originalX: originalX,
          originalY: originalY
        });
      }
    }
    
    // 保存状态
    if (typeof GridStateManager !== 'undefined') {
      GridStateManager.save();
    }
    console.log('[TEST] 网格环境初始化完成');
  }
  
  // 检查exportDeformedSVG能否正常工作
  let exportTest = '未测试';
  try {
    if (typeof exportDeformedSVG !== 'undefined') {
      const testSVG = exportDeformedSVG();
      exportTest = testSVG ? `成功(${testSVG.length}字符)` : '失败-返回null';
    } else {
      exportTest = '函数未定义';
    }
  } catch (e) {
    exportTest = `失败-异常: ${e.message}`;
  }
  
  const testInfo = `
    <div style="font-size: 10px; color: var(--muted); line-height: 1.3;">
      <strong>基础状态:</strong><br>
      当前字符: ${currentChar}<br>
      D1图状态: ${imgD1?.src ? '已加载' : '未加载'}<br>
      D1图URL: ${imgD1?.src ? imgD1.src.split('/').pop() : '无'}<br>
      <br><strong>网格系统:</strong><br>
      网格画布: ${typeof gridTransform !== 'undefined' && gridTransform.canvas ? '已初始化' : '未初始化'}<br>
      SVG元素: ${typeof gridTransform !== 'undefined' && gridTransform.svgElement ? '已加载' : '未加载'}<br>
      控制点数: ${typeof gridTransform !== 'undefined' && gridTransform.controlPoints ? gridTransform.controlPoints.length : 0}<br>
      网格大小: ${typeof gridTransform !== 'undefined' ? gridTransform.size || '未设置' : '未定义'}<br>
      变形强度: ${typeof gridTransform !== 'undefined' ? gridTransform.deformStrength || '未设置' : '未定义'}<br>
      是否有变形: ${typeof GridStateManager !== 'undefined' && GridStateManager.hasDeformation ? (GridStateManager.hasDeformation() ? '是' : '否') : '未定义'}<br>
      <br><strong>组件状态:</strong><br>
      组件初始化: ${typeof dragTransformComponent !== 'undefined' && dragTransformComponent.isInitialized ? '是' : '否'}<br>
      组件字符: ${typeof dragTransformComponent !== 'undefined' ? dragTransformComponent.currentChar || '未设置' : '未定义'}<br>
      SVG导出测试: ${exportTest}<br>
      变形函数测试: ${(() => {
        try {
          if (typeof deformPoint !== 'undefined') {
            const [testX, testY] = deformPoint(100, 100);
            const hasDeform = (testX !== 100 || testY !== 100);
            return hasDeform ? `有效果(${testX.toFixed(1)},${testY.toFixed(1)})` : '无效果(100,100)';
          } else {
            return '函数未定义';
          }
        } catch (e) {
          return `异常: ${e.message}`;
        }
      })()}<br>
      控制点偏移检查: ${(() => {
        if (typeof gridTransform === 'undefined' || !gridTransform.controlPoints || gridTransform.controlPoints.length === 0) return '无控制点';
        let hasOffset = false;
        for (let i = 0; i < gridTransform.controlPoints.length; i++) {
          const cp = gridTransform.controlPoints[i];
          if (Math.abs(cp.x - cp.originalX) > 1 || Math.abs(cp.y - cp.originalY) > 1) {
            hasOffset = true;
            break;
          }
        }
        return hasOffset ? '有偏移' : '无偏移';
      })()}<br>
      <br><strong>调试信息:</strong><br>
      gridTransform对象: ${typeof gridTransform}<br>
      GridStateManager: ${typeof GridStateManager}<br>
      dragTransformComponent: ${typeof dragTransformComponent}<br>
      时间: ${new Date().toLocaleTimeString()}
    </div>
  `;
  
  box.innerHTML = testInfo;
}

// 测试D2按钮功能
function testD2Button() {
  if (typeof updateTestWindow !== 'undefined') {
    updateTestWindow('🔥 测试函数被调用 - D2按钮点击成功！');
  }
  console.log('🔥 测试函数被调用');
  
  // 调用原始的D2函数
  if (typeof generateD2WithNewInterface !== 'undefined') {
    generateD2WithNewInterface();
  }
}

// 初始化测试窗口
function initializeTestWindow() {
  const box = document.getElementById('anglesBox');
  if (!box) return;
  
  // 显示初始系统状态
  showTestInfo();
}

// 导出全局变量和函数
window.toastManager = toastManager;
window.showToast = showToast;
window.showTestInfo = showTestInfo;
window.testD2Button = testD2Button;
window.initializeTestWindow = initializeTestWindow;

console.log('✅ 测试工具模块已加载');
