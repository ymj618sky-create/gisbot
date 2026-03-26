# GIS Agent 快速开始

> AI驱动的地理信息系统分析助手，具备自主执行能力

## 安装

```bash
# 克隆仓库
git clone https://github.com/ymj618sky-create/gis-agent.git
cd gis-agent

# 安装依赖
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

## 配置

在 `.env` 文件中配置：

```bash
# 必需：至少配置一个API密钥
DASHSCOPE_API_KEY=your-dashscope-api-key
# 或者
ANTHROPIC_API_KEY=your-anthropic-api-key

# 可选配置
DEFAULT_PROVIDER=dashscope
WORKSPACE_DIR=./workspace
LOG_LEVEL=INFO
```

## 启动

```bash
# Web界面
python main.py

# 访问: http://localhost:8080
```

## 功能特性

- 🤖 **自主执行**: 自动任务规划和并行处理
- 📊 **GIS分析**: 空间数据处理和分析
- 💾 **智能记忆**: LLM驱动的记忆系统
- 🧩 **消息总线**: 解耦的异步通信架构
- 🛠️ **工具丰富**: 数据读取、转换、分析等

## 获取帮助

- 详细安装: [INSTALL.md](INSTALL.md)
- 开发指南: [CLAUDE.md](CLAUDE.md)
- 问题反馈: [GitHub Issues](https://github.com/ymj618sky-create/gis-agent/issues)