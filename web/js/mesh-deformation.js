/**
 * 网格变形系统模块
 * 管理网格变形的核心功能和交互逻辑
 */

class MeshDeformationSystem {
    constructor() {
        this.meshControlPointsData = [];
        this.meshGridSize = 2;
        this.isDraggingMeshPoint = false;
        this.currentDragPoint = null;
        this.initialized = false;
    }

    /**
     * 初始化网格变形系统
     */
    init() {
        if (this.initialized) return;
        
        this.initMeshGrid();
        this.initialized = true;
        
        console.log('✅ 网格变形系统已初始化');
    }

    /**
     * 初始化网格
     */
    initMeshGrid() {
        // 2x2网格，只有4个控制点
        this.meshGridSize = 2;
        this.createMeshControlPoints();
        this.setupMeshEventListeners();
    }

    /**
     * 创建网格控制点
     */
    createMeshControlPoints() {
        const container = document.getElementById('meshControlPoints');
        
        if (!container) {
            console.error('网格控制点容器未找到');
            return;
        }
        
        // 清空现有控制点
        container.innerHTML = '';
        this.meshControlPointsData = [];
        
        // 等待容器正确调整大小
        setTimeout(() => {
            const containerRect = container.getBoundingClientRect();
            
            // 创建控制点网格 - 使用容器尺寸
            const spacing = Math.min(containerRect.width, containerRect.height) / (this.meshGridSize - 1);
            const gridSize = spacing * (this.meshGridSize - 1);
            const offsetX = (containerRect.width - gridSize) / 2;
            const offsetY = (containerRect.height - gridSize) / 2;
            
            for (let row = 0; row < this.meshGridSize; row++) {
                this.meshControlPointsData[row] = [];
                for (let col = 0; col < this.meshGridSize; col++) {
                    const x = offsetX + col * spacing;
                    const y = offsetY + row * spacing;
                    
                    // 存储原始和当前位置
                    const pointData = {
                        originalX: x,
                        originalY: y,
                        currentX: x,
                        currentY: y,
                        row: row,
                        col: col
                    };
                    
                    this.meshControlPointsData[row][col] = pointData;
                    
                    // 创建可视化控制点
                    const point = document.createElement('div');
                    point.className = 'mesh-control-point';
                    point.style.cssText = `
                        position: absolute;
                        width: 12px;
                        height: 12px;
                        background: #ff6b6b;
                        border: 2px solid #fff;
                        border-radius: 50%;
                        cursor: grab;
                        z-index: 10;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                        transition: transform 0.2s ease;
                        left: ${x - 6}px;
                        top: ${y - 6}px;
                    `;
                    
                    point.dataset.row = row;
                    point.dataset.col = col;
                    
                    container.appendChild(point);
                }
            }
            
            this.drawMeshGrid();
        }, 100);
    }

    /**
     * 绘制网格
     */
    drawMeshGrid() {
        const svg = document.getElementById('meshGrid');
        if (!svg) return;
        
        svg.innerHTML = `
            <defs>
                <pattern id="gridPattern" width="10" height="10" patternUnits="userSpaceOnUse">
                    <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#333" stroke-width="0.5" opacity="0.3"/>
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#gridPattern)" opacity="0.2"/>
        `;
        
        // 绘制网格线
        this.drawGridLines(svg);
    }

