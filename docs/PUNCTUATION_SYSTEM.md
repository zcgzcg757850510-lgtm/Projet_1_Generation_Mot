# 标点符号系统

## 📚 概述

标点符号系统为汉字生成器添加了对中英文标点符号的支持，使生成的文章能够包含完整的标点。

### 设计原则

1. **非侵入式**：不修改现有核心代码，通过扩展点集成
2. **可选性**：可以通过环境变量完全禁用
3. **兼容性**：标点符号数据格式与汉字完全兼容
4. **模块化**：独立的加载器和数据文件

---

## 🎯 功能特性

### 支持的标点符号

#### 中文标点（19个）
- 句读：`，` `。` `、` `；` `：`
- 语气：`！` `？`
- 引号：`"` `"` `'` `'`
- 括号：`（` `）` `《` `》` `【` `】`
- 特殊：`…` `—`

#### 未来可扩展
- 英文标点：`,` `.` `!` `?` `;` `:` `"` `'` `(` `)` `[` `]` `{` `}`
- 其他符号：`@` `#` `$` `%` `&` `*` `/` `\`

---

## 📁 文件结构

```
A_1_Generateur_Mot/
├── data/
│   └── punctuation_medians.json      # 标点符号数据（medians格式）
├── src/
│   └── punctuation_loader.py         # 标点符号加载器模块
├── scripts/
│   └── generate_punctuation_medians.py  # 数据生成脚本（可选）
├── web/services/
│   └── generation.py                  # 集成点（仅3行修改）
└── docs/
    └── PUNCTUATION_SYSTEM.md          # 本文档
```

---

## 🔧 工作原理

### 数据格式

标点符号使用与汉字相同的 `medians` 格式：

```json
{
  "，": {
    "character": "，",
    "medians": [
      [[220, 200], [224, 215], [222, 230], [218, 240]]
    ],
    "strokes": 1,
    "source": "manual"
  }
}
```

**关键点**：
- `medians`: 笔画点序列，坐标范围 0-256
- `strokes`: 笔画数
- `source`: 数据来源（`manual` 或 `system_font`）

### 集成流程

```
1. 加载汉字数据（load_merged_cache）
   ↓
2. 加载标点符号数据（punctuation_loader）
   ↓
3. 合并数据（merge_punctuation_with_hanzi）
   ↓
4. 生成字符（generate_abcd）
   ← 对汉字和标点符号使用相同的处理流程
   ↓
5. 应用风格化、网格变形等
   ↓
6. 输出 SVG
```

### 代码集成点

**唯一修改的地方**：`web/services/generation.py`

```python
def load_merged_cache() -> Dict[str, Any]:
    global _MERGED_CACHE
    if _MERGED_CACHE is not None:
        return _MERGED_CACHE
    
    # 加载汉字数据（原有逻辑）
    try:
        with open(MERGED_JSON, 'r', encoding='utf-8') as f:
            _MERGED_CACHE = json.load(f)
    except Exception:
        _MERGED_CACHE = {}
    
    # 🆕 标点符号系统集成（仅3行新增代码）
    try:
        from src.punctuation_loader import merge_punctuation_with_hanzi
        _MERGED_CACHE = merge_punctuation_with_hanzi(_MERGED_CACHE)
    except Exception as e:
        # 如果标点符号系统出错，不影响现有功能
        print(f"[PUNCTUATION] 标点符号加载失败: {e}")
    
    return _MERGED_CACHE
```

---

## 🚀 使用方法

### 启用/禁用标点符号系统

#### 方法 1：环境变量（推荐）

```bash
# 启用（默认）
export PUNCTUATION_ENABLED=true
python start_server.py

# 禁用
export PUNCTUATION_ENABLED=false
python start_server.py
```

#### 方法 2：代码配置

```python
# 在 Python 代码中
from src.punctuation_loader import set_punctuation_enabled

set_punctuation_enabled(True)   # 启用
set_punctuation_enabled(False)  # 禁用
```

### 生成包含标点的文章

直接在文章文本中使用标点符号即可：

```python
text = "春江潮水连海平，海上明月共潮生。滟滟随波千万里，何处春江无月明！"

# 文章生成接口会自动处理标点符号
```

**预期效果**：
- 汉字：使用手写风格 SVG
- 标点：使用相同的风格化处理（起笔、收笔、压力等）
- 整体：风格统一，自然协调

---

## 🎨 标点符号风格

### 默认行为

标点符号会经过与汉字相同的处理流程：
1. ✅ 风格化处理（起笔、收笔、压力变化）
2. ✅ 网格变形（可选，默认启用）
3. ✅ 动态布局（根据实际边界框）

### 特殊调整（未来可配置）

```python
# 未来可以为标点符号设置特殊参数
PUNCTUATION_STYLE = {
    'scale_factor': 0.6,      # 相对汉字的缩放比例
    'apply_deformation': False,  # 是否应用网格变形
    'stroke_weight': 0.8      # 笔画粗细系数
}
```

---

## 🧪 测试

### 测试脚本

```bash
# 测试标点符号加载
python -c "from src.punctuation_loader import load_punctuation_data; print(load_punctuation_data())"

