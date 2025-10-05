/**
 * 网格状态管理模块
 * 处理网格变形状态的保存、加载和管理
 */

class GridStateManager {
    constructor() {
        this.storageKey = 'gridTransform_state';
    }

    // 获取当前网格状态
    getState() {
        // 优先尝试从localStorage加载保存的变形状态
        const savedState = this.loadFromStorage();
        if (savedState && savedState.controlPoints && savedState.controlPoints.length > 0) {
            return savedState;
        }
        
        // 如果画布不存在，尝试初始化
        if (!window.gridTransform || !window.gridTransform.canvas) {
            const canvas = document.getElementById('gridCanvas');
            if (canvas) {
                const container = canvas.parentElement;
                canvas.width = container.clientWidth;
                canvas.height = container.clientHeight;
                if (window.gridTransform) {
                    window.gridTransform.canvas = canvas;
                    window.gridTransform.ctx = canvas.getContext('2d');
                }
            } else {
                return this.getDefaultGridState();
            }
        }
        
        if (!window.gridTransform || !window.gridTransform.controlPoints || window.gridTransform.controlPoints.length === 0) {
            if (window.gridTransform && window.gridTransform.canvas && window.createGridPoints) {
                window.createGridPoints();
            } else {
                return this.getDefaultGridState();
            }
        }
        
        const state = {
            controlPoints: window.gridTransform.controlPoints.map(point => ({
                x: point.x,
                y: point.y,
                originalX: point.originalX,
                originalY: point.originalY
            })),
            size: window.gridTransform.size,
            deformStrength: window.gridTransform.deformStrength
        };
        
        return state;
    }

    // 检查是否有变形
    hasDeformation() {
        const state = this.getState();
        if (!state || !state.controlPoints) {
            return false;
        }
        
        return state.controlPoints.some(point => {
            const dx = Math.abs(point.x - point.originalX);
            const dy = Math.abs(point.y - point.originalY);
            return dx > 0.1 || dy > 0.1;
        });
    }

    // 获取默认网格状态（当画布不可用时）
    getDefaultGridState() {
        // 尝试从UI选择器获取当前选择的网格大小
        let size = 4; // 默认值
        const sizeSelect = document.getElementById('gridSize');
        if (sizeSelect && sizeSelect.value) {
            size = parseInt(sizeSelect.value);
            console.log('[GRID_STATE_DEBUG] 从UI选择器获取网格大小:', size);
        } else {
            // 尝试从localStorage获取上次保存的网格大小
            try {
                const savedState = localStorage.getItem(this.storageKey);
                if (savedState) {
                    const state = JSON.parse(savedState);
                    if (state.size) {
                        size = state.size;
                        console.log('[GRID_STATE_DEBUG] 从localStorage获取网格大小:', size);
                    }
                }
            } catch (error) {
                console.warn('[GRID_STATE_DEBUG] 无法从localStorage读取网格大小:', error);
            }
        }
        
        const controlPoints = [];
        
        // 创建指定大小的网格控制点（无变形）
        for (let row = 0; row < size; row++) {
            for (let col = 0; col < size; col++) {
                const x = 200 + (col * 100); // 默认位置
                const y = 200 + (row * 100);
                
                const point = { x, y, originalX: x, originalY: y };
                controlPoints.push(point);
            }
        }
        
        console.log('[GRID_STATE_DEBUG] 创建默认网格状态，大小:', size, '控制点数量:', controlPoints.length);
        
        return {
            controlPoints: controlPoints,
            size: size,
            deformStrength: 1
        };
    }

    // 从localStorage加载状态
    loadFromStorage() {
        try {
            const savedState = localStorage.getItem(this.storageKey);
            if (savedState) {
                const state = JSON.parse(savedState);
                return state;
            }
        } catch (error) {
            console.error('[GRID_STATE_DEBUG] 读取localStorage状态失败:', error);
        }
        return null;
    }

