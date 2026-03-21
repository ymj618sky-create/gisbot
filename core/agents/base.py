"""
核心 Agent 基类接口
所有 Agent 必须实现此接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class AgentType(Enum):
    """Agent 类型"""
    GENERAL = "general"           # 通用对话 Agent
    GIS = "gis"                   # GIS 分析 Agent
    DATA = "data"                 # 数据处理 Agent
    CODE = "code"                 # 代码生成 Agent
    RESEARCH = "research"         # 研究分析 Agent


@dataclass
class AgentCapability:
    """Agent 能力描述"""
    name: str                     # 能力名称
    description: str              # 能力描述
    keywords: List[str]           # 触发关键词列表
    requires_data: bool = False   # 是否需要数据文件
    priority: int = 0             # 优先级（越高越优先）


@dataclass
class AgentResponse:
    """Agent 响应"""
    success: bool
    content: str
    data: Optional[Dict[str, Any]] = None
    status: str = "completed"     # completed, failed, in_progress
    errors: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """Agent 基类

    所有 Agent 必须继承此类并实现抽象方法。
    """

    def __init__(self, agent_type: AgentType, name: str, version: str = "1.0.0"):
        self.agent_type = agent_type
        self.name = name
        self.version = version
        self._capabilities: List[AgentCapability] = []

    @property
    @abstractmethod
    def capabilities(self) -> List[AgentCapability]:
        """获取 Agent 能力列表"""
        pass

    @abstractmethod
    async def can_handle(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> float:
        """判断是否能处理该请求

        返回一个 0-1 之间的置信度分数：
        - 0: 完全不能处理
        - 0.5: 可能可以处理
        - 1.0: 确定可以处理

        Args:
            user_query: 用户查询
            context: 上下文信息

        Returns:
            置信度分数 (0-1)
        """
        pass

    @abstractmethod
    async def execute(
        self,
        user_query: str,
        data_paths: List[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """执行 Agent 任务

        Args:
            user_query: 用户查询
            data_paths: 数据文件路径列表
            context: 上下文信息
            session_id: 会话 ID（用于实时推送状态）

        Returns:
            AgentResponse: 执行结果
        """
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        pass

    def matches_keywords(self, query: str) -> float:
        """检查查询是否匹配关键词

        Args:
            query: 用户查询

        Returns:
            匹配分数 (0-1)
        """
        query_lower = query.lower()
        for capability in self.capabilities:
            for keyword in capability.keywords:
                if keyword.lower() in query_lower:
                    return 0.8  # 关键词匹配，返回较高分数
        return 0.0