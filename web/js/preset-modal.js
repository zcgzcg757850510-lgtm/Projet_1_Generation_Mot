// 预设管理系统 - 独立模块
// 包含预设管理弹窗的所有功能

// 预设管理系统
class PresetManager {
  constructor() {
    this.presets = this.loadPresets();
    this.updatePresetSelect();
  }

  // 从localStorage加载预设
  loadPresets() {
    try {
      const saved = localStorage.getItem('hanzi_presets');
      return saved ? JSON.parse(saved) : {};
    } catch (error) {
      console.error('加载预设失败:', error);
      toastManager.show('preset.load.error', '预设数据加载失败');
      return {};
    }
  }

  // 保存预设到localStorage
  savePresets() {
    try {
      localStorage.setItem('hanzi_presets', JSON.stringify(this.presets));
    } catch (error) {
      console.error('保存预设失败:', error);
      toastManager.show('preset.save.error', '预设数据保存失败');
    }
  }

  // 获取当前参数
  getCurrentParameters() {
    const params = {};
    
    // 获取所有表单元素的值（包括输入框、选择框等）
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      if (input.name && input.name.trim()) {
        if (input.type === 'checkbox') {
          params[input.name] = input.checked;
        } else if (input.type === 'radio') {
          if (input.checked) {
            params[input.name] = input.value;
          }
        } else {
          params[input.name] = input.value;
        }
      }
    });
    
    // 获取网格变形状态 - 使用与button-generation.js相同的逻辑
    try {
      let gridState = null;
      
      // 1) 优先通过全局 gridStateManager 获取（标准路径）
      if (window.gridStateManager && typeof window.gridStateManager.getState === 'function') {
        gridState = window.gridStateManager.getState();
        console.log('[PRESET] 从 gridStateManager 获取网格状态:', gridState);
      } else {
        // 2) 尝试从localStorage直接读取
        const saved = localStorage.getItem('gridTransform_state');
        if (saved) {
          gridState = JSON.parse(saved);
          console.log('[PRESET] 从 localStorage 获取网格状态:', gridState);
        }
      }
      
      // 3) 若仍为空，直接从 window.gridTransform 读取当前内存状态构造
      if ((!gridState || !gridState.controlPoints || gridState.controlPoints.length === 0) && window.gridTransform && Array.isArray(window.gridTransform.controlPoints) && window.gridTransform.controlPoints.length > 0) {
        gridState = {
          controlPoints: window.gridTransform.controlPoints.map(p => ({ x: p.x, y: p.y, originalX: p.originalX ?? p.x, originalY: p.originalY ?? p.y })),
          size: window.gridTransform.size,
          deformStrength: window.gridTransform.deformStrength
        };
        console.log('[PRESET] 从 gridTransform 内存状态构造网格状态:', gridState);
      }
      
      if (gridState && gridState.controlPoints && gridState.controlPoints.length > 0) {
        params._gridState = gridState;
        console.log('[PRESET] 网格状态已添加到参数中，控制点数量:', gridState.controlPoints.length);
      } else {
        console.log('[PRESET] 网格状态为空或无控制点，未添加到参数中');
      }
    } catch (error) {
      console.warn('[PRESET] 获取网格状态失败:', error);
    }
    
    return params;
  }

  // 应用参数
  applyParameters(params) {
    // 应用表单参数
    Object.entries(params).forEach(([key, value]) => {
      if (key.startsWith('_')) return; // 跳过内部参数
      
      const element = document.querySelector(`[name="${key}"]`);
      if (element) {
        if (element.type === 'checkbox') {
          element.checked = value;
        } else {
          element.value = value;
        }
        
        // 触发change事件以更新相关UI
        element.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    
    // 应用网格变形状态 - 使用localStorage保存并加载
    try {
      if (params._gridState) {
        // 保存到localStorage
        localStorage.setItem('gridTransform_state', JSON.stringify(params._gridState));
        console.log('[PRESET] 网格状态已保存到localStorage');
        
        // 如果gridStateManager存在，使用它来加载状态
        if (window.gridStateManager && typeof window.gridStateManager.load === 'function') {
          window.gridStateManager.load();
          console.log('[PRESET] 通过gridStateManager加载网格状态');
        } else {
          console.log('[PRESET] gridStateManager不可用，网格状态已保存到localStorage');
        }
      }
    } catch (error) {
      console.warn('[PRESET] 应用网格状态失败:', error);
    }
    
    // 刷新预览
    if (typeof refreshPreview === 'function') {
      refreshPreview();
    }
  }

  // 保存预设
  savePreset(name, params) {
    this.presets[name] = {
      parameters: params,
      timestamp: Date.now(),
      description: params._description || `保存于 ${new Date().toLocaleString()}`
    };

    this.savePresets();
    this.updatePresetSelect();
    
    toastManager.show('preset.save.success', `预设 "${name}" 保存成功`);
    return true;
  }

  // 加载预设
  loadPreset(name) {
    if (!name || !this.presets[name]) {
      toastManager.show('preset.load.error', `预设 "${name}" 不存在或加载失败`);
      return false;
    }

    try {
      const preset = this.presets[name];
      this.applyParameters(preset.parameters);
      
      toastManager.show('preset.load.success', `预设 "${name}" 加载成功`);
      return true;
    } catch (error) {
      toastManager.show('preset.load.error', `预设 "${name}" 加载失败：${error.message}`);
      return false;
    }
  }

  // 删除预设
  deletePreset(name) {
    if (!name || !this.presets[name]) {
      return false;
    }

    if (confirm(`确定要删除预设 "${name}" 吗？`)) {
      delete this.presets[name];
      this.savePresets();
      this.updatePresetSelect();
      
      toastManager.show('preset.delete.success', `预设 "${name}" 删除成功`);
      return true;
    }
    return false;
  }

  // 更新预设下拉框
  updatePresetSelect() {
    const select = document.getElementById('presetSelect');
    if (!select) return;

    // 清空现有选项（保留第一个默认选项）
    select.innerHTML = '<option value="">预设</option>';

    // 添加预设选项
    Object.keys(this.presets).forEach(name => {
      const option = document.createElement('option');
      option.value = name;
      option.textContent = name;
      select.appendChild(option);
    });
  }

  // 获取所有预设名称
  getPresetNames() {
    return Object.keys(this.presets);
  }

  // 获取预设信息
  getPresetInfo(name) {
    return this.presets[name];
  }

  // 保存到存储（兼容方法）
  saveToStorage() {
    this.savePresets();
  }
}

// 全局预设管理器实例
const presetManager = new PresetManager();

// 加载预设
function loadPreset(name) {
  if (name) {
    presetManager.loadPreset(name);
  }
}

// 参数预览更新定时器
let previewUpdateInterval = null;

// 打开预设管理模态框
function openPresetModal() {
  const modal = document.getElementById('presetModal');
  if (modal) {
    modal.classList.remove('hidden');
    
    // 立即刷新预设列表（确保显示最新的预设）
    console.log('[PRESET] 打开预设管理界面，刷新预设列表');
    updatePresetList();
    
    // 延迟更新以确保模态框完全加载
    setTimeout(() => {
      // 再次刷新预设列表，确保完全加载
      updatePresetList();
      updateCurrentParamsPreview();
      
      // 启动定时更新参数预览
      if (previewUpdateInterval) {
        clearInterval(previewUpdateInterval);
      }
      previewUpdateInterval = setInterval(updateCurrentParamsPreview, 2000); // 每2秒更新一次
      
      console.log('[PRESET] 预设管理界面初始化完成');
    }, 100); // 增加延迟时间确保DOM完全准备好
    
    toastManager.show('preset.modal.open', '预设管理界面已打开');
  }
}

// 关闭预设管理模态框
function closePresetModal() {
  const modal = document.getElementById('presetModal');
  if (modal) {
    modal.classList.add('hidden');
    
    // 清除参数预览更新定时器
    if (previewUpdateInterval) {
      clearInterval(previewUpdateInterval);
      previewUpdateInterval = null;
    }
  }
}

// 保存新预设
function saveNewPreset() {
  const nameInput = document.getElementById('newPresetName');
  const descInput = document.getElementById('newPresetDescription');
  let name = nameInput.value.trim();
  const description = descInput.value.trim();
  
  // 如果没有输入名称，使用默认名称
  if (!name) {
    name = '未命名';
    // 如果"未命名"已存在，则添加数字后缀
    let counter = 1;
    while (presetManager.presets[name]) {
      name = `未命名${counter}`;
      counter++;
    }
    // 将生成的名称填入输入框
    nameInput.value = name;
  }
  
  if (presetManager.presets[name]) {
    if (!confirm(`预设 "${name}" 已存在，是否覆盖？`)) {
      return;
    }
  }
  
  const params = presetManager.getCurrentParameters();
  if (description) {
    params._description = description;
  }
  
  if (presetManager.savePreset(name, params)) {
    nameInput.value = '';
    descInput.value = '';
    updatePresetList();
  }
}

// 更新当前参数预览
function updateCurrentParamsPreview() {
  const preview = document.getElementById('currentParamsPreview');
  if (!preview) {
    console.warn('找不到参数预览元素 #currentParamsPreview');
    return;
  }
  
  try {
    const params = presetManager.getCurrentParameters();
    console.log('获取到的参数:', params);
    
    // 按类别分组参数 - 对应界面顶部栏的5个分类
    const categories = {
      '字符': ['char'],
      '原始中轴(B)': [
        // 原始中轴相关的基础参数
        'start_region_frac', 'end_region_frac', 'isolate_on', 'isolate_min_len'
      ],
      '起笔+笔锋(C)': [
        // 起笔相关参数
        'start_angle_on', 'start_angle', 'start_trim_on', 'start_trim', 'start_ori', 'start_frac', 'disable_start',
        // 笔锋相关参数
        'end_angle_on', 'end_angle', 'end_trim_on', 'end_trim', 'keep_start', 'keep_end'
      ],
      '最终调整(C)': [
        // 平滑处理
        'chaikin_on', 'chaikin', 'smooth_on', 'smooth', 'resample_on', 'resample',
        // 变形效果
        'tilt_on', 'tilt', 'tilt_k', 'tilt_range', 'scale_on', 'scale', 'scale_range',
        'move_on', 'move', 'pcv', 'pcjitter',
        // 角点范围设置
        'corner_range_on', 'corner_thresh_min_deg', 'corner_thresh_max_deg'
      ],
      '网格变形(D1)': ['_gridState']
    };
    
    let html = '';
    let totalCount = 0;
    let allActiveParams = [];
    
    Object.entries(categories).forEach(([category, keys]) => {
      const activeParams = keys.filter(key => {
        const value = params[key];
        if (key === '_gridState') {
          // 对于网格变形，总是返回true以显示这个类别（即使没有数据）
          console.log('[PRESET] 检查网格变形状态:', value);
          return true; // 总是显示网格变形类别
        }
        if (typeof value === 'boolean') {
          return value === true;
        }
        if (typeof value === 'string') {
          return value !== '' && value !== '0';
        }
        if (typeof value === 'number') {
          return value !== 0;
        }
        return value !== undefined && value !== null;
      });
      
      if (activeParams.length > 0) {
        // 参数名称映射 - 将技术名称转换为用户友好的显示名称
        const paramNameMap = {
          // 字符
          'char': '字符',
          
          // 原始中轴(B)
          'start_region_frac': '起始段比例',
          'end_region_frac': '结束段比例',
          'raw_start_frac': '起始段比例',
          'raw_end_frac': '结束段比例',
          'raw_window_on': '三色分段',
          'isolate_on': '短边全紫',
          'isolate_min_len': '短边长度阈值',
          
          // 起笔+笔锋(C)
          'start_angle_on': '起笔角度开关',
          'start_angle': '起笔角度',
          'start_trim_on': '裁剪起点开关',
          'start_trim': '裁剪起点',
          'start_ori': '起笔方向',
          'start_frac': '起笔比例',
          'disable_start': '禁用起笔',
          'end_angle_on': '笔锋角度开关',
          'end_angle': '笔锋角度',
          'end_trim_on': '裁剪终点开关',
          'end_trim': '裁剪终点',
          'keep_start': '保持起点',
          'keep_end': '保持终点',
          
          // 最终调整(C)
          'chaikin_on': '细化开关',
          'chaikin': '细化次数',
          'smooth_on': '平滑开关',
          'smooth': '平滑窗口',
          'resample_on': '重采样开关',
          'resample': '重采样密度',
          'tilt_on': '笔画倾斜开关',
          'tilt': '笔画倾斜',
          'tilt_k': '倾斜强度',
          'tilt_range': '倾斜角度',
          'scale_on': '缩放开关',
          'scale': '缩放比例',
          'scale_range': '缩放范围',
          'move_on': '笔画移动开关',
          'move': '移动偏移',
          'move_offset': '移动偏移',
          'pcv': '笔画变化',
          'pcjitter': '笔画抖动',
          'corner_range_on': '夹角范围开关',
          'corner_thresh_min_deg': '最小夹角',
          'corner_thresh_max_deg': '最大夹角',
          'corner_min': '最小夹角',
          'corner_max': '最大夹角',
          
          // 网格变形(D1)
          '_gridState': '网格变形状态'
        };
        
        const paramDetails = activeParams.map(key => {
          const value = params[key];
          const displayName = paramNameMap[key] || key;
          
          if (key === '_gridState') {
            // 对于网格变形，显示简单的状态信息
            if (!value || typeof value !== 'object') {
              return `${displayName}: 未加载`;
            }
            
            const controlPoints = value.controlPoints || [];
            const pointCount = controlPoints.length;
            
            if (pointCount > 0) {
              // 计算有多少个控制点发生了变形
              const deformedPoints = controlPoints.filter(point => {
                if (!point.originalX || !point.originalY) return false;
                const dx = Math.abs((point.x || 0) - (point.originalX || 0));
                const dy = Math.abs((point.y || 0) - (point.originalY || 0));
                return dx > 0.1 || dy > 0.1;
              }).length;
              
              return `${displayName}: 已加载 (${pointCount}个控制点, ${deformedPoints}个已变形)`;
            } else {
              return `${displayName}: 未加载`;
            }
          }
          
          if (typeof value === 'boolean') return displayName;
          if (typeof value === 'string' && value === '') return displayName;
          if (typeof value === 'number' && value === 0) return displayName;
          return `${displayName}: ${value}`;
        }).join(', ');
        
        html += `<div style="margin-bottom: 6px; padding: 6px 10px; background: rgba(255,255,255,.05); border-radius: 6px; border-left: 3px solid var(--accent);">
          <div style="font-weight: 600; margin-bottom: 2px;">${category} (${activeParams.length}个)</div>
          <div style="font-size: 11px; color: var(--muted); word-break: break-all;">${paramDetails}</div>
        </div>`;
        totalCount += activeParams.length;
        allActiveParams.push(...activeParams);
      }
    });
    
    if (html === '') {
      html = `<div style="color: var(--muted); font-style: italic; text-align: center; padding: 20px;">
        <div style="font-size: 24px; margin-bottom: 8px;">📝</div>
        <div>暂无活动参数</div>
        <div style="font-size: 12px; margin-top: 4px;">调整参数后会在这里显示</div>
      </div>`;
    } else {
      html = `<div style="margin-bottom: 12px; padding: 8px 12px; background: linear-gradient(135deg, rgba(255, 249, 10, 0.1), rgba(255, 235, 59, 0.1)); border-radius: 8px; border: 1px solid rgba(255, 249, 10, 0.2);">
        <div style="font-weight: 600; color: var(--fg-0);">📊 总计: ${totalCount}个参数</div>
        <div style="font-size: 11px; color: var(--muted); margin-top: 4px;">包含 ${Object.keys(categories).filter(cat => categories[cat].some(key => allActiveParams.includes(key))).length} 个类别的设置</div>
      </div>` + html;
    }
    
    preview.innerHTML = html;
    console.log('参数预览更新完成，总参数数:', totalCount);
  } catch (error) {
    console.error('更新参数预览失败:', error);
    preview.innerHTML = `<div style="color: #f44336; padding: 16px; text-align: center;">
      <div style="font-size: 20px; margin-bottom: 8px;">⚠️</div>
      <div>参数预览加载失败</div>
      <div style="font-size: 12px; margin-top: 4px;">${error.message}</div>
    </div>`;
  }
}

// 刷新预设列表
function refreshPresetList() {
  updatePresetList();
  toastManager.show('preset.list.refresh');
}

// 搜索过滤预设
function filterPresets() {
  const searchInput = document.getElementById('presetSearchInput');
  const searchTerm = searchInput.value.toLowerCase().trim();
  const presetItems = document.querySelectorAll('#presetList .preset-item-card');
  
  let visibleCount = 0;
  presetItems.forEach(item => {
    const name = item.dataset.presetName.toLowerCase();
    const description = item.dataset.presetDescription ? item.dataset.presetDescription.toLowerCase() : '';
    
    if (name.includes(searchTerm) || description.includes(searchTerm)) {
      item.style.display = 'block';
      visibleCount++;
    } else {
      item.style.display = 'none';
    }
  });
  
  // 搜索结果反馈
  if (searchTerm) {
    if (visibleCount === 0) {
      toastManager.show('preset.search.no_results', `未找到包含 "${searchTerm}" 的预设`);
    } else {
      toastManager.show('preset.search.results', `找到 ${visibleCount} 个匹配的预设`);
    }
  }
}

// 重命名预设
function renamePreset(oldName) {
  const newName = prompt(`重命名预设 "${oldName}"`, oldName);
  if (!newName || newName === oldName) return;
  
  if (presetManager.presets[newName]) {
    toastManager.show('preset.name.exists');
    return;
  }
  
  // 复制预设数据
  presetManager.presets[newName] = { ...presetManager.presets[oldName] };
  presetManager.presets[newName].timestamp = Date.now();
  
  // 删除旧预设
  delete presetManager.presets[oldName];
  
  presetManager.savePresets();
  presetManager.updatePresetSelect();
  
  // 使用setTimeout确保在prompt关闭后更新列表
  setTimeout(() => {
    updatePresetList();
    toastManager.show('preset.rename.success', `预设已重命名为 "${newName}"`);
  }, 100);
}

// 复制预设
function duplicatePreset(name) {
  const newName = prompt(`复制预设 "${name}"`, `${name} - 副本`);
  if (!newName) return;
  
  if (presetManager.presets[newName]) {
    toastManager.show('preset.name.exists');
    return;
  }
  
  presetManager.presets[newName] = { ...presetManager.presets[name] };
  presetManager.presets[newName].timestamp = Date.now();
  
  presetManager.savePresets();
  presetManager.updatePresetSelect();
  
  // 使用setTimeout确保在prompt关闭后更新列表
  setTimeout(() => {
    updatePresetList();
    toastManager.show('preset.duplicate.success', `预设 "${newName}" 创建成功`);
  }, 100);
}

// 导出预设
function exportPreset(name) {
  const preset = presetManager.presets[name];
  if (!preset) return;
  
  const data = {
    name: name,
    preset: preset,
    exportTime: new Date().toISOString(),
    version: '1.0'
  };
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `preset_${name}.json`;
  a.click();
  URL.revokeObjectURL(url);
  
  toastManager.show('preset.export.success', `预设 "${name}" 导出成功`);
}

// 导入预设
function importPresets() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  input.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        
        if (data.preset && data.name) {
          // 单个预设文件
          if (presetManager.presets[data.name]) {
            if (!confirm(`预设 "${data.name}" 已存在，是否覆盖？`)) return;
          }
          
          presetManager.presets[data.name] = data.preset;
          presetManager.savePresets();
          updatePresetList();
          toastManager.show('preset.import.success', `预设 "${data.name}" 导入成功`);
        } else {
          toastManager.show('preset.import.invalid_format');
        }
      } catch (error) {
        toastManager.show('preset.import.parse_error', '文件解析失败：' + error.message);
      }
    };
    reader.readAsText(file);
  };
  input.click();
}

