"""
Task Planning Skill Implementation

任务规划技能实现，将复杂任务分解为可执行的子任务
"""
import uuid
from typing import Dict, List, Any


class TaskPlanner:
    """
    任务规划器

    负责将用户任务分解为可执行的步骤，生成执行计划
    """

    def __init__(self, available_tools: List[str] | None = None):
        """
        初始化任务规划器

        Args:
            available_tools: 可用工具列表
        """
        self._available_tools = available_tools or []

    def plan(self, task: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """
        规划任务

        Args:
            task: 任务描述
            context: 上下文信息

        Returns:
            执行计划
        """
        task_id = str(uuid.uuid4())[:8]

        # 分析任务类型
        task_type = self._analyze_task_type(task)

        # 生成步骤
        steps = self._generate_steps(task, task_type)

        # 估算耗时
        duration = self._estimate_duration(steps)

        # 识别风险
        risks = self._identify_risks(task, steps)

        # 定义成功标准
        success_criteria = self._define_success_criteria(task, steps)

        return {
            "task_id": task_id,
            "summary": self._generate_summary(task, task_type),
            "task_type": task_type,
            "steps": steps,
            "estimated_duration": duration,
            "risks": risks,
            "success_criteria": success_criteria,
        }

    def _analyze_task_type(self, task: str) -> str:
        """分析任务类型"""
        task_lower = task.lower()

        if any(word in task_lower for word in ["读取", "加载", "import", "read", "load"]):
            return "data_import"
        elif any(word in task_lower for word in ["分析", "计算", "analyze", "calculate"]):
            return "analysis"
        elif any(word in task_lower for word in ["图表", "可视化", "chart", "plot", "visualize"]):
            return "visualization"
        elif any(word in task_lower for word in ["报告", "导出", "report", "export"]):
            return "reporting"
        elif "并" in task_lower or "和" in task_lower or "and" in task_lower:
            return "multi_step"
        else:
            return "general"

    def _generate_steps(self, task: str, task_type: str) -> List[Dict[str, Any]]:
        """生成执行步骤"""
        steps = []

        if task_type == "data_import":
            steps = [
                {
                    "id": "step-1",
                    "description": "读取数据文件",
                    "action": "read_data",
                    "params": {"path": self._extract_path(task)},
                    "depends_on": [],
                    "estimated_time": "1m"
                }
            ]
        elif task_type == "analysis":
            steps = [
                {
                    "id": "step-1",
                    "description": "读取数据",
                    "action": "read_data",
                    "params": {},
                    "depends_on": [],
                    "estimated_time": "1m"
                },
                {
                    "id": "step-2",
                    "description": "执行分析",
                    "action": "analyze",
                    "params": self._extract_analysis_params(task),
                    "depends_on": ["step-1"],
                    "estimated_time": "2m"
                }
            ]
        elif task_type == "multi_step":
            steps = [
                {
                    "id": "step-1",
                    "description": "读取数据",
                    "action": "read_data",
                    "params": {},
                    "depends_on": [],
                    "estimated_time": "1m"
                },
                {
                    "id": "step-2",
                    "description": "分析数据",
                    "action": "analyze",
                    "params": {},
                    "depends_on": ["step-1"],
                    "estimated_time": "2m"
                },
                {
                    "id": "step-3",
                    "description": "生成结果",
                    "action": "generate_output",
                    "params": {},
                    "depends_on": ["step-2"],
                    "estimated_time": "1m"
                }
            ]
        else:
            steps = [
                {
                    "id": "step-1",
                    "description": f"执行任务: {task}",
                    "action": "execute",
                    "params": {},
                    "depends_on": [],
                    "estimated_time": "5m"
                }
            ]

        return steps

    def _estimate_duration(self, steps: List[Dict[str, Any]]) -> str:
        """估算总耗时"""
        total_minutes = 0
        for step in steps:
            time_str = step.get("estimated_time", "0m")
            minutes = int(time_str.rstrip("m"))
            total_minutes += minutes

        return f"{total_minutes}m"

    def _identify_risks(self, task: str, steps: List[Dict[str, Any]]) -> List[str]:
        """识别潜在风险"""
        risks = []

        task_lower = task.lower()

        if "shp" in task_lower or "shapefile" in task_lower:
            risks.append("Shapefile需要配套的shx/dbf文件")

        if "未知" in task_lower or "unknown" in task_lower:
            risks.append("数据来源未知，可能存在质量问题")

        if len(steps) > 5:
            risks.append("步骤较多，执行时间可能超出预期")

        if not risks:
            return []

        return risks

    def _define_success_criteria(self, task: str, steps: List[Dict[str, Any]]) -> List[str]:
        """定义成功标准"""
        criteria = []

        task_lower = task.lower()

        if "报告" in task_lower or "report" in task_lower:
            criteria.append("生成报告文件")
        if "图表" in task_lower or "chart" in task_lower:
            criteria.append("生成可视化图表")
        if "分析" in task_lower or "analyze" in task_lower:
            criteria.append("分析结果符合预期")

        if not criteria:
            criteria.append("任务成功完成")

        return criteria

    def _generate_summary(self, task: str, task_type: str) -> str:
        """生成任务摘要"""
        type_names = {
            "data_import": "数据导入",
            "analysis": "数据分析",
            "visualization": "数据可视化",
            "reporting": "报告生成",
            "multi_step": "多步骤任务",
            "general": "通用任务"
        }
        type_name = type_names.get(task_type, "任务")

        return f"{type_name}: {task}"

    def _extract_path(self, task: str) -> Dict[str, str]:
        """从任务描述中提取路径"""
        # 简化实现，实际可以更智能
        if "." in task:
            # 尝试提取文件扩展名
            for ext in [".shp", ".gpkg", ".csv", ".tif"]:
                if ext in task.lower():
                    idx = task.lower().find(ext)
                    return {"path": f"workspace/data/{task[:idx+len(ext)]}"}
        return {"path": "workspace/data/input"}

    def _extract_analysis_params(self, task: str) -> Dict[str, Any]:
        """从任务描述中提取分析参数"""
        params = {}

        if "面积" in task or "area" in task.lower():
            params["calculation"] = "area"
        if "数量" in task or "count" in task.lower():
            params["calculation"] = "count"
        if "统计" in task or "stats" in task.lower():
            params["calculation"] = "statistics"

        return params
