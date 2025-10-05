/**
 * 预览管理模块 - 处理图片预览、SVG加载、测试窗口等功能
 * 从 ui.html 中抽离的预览相关功能
 */

class PreviewManager {
    constructor() {
        this.loadedFiles = {};
        this.testWindow = null;
        this.initializeTestWindow();
    }

    /**
     * 带时间戳的URL生成
     */
    withTimestamp(url) {
        return url ? (url + (url.includes('?') ? '&' : '?') + 'ts=' + Date.now()) : url;
    }

    /**
     * 设置图片元素的src并处理加载状态
     */
    setImg(element, url) {
        if (!element || !url) return;
        
        element.onerror = () => { 
            console.warn('❌ 图片加载失败:', url);
            element.style.opacity = '0.5'; 
        }; 
        
        element.onload = () => {      
            element.style.opacity = '1'; 
        }; 
        
        element.src = url; 
        element.style.display = 'block';
    }

    /**
     * 加载现有的SVG文件
     */
    async loadExistingSVGs() {
        console.log('🔄 开始自动加载现有SVG文件...');
        
        try {
            // 获取当前字符
            const charInput = document.querySelector('input[name="char"]');
            const currentChar = charInput?.value?.trim();
            
            if (!currentChar) {
                console.log('ℹ️ 没有设置字符，跳过SVG加载');
                this.updateTestWindow('没有设置字符，跳过自动加载');
                return;
            }

            // 检查文件状态 - 添加timestamp避免缓存
            const cacheBreaker = Date.now();
            const response = await fetch(`/status?ch=${encodeURIComponent(currentChar)}&_t=${cacheBreaker}`);
            if (!response.ok) {
                console.warn('⚠️ 无法获取文件状态');
                this.updateTestWindow('无法获取文件状态，可能还没有生成过文件');
                return;
            }

            const statusData = await response.json();
            const files = statusData.files || {};
            console.log('📁 检测到的文件:', files);
            console.log('🔍 [DEBUG] PreviewCardManager状态:', window.previewCardManager ? '存在' : '不存在');
            console.log('🔍 [DEBUG] PreviewCardManager初始化状态:', window.previewCardManager?.initialized);
            
            // Debug spécial pour D1 et D2 - 显示完整状态数据
            console.log('🔍 [DEBUG] 完整状态数据:', JSON.stringify(statusData, null, 2));
            if (files.D1) console.log('🎯 D1 文件检测到:', files.D1);
            if (files.D2) console.log('🎯 D2 文件检测到:', files.D2);
            if (files.D0) console.log('🎯 D0 文件检测到:', files.D0);
            if (files.D) console.log('🎯 D 文件检测到:', files.D);
            if (!files.D1) console.log('❌ D1 文件未检测到');
            if (!files.D2) console.log('❌ D2 文件未检测到');

            let loadedCount = 0;

            // 使用PreviewCardManager加载图片（如果可用）
            if (window.previewCardManager && window.previewCardManager.initialized) {
                // 🔧 MAPPING DIRECT avec les nouveaux dossiers
                console.log('📁 Files disponibles:', files);
                
                // A窗口 (轮廓) ← API.A (A_outlines)
                if (files.A) {
                    console.log('🖼️ A窗口 (轮廓) ← API.A:', files.A);
                    window.previewCardManager.setCardImage('A', this.withTimestamp(`/A_outlines/${files.A}`));
                    loadedCount++;
                }

                // C窗口 (原始中轴 B) ← API.B (B_raw_centerline) 
                if (files.B) {
                    console.log('🖼️ C窗口 (原始中轴 B) ← API.B:', files.B);
                    window.previewCardManager.setCardImage('C', this.withTimestamp(`/B_raw_centerline/${files.B}`));
                    loadedCount++;
                }

                // D1窗口 (处理中轴 C) ← API.C (C_processed_centerline)
                if (files.C) {
                    console.log('🖼️ D1窗口 (处理中轴 C) ← API.C:', files.C);
                    window.previewCardManager.setCardImage('D1', this.withTimestamp(`/C_processed_centerline/${files.C}`));
                    loadedCount++;
                    if (statusData.angles) {
                        window.previewCardManager.setAngles(statusData.angles);
                    }
                }

                // D2窗口 (网格变形 D1) ← API.D1 (D1_grid_transform)
                if (files.D1) {
                    console.log('🖼️ D2窗口 (网格变形 D1) ← API.D1:', files.D1);
                    const d1Url = this.withTimestamp(`/D1_grid_transform/${files.D1}`);
                    console.log('🔍 [DEBUG] D2窗口 (网格变形 D1) URL:', d1Url);
                    window.previewCardManager.setCardImage('D2', d1Url);
                    loadedCount++;
                    console.log('✅ [DEBUG] D2窗口已加载D1文件，当前计数:', loadedCount);
                } else {
                    console.log('❌ [DEBUG] 没有找到D1文件');
                }

                // B窗口 (中轴填充 D2) ← API.D2 (D2_median_fill)
                if (files.D2) {
                    console.log('🖼️ B窗口 (中轴填充 D2) ← API.D2:', files.D2);
                    const d2Url = this.withTimestamp(`/D2_median_fill/${files.D2}`);
                    console.log('🔍 [DEBUG] B窗口 (中轴填充 D2) URL:', d2Url);
                    window.previewCardManager.setCardImage('B', d2Url);
                    loadedCount++;
                    console.log('✅ [DEBUG] B窗口已加载D2文件，当前计数:', loadedCount);
                } else {
                    console.log('❌ [DEBUG] 没有找到D2文件');
                }
            } else {
                // 回退到直接DOM操作
                console.log('⚠️ PreviewCardManager不可用，使用传统方法加载');
                
                // 获取图片元素
                const imgA = document.getElementById('imgA');
                const imgB = document.getElementById('imgB'); 
                const imgC = document.getElementById('imgC');
                const imgD1 = document.getElementById('imgD1');
                const imgD2 = document.getElementById('imgD2');

                // 加载各类型图片
                if (files.A && imgA) {
                    console.log('🖼️ 加载A图 (轮廓):', files.A);
                    this.setImg(imgA, this.withTimestamp(`/A_outlines/${files.A}`));
                    loadedCount++;
                }

                if (files.B && imgB) {
                    console.log('🖼️ 加载B图 (填充):', files.B);
                    this.setImg(imgB, this.withTimestamp(`/D2_median_fill/${files.B}`));
                    loadedCount++;
                }

                if (files.C && imgC) {
                    console.log('🖼️ 加载C图 (原始中轴):', files.C);
                    this.setImg(imgC, this.withTimestamp(`/B_raw_centerline/${files.C}`));
                    loadedCount++;
                }

                // 优先加载D1文件
                if (files.D1 && imgD1) {
                    console.log('🖼️ 加载D1图 (处理中轴):', files.D1);
                    this.setImg(imgD1, this.withTimestamp(`/C_processed_centerline/${files.D1}`));
                    loadedCount++;
                } else if (files.D && imgD1) {
                    console.log('🖼️ 加载D图 (处理中轴) 作为D1:', files.D);
                    this.setImg(imgD1, this.withTimestamp(`/C_processed_centerline/${files.D}`));
                    loadedCount++;
                }

                // 加载D2图片（网格变形结果）
                if (files.D2 && imgD2) {
                    console.log('🖼️ 加载D2图 (网格变形):', files.D2);
                    this.setImg(imgD2, this.withTimestamp(`/C_processed_centerline/${files.D2}`));
                    loadedCount++;
                }
            }

            if (loadedCount > 0) {
                console.log(`✅ 成功自动加载 ${loadedCount} 个图片文件`);
                this.updateTestWindow(`✅ 自动加载了 ${loadedCount} 个现有图片文件 (字符: ${currentChar})`);
            } else {
                console.log(`ℹ️ 字符 "${currentChar}" 还没有生成过图片文件`);
                this.updateTestWindow(`字符 "${currentChar}" 还没有生成过图片文件`);
            }

            // 保存加载的文件信息
            this.loadedFiles = files;

        } catch (error) {
            console.error('❌ 加载SVG文件时出错:', error);
            this.updateTestWindow(`❌ 加载SVG文件出错: ${error.message}`);
        }
    }