// 更新预设列表
function updatePresetList() {
  console.log('[PRESET] 开始更新预设列表...');
  
  const list = document.getElementById('presetList');
  if (!list) {
    console.warn('[PRESET] 预设列表容器未找到');
    return;
  }

  list.innerHTML = '';
  
  // 重新加载预设数据，确保获取最新的预设
  presetManager.loadPresets();
  const presetNames = presetManager.getPresetNames();
  
  console.log('[PRESET] 找到预设数量:', presetNames.length);
  console.log('[PRESET] 预设名称列表:', presetNames);
  
  if (presetNames.length === 0) {
    list.innerHTML = `
      <div style="text-align: center; color: var(--muted); padding: 40px 20px; grid-column: 1; justify-self: center; align-self: center;">
        <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.3;">📋</div>
        <div style="font-size: 16px; margin-bottom: 8px;">暂无预设</div>
        <div style="font-size: 12px;">创建第一个预设来开始使用</div>
      </div>
    `;
    return;
  }

  presetNames.forEach(name => {
    const preset = presetManager.getPresetInfo(name);
    const item = document.createElement('div');
    item.className = 'preset-item-card';
    item.dataset.presetName = name;
    item.dataset.presetDescription = preset.parameters._description || '';
    
    const date = new Date(preset.timestamp);
    const timeStr = date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    const description = preset.parameters._description || '无描述';
    const paramCount = Object.keys(preset.parameters).filter(key => !key.startsWith('_')).length;
    
    item.innerHTML = `
      <div style="padding: 16px; background: rgba(255,255,255,.03); border: 1px solid var(--border); border-radius: 12px; transition: all 0.2s; cursor: pointer; width: 100%;"
           onmouseover="this.style.background='rgba(255,255,255,.06)'" 
           onmouseout="this.style.background='rgba(255,255,255,.03)'">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
          <div style="flex: 1;">
            <div style="color: var(--fg-0); font-weight: 600; font-size: 16px; margin-bottom: 4px;">${name}</div>
            <div style="color: var(--muted); font-size: 12px; margin-bottom: 8px;">${description}</div>
            <div style="display: flex; gap: 12px; font-size: 11px; color: var(--muted);">
              <span>📊 ${paramCount}个参数</span>
              <span>🕒 ${timeStr}</span>
            </div>
          </div>
          <div style="display: flex; gap: 4px; flex-shrink: 0;">
            <button onclick="event.stopPropagation(); presetManager.loadPreset('${name}'); closePresetModal();" 
                    style="padding: 4px 8px; background: linear-gradient(135deg, #fff90a, #ffeb3b); color: #000; border: none; border-radius: 6px; font-size: 11px; cursor: pointer; font-weight: 600;"
                    title="加载预设">
              📥
            </button>
            <button onclick="event.stopPropagation(); showPresetActions('${name}', event);" 
                    style="padding: 4px 8px; background: var(--glass); color: var(--fg-0); border: 1px solid var(--border); border-radius: 6px; font-size: 11px; cursor: pointer;"
                    title="更多操作">
              ⋯
            </button>
          </div>
        </div>
      </div>
    `;
    
    // 点击卡片加载预设
    item.addEventListener('click', () => {
      presetManager.loadPreset(name);
      closePresetModal();
    });
    
    list.appendChild(item);
  });
  
  // 动态调整列数：当预设数量多时使用两列布局
  if (presetNames.length >= 6) {
    list.style.gridTemplateColumns = '1fr 1fr';
    console.log('[PRESET] 预设数量较多，使用两列布局');
  } else {
    list.style.gridTemplateColumns = '1fr';
    console.log('[PRESET] 预设数量较少，使用单列布局');
  }
  
  console.log('[PRESET] 预设列表更新完成，显示了', presetNames.length, '个预设');
}

