/**
 * 统一预览卡片组件系统
 * 为所有预览窗口提供统一的UI构建逻辑和交互行为
 */

class PreviewCard {
    constructor(config) {
        this.id = config.id;           // 卡片ID (A, B, C, D1, D2)
        this.title = config.title;     // 显示标题
        this.type = config.type;       // 卡片类型: 'simple', 'compare', 'transform'
        this.container = null;         // DOM容器
        this.imageElement = null;      // 主图片元素
        this.compareElements = null;   // 对比元素（仅对比类型）
        this.isVisible = false;        // 可见状态
        this.hasContent = false;       // 是否有内容
        
        // 回调函数
        this.onLoad = config.onLoad || null;
        this.onError = config.onError || null;
        this.onClick = config.onClick || null;
        
        this.init();
    }

    /**
     * 初始化卡片
     */
    init() {
        this.createStructure();
        this.bindEvents();
        console.log(`✅ 预览卡片 ${this.id} 初始化完成`);
    }

    /**
     * 创建统一的HTML结构
     */
    createStructure() {
        const cardHtml = this.generateCardHTML();
        
        // 查找或创建容器
        const existingCard = document.querySelector(`[data-card="${this.id}"]`);
        if (existingCard) {
            existingCard.innerHTML = cardHtml;
            this.container = existingCard;
        } else {
            // 创建新卡片
            const cardElement = document.createElement('div');
            cardElement.className = 'cell preview-card';
            cardElement.setAttribute('data-card', this.id);
            cardElement.innerHTML = cardHtml;
            this.container = cardElement;
        }

        // 获取关键元素引用
        this.imageElement = this.container.querySelector('.preview-image');
        if (this.type === 'compare') {
            this.compareElements = {
                baseImage: this.container.querySelector('.compare-base'),
                overlayImage: this.container.querySelector('.compare-overlay'),
                handle: this.container.querySelector('.compare-handle'),
                wrapper: this.container.querySelector('.compare-wrapper')
            };
        }
    }

    /**
     * 生成卡片HTML结构
     */
    generateCardHTML() {
        const titleHtml = `
            <div class="preview-title" style="display:flex;align-items:center;justify-content:space-between;">
                <span>${this.title}</span>
                <button class="expand-btn" data-card-id="${this.id}" style="background:none;border:none;color:var(--muted);cursor:pointer;padding:2px 4px;border-radius:3px;font-size:14px;line-height:1;" title="放大/还原窗口">⛶</button>
            </div>
        `;
        
        switch (this.type) {
            case 'simple':
                return `
                    ${titleHtml}
                    <div class="preview-content">
                        <img class="preview-image" alt="${this.id}" style="width:100%;height:auto;display:none"/>
                    </div>
                `;
                
            case 'compare':
                return `
                    ${titleHtml}
                    <div class="preview-content">
                        <div class="compare-wrapper" style="position:relative;width:100%;cursor:ew-resize;">
                            <img class="compare-base preview-image" alt="${this.id} 基线" style="width:100%;height:auto;display:none"/>
                            <img class="compare-overlay" alt="${this.id} 对比" style="position:absolute;inset:0;width:100%;height:auto;display:none;clip-path:inset(0 0 0 0)"/>
                            <div class="compare-handle" style="position:absolute;top:0;bottom:0;width:2px;background:#fff90a;left:50%;display:none;cursor:ew-resize;visibility:hidden"></div>
                        </div>
                    </div>
                `;
                
            case 'transform':
                return `
                    ${titleHtml}
                    <div class="preview-content">
                        <img class="preview-image" alt="${this.id}" style="width:100%;height:auto;display:none"/>
                        <div class="transform-indicator" style="display:none;">🔄</div>
                    </div>
                `;
                
            default:
                return `${titleHtml}<div class="preview-content">未知类型</div>`;
        }
    }

    /**
     * 绑定事件监听器
     */
    bindEvents() {
        if (this.container) {
            // 点击事件
            this.container.addEventListener('click', (e) => {
                // 检查是否点击了放大按钮
                if (e.target.classList.contains('expand-btn')) {
                    e.stopPropagation();
                    this.handleExpandToggle();
                    return;
                }
                
                if (this.onClick) {
                    this.onClick(this, e);
                }
                this.handleClick(e);
            });

            // 对比滑块事件（仅对比类型）
            if (this.type === 'compare' && this.compareElements) {
                this.bindCompareEvents();
            }
        }
    }

    /**
     * 绑定对比滑块事件
     */
    bindCompareEvents() {
        const { wrapper, handle } = this.compareElements;
        
        let isDragging = false;
        
        const handleMouseDown = (e) => {
            isDragging = true;
            e.preventDefault();
        };
        
        const handleMouseMove = (e) => {
            if (!isDragging) return;
            
            const rect = wrapper.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const percentage = Math.max(0, Math.min(100, (x / rect.width) * 100));
            
            this.updateComparePosition(percentage);
        };
        
        const handleMouseUp = () => {
            isDragging = false;
        };
        
        wrapper.addEventListener('mousedown', handleMouseDown);
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
    }

