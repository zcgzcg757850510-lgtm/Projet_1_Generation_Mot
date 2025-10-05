# 开发指南

## 开发环境搭建

### 环境要求
- Python 3.9+
- Git
- 文本编辑器或IDE（推荐VS Code、PyCharm、Windsurf等）

### 项目克隆和初始化
```bash
git clone <repository-url>
cd Generateur_Mot

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### IDE开发环境配置

#### 1. 项目导入
```bash
# 在IDE中打开项目根目录
# 确保工作目录为：c:\Users\chenggong.zhang\OneDrive - ESTIA\Bureau\Generateur_Mot
```

#### 2. Flask开发服务器启动
```bash
# 方法1：使用项目启动脚本（推荐）
python start_server.py

# 方法2：使用Flask命令
python -m flask --app web.app run --host=127.0.0.1 --port=5000 --debug

# 方法3：使用批处理文件（Windows）
start_server_debug.bat
```

#### 3. IDE浏览器预览配置
- **服务器地址**：`http://127.0.0.1:5000`
- **开发模式**：启用debug模式支持代码热重载
- **端口配置**：默认5000端口，可在`start_server.py`中修改
- **浏览器预览**：在IDE中配置浏览器预览功能，指向上述地址

#### 4. 开发环境验证
启动服务器后，访问以下端点验证环境：
- 主界面：`http://127.0.0.1:5000/`
- 系统检查：`http://127.0.0.1:5000/system-check.html`
- API状态：`http://127.0.0.1:5000/status`

#### 5. 常见问题解决
- **白屏问题**：确保Flask服务器正常启动，检查控制台错误信息
- **端口占用**：修改`start_server.py`中的端口号或终止占用进程
- **依赖缺失**：运行`pip install -r requirements.txt`安装所有依赖
- **路径问题**：确保在项目根目录下启动服务器

### 数据准备
```bash
# 下载MMH数据
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File mmh_pipeline/scripts/get_mmh.ps1

# macOS/Linux
bash mmh_pipeline/scripts/get_mmh.sh

# 合并数据
python mmh_pipeline/scripts/merge_mmh.py
```

## 项目结构详解

### 核心模块
```
src/
├── __init__.py              # 包初始化
├── main.py                  # 命令行入口
├── parser.py                # MMH数据解析
├── classifier.py            # 笔画分类
├── centerline.py            # 中轴线处理（核心）
├── styler.py                # 风格应用
├── renderer.py              # SVG渲染
├── geometry.py              # 几何计算工具
├── utils.py                 # 通用工具函数
└── types.py                 # 数据类型定义
```

### Web模块
```
web/
├── __init__.py              # Web包初始化
├── app.py                   # Flask应用主入口
├── config.py                # 配置管理
├── ui.html                  # 前端界面
└── services/
    ├── __init__.py          # 服务包初始化
    ├── generation.py        # 生成服务
    ├── style.py             # 风格服务
    └── files.py             # 文件服务
```

### 测试模块
```
tests/
├── test_parser.py           # 解析器测试
├── test_classifier.py       # 分类器测试
├── test_centerline.py       # 中轴线处理测试
├── test_styler.py           # 风格应用测试
└── test_web.py              # Web接口测试
```

## 核心类和接口

### 数据类型
```python
# src/types.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Point:
    """笔画点数据结构"""
    x: float
    y: float
    color: int = 0  # 段落标识

@dataclass
class Stroke:
    """笔画数据结构"""
    points: List[Point]
    stroke_type: str
    metadata: dict
```

### 处理器接口
```python
# src/centerline.py
class CenterlineProcessor:
    """中轴线处理器主类"""
    
    def __init__(self, style_params: dict):
        self.style_params = style_params
    
    def process(self, medians: List[List[Point]]) -> List[List[Point]]:
        """主处理流程"""
        pass
    
    def start_orientation_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        """起笔方向调整阶段"""
        pass
    
    def end_orientation_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        """终笔方向调整阶段"""
        pass
    
    def trim_protect_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
        """裁剪和保护阶段"""
        pass
```

## 开发工作流

### 1. 功能开发流程
1. **需求分析**：明确功能需求和技术规格
2. **设计方案**：设计算法和接口
3. **编写测试**：先写测试用例（TDD）
4. **实现功能**：编写实际代码
5. **测试验证**：运行测试确保功能正确
6. **集成测试**：在完整系统中测试
7. **文档更新**：更新相关文档