// 显示预设操作菜单
function showPresetActions(name, event) {
  // 先移除已存在的菜单
  const existingMenu = document.querySelector('.preset-actions-menu');
  if (existingMenu) {
    existingMenu.remove();
  }
  
  const actions = [
    { text: '🏷️ 重命名', action: () => renamePreset(name) },
    { text: '📋 复制', action: () => duplicatePreset(name) },
    { text: '📤 导出', action: () => exportPreset(name) },
    { text: '🗑️ 删除', action: () => deletePresetConfirm(name) }
  ];
  
  const menu = document.createElement('div');
  menu.className = 'preset-actions-menu';
  menu.style.cssText = `
    position: fixed; z-index: 10000; background: var(--glass); 
    border: 1px solid var(--border); border-radius: 8px; 
    backdrop-filter: blur(12px) saturate(120%); 
    -webkit-backdrop-filter: blur(12px) saturate(120%);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
  `;
  
  actions.forEach(({ text, action }) => {
    const item = document.createElement('div');
    item.textContent = text;
    item.style.cssText = `
      padding: 8px 16px; cursor: pointer; color: var(--fg-0); 
      font-size: 14px; transition: background 0.2s;
      border-bottom: 1px solid var(--border);
    `;
    item.onmouseover = () => item.style.background = 'rgba(255,255,255,.1)';
    item.onmouseout = () => item.style.background = 'transparent';
    item.onclick = () => {
      action();
      menu.remove();
    };
    menu.appendChild(item);
  });
  
  // 移除最后一个分割线
  if (menu.lastChild) {
    menu.lastChild.style.borderBottom = 'none';
  }
  
  // 定位菜单
  const rect = event.target.getBoundingClientRect();
  menu.style.left = rect.left + 'px';
  menu.style.top = (rect.bottom + 5) + 'px';
  
  document.body.appendChild(menu);
  
  // 点击外部关闭
  setTimeout(() => {
    const closeMenu = (e) => {
      if (!menu.contains(e.target)) {
        menu.remove();
        document.removeEventListener('click', closeMenu);
      }
    };
    document.addEventListener('click', closeMenu);
  }, 100);
}

