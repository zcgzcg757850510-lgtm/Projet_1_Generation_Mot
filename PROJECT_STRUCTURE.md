# 项目结构说明

## 📁 核心目录结构

```
A_1_Generateur_Mot/
├── src/                    # 核心处理引擎（23个Python模块）
│   ├── main.py            # 主入口
│   ├── parser.py          # 数据解析
│   ├── classifier.py      # 笔画分类
│   ├── renderer.py        # SVG渲染
│   ├── styler.py          # 风格处理
│   ├── transformer.py     # 几何变换
│   └── transforms/        # 模块化变换系统
│
├── web/                   # Web界面系统（66个文件）
│   ├── app.py            # Flask应用入口
│   ├── css/              # 样式表模块
│   ├── js/               # JavaScript模块
│   ├── html/             # HTML模板
│   ├── routes/           # API路由
│   └── services/         # 业务逻辑服务
│
├── scripts/              # 生产辅助脚本（40个）
│   ├── create_alphanumeric.py
│   ├── create_punctuation_data.py
│   ├── extract_from_hershey.py
│   └── ...
│
├── data/                 # 核心数据文件
│   ├── alphanumeric_medians.json        # 字母数字中轴数据
│   ├── punctuation_medians.json         # 标点符号数据
│   ├── stroke_types.json                # 笔画类型定义
│   ├── style_profiles.json              # 风格配置
│   └── make-me-a-hanzi/                 # 汉字数据库
│
├── docs/                 # 官方技术文档（10个）
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── WEB_INTERFACE.md
│   └── ...
│
├── tests/                # 规范单元测试
│   ├── test_parser.py
│   ├── test_classifier.py
│   └── ...
│
├── mmh_pipeline/         # Make Me a Hanzi数据处理
│   ├── data/            # 汉字数据（19,000+ SVG文件）
│   └── scripts/         # 数据处理脚本
│
├── fonts/               # 字体资源文件
│   ├── NotoSansCJK-Regular.otf
│   ├── SourceHanSans-Regular.otf
│   └── ...
│
├── output/              # 生成结果输出
│   ├── compare/         # 对比图像
│   ├── preview/         # 预览图像
│   └── ...
│
└── archive/             # 归档文件（已清理）
    ├── tests/           # 临时测试文件（12个）
    ├── debug/           # 调试脚本（13个）
    ├── docs/            # 历史文档（27个）
    ├── scripts/         # 历史脚本（9个）
    ├── backups/         # 数据备份（14个）
    └── reference/       # 参考文件（3个）
```

## 🚀 快速启动

### 启动Web界面
```bash
python start_server.py
# 访问 http://127.0.0.1:5000/
```

### 命令行模式
```bash
python -m src.main --text 你好 --seed 42
```

## 📊 文件统计

| 目录 | 文件数 | 说明 |
|------|--------|------|
| `src/` | 23 | 核心处理引擎 |
| `web/` | 66 | Web界面系统 |
| `scripts/` | 40 | 辅助脚本 |
| `docs/` | 11 | 官方文档 |
| `tests/` | 5 | 单元测试 |
| `archive/` | 78 | 归档文件（可选） |

## 🗑️ 清理记录

**清理时间**: 2025-10-05  
**清理文件**: 78个  
**清理说明**: 查看 `archive/CLEANUP_REPORT.md`

### 归档内容
- ✅ 测试文件: 12个
- ✅ 调试脚本: 13个  
- ✅ 历史文档: 27个
- ✅ 历史脚本: 9个
- ✅ 数据备份: 14个
- ✅ 参考文件: 3个

### 核心功能保留
所有核心功能文件完整保留，项目正常运行不受影响。

## 📝 重要文件

| 文件 | 说明 |
|------|------|
| `README.md` | 项目主文档 |
| `CHANGELOG.md` | 更新日志 |
| `Prompt.md` | 功能变更管理规范 |
| `PROJECT_STRUCTURE.md` | 本文档 |
| `requirements.txt` | Python依赖 |
| `docker-compose.yml` | Docker配置 |

## 🔄 恢复归档文件

如需恢复某个归档文件：

```bash
# Windows
copy archive\tests\test_xxx.py .\

# Linux/Mac
cp archive/tests/test_xxx.py ./
```

## 💡 维护建议

1. **保留期限**: archive/目录建议保留3个月
2. **定期清理**: 确认无需恢复后可删除归档
3. **备份策略**: data/目录保留2个最新备份即可
4. **文档更新**: 新功能开发请更新docs/相应文档

## 📞 技术支持

- 架构文档: `docs/ARCHITECTURE.md`
- API文档: `docs/API_REFERENCE.md`
- 开发指南: `docs/DEVELOPMENT.md`
- Web界面: `docs/WEB_INTERFACE.md`