    /**
     * 绘制网格线
     */
    drawGridLines(svg) {
        if (!this.meshControlPointsData.length) return;
        
        const svgRect = svg.getBoundingClientRect();
        
        // 绘制水平线
        for (let row = 0; row < this.meshGridSize; row++) {
            const points = [];
            for (let col = 0; col < this.meshGridSize; col++) {
                const pointData = this.meshControlPointsData[row][col];
                points.push(`${pointData.currentX},${pointData.currentY}`);
            }
            
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            line.setAttribute('points', points.join(' '));
            line.setAttribute('stroke', '#4CAF50');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('fill', 'none');
            line.setAttribute('opacity', '0.7');
            svg.appendChild(line);
        }
        
        // 绘制垂直线
        for (let col = 0; col < this.meshGridSize; col++) {
            const points = [];
            for (let row = 0; row < this.meshGridSize; row++) {
                const pointData = this.meshControlPointsData[row][col];
                points.push(`${pointData.currentX},${pointData.currentY}`);
            }
            
            const line = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
            line.setAttribute('points', points.join(' '));
            line.setAttribute('stroke', '#4CAF50');
            line.setAttribute('stroke-width', '2');
            line.setAttribute('fill', 'none');
            line.setAttribute('opacity', '0.7');
            svg.appendChild(line);
        }
    }

    /**
     * 设置网格事件监听器
     */
    setupMeshEventListeners() {
        const container = document.getElementById('meshControlPoints');
        if (!container) return;
        
        // 鼠标按下
        container.addEventListener('mousedown', (e) => {
            if (e.target.classList.contains('mesh-control-point')) {
                this.isDraggingMeshPoint = true;
                this.currentDragPoint = e.target;
                e.target.style.cursor = 'grabbing';
                e.target.style.transform = 'scale(1.2)';
                e.preventDefault();
            }
        });
        
        // 鼠标移动
        document.addEventListener('mousemove', (e) => {
            if (this.isDraggingMeshPoint && this.currentDragPoint) {
                const containerRect = container.getBoundingClientRect();
                const x = e.clientX - containerRect.left;
                const y = e.clientY - containerRect.top;
                
                // 限制在容器内
                const clampedX = Math.max(6, Math.min(containerRect.width - 6, x));
                const clampedY = Math.max(6, Math.min(containerRect.height - 6, y));
                
                this.currentDragPoint.style.left = (clampedX - 6) + 'px';
                this.currentDragPoint.style.top = (clampedY - 6) + 'px';
                
                // 更新数据
                const row = parseInt(this.currentDragPoint.dataset.row);
                const col = parseInt(this.currentDragPoint.dataset.col);
                if (this.meshControlPointsData[row] && this.meshControlPointsData[row][col]) {
                    this.meshControlPointsData[row][col].currentX = clampedX;
                    this.meshControlPointsData[row][col].currentY = clampedY;
                }
                
                // 重绘网格
                this.drawMeshGrid();
            }
        });
        
        // 鼠标释放
        document.addEventListener('mouseup', () => {
            if (this.isDraggingMeshPoint) {
                this.isDraggingMeshPoint = false;
                if (this.currentDragPoint) {
                    this.currentDragPoint.style.cursor = 'grab';
                    this.currentDragPoint.style.transform = 'scale(1)';
                    this.currentDragPoint = null;
                }
            }
        });
    }

    /**
     * 应用网格变形
     */
    applyMeshTransformation() {
        // 这个函数将应用网格变形到实际的字符生成中
        alert('网格变形已应用！这个功能将集成到字符生成流程中。');
        console.log('网格变形数据:', this.meshControlPointsData);
    }

    /**
     * 重置网格
     */
    resetMeshGrid() {
        // 重置网格参数
        const dragCharacter = document.getElementById('dragCharacter');
        if (dragCharacter) {
            dragCharacter.style.left = '50%';
            dragCharacter.style.top = '50%';
            dragCharacter.style.transform = 'translate(-50%, -50%)';
            
            // 恢复原始SVG
            const originalSvg = dragCharacter.dataset.originalSvg;
            const character = dragCharacter.dataset.character;
            if (originalSvg && character) {
                if (typeof displayD0SVG === 'function') {
                    displayD0SVG(originalSvg, character);
                }
            }
        }
        
        // 重置所有网格控制点
        for (let row = 0; row < this.meshGridSize; row++) {
            for (let col = 0; col < this.meshGridSize; col++) {
                if (this.meshControlPointsData[row] && this.meshControlPointsData[row][col]) {
                    const pointData = this.meshControlPointsData[row][col];
                    pointData.currentX = pointData.originalX;
                    pointData.currentY = pointData.originalY;
                }
            }
        }
        
        // 更新可视化控制点
        const points = document.querySelectorAll('.mesh-control-point');
        points.forEach(point => {
            const row = parseInt(point.dataset.row);
            const col = parseInt(point.dataset.col);
            if (this.meshControlPointsData[row] && this.meshControlPointsData[row][col]) {
                const pointData = this.meshControlPointsData[row][col];
                point.style.left = (pointData.originalX - 6) + 'px';
                point.style.top = (pointData.originalY - 6) + 'px';
            }
        });
        
        // 重绘网格
        this.drawMeshGrid();
        
        console.log('网格已重置');
    }