    /**
     * 加载D0和D1图片
     */
    async loadD0D1Images() {
        console.log('🔄 开始加载D0和D1图片...');
        
        try {
            const charInput = document.querySelector('input[name="char"]');
            const currentChar = charInput?.value?.trim();
            
            if (!currentChar) {
                console.log('没有设置字符，跳过D0/D1加载');
                return;
            }

            // 查找D0文件
            const d0Response = await fetch(`/find_d_files?ch=${encodeURIComponent(currentChar)}&type=orig`);
            if (d0Response.ok) {
                const d0Data = await d0Response.json();
                if (d0Data.success && d0Data.filename) {
                    const imgD0 = document.getElementById('imgD0');
                    if (imgD0) {
                        console.log('🖼️ 加载D0图:', d0Data.filename);
                        this.setImg(imgD0, this.withTimestamp(`/C_processed_centerline/${d0Data.filename}`));
                    }
                }
            }

            // 查找D1文件
            const d1Response = await fetch(`/find_d_files?ch=${encodeURIComponent(currentChar)}&type=d1`);
            if (d1Response.ok) {
                const d1Data = await d1Response.json();
                if (d1Data.success && d1Data.filename) {
                    const imgD1 = document.getElementById('imgD1');
                    if (imgD1) {
                        console.log('🖼️ 加载D1图:', d1Data.filename);
                        this.setImg(imgD1, this.withTimestamp(`/C_processed_centerline/${d1Data.filename}`));
                    }
                }
            }

        } catch (error) {
            console.error('加载D0/D1图片时出错:', error);
        }
    }

    /**
     * 刷新预览页面
     */
    refreshPreview() {
        const pv = document.getElementById('pv');
        if (pv) {
            pv.src = '/preview?ts=' + Date.now() + '&v={{version}}';
        }
    }

