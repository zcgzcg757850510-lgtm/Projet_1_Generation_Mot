/**
 * 拖拽变换组件模块
 * 处理字符的拖拽、旋转、缩放变换功能
 */

class DragTransformComponent {
    constructor() {
        this.isInitialized = false;
        this.hasCharacter = false;
        this.currentChar = '';
        
        // 变换参数
        this.transform = {
            translateX: 0,
            translateY: 0,
            rotation: 0,
            scale: 1.0
        };
        
        // 拖拽状态
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.transformStart = { x: 0, y: 0 };
    }

    // 初始化组件
    initialize() {
        if (this.isInitialized) return;
        
        this.setupEventListeners();
        this.autoLoadD1ToGrid();
        this.isInitialized = true;
        console.log('DragTransformComponent initialized');
    }

    // 设置事件监听器
    setupEventListeners() {
        // 变换模式切换
        const modeRadios = document.querySelectorAll('input[name="transformMode"]');
        modeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.handleModeChange(e.target.value);
            });
        });

        // 滑块控制
        this.setupSliderControls();
        
        // 画布交互
        this.setupCanvasInteraction();
        
        // 按钮事件
        this.setupButtonEvents();
    }

    // 设置滑块控制
    setupSliderControls() {
        const sliders = {
            'translateX': (value) => { this.transform.translateX = parseFloat(value); },
            'translateY': (value) => { this.transform.translateY = parseFloat(value); },
            'rotation': (value) => { this.transform.rotation = parseFloat(value); },
            'scale': (value) => { this.transform.scale = parseFloat(value); }
        };

        Object.keys(sliders).forEach(sliderId => {
            const slider = document.getElementById(sliderId);
            if (slider) {
                slider.addEventListener('input', (e) => {
                    sliders[sliderId](e.target.value);
                    this.updateTransformDisplay();
                    this.applyTransform();
                });
            }
        });
    }

    // 设置画布交互
    setupCanvasInteraction() {
        const canvas = document.getElementById('dragCanvas');
        if (!canvas) return;

        // 鼠标拖拽
        canvas.addEventListener('mousedown', (e) => {
            const mode = document.querySelector('input[name="transformMode"]:checked')?.value;
            if (mode === 'translate') {
                this.startDrag(e);
            }
        });

        canvas.addEventListener('mousemove', (e) => {
            if (this.isDragging) {
                this.handleDrag(e);
            }
        });

        canvas.addEventListener('mouseup', () => {
            this.endDrag();
        });

        // 鼠标滚轮缩放
        canvas.addEventListener('wheel', (e) => {
            e.preventDefault();
            const mode = document.querySelector('input[name="transformMode"]:checked')?.value;
            if (mode === 'scale') {
                this.handleWheel(e);
            }
        });
    }

    // 设置按钮事件
    setupButtonEvents() {
        // 应用变换按钮
        const applyBtn = document.getElementById('applyTransformBtn');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                this.generateD2();
            });
        }

        // 重置变换按钮
        const resetBtn = document.getElementById('resetTransformBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetTransform();
            });
        }
    }

    // 处理变换模式变化
    handleModeChange(mode) {
        const canvas = document.getElementById('dragCanvas');
        if (!canvas) return;

        // 更新鼠标样式
        const cursors = {
            'translate': 'move',
            'rotate': 'grab',
            'scale': 'zoom-in'
        };
        
        canvas.style.cursor = cursors[mode] || 'default';
    }

    // 开始拖拽
    startDrag(e) {
        this.isDragging = true;
        const rect = e.target.getBoundingClientRect();
        this.dragStart = {
            x: e.clientX - rect.left,
            y: e.clientY - rect.top
        };
        this.transformStart = {
            x: this.transform.translateX,
            y: this.transform.translateY
        };
    }

    // 处理拖拽
    handleDrag(e) {
        if (!this.isDragging) return;
        
        const rect = e.target.getBoundingClientRect();
        const currentX = e.clientX - rect.left;
        const currentY = e.clientY - rect.top;
        
        const deltaX = currentX - this.dragStart.x;
        const deltaY = currentY - this.dragStart.y;
        
        this.transform.translateX = this.transformStart.x + deltaX;
        this.transform.translateY = this.transformStart.y + deltaY;
        
        // 限制范围
        this.transform.translateX = Math.max(-100, Math.min(100, this.transform.translateX));
        this.transform.translateY = Math.max(-100, Math.min(100, this.transform.translateY));
        
        this.updateSliders();
        this.applyTransform();
    }

    // 结束拖拽
    endDrag() {
        this.isDragging = false;
    }

    // 处理滚轮缩放
    handleWheel(e) {
        const delta = e.deltaY > 0 ? -0.1 : 0.1;
        this.transform.scale = Math.max(0.5, Math.min(2.0, this.transform.scale + delta));
        
        this.updateSliders();
        this.applyTransform();
    }

    // 更新滑块值
    updateSliders() {
        const sliders = {
            'translateX': this.transform.translateX,
            'translateY': this.transform.translateY,
            'rotation': this.transform.rotation,
            'scale': this.transform.scale
        };

        Object.keys(sliders).forEach(sliderId => {
            const slider = document.getElementById(sliderId);
            if (slider) {
                slider.value = sliders[sliderId];
            }
        });

        this.updateTransformDisplay();
    }

    // 更新变换显示
    updateTransformDisplay() {
        const displays = {
            'translateXValue': this.transform.translateX.toFixed(1) + 'px',
            'translateYValue': this.transform.translateY.toFixed(1) + 'px',
            'rotationValue': this.transform.rotation.toFixed(1) + '°',
            'scaleValue': this.transform.scale.toFixed(2) + 'x'
        };

        Object.keys(displays).forEach(displayId => {
            const display = document.getElementById(displayId);
            if (display) {
                display.textContent = displays[displayId];
            }
        });
    }

    // 应用变换到字符
    applyTransform() {
        const character = document.getElementById('dragCharacter');
        if (!character) return;

        const transformString = `
            translate(${this.transform.translateX}px, ${this.transform.translateY}px)
            rotate(${this.transform.rotation}deg)
            scale(${this.transform.scale})
        `;
        
        character.style.transform = transformString;
    }

    // 自动加载D1图像到网格
    async autoLoadD1ToGrid() {
        const charInput = document.querySelector('input[name="char"]');
        let currentChar = charInput ? charInput.value.trim() : '';
        
        if (!currentChar) {
            currentChar = getCookie('last_char') || '字';
        }
        
        currentChar = currentChar.charAt(0) || '字';
        this.currentChar = currentChar;
        
        try {
            await this.loadD1Image(currentChar);
            this.hasCharacter = true;
        } catch (error) {
            console.error('加载D1图像失败:', error);
            this.hasCharacter = false;
        }
    }

    // 加载D1图像
    async loadD1Image(character) {
        const response = await fetch(`/find_d_files?ch=${encodeURIComponent(character)}&type=d1`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // 显示D1图像
        const container = document.getElementById('dragCharacter');
        if (container && data.svg_content) {
            container.innerHTML = data.svg_content;
            
            // 调整SVG样式
            const svg = container.querySelector('svg');
            if (svg) {
                svg.style.width = '100%';
                svg.style.height = '100%';
                svg.style.maxWidth = '200px';
                svg.style.maxHeight = '200px';
            }
        }
    }

    // 生成D2
    async generateD2() {
        if (!this.hasCharacter) {
            alert('请先加载字符');
            return;
        }

        const params = {
            char: this.currentChar,
            transform: this.transform
        };

        try {
            const response = await fetch('/generate_d2_transform', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });

            const result = await response.json();
            
            if (result.success) {
                this.displayD2Result(result);
                if (window.toastManager) {
                    window.toastManager.show('generation.d2.success');
                }
            } else {
                throw new Error(result.error || 'D2生成失败');
            }
        } catch (error) {
            console.error('D2生成错误:', error);
            if (window.toastManager) {
                window.toastManager.show('generation.d2.error', error.message);
            }
        }
    }

    // 显示D2结果
    displayD2Result(result) {
        const resultDiv = document.getElementById('d2Result');
        if (resultDiv && result.d2_path) {
            resultDiv.innerHTML = `
                <div class="d2-result-content">
                    <h4>D2生成完成</h4>
                    <img src="${result.d2_path}" alt="D2结果" style="max-width: 200px; max-height: 200px;">
                    <div class="result-actions">
                        <button onclick="window.open('${result.d2_path}', '_blank')" class="btn btn-sm">
                            查看大图
                        </button>
                    </div>
                </div>
            `;
            resultDiv.style.display = 'block';
        }
    }

    // 重置变换
    resetTransform() {
        this.transform = {
            translateX: 0,
            translateY: 0,
            rotation: 0,
            scale: 1.0
        };
        
        this.updateSliders();
        this.applyTransform();
        
        // 隐藏结果
        const resultDiv = document.getElementById('d2Result');
        if (resultDiv) {
            resultDiv.style.display = 'none';
        }
    }

    // 获取组件状态
    getState() {
        return {
            isInitialized: this.isInitialized,
            hasCharacter: this.hasCharacter,
            currentChar: this.currentChar,
            transform: { ...this.transform }
        };
    }
}

// 创建全局实例
const dragTransformComponent = new DragTransformComponent();

// 导出供其他模块使用
window.DragTransformComponent = DragTransformComponent;
window.dragTransformComponent = dragTransformComponent;

// 兼容性函数
function initDragTransformModal() {
    dragTransformComponent.initialize();
}

function openDragTransformModal() {
    // 打开拖拽变换模态框
    const modal = document.getElementById('dragTransformModal');
    if (modal) {
        modal.style.display = 'block';
        dragTransformComponent.initialize();
    }
}

function generateD2WithNewInterface() {
    dragTransformComponent.generateD2();
}

// 导出全局函数
window.openDragTransformModal = openDragTransformModal;
window.initDragTransformModal = initDragTransformModal;
window.generateD2WithNewInterface = generateD2WithNewInterface;