// 确认删除预设
function deletePresetConfirm(name) {
  if (confirm(`确定要删除预设 "${name}" 吗？此操作不可撤销。`)) {
    if (presetManager.deletePreset(name)) {
      updatePresetList();
    }
  }
}

// 批量导入预设
function importPresetsFromFile() {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  input.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        
        if (data.presets && typeof data.presets === 'object') {
          // 批量预设文件
          let importCount = 0;
          let skipCount = 0;
          
          Object.entries(data.presets).forEach(([name, presetData]) => {
            if (presetManager.presets[name]) {
              if (confirm(`预设 "${name}" 已存在，是否覆盖？`)) {
                presetManager.presets[name] = presetData;
                importCount++;
              } else {
                skipCount++;
              }
            } else {
              presetManager.presets[name] = presetData;
              importCount++;
            }
          });
          
          presetManager.saveToStorage();
          updatePresetList();
          
          toastManager.show('preset.import.batch_success', `导入完成！成功导入 ${importCount} 个预设${skipCount > 0 ? `，跳过 ${skipCount} 个` : ''}`);
        } else {
          toastManager.show('preset.import.invalid_format');
        }
      } catch (error) {
        toastManager.show('preset.import.parse_error', '文件解析失败：' + error.message);
      }
    };
    reader.readAsText(file);
  };
  input.click();
}