    /**
     * 初始化测试窗口
     */
    initializeTestWindow() {
        const box = document.getElementById('anglesBox');
        if (!box) {
            console.error('测试窗口容器未找到');
            return;
        }
        
        this.testWindow = box;
        
        const timestamp = new Date().toLocaleTimeString();
        const charInput = document.querySelector('input[name="char"]');
        const currentChar = charInput?.value?.trim() || '未设置';
        
        box.innerHTML = `<div style="color: var(--fg-0); font-weight: bold; margin-bottom: 8px;">🔧 测试窗口已启动</div>
<div style="color: var(--muted); font-size: 10px; margin-bottom: 6px;">初始化时间: ${timestamp}</div>
<div style="color: var(--fg-1); font-size: 10px; line-height: 1.3;">
  <strong>当前状态:</strong><br>
  • 当前字符: ${currentChar}<br>
  • 网格状态: ${typeof gridTransform !== 'undefined' && gridTransform.controlPoints ? '已初始化' : '未初始化'}<br>
  • 预设管理: ${typeof presetManager !== 'undefined' ? '已加载' : '未加载'}<br>
</div>
<div style="color: var(--success); font-size: 10px; margin-top: 8px;">
  ✅ 测试窗口显示功能正常
</div>`;
        
        // 自动滚动到底部
        box.scrollTop = box.scrollHeight;
    }

    /**
     * 更新测试窗口内容
     */
    updateTestWindow(message) {
        if (!this.testWindow) {
            this.testWindow = document.getElementById('anglesBox');
        }
        
        if (!this.testWindow) return;
        
        const timestamp = new Date().toLocaleTimeString();
        const newLine = `<div style="color: var(--fg-1); font-size: 10px; margin: 2px 0; padding: 2px 4px; background: rgba(255,255,255,0.02); border-radius: 2px;">
    <span style="color: var(--muted);">[${timestamp}]</span> ${message}
</div>`;
        
        this.testWindow.innerHTML += newLine;
        
        // 自动滚动到底部
        this.testWindow.scrollTop = this.testWindow.scrollHeight;
    }

    /**
     * 设置所有ABCD图片
     */
    setAllImages(files) {
        const imgA = document.getElementById('imgA');
        const imgB = document.getElementById('imgB'); 
        const imgC = document.getElementById('imgC');
        const imgD1 = document.getElementById('imgD1');
        const cmpHandle = document.getElementById('cmpHandle');

        if (files.A && imgA) {
            this.setImg(imgA, this.withTimestamp(`/A_outlines/${files.A}`));
        }
        if (files.B && imgB) {
            this.setImg(imgB, this.withTimestamp(`/D2_median_fill/${files.B}`));
        }
        if (files.C && imgC) {
            this.setImg(imgC, this.withTimestamp(`/B_raw_centerline/${files.C}`));
        }
        if (files.D && imgD1) {
            this.setImg(imgD1, this.withTimestamp(`/C_processed_centerline/${files.D}`));
            if (cmpHandle) cmpHandle.style.display = 'block';
        } 
    }

    /**
     * 获取已加载的文件信息
     */
    getLoadedFiles() {
        return this.loadedFiles;
    }

    /**
     * 清除所有预览图片
     */
    clearAllPreviews() {
        const imageIds = ['imgA', 'imgB', 'imgC', 'imgD1', 'imgD2', 'imgD0'];
        imageIds.forEach(id => {
            const img = document.getElementById(id);
            if (img) {
                img.src = '';
                img.style.display = 'none';
                img.style.opacity = '0.5';
            }
        });
        
        const cmpHandle = document.getElementById('cmpHandle');
        if (cmpHandle) {
            cmpHandle.style.display = 'none';
        }
        
        this.loadedFiles = {};
        this.updateTestWindow('已清除所有预览图片');
    }
}

// 延迟初始化预览管理器
let previewManager = null;

// 初始化函数
function initPreviewManager() {
    if (!previewManager) {
        // 确保状态管理器已初始化
        if (typeof window.initStateManager === 'function') {
            window.initStateManager();
        }
        
        previewManager = new PreviewManager();
        
        // 导出全局函数以保持向后兼容性
        window.updateTestWindow = (message) => previewManager.updateTestWindow(message);
        window.loadExistingSVGs = () => previewManager.loadExistingSVGs();
        window.loadD0D1Images = () => previewManager.loadD0D1Images();
        window.refreshPreview = () => previewManager.refreshPreview();
        window.setImg = (element, url) => previewManager.setImg(element, url);
        
        // 导出类和实例
        window.PreviewManager = PreviewManager;
        window.previewManager = previewManager;
        
        console.log('✅ 预览管理器已初始化');
    }
    return previewManager;
}

// DOM加载完成后自动初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initPreviewManager();
        // 自动加载现有SVG文件
        setTimeout(() => {
            if (previewManager) {
                previewManager.loadExistingSVGs();
            }
        }, 1000); // 延迟1秒确保所有组件都已初始化
    });
} else {
    initPreviewManager();
    // 自动加载现有SVG文件
    setTimeout(() => {
        if (previewManager) {
            previewManager.loadExistingSVGs();
        }
    }, 1000);
}

// 导出初始化函数
window.initPreviewManager = initPreviewManager;

console.log('✅ 预览管理模块已加载');
