# 笔画处理文档

## 处理流程概览

笔画处理是Generateur_Mot系统的核心功能，通过多阶段的几何变换和风格应用，将原始的汉字笔画数据转换为具有特定风格的SVG渲染结果。

## D0 / D1 / D2 处理阶段（对齐当前实现）

笔画的最终输出分为两个主要阶段，以提供不同层次的风格化控制：

-   **D0 (处理中轴 - 基础)**：这是标准处理流程的最终输出。它包含了从起笔/终笔调整、裁剪、到模块化变换系统（移动、倾斜、缩放、平滑）在内的所有核心处理。D0代表了一个经过完整基础修正和风格化的笔画。

-   **D1 (处理中轴 - 进阶)**：在 C 的处理中轴基础上应用用户参数；若在前端提供 `grid_state`，服务器会将网格变形应用到 C 的SVG，结果保存到 `D1_grid_transform/`（UI 显示在 D2 窗口）。

    **D1 处理顺序规则**：
    D1的处理顺序与D0的线性流程不同，它遵循一个特定的、以笔画关键部分为优先级的顺序：
    1.  **起笔 (Start)**：首先应用所有与起笔相关的变换。
    2.  **笔锋 (End/Peak)**：接着应用所有与笔锋相关的变换。
    3.  **中间 (Middle)**：最后应用作用于笔画中间部分的变换。

    在每个阶段内部，变换将严格按照其在Web界面中从上到下的UI顺序来执行。

## 多阶段处理流程

### 处理管道架构
```
原始笔画 → [核心处理流程] → D0 输出 → [可选D1处理流程] → D1 输出
             │
             └─ 起笔调整 → 终笔调整 → 裁剪 → 模块化变换(移动,倾斜,缩放,平滑)
```

### 模块化变换系统
系统已实现模块化的变换架构，将原有的分散变换功能统一管理：

- **TransformManager**：统一协调所有变换的执行
- **执行顺序**：移动 → 倾斜 → 缩放 → 平滑
- **配置驱动**：通过配置参数控制每个变换的启用和参数
- **可扩展性**：为未来偏旁级别的精细变换奠定基础

### 详细处理阶段

#### 1. 起笔方向调整 (Start Orientation)
**目的**：统一或调整笔画起始部分的方向

**算法实现**：
```python
def adjust_start_orientation(points, target_angle, influence_frac, strength):
    """
    调整笔画起始方向
    - target_angle: 目标角度（弧度）
    - influence_frac: 影响范围（占总长度比例）
    - strength: 调整强度（0.0-1.0）
    """
```

**参数说明**：
- `enabled`: 是否启用起笔方向调整
- `target_angle_deg`: 目标角度（度数）
- `influence_frac`: 影响范围比例 (0.0-1.0)
- `strength`: 调整强度 (0.0-1.0)

**应用场景**：
- 统一不同笔画的起笔角度
- 创建特定的书法风格效果
- 修正数据中的起笔方向不一致问题

#### 2. 终笔方向调整 (End Orientation)
**目的**：调整笔画结束部分的方向

**算法特点**：
- 与起笔调整算法对称
- 从笔画末端开始应用影响
- 支持独立的参数配置

**参数配置**：
```json
{
  "end_orientation": {
    "enabled": true,
    "target_angle_deg": 45.0,
    "influence_frac": 0.3,
    "strength": 0.8
  }
}
```

#### 3. 裁剪和端点保护 (Trim and Protect)
**目的**：精确控制笔画的起点和终点位置

##### 3.1 起点裁剪 (Start Trim)
**功能**：从笔画起点按比例裁剪
**参数**：`start_trim` (0.0-1.0)
**算法**：基于弧长比例的精确裁剪

##### 3.2 终点裁剪 (End Trim) - 核心功能
**功能**：在第三段（笔锋段）内按比例裁剪终点

**算法实现**：
```python
def trim_last_segment_by_fraction(points, end_frac_seg3, corner_thresh_deg):
    """
    终点裁剪算法 - 只在第三段内裁剪
    
    步骤：
    1. 角点检测：识别笔画的转折点
    2. 第三段定位：确定最后一个角点后的段落
    3. 弧长计算：计算第三段的总弧长
    4. 裁剪长度：根据比例计算需要裁剪的长度
    5. 精确插值：在线段内插值确定裁剪点
    6. 点序列重构：返回裁剪后的点序列
    """
```

**关键特性**：
- **只在第三段裁剪**：保护前两段的完整性
- **角点保护**：所有角点位置完全不变
- **颜色一致性**：第三段颜色保持统一
- **精确插值**：支持线段内的精确裁剪点计算

