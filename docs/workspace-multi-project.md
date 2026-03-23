# Workspace 多项目记忆架构

## 概述

本系统支持多项目隔离，每个项目有独立的工作空间和记忆系统。

## 目录结构

```
gis-agent/
├── workspace/
│   ├── projects/
│   │   ├── default/
│   │   │   ├── data/
│   │   │   ├── outputs/
│   │   │   ├── temp/
│   │   │   └── .memory/
│   │   │       ├── facts.json
│   │   │       ├── preferences.json
│   │   │       ├── workflows.json
│   │   │       └── stats.json
│   │   └── project_xxx/
│   └── shared/
└── sessions/
```

## 项目记忆功能

### 1. 事实记忆
- 存储项目中学习到的重要信息
- 支持分类、重要性评分、标签
- 支持搜索和检索

### 2. 偏好设置
- 项目特定的配置
- 如坐标系、输出格式等

### 3. 工作流
- 常用操作流程记录
- 可保存和复用

### 4. 统计信息
- 会话数、消息数
- 工具使用统计
- 文件记录

## API 使用

```python
# 获取项目记忆
memory = memory_manager.get_memory("project_id")

# 添加事实
memory.add_fact("重要信息", "data", importance=5)

# 获取上下文
context = memory.get_context_for_prompt()
```

## API 端点

- `GET /api/workspace/projects/{project_id}/memory/summary` - 记忆摘要
- `GET /api/workspace/projects/{project_id}/memory/context` - 提示上下文
- `POST /api/workspace/projects/{project_id}/memory/facts` - 添加事实
- `GET /api/workspace/projects/{project_id}/memory/preferences` - 获取偏好
- `POST /api/workspace/projects/{project_id}/memory/preferences` - 设置偏好