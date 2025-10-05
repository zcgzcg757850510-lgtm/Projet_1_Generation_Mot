# API接口文档

## 接口概览

Generateur_Mot系统提供基于Flask的RESTful API接口，支持SVG生成、文件状态查询和静态资源访问等功能。

## 基础信息

- **基础URL**: `http://127.0.0.1:8766`
- **协议**: HTTP/1.1
- **数据格式**: JSON
- **字符编码**: UTF-8

## 核心接口

### 1. 主页面
```
GET /
```

**功能**: 返回Web界面主页

**响应**: HTML页面

**示例**:
```bash
curl http://127.0.0.1:8766/
```

### 2. SVG生成接口
```
POST /api/gen       # 新接口：一次性生成 A/B/C/D1(/D2) 并返回各自URL
GET/POST /gen       # 旧接口/兼容路径：仍可用；POST 时可带 type=D2 触发网格流程
```

**功能**: 根据输入参数生成多种模式的SVG文件，支持一次性生成与网格变形集成

**文件管理机制**:
- 每次生成前自动清理所有现有SVG文件
- 确保输出目录整洁，避免文件累积
- 清理操作记录在服务器日志中

**图像类型（后端文件夹）与界面窗口映射**:
- 后端 A (`A_outlines`) → 界面窗口 A（轮廓）
- 后端 B (`B_raw_centerline`) → 界面窗口 C（原始中轴）
- 后端 C (`C_processed_centerline`) → 界面窗口 D1（处理中轴）
- 后端 D1 (`D1_grid_transform`) → 界面窗口 D2（网格变形）
- 后端 D2 (`D2_median_fill`) → 界面窗口 B（中轴填充）

**参数**:
- `ch` / `char` (string): 要生成的汉字字符
- `type` (string, 可选): 生成类型，支持 "ABCD"（默认）或 "D2"
- `grid_state` / `gridState` (object, 可选): 网格变形状态数据

**网格变形（与D1关联）**:
- 若提供 `grid_state`，会基于当前 C 的SVG应用网格变形，输出到 `D1_grid_transform/`，并在界面 D2 窗口显示
- 旧接口 `POST /gen?type=D2` 也支持从最新 D1 推断并生成带时间戳的 `_d2.svg`

**典型响应（/api/gen）**:
```json
{
  "success": true,
  "urls": {
    "A": "/compare/A_outlines/20250921-210145-方_A.svg",
    "B": "/compare/B_raw_centerline/20250921-210146-方_B.svg",
    "C": "/compare/C_processed_centerline/20250921-210148-方_C.svg",
    "D1": "/compare/D1_grid_transform/20250921-210153-方_D1.svg",
    "D2": "/compare/D2_median_fill/20250921-210154-方_D2.svg"
  },
  "message": "生成成功"
}
```

### 3. 单个图像生成接口
```
POST /api/gen_single
```

**功能**: 生成指定类型的单个图像

**文件管理机制**:
- 每次生成前自动清理所有现有SVG文件
- 确保输出目录整洁，避免文件累积
- 清理操作记录在服务器日志中

**请求格式**:
```json
{
  "char": "一",
  "type": "B"
}
```
**D1（网格变形）特别说明**：
- 推荐传入 `grid_state`（来自网格窗口）
- 若未传，后端可从 `/save_grid_state` 最近保存的状态读取
- D1默认启用“矢量高精度变形 → 2048px 栅格化 → LANCZOS 下采样到 256px”以获得平滑边缘，并以`<image>`形式嵌入SVG（可在内部参数关闭该流程改为纯矢量）


**请求参数**:
- `char` (string, 必需): 要生成的汉字字符
- `type` (string, 必需): 图像类型，支持 "A", "B", "C", "D1", "D2"

**重要说明（前端展示映射）**:
- A → A窗口；B → C窗口；C → D1窗口；D1 → D2窗口；D2 → B窗口
- 也即：界面 B 窗口显示中轴填充（后端 D2），界面 C 窗口显示原始中轴（后端 B）

**响应格式**（示例：生成 C）:
```json
{
  "success": true,
  "url": "/compare/C_processed_centerline/20250919-101234-一_C.svg",
  "message": "C图生成成功"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "无效的图像类型"
}
```

**使用示例**:
```bash
curl -X POST http://127.0.0.1:5000/api/gen_single \
  -H "Content-Type: application/json" \
  -d '{"char":"一","type":"B"}'
```

### 4. 文章生成接口
```
POST /generate_article
```

**功能**: 生成多行文本的手写风格文章SVG，所有字符线条统一为纯黑色