    /**
     * 保存网格预设
     */
    saveMeshPreset() {
        const presetName = prompt('请输入预设名称:');
        if (presetName) {
            const presetData = {
                name: presetName,
                gridSize: this.meshGridSize,
                controlPoints: this.meshControlPointsData.map(row => 
                    row.map(point => ({
                        originalX: point.originalX,
                        originalY: point.originalY,
                        currentX: point.currentX,
                        currentY: point.currentY
                    }))
                ),
                timestamp: Date.now()
            };
            
            localStorage.setItem(`meshPreset_${presetName}`, JSON.stringify(presetData));
            alert(`网格预设 "${presetName}" 已保存！`);
        }
    }

    /**
     * 加载网格预设
     */
    loadMeshPreset() {
        const presetName = prompt('请输入要加载的预设名称:');
        if (presetName) {
            const presetData = localStorage.getItem(`meshPreset_${presetName}`);
            if (presetData) {
                try {
                    const preset = JSON.parse(presetData);
                    this.meshGridSize = preset.gridSize;
                    this.meshControlPointsData = preset.controlPoints;
                    
                    // 重新创建控制点
                    this.createMeshControlPoints();
                    
                    alert(`网格预设 "${presetName}" 已加载！`);
                } catch (error) {
                    alert('加载预设失败：数据格式错误');
                }
            } else {
                alert(`未找到预设 "${presetName}"`);
            }
        }
    }

    /**
     * 获取网格状态
     */
    getGridState() {
        return {
            gridSize: this.meshGridSize,
            controlPoints: this.meshControlPointsData
        };
    }
}

// 延迟初始化网格变形系统
let meshDeformationSystem = null;

// 初始化函数
function initMeshDeformationSystem() {
    if (!meshDeformationSystem) {
        meshDeformationSystem = new MeshDeformationSystem();
        meshDeformationSystem.init();
        
        // 导出全局函数以保持向后兼容性
        window.initMeshGrid = () => meshDeformationSystem.initMeshGrid();
        window.createMeshControlPoints = () => meshDeformationSystem.createMeshControlPoints();
        window.drawMeshGrid = () => meshDeformationSystem.drawMeshGrid();
        window.applyMeshTransformation = () => meshDeformationSystem.applyMeshTransformation();
        window.resetMeshGrid = () => meshDeformationSystem.resetMeshGrid();
        window.saveMeshPreset = () => meshDeformationSystem.saveMeshPreset();
        window.loadMeshPreset = () => meshDeformationSystem.loadMeshPreset();
        
        // 导出全局变量以保持兼容性
        window.meshControlPointsData = meshDeformationSystem.meshControlPointsData;
        window.meshGridSize = meshDeformationSystem.meshGridSize;
        
        // 导出类和实例
        window.MeshDeformationSystem = MeshDeformationSystem;
        window.meshDeformationSystem = meshDeformationSystem;
        
        console.log('✅ 网格变形系统已初始化');
    }
    return meshDeformationSystem;
}

// DOM加载完成后自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMeshDeformationSystem);
} else {
    initMeshDeformationSystem();
}

// 导出初始化函数
window.initMeshDeformationSystem = initMeshDeformationSystem;

console.log('✅ 网格变形系统模块已加载');
