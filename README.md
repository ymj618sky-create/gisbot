<div align="center">
  <h1>🗺️ GIS Agent</h1>
  <p>
    <strong>AI驱动的地理信息系统分析助手</strong>
  </p>
  <p>
    具备自主执行能力 • 支持多种GIS数据格式 • 智能记忆系统
  </p>
  <p>
    <a href="https://github.com/ymj618sky-create/gis-agent/actions/workflows/tests.yml">
      <img src="https://img.shields.io/github/actions/workflow/status/ymj618sky-create/gis-agent/tests?label=Tests" alt="Tests">
    </a>
    <a href="https://pypi.org/project/gis-agent/">
      <img src="https://img.shields.io/pypi/v/gis-agent" alt="PyPI">
    </a>
    <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </p>
</div>

## 📋 简介

GIS Agent 是一个基于AI的地理信息系统分析助手，具备**自主执行能力**。它可以帮助用户：

- 🤖 **自主任务规划**：自动将复杂任务分解为可执行的步骤
- 📊 **GIS数据分析**：处理Shapefile、GeoJSON、栅格数据等
- 💾 **智能记忆**：LLM驱动的记忆系统，记住用户偏好
- 🧩 **并行执行**：支持后台子Agent并行处理任务
- 🔗 **消息总线**：解耦的异步通信架构

参考 [nanobot](https://github.com/HKUDS/nanobot) 架构设计，具备超轻量、易扩展的特点。

## ✨ 核心特性

### 自主执行能力
- **任务规划**：自动分解复杂任务，识别依赖关系
- **子Agent并行**：后台并行执行独立任务
- **智能调度**：根据任务类型自动选择执行策略

### GIS数据处理
- **矢量数据**：Shapefile、GeoJSON、GPKG
- **栅格数据**：TIFF、PNG、JPG
- **表格数据**：CSV、Excel
- **坐标转换**：支持多种坐标系

### 智能记忆系统
- **长期记忆**：MEMORY.md 存储持久化知识
- **历史记录**：HISTORY.md 记录交互历史
- **LLM合并**：智能合并和更新记忆

### 消息总线架构
- **异步队列**：入站和出站消息队列
- **多通道支持**：可扩展到多种聊天平台
- **上下文传递**：完整保留会话上下文

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/ymj618sky-create/gis-agent.git
cd gis-agent

# 安装依赖
pip install -e .

# 配置环境变量
cp .env.example .env
```

### 配置

编辑 `.env` 文件：

```bash
# LLM Provider配置
DASHSCOPE_API_KEY=your-dashscope-api-key
DEFAULT_PROVIDER=dashscope

# 工作目录
WORKSPACE_DIR=./workspace
```

### 启动

```bash
# Web界面
python main.py

# 访问 http://localhost:8080
```

## 📁 项目结构

```
gis-agent/
├── core/               # 核心功能
│   ├── agent/         # Agent循环、记忆、子Agent
│   ├── bus/           # 消息总线
│   ├── tools/         # 工具集
│   └── providers/     # LLM提供商
├── api/               # API路由
├── session/           # 会话管理
├── skills/            # 自主Skill
│   └── autonomous/    # 任务规划、探索、诊断
├── tests/             # 测试
├── workspace/         # 工作目录
├── static/            # Web界面
└── main.py            # 入口文件
```

## 🔧 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DASHSCOPE_API_KEY` | 阿里云API密钥 | - |
| `ANTHROPIC_API_KEY` | Anthropic API密钥 | - |
| `DEFAULT_PROVIDER` | 默认提供商 | dashscope |
| `WORKSPACE_DIR` | 工作目录 | ./workspace |
| `LOG_LEVEL` | 日志级别 | INFO |

### config.json

```json
{
  "models": {
    "dashscope": {"model": "qwen-max"}
  },
  "tools": {
    "enabled": ["read_data", "write_data", "clip"]
  },
  "autonomous": {
    "enable_message_bus": true,
    "enable_subagent": true
  }
}
```

## 📖 使用示例

### Web界面

访问 `http://localhost:8080`，开始与Agent对话：

```
用户: 分析landuse数据，生成图表并导出PDF

Agent: 我来帮您完成这个任务。
      1. 读取landuse.shp数据
      2. 统计各类型面积
      3. 生成饼图
      4. 导出PDF报告
```

### API调用

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8080/api/chat",
        json={"message": "分析数据"}
    )
    print(response.json())
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 查看覆盖率
pytest --cov=core --cov=api --cov-report=html
```

## 🛠️ 开发

### 代码风格

```bash
# 检查代码
ruff check .

# 格式化代码
ruff format .
```

### 添加新工具

在 `core/tools/` 目录创建新工具类：

```python
from core.tools.base import Tool

class MyTool(Tool):
    name = "my_tool"
    description = "我的工具描述"

    async def execute(self, **kwargs):
        # 实现工具逻辑
        return "执行结果"
```

### 添加新Skill

在 `skills/autonomous/` 目录创建新的Skill文档。

## 📚 文档

- [安装指南](INSTALL.md) - 详细安装步骤
- [部署指南](DEPLOYMENT.md) - 生产环境部署
- [开发指南](CLAUDE.md) - 开发规范和约定

## 🤝 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [nanobot](https://github.com/HKUDS/nanobot) - 架构设计参考
- [FastAPI](https://fastapi.tiangolo.com/) - Web框架
- [GeoPandas](https://geopandas.org/) - GIS数据处理

## 📮 联系

- 提交 Issue: https://github.com/ymj618sky-create/gis-agent/issues
- 邮箱: admin@gis-agent.com

---

<div align="center">
  <p>由 ❤️ 用 Python 构建</p>
</div>