    /**
     * 更新对比位置
     */
    updateComparePosition(percentage) {
        if (this.type !== 'compare' || !this.compareElements) return;
        
        const { overlayImage, handle } = this.compareElements;
        
        handle.style.left = `${percentage}%`;
        overlayImage.style.clipPath = `inset(0 ${100 - percentage}% 0 0)`;
    }

    /**
     * 处理放大/还原切换
     */
    handleExpandToggle() {
        console.log(`🔄 ${this.id} 窗口切换放大/还原`);
        
        // 调用管理器的窗口展开切换方法
        if (window.previewCardManager) {
            window.previewCardManager.toggleWindowExpansion(this.id);
        }
    }

    /**
     * 设置图片内容
     */
    setImage(src, type = 'main') {
        console.log(`🖼️ [setImage] ${this.id}: src=${src}, type=${type}`);
        if (!src) {
            console.log(`⚠️ [setImage] ${this.id}: src vide, effacement du contenu`);
            // 不自动隐藏窗口，只是清除内容
            const targetImage = this.getImageElement(type);
            if (targetImage) {
                targetImage.src = '';
                targetImage.style.display = 'none';
            }
            this.hasContent = false;
            return;
        }

        const targetImage = this.getImageElement(type);
        if (!targetImage) return;

        targetImage.onload = () => {
            console.log(`✅ [onload] ${this.id}: Image chargée avec succès, display=block`);
            targetImage.style.display = 'block';
            this.hasContent = true;
            this.show();
            console.log(`✅ [onload] ${this.id}: show() appelée, carte visible`);
            
            // Debug CSS pour D1 et D2
            if (this.id === 'D1' || this.id === 'D2') {
                setTimeout(() => {
                    const cardEl = this.container;  
                    const imgEl = targetImage;
                    console.log(`🔍 [${this.id} DEBUG] cardEl:`, cardEl);
                    console.log(`🔍 [${this.id} DEBUG] imgEl:`, imgEl);
                    if (cardEl && cardEl.style) {
                        console.log(`🔍 [${this.id} DEBUG] Card visible:`, cardEl.style.display !== 'none');
                        console.log(`🔍 [${this.id} DEBUG] Card classList:`, cardEl.classList.toString());
                    }
                    if (imgEl && imgEl.style) {
                        console.log(`🔍 [${this.id} DEBUG] Image visible:`, imgEl.style.display !== 'none');
                    }
                    console.log(`🔍 [${this.id} DEBUG] hasContent:`, this.hasContent);
                    console.log(`🔍 [${this.id} DEBUG] isVisible:`, this.isVisible);
                }, 100);
            }
            
            if (this.onLoad) {
                this.onLoad(this, type);
            }
            
            console.log(`📷 ${this.id} 图片加载成功: ${type}`);
        };

        targetImage.onerror = () => {
            console.log(`❌ [onerror] ${this.id}: ERREUR de chargement image!`);
            targetImage.style.display = 'none';
            this.hasContent = false;
            this.hide();
            
            if (this.onError) {
                this.onError(this, type);
            }
            
            console.log(`❌ ${this.id} 图片加载失败: ${type}`);
        };

        console.log(`🔄 [setImage] ${this.id}: Définition src=${src}`);
        targetImage.src = src;
    }

    /**
     * 获取指定类型的图片元素
     */
    getImageElement(type = 'main') {
        switch (type) {
            case 'main':
                return this.imageElement;
            case 'base':
                return this.compareElements?.baseImage;
            case 'overlay':
                return this.compareElements?.overlayImage;
            default:
                return this.imageElement;
        }
    }

    /**
     * 显示卡片
     */
    show() {
        if (this.container) {
            this.container.style.display = 'block';
            this.isVisible = true;
            
            // 显示对比控件（如果是对比类型且有内容）
            if (this.type === 'compare' && this.hasContent && this.compareElements) {
                this.compareElements.handle.style.display = 'block';
                this.compareElements.handle.style.visibility = 'visible';
            }
        }
    }

    /**
     * 隐藏卡片
     */
    hide() {
        if (this.container) {
            this.container.style.display = 'none';
            this.isVisible = false;
            
            // 隐藏对比控件
            if (this.type === 'compare' && this.compareElements) {
                this.compareElements.handle.style.display = 'none';
                this.compareElements.handle.style.visibility = 'hidden';
            }
        }
    }

