# Result Verification Skill

## 概述

结果验证技能帮助AI Agent确保执行结果的正确性、完整性和有效性。

## 验证维度

### 数据完整性
- 文件是否创建
- 数据量是否合理
- 字段是否完整

### 数据正确性
- 坐标系是否正确
- 数值范围是否合理
- 几何是否有效

### 结果有效性
- 是否符合预期
- 是否满足业务要求
- 是否可复现

## 工作流程

1. **定义验证标准** - 基于任务目标确定验证点
2. **执行验证** - 逐一检查每个验证点
3. **生成报告** - 记录验证结果
4. **处理问题** - 对失败的验证提出修复方案

## 输入格式

```python
{
    "result": {
        "type": "file | data | output",
        "path": "结果路径",
        "metadata": {...}
    },
    "expectations": {
        "format": "预期格式",
        "crs": "预期坐标系",
        "features": "预期要素数量",
        "fields": ["必填字段"]
    },
    "task_context": "任务上下文"
}
```

## 输出格式

```python
{
    "overall": "passed | failed | partial",
    "checks": [
        {
            "check": "检查项名称",
            "status": "passed | failed | warning",
            "details": "详细结果",
            "expected": "预期值",
            "actual": "实际值"
        }
    ],
    "summary": {
        "passed": 5,
        "failed": 1,
        "warning": 2
    },
    "issues": [...],
    "recommendations": [...]
}
```

## 示例

### 输入
```python
{
    "result": {
        "type": "data",
        "path": "workspace/output/landuse_stats.csv"
    },
    "expectations": {
        "format": "csv",
        "rows": ">0",
        "columns": ["type", "area", "count"]
    }
}
```

### 输出
```python
{
    "overall": "partial",
    "checks": [
        {
            "check": "文件存在性",
            "status": "passed",
            "details": "文件存在于 workspace/output/landuse_stats.csv"
        },
        {
            "check": "文件格式",
            "status": "passed",
            "details": "CSV格式正确"
        },
        {
            "check": "行数验证",
            "status": "passed",
            "details": "共15行数据",
            "expected": ">0",
            "actual": 15
        },
        {
            "check": "列验证",
            "status": "failed",
            "details": "缺少count列",
            "expected": ["type", "area", "count"],
            "actual": ["type", "area"]
        }
    ],
    "summary": {
        "passed": 3,
        "failed": 1,
        "warning": 0
    },
    "issues": [
        "输出结果缺少count列"
    ],
    "recommendations": [
        "重新执行统计，确保包含count字段"
    ]
}
```

## 实现要点

1. 建立验证规则库
2. 支持自定义验证函数
3. 生成详细的验证报告
4. 对失败项提出具体修复建议
5. 学习新的验证规则