**参数建议**：
- 推荐范围：0.1-0.5
- 0.0：不裁剪
- 1.0：裁剪到最后一个角点
- 过大值会影响字形识别度

##### 3.3 端点保护机制（已移除）
**变更说明**：端点保护机制已完全移除，以确保所有变换效果能完整作用于整个笔画。

**移除原因**：
- 端点保护会覆盖移动、倾斜等变换效果
- 影响笔画作为整体单元的一致性变换
- 简化处理流程，提高变换效果的可预测性

#### 4. 模块化变换系统 (Modular Transform System)
**目的**：通过模块化的设计实现笔画变换的统一管理和协调执行

**核心组件**：
- `BaseTransform`：所有变换的基础接口
- `MoveTransform`：笔画移动变换
- `TiltTransform`：笔画倾斜变换
- `ScaleTransform`：笔画缩放变换
- `SmoothTransform`：笔画平滑变换
- `TransformManager`：变换管理器

##### 4.1 平滑处理 (Smoothing)
**目的**：减少笔画的锯齿感，创造更自然的曲线

###### 4.1.1 Chaikin平滑算法
**原理**：角点切割算法，通过迭代细分创造平滑曲线

**算法步骤**：
1. 对每条线段进行1/4和3/4点分割
2. 用分割点替换原始点
3. 重复指定次数的迭代

**实现代码**：
```python
def chaikin_smooth(points, iterations=1):
    """
    Chaikin角点切割平滑算法
    - iterations: 迭代次数，越多越平滑但点数增加
    """
    for _ in range(iterations):
        new_points = []
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            # 1/4点和3/4点
            q = Point((3*p1.x + p2.x)/4, (3*p1.y + p2.y)/4, p1.color)
            r = Point((p1.x + 3*p2.x)/4, (p1.y + 3*p2.y)/4, p2.color)
            new_points.extend([q, r])
        points = new_points
    return points
```

**参数调整**：
- `iterations`: 迭代次数 (1-5)
- 1次：轻微平滑
- 3次：中等平滑
- 5次：强烈平滑（可能过度）

###### 4.1.2 移动平均平滑 (Moving Average Smoothing)
**目的**：通过移动平均算法进一步平滑笔画曲线

**算法实现**：
```python
def smooth_by_moving_average(points, window_size):
    """
    移动平均平滑算法
    - window_size: 平滑窗口大小
    """
```

**参数建议**：
- `window_size`: 1-7
- 1：无平滑效果
- 3：轻度平滑
- 5-7：中度到强度平滑

##### 4.2 笔画移动 (Stroke Movement)
**目的**：整体移动笔画位置，保持笔画内部结构不变

**算法实现**：
```python
def move_stroke(points, dx, dy):
    """
    笔画移动算法
    - dx: 水平偏移量
    - dy: 垂直偏移量（正值向下，负值向上）
    """
    return [(x + dx, y + dy) for x, y in points]
```

**关键特性**：
- **整体移动**：所有点统一偏移
- **结构保持**：笔画内部相对位置不变
- **段落一致**：三段同时移动，保持分段关系

##### 4.3 几何变换 (Geometric Transform)
**目的**：应用整体的几何变换效果

###### 4.3.1 倾斜变换 (Tilt)
**功能**：模拟书写时的纸张倾斜效果
**参数**：`tilt_deg` (-30° 到 30°)
**优化特性**：使用统一倾斜角度确保方向一致性，每个笔画围绕自己的边界框中心旋转，保持整体倾斜效果的协调性

###### 4.3.2 缩放变换 (Scale)
**功能**：调整笔画的整体大小
**参数**：`scale_factor` (0.5-2.0)

## 角点检测算法

### 算法原理
基于相邻向量夹角的角点检测方法

```python
def _find_corner_indices(points, angle_threshold_deg):
    """
    角点检测算法
    
    步骤：
    1. 计算相邻线段的向量
    2. 计算向量夹角
    3. 与阈值比较确定角点
    4. 返回角点索引列表
    """
    corners = []
    threshold_rad = math.radians(angle_threshold_deg)
    
    for i in range(1, len(points) - 1):
        # 计算前后向量
        v1 = vector_from_points(points[i-1], points[i])
        v2 = vector_from_points(points[i], points[i+1])
        
        # 计算夹角
        angle = angle_between_vectors(v1, v2)
        
        if angle > threshold_rad:
            corners.append(i)
    
    return corners
```

### 参数调整
- `corner_thresh_deg`: 角点检测阈值（度）
- 15°-45°：常用范围
- 较小值：检测更多角点
- 较大值：只检测明显转折

## 笔画分段机制

### 三段分割
基于角点检测结果，将笔画分为三段：

1. **第一段**：起点到第一个角点
2. **第二段**：第一个角点到最后一个角点
3. **第三段**：最后一个角点到终点

