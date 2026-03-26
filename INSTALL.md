# GIS Agent 安装指南

GIS Agent - 具备自主执行能力的AI地理信息系统分析助手

## 系统要求

- Python 3.10 或更高版本
- 至少 2GB 可用内存
- 至少 1GB 可用磁盘空间

## 快速安装

### 方式一：从源码安装（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/ymj618sky-create/gis-agent.git
cd gis-agent

# 2. 创建虚拟环境（推荐）
python -m venv venv

# 3. 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 4. 安装依赖
pip install -e .

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
nano .env
```

### 方式二：使用 uv 安装（快速）

```bash
# 1. 克隆仓库
git clone https://github.com/ymj618sky-create/gis-agent.git
cd gis-agent

# 2. 使用 uv 安装
uv pip install -e .

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件
nano .env
```

### 方式三：直接安装依赖

```bash
# 1. 克隆仓库
git clone https://github.com/ymj618sky-create/gis-agent.git
cd gis-agent

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件
nano .env
```

## 配置

### 环境变量配置

编辑 `.env` 文件，配置以下必需参数：

```bash
# LLM Provider配置（至少配置一个）
DASHSCOPE_API_KEY=your-dashscope-api-key
# 或者
ANTHROPIC_API_KEY=your-anthropic-api-key
# 或者
OPENAI_API_KEY=your-openai-api-key

# 默认提供商
DEFAULT_PROVIDER=dashscope

# 工作目录
WORKSPACE_DIR=./workspace
DATA_DIR=./workspace/data
MEMORY_DIR=./memory

# 运行环境
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### config.json 配置

在项目根目录创建 `config.json`（可选，已有默认值）：

```json
{
  "models": {
    "dashscope": {
      "model": "qwen-max",
      "temperature": 0.7
    },
    "anthropic": {
      "model": "claude-sonnet-4-6",
      "temperature": 0.7
    },
    "openai": {
      "model": "gpt-4o",
      "temperature": 0.7
    }
  },
  "tools": {
    "enabled": [
      "read_data",
      "write_data",
      "convert",
      "clip",
      "proximity",
      "run_python",
      "file_analysis"
    ],
    "formats": ["shp", "gpkg", "geojson", "csv", "tif", "png", "jpg"]
  },
  "timeout": {
    "llm_request": 300,
    "exec_command": 60,
    "run_python": 120,
    "max_iterations": 15
  },
  "defaults": {
    "crs": "EPSG:4528",
    "workspace": "./workspace"
  },
  "autonomous": {
    "enable_message_bus": true,
    "enable_subagent": true,
    "enable_llm_memory": true,
    "enable_task_planning": true
  }
}
```

## 启动

### Web界面

```bash
# 启动Web服务
python main.py

# 或者使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

访问 `http://localhost:8080` 使用Web界面。

### 命令行

```bash
# 直接运行（开发模式）
python -c "from main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8080)"
```

## 验证安装

```bash
# 运行测试
pytest

# 检查版本
python -c "import gis_agent; print(gis_agent.__version__)"
```

## 获取API密钥

| 提供商 | 获取地址 | 说明 |
|--------|----------|------|
| 阿里云 Dashscope | https://dashscope.aliyun.com/ | 国内推荐 |
| Anthropic | https://console.anthropic.com/ | Claude系列 |
| OpenAI | https://platform.openai.com/ | GPT系列 |

## 目录结构

```
gis-agent/
├── core/           # 核心功能
│   ├── agent/      # Agent相关
│   ├── bus/        # 消息总线
│   ├── tools/      # 工具集
│   └── providers/  # LLM提供商
├── api/            # API路由
├── session/        # 会话管理
├── skills/         # 自主Skill
├── workspace/      # 工作目录（运行时创建）
├── memory/         # 记忆目录（运行时创建）
├── uploads/        # 上传文件（运行时创建）
├── static/         # 静态文件
├── config.json     # 配置文件
├── .env            # 环境变量
├── requirements.txt
└── main.py         # 入口文件
```

## 常见问题

### 1. 依赖安装失败

```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. GDAL相关错误

Windows用户可以预编译的wheel包：

```bash
pip install GDAL==$(gdal-config --version)
```

### 3. OCR功能不可用

安装Tesseract OCR：
- Windows: 下载安装 https://github.com/UB-Mannheim/tesseract/wiki
- Linux: `sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim`
- macOS: `brew install tesseract`

### 4. 端口被占用

修改启动端口：

```bash
uvicorn main:app --port 8081
```

## 开发模式

```bash
# 安装开发依赖
pip install -r requirements.txt

# 启用自动重载
uvicorn main:app --reload

# 运行测试
pytest

# 代码检查
ruff check .
ruff format .
```

## 生产部署

### 使用 Gunicorn

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### 使用 Supervisor

```ini
[program:gis-agent]
command=/path/to/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
directory=/path/to/gis-agent
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/gis-agent.err.log
stdout_logfile=/var/log/gis-agent.out.log
```

## 更新

```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
# 根据你的部署方式重启
```

## 卸载

```bash
# 停止服务
# 根据你的部署方式停止

# 删除虚拟环境（可选）
rm -rf venv

# 删除项目文件
rm -rf gis-agent
```

## 获取帮助

- 查看 [CLAUDE.md](CLAUDE.md) 了解开发规范
- 查看 [DEPLOYMENT.md](DEPLOYMENT.md) 了解部署详情
- 提交 Issue: https://github.com/ymj618sky-create/gis-agent/issues

## 许可证

MIT License