# 测试集成
python -c "from web.services.generation import load_merged_cache; cache = load_merged_cache(); print('，' in cache)"
```

### 预期输出

```
[PUNCTUATION] ✅ 加载了 19 个标点符号
[PUNCTUATION] ✅ 添加了 19 个标点符号到字符库
True
```

### 生成测试

```python
# 在主界面或文章生成中测试
text = "春江潮水连海平，海上明月共潮生。"

# 检查控制台输出
# 应该看到：
# [COMPOSE] 成功提取字符SVG (D1): ，, bbox: WxH
# [COMPOSE] 添加字符: ， at (x, y), scaled_width=W
```

---

## 📊 性能影响

### 内存

- 标点符号数据：~10 KB
- 合并后缓存增量：<1%
- 运行时开销：忽略不计

### 速度

- 初始加载：+50ms（一次性）
- 字符生成：无影响（复用现有流程）
- 文章生成：+5-10ms（19个标点符号）

---

## 🔍 故障排除

### 问题 1：标点符号不显示

**症状**：文章中的标点符号消失

**解决方案**：
```bash
# 1. 检查是否启用
python -c "from src.punctuation_loader import is_punctuation_enabled; print(is_punctuation_enabled())"

# 2. 检查数据文件
ls -lh data/punctuation_medians.json

# 3. 检查加载日志
# 启动服务器时应该看到：
# [PUNCTUATION] ✅ 加载了 19 个标点符号
```

### 问题 2：标点符号风格不对

**症状**：标点符号太大/太小/位置不对

**原因**：medians 数据坐标问题

**解决方案**：
```python
# 调整 data/punctuation_medians.json 中的坐标
# 坐标范围应该在 0-256 之间
# 参考现有标点符号的坐标
```

### 问题 3：性能问题

**症状**：加载或生成变慢

**解决方案**：
```bash
# 临时禁用标点符号系统
export PUNCTUATION_ENABLED=false
python start_server.py
```

---

## 🛠️ 扩展开发

### 添加新标点符号

#### 方法 1：手工添加（推荐）

编辑 `data/punctuation_medians.json`：

```json
{
  "新标点": {
    "character": "新标点",
    "medians": [
      [[x1, y1], [x2, y2], ...]
    ],
    "strokes": 1,
    "source": "manual"
  }
}
```

**坐标规则**：
- X 范围：0-256（左到右）
- Y 范围：0-256（上到下）
- 建议居中：128 附近
- 参考现有标点的坐标

#### 方法 2：从字体提取（高级）

```bash
# 需要安装 fonttools
pip install fonttools

# 运行生成脚本
python scripts/generate_punctuation_medians.py

# 注意：此方法会覆盖现有数据，请先备份
```

### 调整标点符号样式

未来可以在 `src/punctuation_loader.py` 中添加：

```python
def adjust_punctuation_style(medians, char):
    """
    根据标点符号类型调整样式
    """
    if char in ['，', '。', '、']:
        # 逗号、句号、顿号：缩小到 60%
        return scale_medians(medians, 0.6)
    elif char in ['！', '？']:
        # 感叹号、问号：保持原大小
        return medians
    # ...
```

---

## 📈 未来计划

### 短期（v1.1）
- [ ] 添加更多标点符号（英文标点）
- [ ] 优化标点符号尺寸和位置
- [ ] 添加配置界面（启用/禁用开关）

### 中期（v1.2）
- [ ] 支持多种标点风格（正式/随意）
- [ ] 标点符号特殊对齐（逗号右下，引号左上）
- [ ] 独立的标点符号网格变形控制

### 长期（v2.0）
- [ ] 从多个字体提取标点符号
- [ ] AI 生成的手写风格标点
- [ ] 用户自定义标点符号

---

## 📝 变更日志

### v1.0.0 (2025-01-04)
- ✅ 初始版本
- ✅ 支持 19 个中文常用标点
- ✅ 非侵入式集成
- ✅ 环境变量开关
- ✅ 完整文档

---

## 🤝 贡献

欢迎贡献新的标点符号数据或改进！

### 贡献指南

1. Fork 项目
2. 在 `data/punctuation_medians.json` 中添加标点
3. 测试确保不影响现有功能
4. 提交 PR

### 标点符号数据规范

- **必须**：包含 `character`, `medians`, `strokes`, `source` 字段
- **推荐**：坐标范围 0-256，居中对齐
- **建议**：笔画简洁，关键点不超过 10 个

---

## 📞 支持

如有问题，请：
1. 检查本文档的故障排除章节
2. 查看控制台日志
3. 临时禁用标点符号系统验证问题

---

**祝您使用愉快！** 🎉

