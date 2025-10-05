/**
 * 状态管理系统 - 协调各个模块之间的状态同步和事件通信
 * 提供全局状态管理和模块间通信机制
 */

class StateManager {
    constructor() {
        this.state = {
            currentChar: '',
            activeTab: 'tab-start',
            gridTransform: null,
            previewFiles: {},
            generationInProgress: false,
            lastUpdate: Date.now()
        };
        
        this.listeners = new Map();
        this.modules = new Map();
        
        this.initializeStateManager();
    }

    /**
     * 初始化状态管理器
     */
    initializeStateManager() {
        // 从localStorage恢复状态
        this.loadState();
        
        // 设置定期状态保存
        setInterval(() => {
            this.saveState();
        }, 30000); // 每30秒自动保存一次
        
        // 页面卸载时保存状态
        window.addEventListener('beforeunload', () => {
            this.saveState();
        });
        
        console.log('🔧 状态管理系统已初始化');
    }

    /**
     * 注册模块
     */
    registerModule(name, moduleInstance) {
        this.modules.set(name, moduleInstance);
        console.log(`📦 模块已注册: ${name}`);
        
        // 触发模块注册事件
        this.emit('moduleRegistered', { name, module: moduleInstance });
    }

    /**
     * 获取模块实例
     */
    getModule(name) {
        return this.modules.get(name);
    }

    /**
     * 设置状态
     */
    setState(key, value, silent = false) {
        const oldValue = this.state[key];
        this.state[key] = value;
        this.state.lastUpdate = Date.now();
        
        if (!silent) {
            console.log(`🔄 状态更新: ${key} =`, value);
            this.emit('stateChanged', { key, value, oldValue });
            this.emit(`${key}Changed`, { value, oldValue });
        }
    }

    /**
     * 获取状态
     */
    getState(key) {
        return key ? this.state[key] : { ...this.state };
    }

    /**
     * 批量更新状态
     */
    updateState(updates, silent = false) {
        const changes = {};
        
        Object.entries(updates).forEach(([key, value]) => {
            const oldValue = this.state[key];
            this.state[key] = value;
            changes[key] = { value, oldValue };
        });
        
        this.state.lastUpdate = Date.now();
        
        if (!silent) {
            console.log('🔄 批量状态更新:', updates);
            this.emit('stateChanged', { changes });
            
            // 为每个更改的键触发特定事件
            Object.entries(changes).forEach(([key, { value, oldValue }]) => {
                this.emit(`${key}Changed`, { value, oldValue });
            });
        }
    }