    // 保存网格状态到localStorage
    save() {
        console.log('[GRID_STATE_DEBUG] 开始保存网格状态...');
        
        // 检查必要的对象是否存在
        if (!window.gridTransform) {
            console.warn('GridStateManager: gridTransform对象不存在');
            return false;
        }
        
        // 调试信息
        const debugInfo = {
            hasControlPoints: !!window.gridTransform.controlPoints,
            controlPointsLength: window.gridTransform.controlPoints ? window.gridTransform.controlPoints.length : 0,
            hasOriginalPoints: !!window.gridTransform.originalPoints,
            hasCurrentPoints: !!window.gridTransform.currentPoints,
            gridSize: window.gridTransform.size,
            deformStrength: window.gridTransform.deformStrength
        };
        
        console.log('[GRID_STATE_DEBUG] 保存前状态检查:', debugInfo);
        
        // 发送详细调试信息到测试窗口
        const testBox = document.getElementById('anglesBox');
        if (testBox) {
            testBox.innerHTML = `<div style="font-size: 10px; color: #666; line-height: 1.3;">
                <strong>GridStateManager.save() 调试:</strong><br>
                controlPoints存在: ${debugInfo.hasControlPoints}<br>
                controlPoints长度: ${debugInfo.controlPointsLength}<br>
                originalPoints存在: ${debugInfo.hasOriginalPoints}<br>
                currentPoints存在: ${debugInfo.hasCurrentPoints}<br>
                网格大小: ${debugInfo.gridSize}<br>
                变形强度: ${debugInfo.deformStrength}<br>
                时间: ${new Date().toLocaleTimeString()}
            </div>`;
        }
        
        if (!window.gridTransform.controlPoints || window.gridTransform.controlPoints.length === 0) {
            console.warn('❌ GridStateManager: controlPoints为空，尝试创建默认控制点');
            
            // 尝试创建默认控制点
            if (window.createGridPoints && typeof window.createGridPoints === 'function') {
                console.log('🔧 创建默认控制点...');
                window.createGridPoints();
                
                // 再次检查是否创建成功
                if (!window.gridTransform.controlPoints || window.gridTransform.controlPoints.length === 0) {
                    console.error('❌ 创建默认控制点失败');
                    if (testBox) {
                        testBox.innerHTML += '<br><span style="color: red;">⚠️ 保存失败：无法创建控制点</span>';
                    }
                    return false;
                }
            } else {
                console.error('❌ createGridPoints函数不可用');
                if (testBox) {
                    testBox.innerHTML += '<br><span style="color: red;">⚠️ 保存失败：controlPoints为空</span>';
                }
                return false;
            }
        }
        
        try {
            const state = {
                controlPoints: window.gridTransform.controlPoints.map(point => ({
                    x: point.x,
                    y: point.y,
                    originalX: point.originalX || point.x,
                    originalY: point.originalY || point.y
                })),
                size: window.gridTransform.size || 4,
                deformStrength: window.gridTransform.deformStrength || 1,
                timestamp: Date.now()
            };
            
            localStorage.setItem(this.storageKey, JSON.stringify(state));
            console.log('[GRID_STATE_DEBUG] ✅ 网格状态已保存到localStorage');
            console.log('[GRID_STATE_DEBUG] 💾 保存的状态数据:', state);
            
            if (testBox) {
                testBox.innerHTML += '<br><span style="color: green;">✅ 状态保存成功</span>';
            }
            
            // 验证保存是否成功
            const verification = localStorage.getItem(this.storageKey);
            if (verification) {
                console.log('[GRID_STATE_DEBUG] ✅ localStorage验证成功，数据已保存');
            } else {
                console.error('[GRID_STATE_DEBUG] ❌ localStorage验证失败，数据未保存');
                return false;
            }
            
            // 显示保存提示
            if (window.toastManager) {
                window.toastManager.show('grid.state.saved');
            }
            
            return true;
        } catch (error) {
            console.error('[GRID_STATE_DEBUG] 保存状态到localStorage失败:', error);
            if (testBox) {
                testBox.innerHTML += `<br><span style="color: red;">❌ 保存失败: ${error.message}</span>`;
            }
            return false;
        }
    }

