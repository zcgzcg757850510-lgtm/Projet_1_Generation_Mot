/**
 * 文章生成模块
 * 处理文章生成功能的所有逻辑
 */

class ArticleGenerator {
    constructor() {
        this.isInitialized = false;
        this.cachedSamples = new Map(); // Cache des échantillons par configuration
        this.currentSampleKey = null; // Clé de configuration actuelle
        this.updateDebounceTimer = null; // Timer pour debounce
        this.lastUpdateTime = 0; // Timestamp de la dernière mise à jour
    }

    // 初始化文章生成器
    initialize() {
        if (this.isInitialized) return;
        
        this.initializeEventListeners();
        
        // 初始化默认背景预览和选项样式，生成初始字体样例
        setTimeout(() => {
            this.updatePreviewBackground('a4');
            this.updateBackgroundOptionStyles();
            this.smartUpdatePreview(true); // ⚡ Charger la prévisualisation initiale
        }, 100);
        
        // 监听窗口大小变化，自动调整缩放
        if (!this.resizeListener) {
            this.resizeListener = () => {
                this.applyAutoScale();
            };
            window.addEventListener('resize', this.resizeListener);
        }
        
        this.isInitialized = true;
        console.log('ArticleGenerator initialized');
    }

    // 初始化事件监听器
    initializeEventListeners() {
        // 背景类型变化处理
        const backgroundSelect = document.getElementById('backgroundType');
        if (backgroundSelect) {
            backgroundSelect.addEventListener('change', (e) => {
                this.handleBackgroundTypeChange(e.target.value);
            });
        }

        // 生成文章按钮
        const generateBtn = document.getElementById('btnGenerateArticle');
        if (generateBtn) {
            generateBtn.addEventListener('click', () => {
                this.generateArticle();
            });
        }
        
        // 重置按钮
        const resetBtn = document.getElementById('btnResetInput');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.resetForm();
            });
        }
        
        // 字体大小滑块 - mise à jour intelligente
        const fontSizeSlider = document.getElementById('fontSize');
        const fontSizeValue = document.getElementById('fontSizeValue');
        if (fontSizeSlider && fontSizeValue) {
            fontSizeSlider.addEventListener('input', (e) => {
                fontSizeValue.textContent = e.target.value;
                this.smartUpdatePreview(); // ⚡ Mise à jour intelligente
            });
        }
        
        // 行间距变化 - mise à jour intelligente
        const lineSpacingInput = document.getElementById('lineSpacing');
        if (lineSpacingInput) {
            lineSpacingInput.addEventListener('input', () => {
                this.smartUpdatePreview(); // ⚡ Mise à jour intelligente
            });
        }
        
        // 字间距变化 - mise à jour intelligente
        const charSpacingInput = document.getElementById('charSpacing');
        if (charSpacingInput) {
            charSpacingInput.addEventListener('input', () => {
                this.smartUpdatePreview(); // ⚡ Mise à jour intelligente
            });
        }
        
        // 字体类型选择
        const fontTypeRadios = document.querySelectorAll('input[name="fontType"]');
        fontTypeRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.handleFontTypeChange(e.target.value);
                this.smartUpdatePreview(true); // Force update avec nouveau type
            });
        });
        
        // 背景类型选择
        const backgroundRadios = document.querySelectorAll('input[name="backgroundType"]');
        backgroundRadios.forEach(radio => {
            radio.addEventListener('change', (e) => {
                this.handleBackgroundTypeChange(e.target.value);
                this.updateBackgroundOptionStyles();
                this.smartUpdatePreview(true); // 更新预览以显示新背景
            });
        });
        
        // 下载按钮
        const downloadBtn = document.getElementById('btnDownloadArticle');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => {
                this.downloadArticle();
            });
        }

        // PDF下载按钮
        const downloadPdfBtn = document.getElementById('btnDownloadPDF');
        if (downloadPdfBtn) {
            downloadPdfBtn.addEventListener('click', () => {
                this.downloadPDF();
            });
        }
        
        // 自定义背景图片上传
        const backgroundUpload = document.getElementById('backgroundUpload');
        if (backgroundUpload) {
            backgroundUpload.addEventListener('change', (e) => {
                this.handleBackgroundImageUpload(e);
            });
        }
    }

    // 处理字体类型变化
    handleFontTypeChange(fontType) {
        console.log('[ARTICLE] 字体类型变更为:', fontType);
        
        // 可以在这里添加字体类型变化时的UI反馈
        if (window.toastManager) {
            const message = fontType === 'D1' ? '已选择D1字体 (网格变形)' : '已选择D2字体 (中轴填充)';
            window.toastManager.show('article.font.changed', message);
        }
    }

    // 处理背景类型变化
    handleBackgroundTypeChange(backgroundType) {
        const backgroundUpload = document.getElementById('backgroundUpload');
        
        if (backgroundType === 'custom') {
            // 显示文件上传
            if (backgroundUpload) {
                backgroundUpload.style.display = 'block';
            }
        } else {
            // 隐藏文件上传
            if (backgroundUpload) {
                backgroundUpload.style.display = 'none';
            }
        }
        
        // 立即更新预览背景
        this.updatePreviewBackground(backgroundType);
        
        console.log('[ARTICLE] 背景类型变更为:', backgroundType);
    }

    // 更新预览背景
    updatePreviewBackground(backgroundType) {
        const previewDiv = document.getElementById('articlePreview');
        if (!previewDiv) return;
        
        // 根据背景类型设置预览区域的背景
        switch (backgroundType) {
            case 'a4':
                previewDiv.style.background = '#ffffff';
                previewDiv.style.backgroundImage = 'none';
                break;
                
            case 'lined':
                // 创建下划线背景
                const lineHeight = 30; // 行高
                const svgLines = `
                    <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="${lineHeight}">
                        <line x1="0" y1="${lineHeight - 2}" x2="100%" y2="${lineHeight - 2}" 
                              stroke="#e0e0e0" stroke-width="1"/>
                    </svg>
                `;
                const encodedSvg = encodeURIComponent(svgLines);
                previewDiv.style.background = '#ffffff';
                previewDiv.style.backgroundImage = `url("data:image/svg+xml,${encodedSvg}")`;
                previewDiv.style.backgroundRepeat = 'repeat-y';
                previewDiv.style.backgroundSize = `100% ${lineHeight}px`;
                break;
                
            case 'custom':
                // 自定义背景将在文件上传时处理
                previewDiv.style.background = '#f5f5f5';
                previewDiv.style.backgroundImage = 'none';
                break;
                
            default:
                previewDiv.style.background = '#ffffff';
                previewDiv.style.backgroundImage = 'none';
        }
        
        // 如果预览区域当前显示的是空状态，更新文本提示
        if (previewDiv.innerHTML.includes('预览区域')) {
            previewDiv.innerHTML = `
                <div style="padding: 40px; color: #999; text-align: center; font-size: 14px;">
                    <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.3;">📝</div>
                    <div>预览区域 (A4: 210mm × 297mm)</div>
                    <div style="font-size: 12px; margin-top: 8px;">背景: ${this.getBackgroundTypeName(backgroundType)}</div>
                    <div style="font-size: 12px; margin-top: 4px;">请输入文本并点击生成</div>
                    <div style="font-size: 11px; margin-top: 4px; color: #bbb;">预览显示实际大小（自动缩放以适应窗口）</div>
                </div>
            `;
        }
        
        // 应用自动缩放
        this.applyAutoScale();
        
        console.log('[ARTICLE] 预览背景已更新为:', backgroundType);
    }

    // 获取背景类型的友好名称
    getBackgroundTypeName(backgroundType) {
        switch (backgroundType) {
            case 'a4': return 'A4纸背景';
            case 'lined': return '下划线纸';
            case 'custom': return '自定义图片';
            default: return '默认背景';
        }
    }

    // 处理背景图片上传
    handleBackgroundImageUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // 检查文件类型
        if (!file.type.startsWith('image/')) {
            if (window.toastManager) {
                window.toastManager.show('article.upload.invalid_type', '请选择图片文件');
            } else {
                alert('请选择图片文件');
            }
            return;
        }
        
        // 检查文件大小 (限制为5MB)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            if (window.toastManager) {
                window.toastManager.show('article.upload.too_large', '图片文件不能超过5MB');
            } else {
                alert('图片文件不能超过5MB');
            }
            return;
        }
        
        // 读取并预览图片
        const reader = new FileReader();
        reader.onload = (e) => {
            this.updateCustomBackgroundPreview(e.target.result);
        };
        reader.readAsDataURL(file);
        
        console.log('[ARTICLE] 背景图片上传:', file.name);
    }

    // 更新自定义背景预览
    updateCustomBackgroundPreview(imageDataUrl) {
        const previewDiv = document.getElementById('articlePreview');
        if (!previewDiv) return;
        
        // 设置背景图片
        previewDiv.style.background = '#ffffff';
        previewDiv.style.backgroundImage = `url("${imageDataUrl}")`;
        previewDiv.style.backgroundSize = 'cover';
        previewDiv.style.backgroundPosition = 'center';
        previewDiv.style.backgroundRepeat = 'no-repeat';
        
        // 更新提示文本
        if (previewDiv.innerHTML.includes('预览区域')) {
            previewDiv.innerHTML = `
                <div style="padding: 40px; color: #333; text-align: center; font-size: 14px; background: rgba(255,255,255,0.8); border-radius: 8px; margin: 20px;">
                    <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.7;">📝</div>
                    <div>预览区域</div>
                    <div style="font-size: 12px; margin-top: 8px;">背景: 自定义图片</div>
                    <div style="font-size: 12px; margin-top: 4px;">请输入文本并点击生成</div>
                </div>
            `;
        }
        
        // 存储背景图片数据，用于后续生成
        this.customBackgroundImage = imageDataUrl;
        
        console.log('[ARTICLE] 自定义背景预览已更新');
    }

    // 更新背景选项样式
    updateBackgroundOptionStyles() {
        const backgroundOptions = document.querySelectorAll('.background-option');
        backgroundOptions.forEach(option => {
            const radio = option.querySelector('input[type="radio"]');
            if (radio.checked) {
                // 选中状态
                option.style.background = 'rgba(255, 249, 10, 0.1)';
                option.style.borderColor = '#fff90a';
                option.style.transform = 'scale(1.02)';
            } else {
                // 未选中状态
                option.style.background = 'rgba(255,255,255,.03)';
                option.style.borderColor = 'var(--border)';
                option.style.transform = 'scale(1)';
            }
        });
    }

    // 更新字体样例预览
    async updateFontSample() {
        // 防抖处理，避免频繁请求
        if (this.sampleUpdateTimeout) {
            clearTimeout(this.sampleUpdateTimeout);
        }
        
        this.sampleUpdateTimeout = setTimeout(async () => {
            await this.generateFontSample();
        }, 500); // 500ms延迟
    }

    // 生成字体样例
    async generateFontSample() {
        try {
            const params = this.collectArticleParams();
            params.sampleText = '春江潮水连海平海上明月共潮生'; // 固定样例文本
            
            const response = await fetch('/generate_font_sample', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });

            const result = await response.json();
            
            if (result.success) {
                this.displayFontSample(result.sample_url);
            } else {
                console.warn('[SAMPLE] 字体样例生成失败:', result.error);
            }
        } catch (error) {
            console.error('[SAMPLE] 字体样例生成错误:', error);
        }
    }

    // 显示字体样例
    displayFontSample(sampleUrl) {
        const previewDiv = document.getElementById('articlePreview');
        if (!previewDiv) return;
        
        // 检查是否还在空状态
        if (previewDiv.innerHTML.includes('预览区域')) {
            // 在预览区域的上方添加字体样例
            previewDiv.innerHTML = `
                <div style="padding: 20px; text-align: center;">
                    <div style="margin-bottom: 16px; font-size: 14px; color: var(--muted);">字体样例预览</div>
                    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                        <iframe src="${sampleUrl}" 
                                style="width: 400px; height: 200px; border: 1px solid var(--border); border-radius: 8px; background: white;
                                       overflow: hidden; scrollbar-width: none; -ms-overflow-style: none;"
                                scrolling="no"
                                title="字体样例预览">
                        </iframe>
                    </div>
                    <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.3;">📝</div>
                    <div>预览区域</div>
                    <div style="font-size: 12px; margin-top: 8px;">请输入文本并点击生成完整文章</div>
                </div>
            `;
        }
        
        console.log('[SAMPLE] 字体样例显示完成:', sampleUrl);
    }

    // 生成文章
    async generateArticle() {
        const text = document.getElementById('articleText')?.value?.trim();
        if (!text) {
            if (window.toastManager) {
                window.toastManager.show('article.text.empty');
            } else {
                alert('请输入要生成的文章内容');
            }
            return;
        }

        const params = this.collectArticleParams();
        
        try {
            // 显示加载状态
            this.setGenerationState(true);
            
            const response = await fetch('/generate_article', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(params)
            });

            const result = await response.json();
            
            if (result.success) {
                this.displayArticleResult(result);
                if (window.toastManager) {
                    window.toastManager.show('article.generate.success');
                } else {
                    alert('文章生成成功！');
                }
            } else {
                throw new Error(result.error || '生成失败');
            }
        } catch (error) {
            console.error('文章生成错误:', error);
            if (window.toastManager) {
                window.toastManager.show('article.generate.error', error.message);
            } else {
                alert('生成失败: ' + error.message);
            }
        } finally {
            this.setGenerationState(false);
        }
    }

    // 收集文章生成参数
    collectArticleParams() {
        // 获取选中的背景类型
        const backgroundTypeRadio = document.querySelector('input[name="backgroundType"]:checked');
        const backgroundType = backgroundTypeRadio ? backgroundTypeRadio.value : 'a4';
        
        // 获取选中的字体类型
        const fontTypeRadio = document.querySelector('input[name="fontType"]:checked');
        const fontType = fontTypeRadio ? fontTypeRadio.value : 'D1';
        
        const params = {
            text: document.getElementById('articleText')?.value?.trim() || '',
            backgroundType: backgroundType,
            fontType: fontType,
            fontSize: parseInt(document.getElementById('fontSize')?.value) || 26,
            lineSpacing: parseInt(document.getElementById('lineSpacing')?.value) || 16,
            charSpacing: parseInt(document.getElementById('charSpacing')?.value) || 3,
            referenceChar: '一' // 默认参考字符
        };

        console.log('[ARTICLE] 收集的参数:', params);
        return params;
    }

    // 设置生成状态
    setGenerationState(isGenerating) {
        const generateBtn = document.getElementById('btnGenerateArticle');
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (generateBtn) {
            generateBtn.disabled = isGenerating;
            generateBtn.textContent = isGenerating ? '生成中...' : '生成文章';
        }
        
        if (progressContainer) {
            progressContainer.style.display = isGenerating ? 'block' : 'none';
        }
        
        if (isGenerating && progressBar && progressText) {
            // 模拟进度
            let progress = 0;
            const interval = setInterval(() => {
                progress += Math.random() * 30;
                if (progress > 90) progress = 90;
                progressBar.style.width = progress + '%';
                progressText.textContent = `正在生成... ${Math.round(progress)}%`;
                
                if (!generateBtn.disabled) {
                    clearInterval(interval);
                    progressBar.style.width = '100%';
                    progressText.textContent = '生成完成';
                    setTimeout(() => {
                        progressContainer.style.display = 'none';
                    }, 1000);
                }
            }, 200);
        }
    }

    // 显示文章生成结果
    displayArticleResult(result) {
        const previewDiv = document.getElementById('articlePreview');
        const downloadBtn = document.getElementById('btnDownloadArticle');
        const downloadPdfBtn = document.getElementById('btnDownloadPDF');
        
        if (previewDiv && result.svg_url) {
            // 在预览区域显示SVG - 使用绝对定位填充整个A4区域
            previewDiv.innerHTML = `
                <iframe src="${result.svg_url}" 
                        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; 
                               border: none; background: white;
                               overflow: hidden; scrollbar-width: none; -ms-overflow-style: none;"
                        scrolling="no"
                        title="文章预览">
                </iframe>
            `;
            
            // 应用自动缩放
            this.applyAutoScale();
            
            // 存储下载URL
            this.currentDownloadUrl = result.svg_url;
        }
        
        if (downloadBtn) {
            downloadBtn.style.display = 'block';
        }
        if (downloadPdfBtn) {
            downloadPdfBtn.style.display = 'block';
        }
        
        console.log('[ARTICLE] 结果显示完成:', result);
    }

    // 下载文章
    downloadArticle() {
        if (!this.currentDownloadUrl) {
            if (window.toastManager) {
                window.toastManager.show('article.download.no_file');
            } else {
                alert('没有可下载的文件');
            }
            return;
        }
        
        const a = document.createElement('a');
        a.href = this.currentDownloadUrl;
        a.download = `article_${Date.now()}.svg`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        console.log('[ARTICLE] 下载文件:', this.currentDownloadUrl);
    }

    // 下载PDF
    async downloadPDF() {
        if (!this.currentDownloadUrl) {
            if (window.toastManager) {
                window.toastManager.show('article.download.no_file');
            } else {
                alert('没有可下载的文件');
            }
            return;
        }

        try {
            // 显示加载状态
            const downloadPdfBtn = document.getElementById('btnDownloadPDF');
            const originalText = downloadPdfBtn.innerHTML;
            downloadPdfBtn.innerHTML = '🔄 生成PDF...';
            downloadPdfBtn.disabled = true;

            // 调用后端API生成PDF
            const response = await fetch('/generate_pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    svg_url: this.currentDownloadUrl
                })
            });

            if (!response.ok) {
                throw new Error(`PDF生成失败: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.success) {
                if (result.method === 'cairosvg') {
                    // 真正的PDF文件
                    const a = document.createElement('a');
                    a.href = result.pdf_url;
                    a.download = `article_${Date.now()}.pdf`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);

                    // 在新窗口中打开PDF预览
                    setTimeout(() => {
                        window.open(result.pdf_url, '_blank');
                    }, 500);

                    console.log('[ARTICLE] PDF下载成功:', result.pdf_url);
                    
                    if (window.toastManager) {
                        window.toastManager.show('PDF生成成功！正在下载并打开预览...', 'success');
                    }
                } else if (result.method === 'html_fallback') {
                    // HTML替代方案
                    console.log('[ARTICLE] HTML替代方案生成成功:', result.pdf_url);
                    
                    // 在新窗口中打开HTML文件
                    window.open(result.pdf_url, '_blank');
                    
                    // 显示用户指导消息
                    const message = result.message || 'PDF生成功能不可用，已生成可打印的HTML文件。您可以在浏览器中使用"打印"功能保存为PDF。';
                    
                    if (window.toastManager) {
                        window.toastManager.show(message, 'warning', 8000); // 显示8秒
                    } else {
                        alert(message);
                    }
                }
            } else {
                throw new Error(result.error || 'PDF生成失败');
            }

        } catch (error) {
            console.error('[ARTICLE] PDF下载失败:', error);
            
            let errorMessage = `PDF生成失败: ${error.message}`;
            
            // 尝试解析后端返回的详细错误信息
            try {
                const errorResponse = await error.response?.json();
                if (errorResponse && errorResponse.error) {
                    errorMessage = errorResponse.error;
                    
                    // 如果有解决方案，显示更详细的信息
                    if (errorResponse.solution) {
                        errorMessage += `\n\n建议: ${errorResponse.solution}`;
                    }
                }
            } catch (parseError) {
                // 如果无法解析错误响应，使用默认错误信息
                console.log('[ARTICLE] 无法解析错误响应:', parseError);
            }
            
            if (window.toastManager) {
                window.toastManager.show(errorMessage, 'error');
            } else {
                alert(errorMessage);
            }
        } finally {
            // 恢复按钮状态
            const downloadPdfBtn = document.getElementById('btnDownloadPDF');
            if (downloadPdfBtn) {
                downloadPdfBtn.innerHTML = originalText;
                downloadPdfBtn.disabled = false;
            }
        }
    }

    // 重置表单
    resetForm() {
        // 重置文本区域
        const articleText = document.getElementById('articleText');
        if (articleText) {
            articleText.value = '春江潮水连海平，海上明月共潮生。滟滟随波千万里，何处春江无月明！';
        }
        
        // 重置字体类型选择
        const d1Radio = document.querySelector('input[name="fontType"][value="D1"]');
        if (d1Radio) {
            d1Radio.checked = true;
        }
        
        // 重置背景选择
        const a4Radio = document.querySelector('input[name="backgroundType"][value="a4"]');
        if (a4Radio) {
            a4Radio.checked = true;
            this.handleBackgroundTypeChange('a4');
        }
        
        // 重置间距设置
        const lineSpacing = document.getElementById('lineSpacing');
        const charSpacing = document.getElementById('charSpacing');
        if (lineSpacing) lineSpacing.value = '16';
        if (charSpacing) charSpacing.value = '3';
        
        // 重置字体大小
        const fontSize = document.getElementById('fontSize');
        const fontSizeValue = document.getElementById('fontSizeValue');
        if (fontSize) fontSize.value = '26';
        if (fontSizeValue) fontSizeValue.textContent = '26';
        
        // 重置预览区域 - 显示初始的字体预览
        this.smartUpdatePreview(true); // 强制更新，显示默认字体预览
        
        // 重置背景选项样式
        this.updateBackgroundOptionStyles();
        
        // 隐藏下载按钮
        const downloadBtn = document.getElementById('btnDownloadArticle');
        if (downloadBtn) {
            downloadBtn.style.display = 'none';
        }
        const downloadPdfBtn = document.getElementById('btnDownloadPDF');
        if (downloadPdfBtn) {
            downloadPdfBtn.style.display = 'none';
        }
        
        // 清除下载URL
        this.currentDownloadUrl = null;
        
        console.log('[ARTICLE] 表单已重置，恢复到初始字体预览界面');
    }

    // 自动缩放预览以适应容器
    applyAutoScale() {
        const previewDiv = document.getElementById('articlePreview');
        const containerDiv = document.getElementById('articlePreviewContainer');
        const scaleInfo = document.getElementById('scaleInfo');
        const scaleValue = document.getElementById('scaleValue');
        
        if (!previewDiv || !containerDiv) return;
        
        // 延迟执行以确保DOM已更新
        setTimeout(() => {
            // A4尺寸（毫米转像素，假设96 DPI: 1mm ≈ 3.7795px）
            const a4Width = 210 * 3.7795;  // 约794px
            const a4Height = 297 * 3.7795; // 约1123px
            
            // 获取容器可用空间（减去padding）
            const containerWidth = containerDiv.clientWidth - 40; // 减去左右padding
            const containerHeight = containerDiv.clientHeight - 40; // 减去上下padding
            
            // 计算缩放比例
            const scaleX = containerWidth / a4Width;
            const scaleY = containerHeight / a4Height;
            const scale = Math.min(scaleX, scaleY, 1); // 不超过100%
            
            // 应用缩放
            previewDiv.style.transform = `scale(${scale})`;
            
            // 更新缩放信息显示
            if (scale < 1) {
                if (scaleInfo) scaleInfo.style.display = 'block';
                if (scaleValue) scaleValue.textContent = Math.round(scale * 100);
                console.log(`[ARTICLE] 自动缩放至 ${Math.round(scale * 100)}% 以适应窗口`);
            } else {
                if (scaleInfo) scaleInfo.style.display = 'none';
                console.log('[ARTICLE] 显示100%实际大小');
            }
        }, 100);
    }

    // ⚡ Mise à jour instantanée de la prévisualisation (génération client-side)
    smartUpdatePreview(forceUpdate = false) {
        // Annuler le timer précédent
        if (this.updateDebounceTimer) {
            clearTimeout(this.updateDebounceTimer);
        }
        
        // Génération instantanée côté client (pas de backend !)
        this.updateDebounceTimer = setTimeout(() => {
            this.generateLayoutPreview();
        }, 50); // Très court délai juste pour éviter le lag pendant le drag
        
        console.log('[ARTICLE] ⚡ Mise à jour de la prévisualisation de mise en page');
    }

    // Générer une prévisualisation de mise en page instantanée
    generateLayoutPreview() {
        const params = this.getCurrentPreviewParams();
        
        // Générer un SVG simple côté client pour montrer la mise en page
        const svgContent = this.createLayoutSVG(params);
        
        // Afficher immédiatement
        this.displayLayoutPreview(svgContent, params);
        
        console.log('[ARTICLE] ✅ Prévisualisation générée instantanément');
    }

    // Créer un SVG de mise en page réaliste (format A4)
    createLayoutSVG(params) {
        const { font_size, line_spacing, char_spacing } = params;
        
        // Obtenir le type de fond sélectionné
        const backgroundTypeRadio = document.querySelector('input[name="backgroundType"]:checked');
        const backgroundType = backgroundTypeRadio ? backgroundTypeRadio.value : 'a4';
        
        // Dimensions A4 en pixels (96 DPI: 1mm ≈ 3.7795px)
        const a4Width = 210 * 3.7795;   // ~794px
        const a4Height = 297 * 3.7795;  // ~1123px
        
        // Marges réalistes (comme dans l'article final)
        const margin = 60; // 60px de marge comme dans compose_article_svg
        
        // Texte d'exemple - poème complet pour remplir la page
        const fullText = '春江潮水连海平海上明月共潮生滟滟随波千万里何处春江无月明';
        
        let svgContent = `<svg xmlns="http://www.w3.org/2000/svg" width="${a4Width}" height="${a4Height}" viewBox="0 0 ${a4Width} ${a4Height}">`;
        
        // Ajouter le fond selon le type sélectionné
        svgContent += this.createBackgroundLayer(backgroundType, a4Width, a4Height, margin, font_size, line_spacing);
        
        // Calculer combien de caractères par ligne et combien de lignes
        const availableWidth = a4Width - (2 * margin);
        const charsPerLine = Math.floor(availableWidth / (font_size + char_spacing));
        
        const availableHeight = a4Height - (2 * margin) - font_size;
        const maxLines = Math.floor(availableHeight / (font_size + line_spacing)) + 1;
        
        // Position de départ
        let currentX = margin;
        let currentY = margin + font_size;
        let currentLine = 0;
        let charIndex = 0;
        
        // Dessiner les caractères
        while (currentLine < maxLines && charIndex < fullText.length) {
            let charsInLine = 0;
            
            while (charsInLine < charsPerLine && charIndex < fullText.length) {
                const char = fullText[charIndex];
                
                // Dessiner le caractère
                svgContent += `<text x="${currentX}" y="${currentY}" font-size="${font_size}" font-family="SimSun, 宋体, serif" fill="#333">${char}</text>`;
                
                currentX += font_size + char_spacing;
                charsInLine++;
                charIndex++;
            }
            
            // Passer à la ligne suivante
            currentLine++;
            currentX = margin;
            currentY += font_size + line_spacing;
        }
        
        svgContent += '</svg>';
        
        return svgContent;
    }

    // Créer la couche de fond selon le type
    createBackgroundLayer(backgroundType, width, height, margin, fontSize, lineSpacing) {
        let backgroundLayer = '';
        
        switch (backgroundType) {
            case 'a4':
                // Fond blanc simple
                backgroundLayer = `<rect width="${width}" height="${height}" fill="white"/>`;
                break;
                
            case 'lined':
                // Fond blanc avec lignes
                backgroundLayer = `<rect width="${width}" height="${height}" fill="white"/>`;
                
                // Ajouter des lignes horizontales
                const lineHeight = fontSize + lineSpacing;
                let y = margin + fontSize + 5; // Position de la première ligne
                
                while (y < height - margin) {
                    backgroundLayer += `<line x1="${margin}" y1="${y}" x2="${width - margin}" y2="${y}" stroke="#e0e0e0" stroke-width="1" opacity="0.8"/>`;
                    y += lineHeight;
                }
                break;
                
            case 'custom':
                // Pour l'image personnalisée, on affiche juste un fond gris avec indication
                backgroundLayer = `<rect width="${width}" height="${height}" fill="#f5f5f5"/>`;
                backgroundLayer += `<text x="${width/2}" y="${height/2}" font-size="16" fill="#999" text-anchor="middle">自定义背景 (需生成文章查看效果)</text>`;
                break;
                
            default:
                backgroundLayer = `<rect width="${width}" height="${height}" fill="white"/>`;
        }
        
        return backgroundLayer;
    }

    // Afficher la prévisualisation de mise en page
    displayLayoutPreview(svgContent, params) {
        const previewDiv = document.getElementById('articlePreview');
        if (!previewDiv) return;
        
        // Encoder le SVG pour l'utiliser comme data URL
        const encodedSvg = encodeURIComponent(svgContent);
        const dataUrl = `data:image/svg+xml,${encodedSvg}`;
        
        // Affichage minimaliste - juste le SVG A4
        previewDiv.innerHTML = `
            <div id="fontSampleContainer" style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; padding: 0;">
                <img src="${dataUrl}" 
                     style="max-width: 100%; max-height: 100%; 
                            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                            image-rendering: -webkit-optimize-contrast;
                            image-rendering: crisp-edges;"
                     alt="排版预览">
            </div>
        `;
        
        console.log('[ARTICLE] 📺 Prévisualisation A4 affichée');
    }

    // Récupérer les paramètres actuels de prévisualisation
    getCurrentPreviewParams() {
        const fontTypeRadio = document.querySelector('input[name="fontType"]:checked');
        return {
            font_type: fontTypeRadio ? fontTypeRadio.value : 'D1',
            font_size: parseInt(document.getElementById('fontSize')?.value) || 26,
            line_spacing: parseInt(document.getElementById('lineSpacing')?.value) || 16,
            char_spacing: parseInt(document.getElementById('charSpacing')?.value) || 3
        };
    }
}

// 创建全局实例
const articleGenerator = new ArticleGenerator();

// 导出供其他模块使用
window.ArticleGenerator = ArticleGenerator;
window.articleGenerator = articleGenerator;

// 兼容性函数
function initArticleModal() {
    articleGenerator.initialize();
}

function openArticleModal() {
    // 打开文章生成模态框
    const modal = document.getElementById('articleModal');
    if (modal) {
        modal.style.display = 'block';
        articleGenerator.initialize();
    }
}

function generateArticle() {
    articleGenerator.generateArticle();
}

function resetArticle() {
    articleGenerator.resetForm();
}

// 导出全局函数（避免与modal-manager.js冲突）
// window.openArticleModal 由 modal-manager.js 统一管理
window.generateArticle = generateArticle;
window.resetArticle = resetArticle;

// 延迟初始化
document.addEventListener('DOMContentLoaded', () => {
    // 不立即初始化，等待模态框打开时再初始化
});

console.log('✅ 文章生成模块已加载');