### 2. 代码提交规范
```bash
# 提交信息格式
git commit -m "类型(范围): 简短描述

详细描述（可选）

相关问题: #123"

# 类型说明
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建工具或辅助工具变动
```

### 3. 分支管理
- `main`: 主分支，稳定版本
- `develop`: 开发分支，集成新功能
- `feature/功能名`: 功能开发分支
- `hotfix/修复名`: 紧急修复分支

## 测试指南

### 单元测试
```python
# tests/test_centerline.py
import unittest
from src.centerline import trim_last_segment_by_fraction
from src.types import Point

class TestCenterlineProcessing(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.sample_points = [
            Point(0, 0, 0),
            Point(10, 0, 0),
            Point(20, 10, 1),
            Point(30, 10, 2)
        ]
    
    def test_trim_last_segment(self):
        """测试终点裁剪功能"""
        result = trim_last_segment_by_fraction(
            self.sample_points, 
            end_frac_seg3=0.5, 
            corner_thresh_deg=25.0
        )
        
        # 验证结果
        self.assertLess(len(result), len(self.sample_points))
        self.assertEqual(result[-1].color, 2)  # 保持第三段颜色
    
    def test_corner_detection(self):
        """测试角点检测"""
        # 实现角点检测测试
        pass

if __name__ == '__main__':
    unittest.main()
```

### 运行测试
```bash
# 运行所有测试
python -m unittest discover -s tests -p "test_*.py"

# 运行特定测试文件
python -m unittest tests.test_centerline

# 运行特定测试方法
python -m unittest tests.test_centerline.TestCenterlineProcessing.test_trim_last_segment

# 生成测试覆盖率报告
pip install coverage
coverage run -m unittest discover -s tests
coverage report
coverage html  # 生成HTML报告
```

### 集成测试
```python
# tests/test_integration.py
import unittest
from src.main import generate_character
from web.app import app

class TestIntegration(unittest.TestCase):
    
    def test_end_to_end_generation(self):
        """端到端生成测试"""
        result = generate_character(
            char='你',
            seed=42,
            params={'end_trim': 0.3}
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(result.endswith('.svg'))
    
    def test_web_api(self):
        """Web API测试"""
        with app.test_client() as client:
            response = client.post('/gen', json={
                'text': '你',
                'seed': 42,
                'params': {'end_trim': 0.3}
            })
            
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertEqual(data['status'], 'success')
```

## 调试技巧

### 1. 日志配置
```python
# src/utils.py
import logging

def setup_logging(level=logging.INFO):
    """配置日志系统"""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/debug.log'),
            logging.StreamHandler()
        ]
    )

# 使用示例
logger = logging.getLogger(__name__)
logger.debug(f"处理点数: {len(points)}")
```

### 2. 可视化调试
```python
# src/debug_utils.py
import matplotlib.pyplot as plt

def plot_points(points, title="Points Visualization"):
    """可视化点序列"""
    x_coords = [p.x for p in points]
    y_coords = [p.y for p in points]
    colors = [p.color for p in points]
    
    plt.figure(figsize=(10, 8))
    plt.scatter(x_coords, y_coords, c=colors, cmap='viridis')
    plt.title(title)
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.colorbar(label='Segment')
    plt.show()

def save_debug_svg(points, filename):
    """保存调试SVG"""
    # 实现SVG保存逻辑
    pass
```

### 3. 性能分析
```python
# src/profiling.py
import time
import functools

def timing_decorator(func):
    """性能计时装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 执行时间: {end_time - start_time:.4f}秒")
        return result
    return wrapper

# 使用示例
@timing_decorator
def process_stroke(points):
    # 处理逻辑
    pass
```

## 扩展开发

### 1. 添加新的处理阶段
```python
# src/centerline.py
def custom_processing_stage(self, medians: List[List[Point]]) -> List[List[Point]]:
    """自定义处理阶段"""
    result = []
    
    for stroke_points in medians:
        # 实现自定义处理逻辑
        processed_points = self._apply_custom_transform(stroke_points)
        result.append(processed_points)
    
    return result

def _apply_custom_transform(self, points: List[Point]) -> List[Point]:
    """应用自定义变换"""
    # 实现具体变换算法
    return transformed_points
```

