# GIS Agent 部署指南

本文档提供GIS Agent的部署指南，适合生产环境使用。

## 目录

- [前置要求](#前置要求)
- [安装](#安装)
- [配置](#配置)
- [启动](#启动)
- [生产部署](#生产部署)
- [监控和日志](#监控和日志)
- [故障排查](#故障排查)

## 前置要求

### 系统要求
- Python 3.10 或更高版本
- 至少 2GB 可用内存
- 至少 1GB 可用磁盘空间

### 操作系统支持
- Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- macOS 10.15+
- Windows 10+

## 安装

### 方式一：从源码安装（推荐）

```bash
# 1. 克隆仓库
git clone https://github.com/ymj618sky-create/gis-agent.git
cd gis-agent

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Linux/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# 4. 安装依赖（开发模式）
pip install -e .

# 5. 验证安装
python -c "import gis_agent; print('安装成功')"
```

### 方式二：使用 uv（快速）

```bash
# 1. 克隆仓库
git clone https://github.com/ymj618sky-create/gis-agent.git
cd gis-agent

# 2. 使用 uv 安装
uv venv
uv pip install -e .

# 3. 验证安装
uv run python -c "import gis_agent; print('安装成功')"
```

### 方式三：直接安装依赖

```bash
# 1. 克隆仓库
git clone https://github.com/ymj618sky-create/gis-agent.git
cd gis-agent

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt
```

## 配置

### 环境变量配置

创建 `.env` 文件：

```bash
cp .env.example .env
nano .env
```

配置必需的环境变量：

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
ENVIRONMENT=production
LOG_LEVEL=INFO

# 服务端口
PORT=8080
HOST=0.0.0.0
```

### config.json 配置

创建或编辑 `config.json`：

```json
{
  "models": {
    "dashscope": {
      "model": "qwen-max",
      "temperature": 0.7
    }
  },
  "tools": {
    "enabled": [
      "read_data",
      "write_data",
      "convert",
      "clip",
      "proximity"
    ]
  },
  "timeout": {
    "llm_request": 300,
    "max_iterations": 15
  },
  "defaults": {
    "crs": "EPSG:4528"
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

### 开发模式（自动重载）

```bash
# 使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8080

# 或使用 python
python main.py
```

### 生产模式

```bash
# 使用 Gunicorn（推荐）
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8080

# 使用 uvicorn（简单）
uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
```

### 后台运行

#### Linux/macOS

```bash
# 使用 nohup
nohup uvicorn main:app --host 0.0.0.0 --port 8080 > gis-agent.log 2>&1 &

# 使用 screen
screen -S gis-agent
uvicorn main:app --host 0.0.0.0 --port 8080
# 按 Ctrl+A, D 分离会话

# 使用 tmux
tmux new -s gis-agent
uvicorn main:app --host 0.0.0.0 --port 8080
# 按 Ctrl+B, D 分离会话
```

#### Windows

```bash
# 使用 start /B
start /B uvicorn main:app --host 0.0.0.0 --port 8080

# 使用 NSSM（推荐）
# 下载并安装 NSSM
nssm install GIS-Agent venv\Scripts\python.exe
nssm set GIS-Agent AppParameters "-m uvicorn main:app --host 0.0.0.0 --port 8080"
nssm start GIS-Agent
```

## 生产部署

### 使用 Systemd（Linux）

创建服务文件 `/etc/systemd/system/gis-agent.service`：

```ini
[Unit]
Description=GIS Agent API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/gis-agent
Environment="PATH=/path/to/gis-agent/venv/bin"
ExecStart=/path/to/gis-agent/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8080
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable gis-agent
sudo systemctl start gis-agent
sudo systemctl status gis-agent
```

### 使用 Supervisor（通用）

创建配置文件 `/etc/supervisor/conf.d/gis-agent.conf`：

```ini
[program:gis-agent]
command=/path/to/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
directory=/path/to/gis-agent
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/gis-agent.err.log
stdout_logfile=/var/log/gis-agent.out.log
environment=PATH="/path/to/venv/bin"
```

启用服务：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start gis-agent
```

### 使用 Nginx 反向代理

创建配置文件 `/etc/nginx/sites-available/gis-agent`：

```nginx
upstream gis_agent {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://gis_agent;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE支持
        proxy_buffering off;
        proxy_cache off;
    }

    location /static/ {
        alias /path/to/gis-agent/static/;
        expires 7d;
    }

    location /uploads/ {
        alias /path/to/gis-agent/uploads/;
        expires 1h;
    }

    location /workspace/ {
        alias /path/to/gis-agent/workspace/;
        expires 1h;
    }

    location /health {
        proxy_pass http://gis_agent/health;
        access_log off;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/gis-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 使用 SSL/HTTPS

使用 Certbot 获取免费证书：

```bash
sudo certbot --nginx -d your-domain.com
```

## 监控和日志

### 日志配置

配置日志级别和输出位置：

```bash
# 环境变量设置
export LOG_LEVEL=DEBUG
export LOG_FILE=/var/log/gis-agent/app.log
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8080/health

# 查看响应
{"status":"healthy"}
```

### 日志查看

```bash
# 查看实时日志
tail -f /var/log/gis-agent/app.log

# Systemd服务日志
sudo journalctl -u gis-agent -f

# Supervisor服务日志
sudo supervisorctl tail -f gis-agent
```

### 性能监控

使用 `htop` 或 `top` 监控资源使用：

```bash
htop
```

## 故障排查

### 常见问题

#### 1. 端口被占用

```bash
# 查看端口占用
lsof -i :8080  # Linux/macOS
netstat -ano | findstr :8080  # Windows

# 修改端口
uvicorn main:app --port 8081
```

#### 2. 依赖安装失败

```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 升级 pip
pip install --upgrade pip
```

#### 3. 内存不足

```bash
# 减少工作进程数
gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app

# 增加交换空间
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. 权限问题

```bash
# 修复工作目录权限
sudo chown -R www-data:www-data /path/to/gis-agent
sudo chmod -R 755 /path/to/gis-agent/workspace
```

#### 5. API密钥无效

```bash
# 检查环境变量
cat .env | grep API_KEY

# 测试API密钥
curl -H "Authorization: Bearer $DASHSCOPE_API_KEY" \
  https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
```

### 调试模式

```bash
# 启用调试日志
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug
```

## 备份和恢复

### 备份数据

```bash
# 备份工作空间
tar -czf workspace-backup-$(date +%Y%m%d).tar.gz workspace/

# 备份记忆
tar -czf memory-backup-$(date +%Y%m%d).tar.gz memory/

# 备份配置
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env config.json
```

### 恢复数据

```bash
# 恢复工作空间
tar -xzf workspace-backup-YYYYMMDD.tar.gz

# 恢复记忆
tar -xzf memory-backup-YYYYMMDD.tar.gz
```

## 更新和维护

### 更新应用

```bash
# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
sudo systemctl restart gis-agent
```

### 定期维护

```bash
# 清理临时文件
find workspace/data/sessions -type f -mtime +30 -delete

# 清理日志
find /var/log/gis-agent -type f -mtime +7 -delete

# 重建虚拟环境（可选）
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --force-reinstall
```

## 安全建议

1. **使用HTTPS** - 在生产环境始终使用SSL/TLS
2. **限制CORS** - 不要在生产环境使用 `allow_origins=["*"]`
3. **保护API密钥** - 不要将 `.env` 文件提交到版本控制
4. **定期更新** - 及时更新依赖包
5. **备份重要数据** - 定期备份工作空间和记忆
6. **监控日志** - 定期检查访问日志和错误日志

## 获取帮助

- 提交 Issue: https://github.com/ymj618sky-create/gis-agent/issues
- 邮件: admin@gis-agent.com

---

更多详细信息，请参考：
- [安装指南](INSTALL.md)
- [快速开始](SETUP.md)
- [README](README.md)