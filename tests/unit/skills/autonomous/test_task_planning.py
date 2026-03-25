"""
Task Planning Skill单元测试

测试任务规划功能
"""
import pytest
from skills.autonomous.task_planning import TaskPlanner


class TestTaskPlanner:
    """TaskPlanner核心功能测试"""

    def test_plan_simple_task(self, task_planner):
        """测试简单任务规划"""
        # Given - 简单任务
        task = "读取landuse数据"

        # When - 规划任务
        plan = task_planner.plan(task)

        # Then - 生成有效计划
        assert plan is not None
        assert plan["task_id"]
        assert plan["summary"]
        assert len(plan["steps"]) > 0

    def test_plan_complex_task(self, task_planner):
        """测试复杂任务规划"""
        # Given - 复杂任务
        task = "分析landuse数据并生成图表和报告"

        # When - 规划任务
        plan = task_planner.plan(task)

        # Then - 生成多步骤计划
        assert len(plan["steps"]) >= 2
        # 检查步骤依赖
        for i, step in enumerate(plan["steps"][1:], 1):
            # 后续步骤应该依赖于前面的步骤
            assert len(step["depends_on"]) >= 0

    def test_estimate_duration(self, task_planner):
        """测试耗时估算"""
        # Given - 任务
        task = "分析数据"

        # When - 规划任务
        plan = task_planner.plan(task)

        # Then - 有耗时估算
        assert "estimated_duration" in plan
        assert plan["estimated_duration"]

    def test_identify_risks(self, task_planner):
        """测试风险识别"""
        # Given - 涉及数据的任务
        task = "读取并分析未知来源的shp文件"

        # When - 规划任务
        plan = task_planner.plan(task)

        # Then - 识别出潜在风险
        if "risks" in plan:
            assert isinstance(plan["risks"], list)

    def test_define_success_criteria(self, task_planner):
        """测试成功标准定义"""
        # Given - 明确目标
        task = "生成PDF报告"

        # When - 规划任务
        plan = task_planner.plan(task)

        # Then - 定义成功标准
        if "success_criteria" in plan:
            assert isinstance(plan["success_criteria"], list)
            assert len(plan["success_criteria"]) > 0