    /**
     * 清空内容
     */
    clear() {
        if (this.imageElement) {
            this.imageElement.src = '';
            this.imageElement.style.display = 'none';
        }
        
        if (this.compareElements) {
            this.compareElements.baseImage.src = '';
            this.compareElements.baseImage.style.display = 'none';
            this.compareElements.overlayImage.src = '';
            this.compareElements.overlayImage.style.display = 'none';
        }
        
        this.hasContent = false;
        this.hide();
    }

    /**
     * 处理点击事件
     */
    handleClick(e) {
        // 如果有内容，打开放大预览
        if (this.hasContent && this.imageElement && this.imageElement.src) {
            this.openZoomModal();
        }
    }

    /**
     * 打开放大预览模态框
     */
    openZoomModal() {
        if (window.openImageModal) {
            const imageSrc = this.imageElement.src;
            
            // 根据窗口ID确定对比图逻辑
            let compareData = null;
            const compareSrc = this.getCompareImageSrc();
            
            if (compareSrc) {
                compareData = {
                    baseSrc: imageSrc,     // 左侧显示当前图
                    overlaySrc: compareSrc // 右侧显示对比图（前一张）
                };
            }
            
            window.openImageModal(imageSrc, this.title, compareData);
        }
    }
    
    /**
     * 获取对比图片的源地址
     */
    getCompareImageSrc() {
        // 定义对比关系：当前窗口 -> 对比窗口
        // 注意：窗口ID与显示内容的映射关系
        const compareMap = {
            'A': 'A',    // A窗口(轮廓)对比自身
            'C': 'C',    // C窗口(显示"原始中轴 B")对比自身
            'D1': 'C',   // D1窗口(显示"处理中轴 C")对比C窗口(原始中轴)
            'D2': 'D1',  // D2窗口(显示"网格变形 D1")对比D1窗口(处理中轴)
            'B': 'D2'    // B窗口(显示"中轴填充 D2")对比D2窗口(网格变形)
        };
        
        const compareId = compareMap[this.id];
        if (!compareId) return null;
        
        // 如果对比自身，返回当前图片
        if (compareId === this.id) {
            return this.imageElement.src;
        }
        
        // 获取对比窗口的图片
        const compareCard = window.previewCardManager?.getCard(compareId);
        if (compareCard && compareCard.imageElement && compareCard.imageElement.src) {
            return compareCard.imageElement.src;
        }
        
        return null;
    }

    /**
     * 获取卡片状态
     */
    getState() {
        return {
            id: this.id,
            title: this.title,
            type: this.type,
            isVisible: this.isVisible,
            hasContent: this.hasContent,
            imageSrc: this.imageElement?.src || null
        };
    }
}

/**
 * 预览卡片管理器
 */
class PreviewCardManager {
    constructor() {
        this.cards = new Map();
        this.initialized = false;
    }

    /**
     * 初始化所有预览卡片
     */
    initialize() {
        if (this.initialized) return;

        // 定义5个预览卡片的配置（重新排序）
        const cardConfigs = [
            { id: 'A', title: '轮廓 (A)', type: 'simple' },
            { id: 'C', title: '原始中轴 (B)', type: 'simple' },
            { id: 'D1', title: '处理中轴 (C)', type: 'simple' },
            { id: 'D2', title: '网格变形 (D1)', type: 'transform' },
            { id: 'B', title: '中轴填充 (D2)', type: 'simple' }
        ];
        
        console.log('🔧 [CARDS] 创建卡片配置:', cardConfigs);

        // 获取容器
        const container = document.querySelector('.cards__inner');
        if (!container) {
            console.error('❌ 未找到预览卡片容器');
            return;
        }

        // 创建所有卡片并插入容器
        cardConfigs.forEach(config => {
            const card = new PreviewCard(config);
            this.cards.set(config.id, card);
            
            // 将卡片插入容器
            if (card.container) {
                container.appendChild(card.container);
            }
        });

        // 设置兼容性ID映射
        this.setupCompatibilityIds();

        this.initialized = true;
        console.log('✅ 预览卡片管理器初始化完成');
    }

    /**
     * 设置兼容性ID映射，确保现有代码能正常工作
     */
    setupCompatibilityIds() {
        // 为现有代码提供向后兼容的元素引用
        const idMappings = {
            'imgA': ['A', 'main'],
            'imgB': ['B', 'main'],
            'imgC': ['C', 'main'],
            'imgD0': ['D1', 'base'],
            'imgD1': ['D1', 'main'],
            'imgD2': ['D2', 'main'],
            'cmpWrap': ['D1', 'wrapper'],
            'cmpHandle': ['D1', 'handle']
        };

        Object.entries(idMappings).forEach(([oldId, [cardId, elementType]]) => {
            const card = this.getCard(cardId);
            if (!card) return;

            let element = null;
            switch (elementType) {
                case 'main':
                    element = card.imageElement;
                    break;
                case 'base':
                    element = card.compareElements?.baseImage;
                    break;
                case 'overlay':
                    element = card.compareElements?.overlayImage;
                    break;
                case 'wrapper':
                    element = card.compareElements?.wrapper;
                    break;
                case 'handle':
                    element = card.compareElements?.handle;
                    break;
            }

            if (element) {
                element.id = oldId;
                // 同时添加到全局window对象以确保兼容性
                window[oldId] = element;
            }
        });
    }

