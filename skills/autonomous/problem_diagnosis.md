# Problem Diagnosis Skill

## 概述

问题诊断技能帮助AI Agent主动发现、分析和解决执行过程中遇到的问题。

## 工作流程

1. **检测异常** - 识别错误、警告和异常情况
2. **分析原因** - 追溯问题根源
3. **提出方案** - 生成可能的解决方案
4. **执行修复** - 自动应用最佳方案
5. **验证结果** - 确认问题已解决

## 问题分类

### 数据问题
- 文件不存在
- 格式不支持
- 坐标系不匹配
- 数据缺失或损坏

### 工具问题
- 工具不可用
- 参数错误
- 执行失败
- 资源不足

### 逻辑问题
- 依赖关系错误
- 执行顺序不当
- 结果不符合预期

## 输入格式

```python
{
    "error": {
        "type": "error_type",
        "message": "错误信息",
        "context": {...}
    },
    "execution_history": [...],
    "state": "当前状态"
}
```

## 输出格式

```python
{
    "diagnosis": {
        "problem_type": "问题类型",
        "root_cause": "根本原因",
        "severity": "critical | high | medium | low"
    },
    "solutions": [
        {
            "approach": "解决方案描述",
            "steps": [...],
            "confidence": 0.9,
            "estimated_effort": "5m"
        }
    ],
    "recommended": 0,
    "prevention": "预防措施"
}
```

## 示例

### 输入
```python
{
    "error": {
        "type": "CRSError",
        "message": "坐标系统不匹配: EPSG:4326 vs EPSG:4528"
    },
    "execution_history": [
        "读取数据A (EPSG:4326)",
        "读取数据B (EPSG:4528)",
        "尝试叠加分析"
    ]
}
```

### 输出
```python
{
    "diagnosis": {
        "problem_type": "CRSMismatch",
        "root_cause": "数据A使用WGS84坐标系，数据B使用CGCS2000坐标系，无法直接叠加",
        "severity": "high"
    },
    "solutions": [
        {
            "approach": "将数据A转换为EPSG:4528",
            "steps": [
                "使用reproject工具转换数据A",
                "使用转换后的数据进行叠加分析"
            ],
            "confidence": 0.95,
            "estimated_effort": "2m"
        },
        {
            "approach": "将数据B转换为EPSG:4326",
            "steps": [
                "使用reproject工具转换数据B",
                "使用转换后的数据进行叠加分析"
            ],
            "confidence": 0.9,
            "estimated_effort": "2m"
        }
    ],
    "recommended": 0,
    "prevention": "在读取数据时统一检查并转换坐标系"
}
```

## 实现要点

1. 建立错误知识库
2. 使用LLM分析错误模式
3. 生成多个解决方案并评估
4. 自动执行最佳方案
5. 记录解决方案到记忆
