/**
 * 工具函数库 - 通用工具函数和状态管理
 * 从 ui.html 中抽离的工具函数
 */

class Utils {
    constructor() {
        this.initializeUtils();
    }

    /**
     * 初始化工具函数
     */
    initializeUtils() {
        console.log('🔧 工具函数库已初始化');
    }

    /**
     * Cookie 管理
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
        return null;
    }

    setCookie(name, value, days = 30) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${encodeURIComponent(value)};expires=${expires.toUTCString()};path=/`;
        console.log(`🍪 Cookie已设置: ${name} = ${value}`);
    }

    setPref(name, value) {
        try {
            document.cookie = name + '=' + encodeURIComponent(value) + '; path=/; max-age=' + (3600 * 24 * 365);
        } catch (e) {
            console.warn('设置偏好失败:', e);
        }
    }

    /**
     * 状态管理
     */
    saveCurrentState() {
        const charInput = document.querySelector('input[name="char"]');
        if (charInput && charInput.value) {
            this.setCookie('last_char', charInput.value);
            localStorage.setItem('mmh_last_char', charInput.value);
            localStorage.setItem('mmh_last_update', Date.now().toString());
            console.log('💾 当前状态已保存:', charInput.value);
        }

        // 保存活动标签页
        const activeTab = document.querySelector('.tab.active');
        if (activeTab) {
            const tabId = activeTab.getAttribute('onclick')?.match(/'([^']+)'/)?.[1];
            if (tabId) {
                this.setCookie('activeTab', tabId);
                console.log('📑 活动标签页已保存:', tabId);
            }
        }
    }

    getLastCharacter() {
        // 优先从localStorage获取（更可靠）
        const lsChar = localStorage.getItem('mmh_last_char');
        const lsTime = localStorage.getItem('mmh_last_update');
        
        if (lsChar && lsTime) {
            const timeDiff = Date.now() - parseInt(lsTime);
            // 如果在24小时内，使用localStorage的值
            if (timeDiff < 24 * 60 * 60 * 1000) {
                console.log('📱 从localStorage获取字符:', lsChar);
                return lsChar;
            }
        }
        
        // 回退到Cookie
        const cookieChar = this.getCookie('last_char');
        if (cookieChar) {
            console.log('🍪 从Cookie获取字符:', cookieChar);
            return cookieChar;
        }
        
        return null;
    }

    /**
     * 标签页管理
     */
    restoreActiveTab() {
        const savedTab = this.getCookie('activeTab');
        if (savedTab) {
            console.log('🔄 恢复活动标签页:', savedTab);
            try {
                // 调用全局的showTab函数
                if (typeof showTab === 'function') {
                    showTab(savedTab);
                }
            } catch (e) {
                console.warn('恢复标签页失败:', e);
            }
        }
    }

    restoreLastChar() {
        const lastChar = this.getLastCharacter();
        if (lastChar) {
            const charInput = document.querySelector('input[name="char"]');
            if (charInput) {
                charInput.value = lastChar;
                console.log('🔄 恢复上次字符:', lastChar);
            }
        }
    }

    /**
     * 自动保存绑定
     */
    bindAutoSave() {
        const form = document.querySelector('form');
        if (!form) return;
        
        const handler = (ev) => {
            const el = ev.target;
            if (!el || !el.name) return;
            
            let val = '';
            if (el.type === 'checkbox') {
                val = el.checked ? '1' : '0';
            } else {
                val = el.value || '';
            }
            
            this.setPref(el.name, val);
        };
        
        form.querySelectorAll('input').forEach((el) => {
            el.addEventListener('change', handler);
            if (el.type === 'number' || el.type === 'text') {
                el.addEventListener('input', handler);
            }
        });
        
        console.log('🔄 自动保存已绑定');
    }

    /**
     * 网格状态调试
     */
    debugGridState() {
        console.log('🔧 === 网格状态调试信息 ===');
        
        // 检查localStorage存储
        const savedState = localStorage.getItem('gridTransformState');
        console.log('💾 localStorage状态:', savedState ? '存在' : '不存在');
        if (savedState) {
            try {
                const parsed = JSON.parse(savedState);
                console.log('📊 保存的状态数据:', {
                    controlPoints: parsed.controlPoints?.length || 0,
                    originalPoints: parsed.originalPoints?.length || 0,
                    currentPoints: parsed.currentPoints?.length || 0,
                    gridSize: parsed.gridSize,
                    timestamp: new Date(parsed.timestamp).toLocaleString()
                });
            } catch (e) {
                console.error('❌ 状态数据解析失败:', e);
            }
        }
        
        // 检查全局gridTransform对象
        if (typeof gridTransform !== 'undefined') {
            console.log('🌐 全局gridTransform状态:', {
                canvas: !!gridTransform.canvas,
                controlPoints: gridTransform.controlPoints?.length || 0,
                originalPoints: gridTransform.originalPoints?.length || 0,
                currentPoints: gridTransform.currentPoints?.length || 0,
                svgElement: !!gridTransform.svgElement,
                originalSVG: !!gridTransform.originalSVG
            });
        } else {
            console.log('❌ 全局gridTransform对象不存在');
        }
        
        // 检查GridStateManager
        if (typeof GridStateManager !== 'undefined') {
            console.log('🔧 GridStateManager可用');
            console.log('📊 是否有变形:', GridStateManager.hasDeformation());
        } else {
            console.log('❌ GridStateManager不可用');
        }
        
        console.log('🔧 === 调试信息结束 ===');
    }

    /**
     * 测试网格状态持久化
     */
    testGridStatePersistence() {
        console.log('🧪 === 开始测试网格状态持久化 ===');
        
        // 记录当前状态
        const initialState = localStorage.getItem('gridTransformState');
        console.log('📊 初始状态:', initialState ? '存在' : '不存在');
        
        // 如果GridStateManager可用，测试保存和加载
        if (typeof GridStateManager !== 'undefined') {
            console.log('💾 测试保存状态...');
            const saveResult = GridStateManager.save();
            console.log('💾 保存结果:', saveResult);
            
            console.log('📥 测试加载状态...');
            const loadResult = GridStateManager.load();
            console.log('📥 加载结果:', loadResult);
            
            console.log('🔍 测试变形检测...');
            const hasDeformation = GridStateManager.hasDeformation();
            console.log('🔍 是否有变形:', hasDeformation);
        } else {
            console.log('❌ GridStateManager不可用，跳过测试');
        }
        
        console.log('🧪 === 测试结束 ===');
    }

    /**
     * 网格状态管理（向后兼容）
     */
    saveGridTransformState() {
        if (typeof GridStateManager !== 'undefined') {
            const success = GridStateManager.save();
            if (success) {
                console.log('✅ 网格变形状态已保存');
            }
            return success;
        }
        return false;
    }

    clearGridTransformState() {
        if (typeof GridStateManager !== 'undefined') {
            GridStateManager.clear();
            console.log('🗑️ 网格变形状态已清除');
        }
    }

    /**
     * 复制测试窗口内容
     */
    copyTestWindow() {
        const anglesBox = document.getElementById('anglesBox');
        if (!anglesBox) {
            alert('测试窗口不存在');
            return;
        }
        
        const content = anglesBox.textContent || anglesBox.innerText;
        
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(content).then(() => {
                alert('测试窗口内容已复制到剪贴板');
            }).catch(err => {
                console.error('复制失败:', err);
                this.fallbackCopyTextToClipboard(content);
            });
        } else {
            this.fallbackCopyTextToClipboard(content);
        }
    }

    fallbackCopyTextToClipboard(text) {
        const textArea = document.createElement("textarea");
        textArea.value = text;
        textArea.style.position = "fixed";
        textArea.style.left = "-999999px";
        textArea.style.top = "-999999px";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            if (successful) {
                alert('测试窗口内容已复制到剪贴板');
            } else {
                alert('复制失败，请手动复制');
            }
        } catch (err) {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        }
        
        document.body.removeChild(textArea);
    }

    /**
     * 清空测试窗口
     */
    clearTestWindow() {
        const anglesBox = document.getElementById('anglesBox');
        if (!anglesBox) {
            alert('测试窗口不存在');
            return;
        }
        
        anglesBox.innerHTML = '<div style="color: var(--muted); font-style: italic;">测试窗口已清空</div>';
        console.log('🗑️ 测试窗口已清空');
    }

    /**
     * 格式化时间戳
     */
    formatTimestamp(timestamp) {
        return new Date(timestamp).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    /**
     * 生成唯一ID
     */
    generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    /**
     * 防抖函数
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * 节流函数
     */
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// 创建全局工具实例
const utils = new Utils();

// 导出全局函数以保持向后兼容性
window.getCookie = (name) => utils.getCookie(name);
window.setCookie = (name, value, days) => utils.setCookie(name, value, days);
window.setPref = (name, value) => utils.setPref(name, value);
window.saveCurrentState = () => utils.saveCurrentState();
window.getLastCharacter = () => utils.getLastCharacter();
window.restoreActiveTab = () => utils.restoreActiveTab();
window.restoreLastChar = () => utils.restoreLastChar();
window.bindAutoSave = () => utils.bindAutoSave();
window.debugGridState = () => utils.debugGridState();
window.testGridStatePersistence = () => utils.testGridStatePersistence();
window.saveGridTransformState = () => utils.saveGridTransformState();
window.clearGridTransformState = () => utils.clearGridTransformState();
window.copyTestWindow = () => utils.copyTestWindow();
window.clearTestWindow = () => utils.clearTestWindow();

// 导出类和实例
window.Utils = Utils;
window.utils = utils;

console.log('✅ 工具函数库已加载');
