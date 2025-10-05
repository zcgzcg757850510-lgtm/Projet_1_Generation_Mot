/**
 * 标签页管理模块
 * 处理标签页切换、状态保存和恢复功能
 */

class TabManager {
    constructor() {
        this.activeTab = 'tab-start-peak';
        this.initialized = false;
        this.aliasMap = {
            'tab-start': 'tab-start-peak',
            'tab-processed': 'tab-start-peak',
            'tab-peak': 'tab-start-peak'
        };
    }

    /**
     * 初始化标签页管理器
     */
    initialize() {
        if (this.initialized) return;
        
        // 立即隐藏所有标签页和移除按钮active状态，防止闪烁
        this.hideAllTabs();
        this.clearAllButtonStates();
        
        this.setupTabEventListeners();
        this.restoreActiveTab();
        this.initialized = true;
        
        console.log('✅ 标签页管理器已初始化');
    }

    /**
     * 隐藏所有标签页
     */
    hideAllTabs() {
        const tabPanels = document.querySelectorAll('.tab-panel');
        tabPanels.forEach(panel => {
            panel.classList.add('hidden');
            panel.style.display = 'none';
        });
        console.log('🔒 所有标签页已隐藏');
    }

    /**
     * 清除所有按钮的active状态
     */
    clearAllButtonStates() {
        const tabButtons = document.querySelectorAll('button[data-tab]');
        tabButtons.forEach(btn => {
            btn.classList.remove('active');
        });
        console.log('🔄 清除所有按钮active状态');
    }

    /**
     * 设置标签页事件监听器
     */
    setupTabEventListeners() {
        const tabButtons = document.querySelectorAll('button[data-tab]');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabId = e.target.getAttribute('data-tab');
                this.activate(tabId);
            });
        });
    }

    /**
     * 激活指定标签页
     */
    activate(tabId) {
        console.log('🎯 激活标签页:', tabId);
        // 兼容旧ID，映射到新合并面板
        if (this.aliasMap && this.aliasMap[tabId]) {
            tabId = this.aliasMap[tabId];
        }
        
        // 立即隐藏所有面板，防止闪烁
        const tabPanels = document.querySelectorAll('.tab-panel');
        tabPanels.forEach(panel => {
            panel.classList.add('hidden');
            panel.style.display = 'none';
        });

        // 更新按钮状态
        const tabButtons = document.querySelectorAll('button[data-tab]');
        tabButtons.forEach(btn => {
            if (btn.getAttribute('data-tab') === tabId) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // 显示目标面板
        const targetPanel = document.getElementById(tabId);
        if (targetPanel) {
            targetPanel.classList.remove('hidden');
            targetPanel.style.display = 'block';
            console.log('✅ 标签页激活完成:', tabId);
        }

        // 保存状态
        this.activeTab = tabId;
        this.saveActiveTab(tabId);
        
        // 通知状态管理器
        if (window.stateManager) {
            window.stateManager.setActiveTab(tabId);
        }
        
        console.log(`标签页切换到: ${tabId}`);
    }

    /**
     * 保存活动标签页到Cookie
     */
    saveActiveTab(tabId) {
        // 保存时也做一次别名转换，确保持久化为新ID
        const realId = (this.aliasMap && this.aliasMap[tabId]) ? this.aliasMap[tabId] : tabId;
        document.cookie = `activeTab=${realId}; path=/; max-age=31536000`;
    }

    /**
     * 从Cookie恢复活动标签页
     */
    restoreActiveTab() {
        const cookies = document.cookie.split(';');
        let savedTab = null;
        
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'activeTab') {
                savedTab = value;
                break;
            }
        }
        
        if (savedTab) {
            console.log('🔄 恢复保存的标签页:', savedTab);
            // 立即激活（含别名转换），不显示默认标签页
            this.activate(this.aliasMap[savedTab] || savedTab);
        } else {
            // 默认激活合并后的“起笔+笔锋”标签页
            console.log('🔄 激活默认标签页: tab-start-peak');
            this.activate('tab-start-peak');
        }
    }

    /**
     * 获取当前活动标签页
     */
    getActiveTab() {
        return this.activeTab;
    }
}

// 创建全局实例
const tabManager = new TabManager();

// 全局函数
function activate(tabId) {
    tabManager.activate(tabId);
}

function initTabManager() {
    tabManager.initialize();
}

// 导出全局函数和对象
window.TabManager = TabManager;
window.tabManager = tabManager;
window.activate = activate;
window.initTabManager = initTabManager;

// 立即初始化或在DOM解析完成后立即初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTabManager);
} else {
    // DOM已经加载完成，立即初始化
    initTabManager();
}

// 额外保险：在页面完全加载前也尝试初始化
if (document.readyState !== 'complete') {
    // 使用更早的事件确保初始化
    document.addEventListener('readystatechange', function() {
        if (document.readyState === 'interactive') {
            initTabManager();
        }
    });
}

console.log('✅ 标签页管理模块已加载');
