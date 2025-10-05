/**
 * 预览效果管理模块
 * 管理预览卡片的悬停效果和视觉交互
 */

class PreviewEffectsManager {
    constructor() {
        this.initialized = false;
        this.previewCardsInitialized = false;
    }

    /**
     * 初始化预览效果
     */
    init() {
        if (this.initialized) return;
        
        this.initPreviewCardsEffect();
        this.initialized = true;
        
        console.log('✅ 预览效果管理器已初始化');
    }

    /**
     * 初始化预览卡片悬停效果
     */
    initPreviewCardsEffect() {
        if (this.previewCardsInitialized) return;
        
        const previewContainer = document.querySelector('.preview-cards');
        if (!previewContainer) {
            console.warn('预览容器未找到，跳过预览效果初始化');
            return;
        }

        // 创建遮罩层
        const overlay = document.createElement('div');
        overlay.className = 'preview-overlay';
        
        // 复制卡片结构到遮罩层（不包含文字内容）
        const cardsInner = previewContainer.querySelector('.cards__inner');
        if (cardsInner) {
            const clonedInner = cardsInner.cloneNode(true);
            
            // 移除所有文字内容，只保留结构
            const textElements = clonedInner.querySelectorAll('*');
            textElements.forEach(el => {
                // 移除所有文本节点
                const textNodes = Array.from(el.childNodes).filter(node => node.nodeType === Node.TEXT_NODE);
                textNodes.forEach(textNode => textNode.remove());
                
                // 清空特定元素的文本内容
                if (['H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'SPAN', 'P', 'DIV', 'LABEL'].includes(el.tagName)) {
                    // 保留子元素，只清空直接文本内容
                    const children = Array.from(el.childNodes).filter(node => node.nodeType === Node.ELEMENT_NODE);
                    el.textContent = '';
                    children.forEach(child => el.appendChild(child));
                }
            });
            
            overlay.appendChild(clonedInner);
            previewContainer.appendChild(overlay);
        }

        // 初始化每个预览卡片
        const previewCards = previewContainer.querySelectorAll('.preview-card');
        previewCards.forEach(card => this.initOverlayCard(card));
        
        // 添加全局鼠标移动监听器
        previewContainer.addEventListener('pointermove', (e) => this.applyOverlayMask(e, overlay));
        
        // 鼠标离开时隐藏遮罩
        previewContainer.addEventListener('mouseleave', () => {
            overlay.style.setProperty('--opacity', '0');
        });
        
        this.previewCardsInitialized = true;
        console.log('✅ 预览卡片效果已初始化');
    }

    /**
     * 初始化单个遮罩卡片
     */
    initOverlayCard(card) {
        const cardType = card.getAttribute('data-card');
        if (!cardType) return;

        // 设置CSS变量
        const hueMap = {
            'A': 210,
            'B': 120, 
            'C': 45,
            'D1': 0,
            'D2': 270
        };

        const hue = hueMap[cardType] || 210;
        card.style.setProperty('--hue', hue);
        card.style.setProperty('--saturation', '100%');
        card.style.setProperty('--lightness', cardType === 'B' ? '50%' : cardType === 'C' ? '55%' : cardType === 'D2' ? '65%' : '60%');
    }

    /**
     * 应用遮罩效果
     */
    applyOverlayMask(e, overlay) {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        overlay.style.setProperty('--opacity', '1');
        overlay.style.setProperty('--x', x + 'px');
        overlay.style.setProperty('--y', y + 'px');
    }

    /**
     * 更新变形控件显示
     */
    updateTransformControls() {
        // 始终显示网格控件和元素
        const meshGrid = document.getElementById('meshGrid');
        const meshControlPoints = document.getElementById('meshControlPoints');
        
        if (meshGrid) meshGrid.style.display = 'block';
        if (meshControlPoints) meshControlPoints.style.display = 'block';
        
        if (typeof initMeshGrid === 'function') {
            initMeshGrid();
        }
    }

    /**
     * 加载D0 SVG用于网格变形
     */
    async loadD0SVGForMeshDeformation() {
        const charInput = document.querySelector('input[name="char"]');
        let currentChar = charInput ? charInput.value.trim() : '';
        
        if (!currentChar) {
            currentChar = this.getCookie('last_char') || '字';
        }
        
        console.log(`正在为网格变形加载D0 SVG: ${currentChar}`);
        
        try {
            const response = await fetch(`/svg/D0/${currentChar}.svg`);
            if (response.ok) {
                const svgContent = await response.text();
                this.displayD0SVGForMeshDeformation(svgContent, currentChar);
            } else {
                throw new Error(`HTTP ${response.status}`);
            }
        } catch (error) {
            console.error('加载D0 SVG失败:', error);
            this.showMeshDeformationError(`无法加载字符 "${currentChar}" 的D0 SVG文件`);
        }
    }

    /**
     * 显示D0 SVG用于网格变形
     */
    displayD0SVGForMeshDeformation(svgContent, character) {
        const container = document.getElementById('dragCharacter');
        if (!container) {
            console.error('字符容器未找到');
            return;
        }
        
        // 存储原始SVG和字符信息
        container.dataset.originalSvg = svgContent;
        container.dataset.character = character;
        
        container.innerHTML = `
            <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;">
                ${svgContent}
            </div>
        `;
        
        // 缩放SVG以适应容器
        const svgElement = container.querySelector('svg');
        if (svgElement) {
            svgElement.style.width = '100%';
            svgElement.style.height = '100%';
            svgElement.style.maxWidth = '200px';
            svgElement.style.maxHeight = '200px';
        }
        
        console.log(`D0 SVG已加载: ${character}`);
        
        // 延迟初始化网格，确保SVG已渲染
        setTimeout(() => {
            if (typeof initMeshGrid === 'function') {
                initMeshGrid();
            }
        }, 150);
    }

    /**
     * 显示网格变形错误
     */
    showMeshDeformationError(message) {
        const container = document.getElementById('dragCharacter');
        if (container) {
            container.innerHTML = `
                <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; 
                           border: 2px dashed #f56565; border-radius: 8px; color: #e53e3e; font-size: 14px; text-align: center;">
                    <div>${message}</div>
                </div>
            `;
        }
    }

    /**
     * 获取Cookie值
     */
    getCookie(name) {
        if (typeof window.utilsManager !== 'undefined' && window.utilsManager.getCookie) {
            return window.utilsManager.getCookie(name);
        }
        
        // 备用实现
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    /**
     * 测试D2按钮功能
     */
    testD2Button() {
        if (typeof updateTestWindow === 'function') {
            updateTestWindow('🔥 测试函数被调用 - D2按钮点击成功！');
        }
        console.log('🔥 测试函数被调用');
        
        // 调用原始的D2函数
        if (typeof generateD2WithNewInterface === 'function') {
            generateD2WithNewInterface();
        }
    }
}

// 延迟初始化预览效果管理器
let previewEffectsManager = null;

// 初始化函数
function initPreviewEffectsManager() {
    if (!previewEffectsManager) {
        previewEffectsManager = new PreviewEffectsManager();
        previewEffectsManager.init();
        
        // 导出全局函数以保持向后兼容性
        window.updateTransformControls = () => previewEffectsManager.updateTransformControls();
        window.loadD0SVGForMeshDeformation = () => previewEffectsManager.loadD0SVGForMeshDeformation();
        window.displayD0SVGForMeshDeformation = (svgContent, character) => previewEffectsManager.displayD0SVGForMeshDeformation(svgContent, character);
        window.showMeshDeformationError = (message) => previewEffectsManager.showMeshDeformationError(message);
        window.testD2Button = () => previewEffectsManager.testD2Button();
        
        // 导出类和实例
        window.PreviewEffectsManager = PreviewEffectsManager;
        window.previewEffectsManager = previewEffectsManager;
        
        console.log('✅ 预览效果管理器已初始化');
    }
    return previewEffectsManager;
}

// DOM加载完成后自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPreviewEffectsManager);
} else {
    initPreviewEffectsManager();
}

// 导出初始化函数
window.initPreviewEffectsManager = initPreviewEffectsManager;

console.log('✅ 预览效果管理模块已加载');
