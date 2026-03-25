"""
pytest fixtures for autonomous skills tests
"""
import pytest
from skills.autonomous.task_planning import TaskPlanner


@pytest.fixture
def task_planner():
    """创建TaskPlanner实例用于测试"""
    return TaskPlanner(available_tools=[
        "read_data",
        "analyze",
        "generate_output",
        "create_chart",
        "write_report"
    ])
