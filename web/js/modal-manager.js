/**
 * 模态框管理模块
 * 统一管理所有模态框的打开、关闭和初始化
 */

class ModalManager {
    constructor() {
        this.modals = new Map();
        this.initialized = false;
    }

    /**
     * 初始化模态框管理器
     */
    init() {
        if (this.initialized) return;
        
        this.registerModals();
        this.setupEventListeners();
        this.initialized = true;
        
        console.log('✅ 模态框管理器已初始化');
    }

    /**
     * 注册所有模态框
     */
    registerModals() {
        // 文章生成模态框
        this.modals.set('article', {
            element: () => document.getElementById('articleModal'),
            openHandler: this.openArticleModal.bind(this),
            closeHandler: this.closeArticleModal.bind(this)
        });

        // 网格变形模态框
        this.modals.set('dragTransform', {
            element: () => document.getElementById('dragTransformModal'),
            openHandler: this.openDragTransformModal.bind(this),
            closeHandler: this.closeDragTransformModal.bind(this)
        });

        // 预设管理模态框
        this.modals.set('preset', {
            element: () => document.getElementById('presetModal'),
            openHandler: this.openPresetModal.bind(this),
            closeHandler: this.closePresetModal.bind(this)
        });

        // 帮助说明模态框
        this.modals.set('help', {
            element: () => document.getElementById('helpModal'),
            openHandler: this.openHelpModal.bind(this),
            closeHandler: this.closeHelpModal.bind(this)
        });
    }

    /**
     * 设置事件监听器
     */
    setupEventListeners() {
        // 统一的弹窗关闭逻辑
        this.setupModalCloseLogic('articleModal', 'btnArticleClose', () => this.closeArticleModal());
        this.setupModalCloseLogic('dragTransformModal', 'btnDragTransformClose', () => this.closeDragTransformModal());
        this.setupModalCloseLogic('presetModal', 'btnPresetClose', () => this.closePresetModal());
        this.setupModalCloseLogic('zoomModal', 'btnZoomClose', () => this.closeZoomModal());
    }

    /**
     * 为指定弹窗设置统一的关闭逻辑
     */
    setupModalCloseLogic(modalId, closeBtnId, closeHandler) {
        // 延迟绑定，确保DOM元素已加载
        setTimeout(() => {
            const modal = document.getElementById(modalId);
            const closeBtn = document.getElementById(closeBtnId);
            
            console.log(`🔧 设置模态框关闭逻辑: ${modalId}, 按钮: ${closeBtnId}`);
            console.log(`模态框元素:`, modal);
            console.log(`关闭按钮:`, closeBtn);
            
            if (closeBtn) {
                closeBtn.onclick = closeHandler;
                console.log(`✅ 已绑定关闭按钮点击事件: ${closeBtnId}`);
            } else {
                console.warn(`❌ 未找到关闭按钮: ${closeBtnId}`);
            }
            
            if (modal) {
                // 点击背景关闭
                modal.addEventListener('click', (ev) => {
                    if (ev.target === modal) {
                        closeHandler();
                    }
                });
                
                // ESC键关闭
                const handleEscKey = (ev) => {
                    if (ev.key === 'Escape' && !modal.classList.contains('hidden')) {
                        closeHandler();
                    }
                };
                
                // 存储事件处理器以便后续清理
                if (!modal._escHandler) {
                    modal._escHandler = handleEscKey;
                    document.addEventListener('keydown', handleEscKey);
                }
                console.log(`✅ 已设置背景点击和ESC键关闭: ${modalId}`);
            } else {
                console.warn(`❌ 未找到模态框元素: ${modalId}`);
            }
        }, 500);
    }

    /**
     * 打开指定模态框
     */
    openModal(modalName) {
        // 在打开新弹窗前，立即关闭所有已打开的弹窗，保证唯一可见
        this.closeAll();
        const modal = this.modals.get(modalName);
        if (modal && modal.openHandler) {
            modal.openHandler();
        }
    }

    /**
     * 关闭指定模态框
     */
    closeModal(modalName) {
        const modal = this.modals.get(modalName);
        if (modal && modal.closeHandler) {
            modal.closeHandler();
        }
    }