    /**
     * 事件监听
     */
    on(event, callback) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event).push(callback);
    }

    /**
     * 移除事件监听
     */
    off(event, callback) {
        if (this.listeners.has(event)) {
            const callbacks = this.listeners.get(event);
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }

    /**
     * 触发事件
     */
    emit(event, data) {
        if (this.listeners.has(event)) {
            this.listeners.get(event).forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`事件处理器错误 (${event}):`, error);
                }
            });
        }
    }

    /**
     * 保存状态到localStorage
     */
    saveState() {
        try {
            const stateToSave = {
                ...this.state,
                timestamp: Date.now()
            };
            localStorage.setItem('mmh_global_state', JSON.stringify(stateToSave));
            console.log('💾 全局状态已保存');
        } catch (error) {
            console.error('保存状态失败:', error);
        }
    }

    /**
     * 从localStorage加载状态
     */
    loadState() {
        try {
            const savedState = localStorage.getItem('mmh_global_state');
            if (savedState) {
                const parsed = JSON.parse(savedState);
                
                // 检查状态是否过期（7天）
                const maxAge = 7 * 24 * 60 * 60 * 1000;
                if (Date.now() - parsed.timestamp < maxAge) {
                    this.state = { ...this.state, ...parsed };
                    console.log('📥 全局状态已恢复');
                    return true;
                }
            }
        } catch (error) {
            console.error('加载状态失败:', error);
        }
        return false;
    }

    /**
     * 清除状态
     */
    clearState() {
        this.state = {
            currentChar: '',
            activeTab: 'tab-start',
            gridTransform: null,
            previewFiles: {},
            generationInProgress: false,
            lastUpdate: Date.now()
        };
        localStorage.removeItem('mmh_global_state');
        console.log('🗑️ 全局状态已清除');
        this.emit('stateCleared');
    }

    /**
     * 字符管理
     */
    setCurrentChar(char) {
        if (char !== this.state.currentChar) {
            this.setState('currentChar', char);
            
            // 同步到Cookie和localStorage
            if (typeof utils !== 'undefined') {
                utils.setCookie('last_char', char);
                localStorage.setItem('mmh_last_char', char);
                localStorage.setItem('mmh_last_update', Date.now().toString());
            }
            
            // 触发字符变更事件
            this.emit('characterChanged', { char });
        }
    }

    getCurrentChar() {
        return this.state.currentChar || this.getLastCharacter();
    }

    getLastCharacter() {
        // 优先从状态获取
        if (this.state.currentChar) {
            return this.state.currentChar;
        }
        
        // 从localStorage获取
        const lsChar = localStorage.getItem('mmh_last_char');
        const lsTime = localStorage.getItem('mmh_last_update');
        
        if (lsChar && lsTime) {
            const timeDiff = Date.now() - parseInt(lsTime);
            if (timeDiff < 24 * 60 * 60 * 1000) {
                return lsChar;
            }
        }
        
        // 从Cookie获取
        if (typeof utils !== 'undefined') {
            return utils.getCookie('last_char');
        }
        
        return null;
    }

    /**
     * 标签页管理
     */
    setActiveTab(tabId) {
        if (tabId !== this.state.activeTab) {
            this.setState('activeTab', tabId);
            
            // 同步到Cookie
            if (typeof utils !== 'undefined') {
                utils.setCookie('activeTab', tabId);
            }
        }
    }

    /**
     * 网格变形状态管理
     */
    setGridTransformState(gridState) {
        this.setState('gridTransform', gridState);
    }

    getGridTransformState() {
        return this.state.gridTransform;
    }

    /**
     * 预览文件管理
     */
    setPreviewFiles(files) {
        this.setState('previewFiles', files);
    }

    getPreviewFiles() {
        return this.state.previewFiles;
    }

    /**
     * 生成状态管理
     */
    setGenerationInProgress(inProgress) {
        this.setState('generationInProgress', inProgress);
    }

    isGenerationInProgress() {
        return this.state.generationInProgress;
    }

    /**
     * 模块间通信辅助方法
     */
    
    // 通知预览管理器更新
    notifyPreviewUpdate(files) {
        this.setPreviewFiles(files);
        this.emit('previewUpdate', { files });
    }

    // 通知网格变形状态变更
    notifyGridTransformUpdate(gridState) {
        this.setGridTransformState(gridState);
        this.emit('gridTransformUpdate', { gridState });
    }

    // 通知生成开始
    notifyGenerationStart(type, params) {
        this.setGenerationInProgress(true);
        this.emit('generationStart', { type, params });
    }

    // 通知生成完成
    notifyGenerationComplete(type, result) {
        this.setGenerationInProgress(false);
        this.emit('generationComplete', { type, result });
    }

    // 通知生成错误
    notifyGenerationError(type, error) {
        this.setGenerationInProgress(false);
        this.emit('generationError', { type, error });
    }

    /**
     * 调试方法
     */
    debugState() {
        console.log('🔧 === 状态管理器调试信息 ===');
        console.log('📊 当前状态:', this.state);
        console.log('📦 已注册模块:', Array.from(this.modules.keys()));
        console.log('👂 事件监听器:', Array.from(this.listeners.keys()));
        console.log('🔧 === 调试信息结束 ===');
    }

    /**
     * 获取状态统计
     */
    getStats() {
        return {
            stateKeys: Object.keys(this.state).length,
            registeredModules: this.modules.size,
            eventListeners: this.listeners.size,
            lastUpdate: new Date(this.state.lastUpdate).toLocaleString()
        };
    }
}

// 延迟初始化状态管理器，确保DOM完全加载
let stateManager = null;

// 初始化函数
function initStateManager() {
    if (!stateManager) {
        stateManager = new StateManager();
        
        // 导出全局访问
        window.StateManager = StateManager;
        window.stateManager = stateManager;
        
        // 为了向后兼容，提供一些全局函数
        window.setCurrentChar = (char) => stateManager.setCurrentChar(char);
        window.getCurrentChar = () => stateManager.getCurrentChar();
        window.getLastCharacter = () => stateManager.getLastCharacter();
        window.setActiveTab = (tabId) => stateManager.setActiveTab(tabId);
        
        console.log('✅ 状态管理系统已初始化');
    }
    return stateManager;
}

// DOM加载完成后自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStateManager);
} else {
    // 如果DOM已经加载完成，立即初始化
    initStateManager();
}

// 导出初始化函数和StateManager类供其他模块使用
window.initStateManager = initStateManager;
window.StateManager = StateManager;

console.log('✅ 状态管理系统模块已加载');
