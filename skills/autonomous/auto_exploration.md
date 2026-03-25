# Auto Exploration Skill

## 概述

自主探索技能帮助AI Agent主动发现数据、工具和解决方案，而不是被动等待用户指定。

## 工作流程

1. **扫描环境** - 探索工作目录和可用资源
2. **识别数据** - 发现可用的GIS数据文件
3. **评估工具** - 检查可用的处理工具
4. **提出建议** - 基于发现生成可行的分析方案

## 探索模式

### 目录探索
- 扫描workspace/data目录
- 识别支持的文件格式
- 按类型分组数据

### 工具探索
- 列出已注册的工具
- 按功能分类
- 评估能力

### 数据探索
- 读取文件元数据
- 检查坐标系
- 评估数据质量

## 输入格式

```python
{
    "mode": "workspace" | "tools" | "data",
    "path": "可选路径",
    "filters": {
        "file_types": [...],
        "crs": "EPSG:4528"
    }
}
```

## 输出格式

```python
{
    "mode": "探索模式",
    "discoveries": [...],
    "suggestions": [...],
    "warnings": [...]
}
```

## 示例

### 输入
```python
{
    "mode": "data",
    "path": "workspace/data"
}
```

### 输出
```python
{
    "mode": "data",
    "discoveries": [
        {
            "type": "vector",
            "path": "workspace/data/landuse.shp",
            "features": 1523,
            "fields": ["id", "type", "area"],
            "crs": "EPSG:4528"
        },
        {
            "type": "raster",
            "path": "workspace/data/dem.tif",
            "size": "1000x1000",
            "crs": "EPSG:4528"
        }
    ],
    "suggestions": [
        "可以分析landuse类型的空间分布",
        "DEM数据可用于地形分析",
        "两个数据CRS一致，可直接叠加"
    ],
    "warnings": [
        "landuse数据缺少坐标系定义信息",
        "DEM数据可能需要重采样"
    ]
}
```

## 实现要点

1. 使用Glob工具扫描目录
2. 使用file_analysis工具获取元数据
3. 智能推断数据用途
4. 提供可执行的建议