### 分段应用
- **起笔调整**：主要影响第一段
- **中间处理**：主要影响第二段
- **终点裁剪**：只在第三段内操作

## 颜色和分段保持

### 颜色管理
每个点都携带颜色信息，用于区分不同的处理段：
```python
class Point:
    def __init__(self, x, y, color=0):
        self.x = x
        self.y = y
        self.color = color  # 段落标识
```

### 分段颜色规则
- 第一段：color = 0
- 第二段：color = 1  
- 第三段：color = 2

### 处理中的颜色保持
所有处理算法都确保：
- 插值时保持原点颜色
- 新增点继承邻近点颜色
- 分段边界清晰可识别

## 性能优化策略

### 1. 算法优化
- 向量化计算减少循环
- 预计算常用数学值
- 避免重复的几何计算

### 2. 内存优化
- 就地修改减少内存分配
- 及时释放中间结果
- 优化数据结构设计

### 3. 参数优化建议
```json
{
  "performance_optimized": {
    "chaikin_iterations": 2,
    "target_spacing": 5.0,
    "corner_thresh_deg": 25.0
  },
  "quality_optimized": {
    "chaikin_iterations": 3,
    "target_spacing": 2.0,
    "corner_thresh_deg": 15.0
  }
}
```

## 调试和监控

### 调试信息
系统提供控制台调试输出：
```python
print(f"角点检测: 发现 {len(corners)} 个角点")
print(f"第三段范围: {seg3_start_idx} 到 {len(points)-1}")
print(f"裁剪前点数: {len(points)}, 裁剪后: {len(result)}")
```

**注意**：系统已移除Web界面的日志窗口功能，调试信息主要通过控制台输出。

### 性能监控
- 处理时间统计
- 内存使用监控
- 算法效率分析

## 扩展开发指南

### 添加新的变换模块
1. 在 `src/transforms/` 目录下创建新的变换模块
2. 继承 `BaseTransform` 基类并实现必要方法
3. 在 `TransformManager` 中注册新的变换类型
4. 在配置文件中添加参数定义
5. 在Web界面中添加控制组件

### 模块化变换开发模板
```python
from .base_transform import BaseTransform
from typing import List, Dict, Any
from ..types import Point

class CustomTransform(BaseTransform):
    def apply(self, points: List[Point], params: Dict[str, Any]) -> List[Point]:
        """实现自定义变换逻辑"""
        # 变换实现
        return transformed_points
    
    def get_default_params(self) -> Dict[str, Any]:
        """返回默认参数"""
        return {
            'enabled': False,
            'param1': 0.0,
            'param2': 1.0
        }
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数有效性"""
        return True
    
    def is_enabled(self, params: Dict[str, Any]) -> bool:
        """检查变换是否启用"""
        return params.get('enabled', False)
```

### D0基线生成隔离机制

D0（基线处理中轴线）作为稳定的对比基准，必须完全隔离于用户界面参数。在 `web/services/generation.py` 中实现了严格的参数清理：

**清理的参数类别**：
1. **几何变换参数**：倾斜、缩放、移动全部归零
2. **平滑处理参数**：Chaikin迭代、移动平均窗口重置为默认
3. **裁剪参数**：起点/终点裁剪归零
4. **角度调整参数**：起笔角度、笔锋角度完全禁用
5. **UI控制参数**：三色窗口、分段冻结、角度范围等全部移除

**关键修复点**：
- `end_angle_range_deg` = 0.0 (禁用笔锋角度)
- `end_frac_len` = 1.0 (重置笔锋长度比例)
- `stroke_move.offset` = 0.0 (禁用笔画移动)
- 移除所有preview配置中的UI参数

### D2 含义澄清（当前代码）
- 按钮 D2：生成“中轴填充（Median Fill）”，输出到 `D2_median_fill/`，UI 显示在 B 窗口。
- 兼容路径 D2（`/gen?type=D2`）：对最新 D1 应用网格变形并归档 `_d2.svg` 到 `C_processed_centerline/`，主要用于网格变形工作流的结果保存。

### 未来扩展方向
模块化变换系统为未来的功能扩展奠定了基础：

1. **偏旁识别模块**：识别和分类不同的偏旁部首
2. **偏旁级变换**：对特定偏旁应用独立的变换参数
3. **高级变换**：支持更复杂的几何变换和风格效果
4. **智能参数**：基于机器学习的参数自动调优

---

**相关文档**：
- [技术架构文档](ARCHITECTURE.md) - 系统架构和模块化设计
- [Web界面文档](WEB_INTERFACE.md) - 用户界面和操作指南
- [API接口文档](API_REFERENCE.md) - 接口规范和调用示例