### 2. 添加新的渲染模式
```python
# src/renderer.py
def render_custom_mode(self, strokes: List[List[Point]], output_path: str):
    """自定义渲染模式"""
    svg_content = self._generate_custom_svg(strokes)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(svg_content)

def _generate_custom_svg(self, strokes: List[List[Point]]) -> str:
    """生成自定义SVG内容"""
    # 实现SVG生成逻辑
    return svg_string
```

### 3. 添加新的Web接口
```python
# web/app.py
@app.route('/api/custom', methods=['POST'])
def custom_endpoint():
    """自定义API端点"""
    try:
        data = request.get_json()
        
        # 处理请求
        result = process_custom_request(data)
        
        return jsonify({
            'status': 'success',
            'result': result
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
```

## 配置管理

### 配置文件结构
```json
// config/development.json
{
  "debug": true,
  "log_level": "DEBUG",
  "web": {
    "host": "127.0.0.1",
    "port": 8766,
    "debug": true
  },
  "processing": {
    "default_seed": 42,
    "cache_enabled": true,
    "max_concurrent": 4
  }
}
```

### 配置加载
```python
# web/config.py
import json
import os

class Config:
    def __init__(self, env='development'):
        self.env = env
        self._load_config()
    
    def _load_config(self):
        config_file = f'config/{self.env}.json'
        
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        else:
            self.data = self._get_default_config()
    
    def get(self, key, default=None):
        keys = key.split('.')
        value = self.data
        
        for k in keys:
            value = value.get(k, {})
        
        return value if value != {} else default
```

## 部署指南

### 开发环境部署
```bash
# 启动开发服务器
python web/app.py

# 或使用批处理文件
start_server_debug.bat
```

### 生产环境部署
```bash
# 使用Gunicorn部署
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8766 web.app:app

# 使用uWSGI部署
pip install uwsgi
uwsgi --http :8766 --module web.app:app --processes 4
```

### Docker部署
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8766
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8766", "web.app:app"]
```

## 故障排除

### 常见问题

**1. 导入错误**
```python
# 确保正确的包导入
import sys
sys.path.append('src')

from src.centerline import CenterlineProcessor
```

**2. 编码问题**
```python
# 确保UTF-8编码
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

**3. 路径问题**
```python
# 使用绝对路径
import os
project_root = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(project_root, 'data', 'hanzi_data_full.json')
```

### 调试检查清单
- [ ] Python版本是否正确 (3.9+)
- [ ] 依赖包是否完整安装
- [ ] MMH数据是否正确下载和合并

    from src.centerline import CenterlineProcessor
    ```

    **2. 编码问题**
    ```python
    # 确保UTF-8编码
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    ```

    **3. 路径问题**
    ```python
    # 使用绝对路径
    import os
    project_root = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(project_root, 'data', 'hanzi_data_full.json')
    ```

### 代码审查
- 功能正确性
- 性能影响
- 代码可读性
- 测试完整性
- 文档完整性

## 重要修复记录

### 起笔角度与笔画倾斜冲突修复 (2025-08-19)

**问题描述**：
- 启用起笔角度功能后，笔画倾斜功能失效或角度变小
- 笔锋角度功能也会影响倾斜角度的随机值

**根本原因**：
1. 系统中存在三套倾斜机制冲突：
   - 旧的`tilt_stage`（centerline.py第675行）
   - 新的模块化变换系统（第722行）
   - 外部transformer.py几何变换
2. 缺少关键参数`frac_len`导致起笔角度被跳过
3. 共享随机数生成器导致角度值相互影响

**修复方案**：
1. **参数修复**：在`web/app.py`添加`so['frac_len'] = 1.0 if start_angle_on else 0.0`
2. **机制冲突**：禁用旧的`tilt_stage`，统一使用模块化变换系统
3. **随机数隔离**：为起笔角度、笔锋角度、倾斜角度创建独立的随机数生成器

**修复文件**：
- `web/app.py` - 添加frac_len参数
- `src/centerline.py` - 禁用旧倾斜机制，独立随机数生成器
- `src/transforms/tilt_transform.py` - 支持自定义中心点

**测试验证**：
- 起笔角度、笔锋角度、笔画倾斜可同时启用
- 各功能互不干扰，角度值保持稳定

---

**相关文档**：
- [技术架构文档](ARCHITECTURE.md)
- [Web界面文档](WEB_INTERFACE.md)
- [笔画处理文档](STROKE_PROCESSING.md)
- [API接口文档](API_REFERENCE.md)