    /**
     * 关闭所有弹窗
     */
    closeAll() {
        this.modals.forEach((meta) => {
            const el = meta.element ? meta.element() : null;
            if (!el) return;
            // 判断可见：不存在 hidden 类或 display != none
            const isHiddenByClass = el.classList && el.classList.contains('hidden');
            const isHiddenByStyle = (el.style && (el.style.display === 'none'));
            if (!(isHiddenByClass || isHiddenByStyle)) {
                if (meta.closeHandler) meta.closeHandler();
            }
        });
        // 特殊：帮助弹窗可能用display控制
        const helpEl = document.getElementById('helpModal');
        if (helpEl && helpEl.style && helpEl.style.display !== 'none') {
            this.closeHelpModal();
        }
    }

    /**
     * 文章生成模态框处理
     */
    openArticleModal() {
        const modal = document.getElementById('articleModal');
        if (modal) {
            modal.classList.remove('hidden');
            // 初始化背景类型变化处理器
            this.initArticleModalHandlers();
        }
    }

    closeArticleModal() {
        const modal = document.getElementById('articleModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    initArticleModalHandlers() {
        // 初始化文章生成器
        if (typeof window.articleGenerator !== 'undefined' && window.articleGenerator.initialize) {
            window.articleGenerator.initialize();
            console.log('文章生成器已初始化');
        } else {
            console.log('文章生成器未找到，等待加载...');
        }
    }

    /**
     * 网格变形模态框处理
     */
    openDragTransformModal() {
        const modal = document.getElementById('dragTransformModal');
        if (modal) {
            // 先隐藏画布区域避免闪动
            const canvasArea = modal.querySelector('.viewport');
            if (canvasArea) {
                canvasArea.style.opacity = '0';
                canvasArea.style.transition = 'opacity 0.3s ease';
            }
            
            modal.classList.remove('hidden');
            
            // 同步初始化，避免异步导致的闪动
            this.initializeGridTransformSync();
        }
    }

    /**
     * 同步初始化网格变形系统，避免闪动
     */
    initializeGridTransformSync() {
        console.log('🔄 同步初始化网格变形系统');
        
        // 1. 立即初始化网格变形系统（包含状态恢复）
        if (typeof initializeGridTransform === 'function') {
            initializeGridTransform();
        }
        
        // 2. 恢复网格大小选择器
        if (window.gridStateManager && typeof window.gridStateManager.restoreGridSizeSelector === 'function') {
            window.gridStateManager.restoreGridSizeSelector();
        }
        
        // 3. 立即显示画布区域
        const modal = document.getElementById('dragTransformModal');
        const canvasArea = modal ? modal.querySelector('.viewport') : null;
        if (canvasArea) {
            canvasArea.style.opacity = '1';
        }
        
        // 4. 检查是否有状态恢复并显示提示
        setTimeout(() => {
            const hasControlPoints = window.gridTransform && window.gridTransform.controlPoints && window.gridTransform.controlPoints.length > 0;
            if (hasControlPoints && typeof showToast === 'function') {
                showToast('网格状态已恢复', 'success', 1500);
            }
        }, 100);
    }

    closeDragTransformModal() {
        const modal = document.getElementById('dragTransformModal');
        if (modal) {
            modal.classList.add('hidden');
            // 清理网格变形状态
        }
    }

    initMeshDeformationModal() {
        // 初始化网格变形按钮
        this.initMeshDeformationButtons();
        
        // 初始化网格变形系统
        if (typeof initMeshDeformationSystem === 'function') {
            initMeshDeformationSystem();
        }
    }

    initMeshDeformationButtons() {
        // 应用变形按钮
        const applyBtn = document.getElementById('btnApplyMeshTransform');
        if (applyBtn) {
            applyBtn.onclick = () => {
                if (typeof applyMeshTransformation === 'function') {
                    applyMeshTransformation();
                }
            };
        }
        
        // 重置按钮
        const resetBtn = document.getElementById('btnResetMeshTransform');
        if (resetBtn) {
            resetBtn.onclick = () => {
                if (typeof resetMeshGrid === 'function') {
                    resetMeshGrid();
                }
            };
        }
        
        // 保存预设按钮
        const saveBtn = document.getElementById('btnSaveMeshPreset');
        if (saveBtn) {
            saveBtn.onclick = () => {
                if (typeof saveMeshPreset === 'function') {
                    saveMeshPreset();
                }
            };
        }
        
        // 加载预设按钮
        const loadBtn = document.getElementById('btnLoadMeshPreset');
        if (loadBtn) {
            loadBtn.onclick = () => {
                if (typeof loadMeshPreset === 'function') {
                    loadMeshPreset();
                }
            };
        }
    }

    /**
     * 预设管理模态框处理
     */
    openPresetModal() {
        const modal = document.getElementById('presetModal');
        if (modal) {
            modal.classList.remove('hidden');
            
            // 调用预设模态框的初始化函数，确保刷新预设列表
            if (typeof window.openPresetModal === 'function' && window.openPresetModal !== this.openPresetModal) {
                // 如果存在独立的openPresetModal函数，调用它
                setTimeout(() => {
                    if (typeof updatePresetList === 'function') {
                        console.log('[MODAL_MANAGER] 刷新预设列表');
                        updatePresetList();
                    }
                    if (typeof updateCurrentParamsPreview === 'function') {
                        updateCurrentParamsPreview();
                    }
                }, 50);
            } else if (typeof initPresetModal === 'function') {
                initPresetModal();
            }
        }
    }

    closePresetModal() {
        const modal = document.getElementById('presetModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    /**
     * 帮助说明模态框处理
     */
    openHelpModal() {
        const modal = document.getElementById('helpModal');
        if (modal) {
            modal.style.display = 'flex';
            console.log('📖 帮助说明窗口已打开');
        } else {
            console.error('❌ 帮助说明模态框未找到');
        }
    }

    closeHelpModal() {
        const modal = document.getElementById('helpModal');
        if (modal) {
            modal.style.display = 'none';
            console.log('📖 帮助说明窗口已关闭');
        }
    }

    /**
     * 图片放大模态框处理
     */
    closeZoomModal() {
        const modal = document.getElementById('zoomModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
}

// 延迟初始化模态框管理器
let modalManager = null;

// 初始化函数
function initModalManager() {
    if (!modalManager) {
        modalManager = new ModalManager();
        modalManager.init();
        
        // 导出全局函数以保持向后兼容性
        window.openArticleModal = () => modalManager.openModal('article');
        window.closeArticleModal = () => modalManager.closeModal('article');
        window.openDragTransformModal = () => modalManager.openModal('dragTransform');
        window.openHelpModal = () => modalManager.openModal('help');
        window.closeHelpModal = () => modalManager.closeModal('help');
        window.closeDragTransformModal = () => modalManager.closeModal('dragTransform');
        window.openPresetModal = () => modalManager.openModal('preset');
        window.closePresetModal = () => modalManager.closeModal('preset');
        
        // 图片放大模态框函数 - 仅对比模式
        window.openImageModal = (imageSrc, title, compareData) => {
            if (compareData && compareData.baseSrc && compareData.overlaySrc) {
                // 使用对比模式
                if (typeof openImageCompareModal === 'function') {
                    openImageCompareModal(compareData.baseSrc, compareData.overlaySrc);
                }
            }
            // 移除单图模式 - 没有对比图就不显示弹窗
        };
        window.closeZoomModal = () => modalManager.closeZoomModal();
        
        // 导出类和实例
        window.ModalManager = ModalManager;
        window.modalManager = modalManager;
        
        console.log('✅ 模态框管理器已初始化');
    }
    return modalManager;
}

// 监听模态框HTML加载完成事件
window.addEventListener('modalsLoaded', () => {
    console.log('📦 模态框HTML已加载，开始初始化模态框管理器');
    initModalManager();
});

// 备用初始化：如果modalsLoaded事件未触发，延迟初始化
setTimeout(() => {
    if (!modalManager) {
        console.log('⏰ 备用初始化模态框管理器');
        initModalManager();
    }
}, 1000);

// 导出初始化函数
window.initModalManager = initModalManager;

console.log('✅ 模态框管理模块已加载');
