/**
 * 模态框HTML模板动态加载器
 * 负责在页面加载时动态加载各种弹窗HTML模板
 */

class ModalLoader {
  constructor() {
    this.modals = [
      { id: 'articleModal', file: 'html/modals/article-modal.html' },
      { id: 'dragTransformModal', file: 'html/modals/grid-transform-modal.html' },
      { id: 'presetModal', file: 'html/modals/preset-modal.html' },
      { id: 'zoomModal', file: 'html/modals/image-modal.html' },
      { id: 'helpModal', file: 'html/modals/help-modal.html' }
    ];
    this.loadedModals = new Set();
  }

  /**
   * 加载单个模态框HTML
   */
  async loadModal(modalConfig) {
    try {
      const response = await fetch(modalConfig.file);
      if (!response.ok) {
        throw new Error(`Failed to load ${modalConfig.file}: ${response.status}`);
      }
      
      const html = await response.text();
      
      // 创建临时容器来解析HTML
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;
      
      // 将模态框添加到body
      const modalElement = tempDiv.firstElementChild;
      if (modalElement) {
        document.body.appendChild(modalElement);
        this.loadedModals.add(modalConfig.id);
        console.log(`✓ 已加载模态框: ${modalConfig.id}`);
      }
      
    } catch (error) {
      console.error(`✗ 加载模态框失败 ${modalConfig.id}:`, error);
    }
  }

  /**
   * 加载所有模态框
   */
  async loadAllModals() {
    console.log('🔄 开始加载HTML模板...');
    
    const loadPromises = this.modals.map(modal => this.loadModal(modal));
    await Promise.all(loadPromises);
    
    console.log(`✅ HTML模板加载完成，共加载 ${this.loadedModals.size}/${this.modals.length} 个模态框`);
    
    // 触发自定义事件，通知其他模块模态框已加载完成
    window.dispatchEvent(new CustomEvent('modalsLoaded', {
      detail: { loadedModals: Array.from(this.loadedModals) }
    }));
  }

  /**
   * 检查模态框是否已加载
   */
  isModalLoaded(modalId) {
    return this.loadedModals.has(modalId);
  }

  /**
   * 等待特定模态框加载完成
   */
  async waitForModal(modalId, timeout = 5000) {
    if (this.isModalLoaded(modalId)) {
      return true;
    }

    return new Promise((resolve, reject) => {
      const checkInterval = setInterval(() => {
        if (this.isModalLoaded(modalId)) {
          clearInterval(checkInterval);
          clearTimeout(timeoutHandle);
          resolve(true);
        }
      }, 100);

      const timeoutHandle = setTimeout(() => {
        clearInterval(checkInterval);
        reject(new Error(`等待模态框 ${modalId} 加载超时`));
      }, timeout);
    });
  }
}

// 创建全局实例
window.modalLoader = new ModalLoader();

// 页面加载完成后自动加载所有模态框
document.addEventListener('DOMContentLoaded', () => {
  window.modalLoader.loadAllModals();
});

// 导出供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ModalLoader;
}