// 导出所有预设
function exportAllPresets() {
  const presetNames = presetManager.getPresetNames();
  if (presetNames.length === 0) {
    toastManager.show('preset.export.no_presets');
    return;
  }
  
  const exportData = {
    version: '1.0',
    exportTime: new Date().toISOString(),
    presets: presetManager.presets
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `预设备份_${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
  
  toastManager.show('preset.export.all_success', `已导出 ${presetNames.length} 个预设`);
}

// 导出单个预设（兼容方法）
function exportPresetSingle(name) {
  const preset = presetManager.getPresetInfo(name);
  if (!preset) {
    toastManager.show('preset.not_found');
    return;
  }
  
  const exportData = {
    version: '1.0',
    exportTime: new Date().toISOString(),
    presets: {
      [name]: preset
    }
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `预设_${name}_${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
  
  toastManager.show('preset.export.success', `已导出预设 "${name}"`);
}

// 从模态框加载预设
function loadPresetFromModal(name) {
  presetManager.loadPreset(name);
  closePresetModal();
}

// 清空预设表单
function clearPresetForm() {
  const nameInput = document.getElementById('newPresetName');
  const descInput = document.getElementById('newPresetDescription');
  
  if (nameInput) nameInput.value = '';
  if (descInput) descInput.value = '';
  
  updateCurrentParamsPreview();
}

// 刷新预设列表（兼容方法）
function refreshPresetListCompat() {
  updatePresetList();
  toastManager.show('preset.list.refresh');
}

// 搜索过滤预设（兼容方法）
function filterPresetsCompat() {
  const searchInput = document.getElementById('presetSearchInput');
  const searchTerm = searchInput.value.toLowerCase().trim();
  const presetItems = document.querySelectorAll('.preset-item-card');
  
  presetItems.forEach(item => {
    const name = item.dataset.presetName.toLowerCase();
    const description = item.dataset.presetDescription ? item.dataset.presetDescription.toLowerCase() : '';
    
    if (name.includes(searchTerm) || description.includes(searchTerm)) {
      item.style.display = 'block';
    } else {
      item.style.display = 'none';
    }
  });
}

// 导出全局函数
window.openPresetModal = openPresetModal;
window.closePresetModal = closePresetModal;
window.saveNewPreset = saveNewPreset;
window.clearPresetForm = clearPresetForm;
window.loadPreset = loadPreset;
window.loadPresetFromModal = loadPresetFromModal;
window.refreshPresetList = refreshPresetList;
window.filterPresets = filterPresets;
window.importPresets = importPresets;
window.exportAllPresets = exportAllPresets;
window.renamePreset = renamePreset;
window.duplicatePreset = duplicatePreset;
window.exportPreset = exportPreset;
window.updateCurrentParamsPreview = updateCurrentParamsPreview;
window.presetManager = presetManager;

console.log('✅ 预设模态框模块已加载');