**请求格式**（新SVG文章）：
```json
{
  "text": "春江花月夜",
  "fontSize": 40,
  "lineSpacing": 40,
  "charSpacing": 30,
  "backgroundType": "a4",
  "referenceChar": "一"
}
```

**请求参数**:
- `text` (string, 必需): 要生成的文本内容，最多100个字符
- `fontSize` (integer, 可选): 字体大小，默认40像素
- `lineSpacing` (integer, 可选): 行间距，默认40像素
- `charSpacing` (integer, 可选): 字间距，默认30像素
- `backgroundType` (string, 可选): 背景类型，"a4"（A4纸）、"lined"（下划线纸）或"custom"（自定义），默认"a4"
- `referenceChar` (string, 可选): 参考字符，用于风格生成，默认"一"

**响应格式**:
```json
{
  "success": true,
  "imageUrl": "/articles/article_1692345678901.png",
  "filename": "article_1692345678901.png"
}
```

**错误响应**:
```json
{
  "success": false,
  "error": "文本内容不能为空"
}
```

**示例请求**:
```bash
curl -X POST http://127.0.0.1:8766/generate_article \
  -H "Content-Type: application/json" \
  -d '{
    "text": "春江潮水连海平，海上明月共潮生。滟滟随波千万里，何处春江无月明！",
    "fontSize": 45,
    "lineSpacing": 50,
    "charSpacing": 35,
    "backgroundType": "lined"
  }'
```

（以下旧版 text/seed/params 示例为旧接口，保留于存档，可忽略。）

**错误响应**:
```json
{
  "status": "error",
  "message": "错误描述",
  "error_code": "CHAR_NOT_FOUND"
}
```

**示例请求**:
```bash
curl -X POST http://127.0.0.1:8766/gen \
  -H "Content-Type: application/json" \
  -d '{
    "text": "你",
    "seed": 123,
    "params": {
      "end_trim": 0.3,
      "start_trim": 0.1
    }
  }'
```

### 5. 文章图片访问
```
GET /articles/{filename}
```

**功能**: 访问生成的文章图片文件

**路径参数**:
- `filename`: 文章图片文件名 (格式: article_timestamp.png)

**响应**: PNG图片文件内容

**示例**:
```bash
curl http://127.0.0.1:8766/articles/article_1692345678901.png
```

### 5. 文件状态查询
```
GET /status
```

**功能**: 查询指定字符的SVG文件是否存在

**查询参数**:
- `char` (string, 必需): 要查询的字符
- `seed` (integer, 可选): 随机种子，默认为42

**响应格式**:
```json
{
  "char": "你",
  "seed": 42,
  "files": {
    "A": {
      "exists": true,
      "path": "/compare/A_outlines/你_42.svg",
      "size": 2048
    },
    "B": {
      "exists": true,
      "path": "/compare/D2_median_fill/你_42.svg",
      "size": 1536
    },
    "C": {
      "exists": false,
      "path": "/compare/B_raw_centerline/你_42.svg"
    },
    "D": {
      "exists": false,
      "path": "/compare/C_processed_centerline/你_42.svg"
    }
  }
}
```

**示例请求**:
```bash
curl "http://127.0.0.1:8766/status?char=你&seed=42"
```

## 静态资源接口

### 1. 对比预览文件
```
GET /compare/{type}/{filename}
GET /@compare/{type}/{filename}
GET /{type}/{filename}
```

**功能**: 访问生成的SVG文件

**路径参数**:
- `type`: 文件类型 (A_outlines, D2_median_fill, B_raw_centerline, C_processed_centerline)
- `filename`: 文件名 (格式: 字符_种子.svg)

**响应**: SVG文件内容

**示例**:
```bash
# 以下三种方式等价
curl http://127.0.0.1:8766/compare/A_outlines/你_42.svg
curl http://127.0.0.1:8766/@compare/A_outlines/你_42.svg  
curl http://127.0.0.1:8766/A_outlines/你_42.svg
```

### 2. 对比预览页面
```
GET /compare/
GET /@compare/
```

**功能**: 返回对比预览的HTML页面

**响应**: HTML页面，显示四列对比结果

## 参数配置详解

### 风格参数结构
```json
{
  "start_orientation": {
    "enabled": true,
    "target_angle_deg": 0.0,
    "influence_frac": 0.3,
    "strength": 0.8
  },
  "end_orientation": {
    "enabled": true,
    "target_angle_deg": 45.0,
    "influence_frac": 0.3,
    "strength": 0.8
  },
  "trim_settings": {
    "start_trim": 0.0,
    "end_trim": 0.0,
    "seg_corner_deg": 25.0
  },
  "smoothing": {
    "enabled": true,
    "chaikin_iterations": 2
  },
  "resampling": {
    "enabled": true,
    "target_spacing": 3.0
  },
  "transform": {
    "tilt_deg": 0.0,
    "scale_factor": 1.0
  }
}
```

