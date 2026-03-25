# Task Planning Skill

## 概述

任务规划技能帮助AI Agent将复杂任务分解为可执行的子任务，并制定科学的执行计划。

## 工作流程

1. **理解任务** - 分析用户需求，识别核心目标
2. **分解任务** - 将大任务拆分为小步骤
3. **识别依赖** - 确定任务间的依赖关系
4. **分配资源** - 评估所需工具和数据
5. **制定计划** - 生成执行时间线和里程碑

## 输入格式

```python
{
    "task": "用户任务描述",
    "context": {
        "available_tools": [...],
        "workspace": "工作目录路径",
        "constraints": [...]
    }
}
```

## 输出格式

```python
{
    "task_id": "任务ID",
    "summary": "任务摘要",
    "steps": [
        {
            "id": "step-1",
            "description": "步骤描述",
            "action": "action_name",
            "params": {...},
            "depends_on": [],
            "estimated_time": "5m"
        }
    ],
    "estimated_duration": "30m",
    "risks": [...],
    "success_criteria": [...]
}
```

## 示例

### 输入
```
"分析landuse数据并生成报告"
```

### 输出
```python
{
    "task_id": "landuse-analysis-001",
    "summary": "分析土地利用数据并生成可视化报告",
    "steps": [
        {
            "id": "step-1",
            "description": "读取landuse数据",
            "action": "read_data",
            "params": {"path": "workspace/data/landuse.shp"},
            "depends_on": []
        },
        {
            "id": "step-2", 
            "description": "统计各类型面积",
            "action": "calculate_stats",
            "params": {"field": "landuse_type"},
            "depends_on": ["step-1"]
        },
        {
            "id": "step-3",
            "description": "生成图表",
            "action": "create_chart",
            "params": {"type": "pie"},
            "depends_on": ["step-2"]
        },
        {
            "id": "step-4",
            "description": "导出报告",
            "action": "write_report",
            "params": {"format": "pdf"},
            "depends_on": ["step-3"]
        }
    ],
    "estimated_duration": "15m",
    "risks": ["数据可能缺失", "坐标系统不一致"],
    "success_criteria": [
        "生成PDF报告",
        "包含所有土地类型统计",
        "图表清晰可读"
    ]
}
```