    // 加载状态并应用到网格
    load() {
        const savedState = this.loadFromStorage();
        if (!savedState) {
            console.log('[GRID_STATE_DEBUG] 没有找到保存的网格状态');
            // 即使没有保存状态，也要尝试恢复网格大小选择器
            this.restoreGridSizeSelector();
            return false;
        }
        
        console.log('[GRID_STATE_DEBUG] 加载保存的网格状态:', savedState);
        
        // 重要：首先恢复网格大小选择器
        const loadedSize = savedState.size || 4;
        console.log('[GRID_STATE_DEBUG] 🔢 加载的网格大小:', loadedSize);
        
        // 更新UI选择器以反映加载的大小
        const sizeSelect = document.getElementById('gridSize');
        if (sizeSelect) {
            sizeSelect.value = loadedSize;
            console.log('[GRID_STATE_DEBUG] 🎛️ UI选择器已更新为:', loadedSize);
        }
        
        // 确保gridTransform存在
        if (!window.gridTransform) {
            console.warn('[GRID_STATE_DEBUG] gridTransform不存在，但已恢复UI选择器');
            return false;
        }
        
        // 设置网格大小
        window.gridTransform.size = loadedSize;
        window.gridTransform.deformStrength = savedState.deformStrength || 1;
        
        // 如果有控制点数据，则应用它们
        if (savedState.controlPoints && savedState.controlPoints.length > 0) {
            window.gridTransform.controlPoints = savedState.controlPoints.map(point => ({
                x: point.x,
                y: point.y,
                originalX: point.originalX,
                originalY: point.originalY
            }));
            
            // 重新绘制网格
            if (window.drawGrid) {
                window.drawGrid();
            }
            
            // 立即应用变形到SVG
            if (window.applyGridDeformation) {
                window.applyGridDeformation();
            }
        } else {
            // 没有控制点数据，重新创建网格
            if (window.createGridPoints) {
                window.createGridPoints();
            }
            if (window.drawGrid) {
                window.drawGrid();
            }
        }
        
        console.log('[GRID_STATE_DEBUG] 网格状态加载完成');
        return true;
    }

    // 恢复网格大小选择器（即使没有完整的保存状态）
    restoreGridSizeSelector() {
        try {
            const savedState = localStorage.getItem(this.storageKey);
            if (savedState) {
                const state = JSON.parse(savedState);
                if (state.size) {
                    const sizeSelect = document.getElementById('gridSize');
                    if (sizeSelect) {
                        sizeSelect.value = state.size;
                        console.log('[GRID_STATE_DEBUG] 🔄 仅恢复网格大小选择器:', state.size);
                        
                        // 如果gridTransform存在，也更新它的大小
                        if (window.gridTransform) {
                            window.gridTransform.size = state.size;
                        }
                    }
                }
            }
        } catch (error) {
            console.warn('[GRID_STATE_DEBUG] 恢复网格大小选择器失败:', error);
        }
    }

    // 重置网格状态
    reset() {
        try {
            localStorage.removeItem(this.storageKey);
            console.log('[GRID_STATE_DEBUG] 网格状态已重置');
            
            if (window.toastManager) {
                window.toastManager.show('grid.state.reset');
            }
            
            return true;
        } catch (error) {
            console.error('[GRID_STATE_DEBUG] 重置状态失败:', error);
            return false;
        }
    }

    // 导出状态为JSON
    exportState() {
        const state = this.getState();
        const dataStr = JSON.stringify(state, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `grid_state_${Date.now()}.json`;
        link.click();
        
        if (window.toastManager) {
            window.toastManager.show('grid.state.exported');
        }
    }

    // 导入状态从JSON
    importState(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const state = JSON.parse(e.target.result);
                    localStorage.setItem(this.storageKey, JSON.stringify(state));
                    this.load();
                    
                    if (window.toastManager) {
                        window.toastManager.show('grid.state.imported');
                    }
                    
                    resolve(state);
                } catch (error) {
                    console.error('导入状态失败:', error);
                    if (window.toastManager) {
                        window.toastManager.show('grid.state.import.error', error.message);
                    }
                    reject(error);
                }
            };
            reader.readAsText(file);
        });
    }
}

// 创建全局实例
const gridStateManager = new GridStateManager();

// 导出供其他模块使用
window.GridStateManager = GridStateManager;
window.gridStateManager = gridStateManager;