    /**
     * 获取指定卡片
     */
    getCard(id) {
        return this.cards.get(id);
    }

    /**
     * 设置卡片图片
     */
    setCardImage(id, src, type = 'main') {
        console.log(`🎯 [setCardImage] Tentative: id=${id}, src=${src}, type=${type}`);
        const card = this.getCard(id);
        if (card) {
            console.log(`✅ [setCardImage] Carte trouvée pour ${id}, appel setImage`);
            card.setImage(src, type);
        } else {
            console.log(`❌ [setCardImage] AUCUNE CARTE TROUVÉE pour ${id}!`);
        }
    }

    /**
     * 更新卡片图片 - 兼容性方法
     */
    updateCard(id, src) {
        this.setCardImage(id, src);
    }

    /**
     * 更新对比卡片 - 兼容性方法
     */
    updateCompareCard(id, data) {
        const card = this.getCard(id);
        if (card && card.type === 'compare' && data) {
            if (data.baseSrc) {
                card.setImage(data.baseSrc, 'base');
            }
            if (data.overlaySrc) {
                card.setImage(data.overlaySrc, 'overlay');
            }
        }
    }

    /**
     * 切换窗口展开状态
     */
    toggleWindowExpansion(cardId) {
        console.log(`🔄 切换窗口 ${cardId} 的展开状态`);
        
        const container = document.querySelector('.cards__inner');
        if (!container) {
            console.error('❌ 未找到预览容器');
            return;
        }
        
        // 检查当前是否已经有窗口展开
        const currentExpanded = container.dataset.expandedCard;
        
        if (currentExpanded === cardId) {
            // 如果当前窗口已展开，则恢复所有窗口
            this.restoreAllWindows();
        } else {
            // 展开指定窗口，隐藏其他窗口
            this.expandWindow(cardId);
        }
    }

    /**
     * 展开指定窗口，隐藏其他窗口
     */
    expandWindow(cardId) {
        console.log(`📈 展开窗口: ${cardId}`);
        
        const container = document.querySelector('.cards__inner');
        if (!container) return;
        
        // 记录当前展开的窗口
        container.dataset.expandedCard = cardId;
        
        // 隐藏所有其他窗口，展开指定窗口
        this.cards.forEach((card, id) => {
            if (id === cardId) {
                // 展开目标窗口
                card.container.style.display = 'block';
                card.container.style.gridColumn = '1 / -1'; // 占满整行
                card.container.style.gridRow = '1 / -1';    // 占满整列
                card.container.style.zIndex = '10';         // 置顶
            } else {
                // 隐藏其他窗口
                card.container.style.display = 'none';
            }
        });
        
        // 添加展开状态样式
        container.classList.add('window-expanded');
        
        if (typeof showToast !== 'undefined') {
            showToast(`${cardId} 窗口已展开`, 'info');
        }
    }

    /**
     * 恢复所有窗口的正常显示
     */
    restoreAllWindows() {
        console.log('📉 恢复所有窗口');
        
        const container = document.querySelector('.cards__inner');
        if (!container) return;
        
        // 清除展开状态记录
        delete container.dataset.expandedCard;
        
        // 恢复所有窗口的默认样式
        this.cards.forEach((card) => {
            card.container.style.display = 'block';
            card.container.style.gridColumn = '';
            card.container.style.gridRow = '';
            card.container.style.zIndex = '';
        });
        
        // 移除展开状态样式
        container.classList.remove('window-expanded');
        
        if (typeof showToast !== 'undefined') {
            showToast('窗口已恢复正常显示', 'info');
        }
    }

    /**
     * 清空所有卡片
     */
    clearAll() {
        this.cards.forEach(card => card.clear());
    }

    /**
     * 获取所有卡片状态
     */
    getAllStates() {
        const states = {};
        this.cards.forEach((card, id) => {
            states[id] = card.getState();
        });
        return states;
    }
}

// 创建全局实例
const previewCardManager = new PreviewCardManager();

// 导出到全局
window.PreviewCard = PreviewCard;
window.PreviewCardManager = PreviewCardManager;
window.previewCardManager = previewCardManager;

// 自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => previewCardManager.initialize());
} else {
    previewCardManager.initialize();
}

console.log('✅ 预览卡片组件系统已加载');