### 参数范围和建议值

#### 起笔/终笔方向调整
- `enabled`: boolean - 是否启用
- `target_angle_deg`: float [-180, 180] - 目标角度（度）
- `influence_frac`: float [0.0, 1.0] - 影响范围比例
- `strength`: float [0.0, 1.0] - 调整强度

#### 裁剪设置
- `start_trim`: float [0.0, 1.0] - 起点裁剪比例
- `end_trim`: float [0.0, 1.0] - 终点裁剪比例（建议0.1-0.5）
- `seg_corner_deg`: float [10.0, 60.0] - 角点检测阈值

#### 平滑处理
- `enabled`: boolean - 是否启用平滑
- `chaikin_iterations`: integer [1, 5] - 平滑迭代次数

#### 重采样
- `enabled`: boolean - 是否启用重采样
- `target_spacing`: float [1.0, 10.0] - 目标点间距

#### 几何变换
- `tilt_deg`: float [-30.0, 30.0] - 倾斜角度
- `scale_factor`: float [0.5, 2.0] - 缩放因子

## 错误处理

### 错误码定义
- `CHAR_NOT_FOUND`: 字符在MMH数据中不存在
- `INVALID_PARAMS`: 参数格式或范围错误
- `GENERATION_FAILED`: SVG生成过程失败
- `FILE_ACCESS_ERROR`: 文件访问权限错误

### 错误响应格式
```json
{
  "status": "error",
  "message": "详细错误描述",
  "error_code": "ERROR_CODE",
  "details": {
    "parameter": "invalid_value",
    "expected_range": "[0.0, 1.0]"
  }
}
```

## 性能考虑

### 请求限制
- 单次请求字符数限制：1个字符
- 并发请求限制：10个/秒
- 文件大小限制：10MB

### 缓存策略
- SVG文件自动缓存
- 相同参数的重复请求返回缓存结果
- 缓存有效期：24小时

### 性能优化建议
- 使用合理的参数范围避免过度处理
- 批量生成时适当延迟请求
- 定期清理生成的临时文件

## 集成示例

### JavaScript前端集成
```javascript
// 生成SVG
async function generateSVG(char, params = {}) {
  try {
    const response = await fetch('/gen', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        text: char,
        seed: 42,
        params: params
      })
    });
    
    const result = await response.json();
    
    if (result.status === 'success') {
      return result.urls;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('生成失败:', error);
    throw error;
  }
}

// 使用示例
generateSVG('你', {
  end_trim: 0.3,
  start_trim: 0.1
}).then(urls => {
  console.log('生成成功:', urls);
}).catch(error => {
  console.error('生成失败:', error);
});
```

### Python客户端集成
```python
import requests
import json

class GenerateurMotClient:
    def __init__(self, base_url="http://127.0.0.1:8766"):
        self.base_url = base_url
    
    def generate_svg(self, char, seed=42, params=None):
        """生成SVG文件"""
        url = f"{self.base_url}/gen"
        data = {
            "text": char,
            "seed": seed,
            "params": params or {}
        }
        
        response = requests.post(url, json=data)
        return response.json()
    
    def check_status(self, char, seed=42):
        """检查文件状态"""
        url = f"{self.base_url}/status"
        params = {"char": char, "seed": seed}
        
        response = requests.get(url, params=params)
        return response.json()

# 使用示例
client = GenerateurMotClient()

# 生成SVG
result = client.generate_svg('你', params={
    'end_trim': 0.3,
    'start_trim': 0.1
})

if result['status'] == 'success':
    print(f"生成成功: {result['urls']}")
else:
    print(f"生成失败: {result['message']}")
```

## 版本信息

- **API版本**: v1.0
- **兼容性**: Python 3.9+
- **依赖**: Flask 2.0+, numpy, svgwrite

## 更新日志

### v1.0 (当前版本)
- 初始API版本
- 支持四种SVG渲染模式
- 完整的参数配置系统
- 文件状态查询功能
- **D0基线生成隔离修复**：确保D0不受任何用户界面参数影响
- **起笔角度与笔画倾斜冲突修复** (2025-08-19)：解决功能间相互干扰问题

---

**相关文档**：
- [技术架构文档](ARCHITECTURE.md)
- [Web界面文档](WEB_INTERFACE.md)
- [笔画处理文档](STROKE_PROCESSING.md)
