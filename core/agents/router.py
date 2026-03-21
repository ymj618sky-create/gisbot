"""
统一 Agent 路由器
智能地将用户请求路由到最合适的 Agent
"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from core.agents.base import BaseAgent, AgentResponse
from core.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)


@dataclass
class RouteDecision:
    """路由决策结果"""
    agent: Optional[BaseAgent]
    confidence: float
    reason: str


class AgentRouter:
    """统一 Agent 路由器

    负责将用户请求智能路由到最合适的 Agent。
    支持多级路由策略：
    1. 关键词匹配（快速路由）
    2. 意图识别（基于 LLM）
    3. 能力匹配（基于 Agent 能力声明）
    """

    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or AgentRegistry()

    async def route(
        self,
        user_query: str,
        data_paths: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> RouteDecision:
        """路由请求到最合适的 Agent

        Args:
            user_query: 用户查询
            data_paths: 数据文件路径列表
            context: 上下文信息
            session_id: 会话 ID

        Returns:
            RouteDecision: 路由决策结果
        """
        # 检查是否有数据文件
        has_data = data_paths and len(data_paths) > 0

        # 快速路由：基于关键词
        decision = self._route_by_keywords(user_query, has_data)
        if decision.agent:
            return decision

        # 智能路由：基于能力匹配
        decision = await self._route_by_capabilities(user_query, context, has_data)
        if decision.agent:
            return decision

        # 兜底路由：使用通用 Agent
        general_agent = self._get_fallback_agent()
        if general_agent:
            return RouteDecision(
                agent=general_agent,
                confidence=0.3,
                reason="Using fallback general agent"
            )

        # 没有可用的 Agent
        return RouteDecision(
            agent=None,
            confidence=0.0,
            reason="No available agents"
        )

    def _route_by_keywords(self, query: str, has_data: bool) -> RouteDecision:
        """基于关键词快速路由

        Args:
            query: 用户查询
            has_data: 是否有数据文件

        Returns:
            RouteDecision: 路由决策
        """
        query_lower = query.lower()

        # GIS 相关关键词
        gis_keywords = [
            "地图", "gis", "空间", "地理", "坐标", "缓冲区",
            "buffer", "地理信息系统", "投影", "坐标系", "crs",
            "矢量", "栅格", "shp", "geojson", "kml",
            "空间分析", "地图制作", " choropleth", "热力图"
        ]

        # 数据处理关键词
        data_keywords = [
            "数据", "csv", "excel", "导入", "导出",
            "清洗", "转换", "格式", "解析"
        ]

        # 代码生成关键词
        code_keywords = [
            "代码", "生成", "python", "写代码",
            "编程", "函数", "脚本"
        ]

        # 判断查询类型
        has_gis_keywords = any(kw in query_lower for kw in gis_keywords)
        has_data_keywords = any(kw in query_lower for kw in data_keywords)
        has_code_keywords = any(kw in query_lower for kw in code_keywords)

        # 优先级：GIS > 数据处理 > 代码 > 通用
        if has_gis_keywords or has_data:
            gis_agent = self._get_best_gis_agent()
            if gis_agent:
                return RouteDecision(
                    agent=gis_agent,
                    confidence=0.9,
                    reason="GIS keywords detected" if has_gis_keywords else "Data files provided"
                )

        if has_data_keywords:
            data_agent = self._get_best_data_agent()
            if data_agent:
                return RouteDecision(
                    agent=data_agent,
                    confidence=0.85,
                    reason="Data processing keywords detected"
                )

        if has_code_keywords:
            code_agent = self._get_best_code_agent()
            if code_agent:
                return RouteDecision(
                    agent=code_agent,
                    confidence=0.8,
                    reason="Code generation keywords detected"
                )

        return RouteDecision(
            agent=None,
            confidence=0.0,
            reason="No matching keywords"
        )

    async def _route_by_capabilities(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        has_data: bool
    ) -> RouteDecision:
        """基于 Agent 能力进行智能路由

        Args:
            query: 用户查询
            context: 上下文信息
            has_data: 是否有数据文件

        Returns:
            RouteDecision: 路由决策
        """
        best_agent = await self.registry.route(query, context, require_data=has_data)

        if best_agent:
            return RouteDecision(
                agent=best_agent,
                confidence=0.7,
                reason=f"Matched capabilities of {best_agent.name}"
            )

        return RouteDecision(
            agent=None,
            confidence=0.0,
            reason="No capability match"
        )

    def _get_best_gis_agent(self) -> Optional[BaseAgent]:
        """获取最佳 GIS Agent"""
        agents = self.registry.get_agents_by_type("gis")
        return agents[0] if agents else None

    def _get_best_data_agent(self) -> Optional[BaseAgent]:
        """获取最佳数据处理 Agent"""
        agents = self.registry.get_agents_by_type("data")
        return agents[0] if agents else None

    def _get_best_code_agent(self) -> Optional[BaseAgent]:
        """获取最佳代码生成 Agent"""
        agents = self.registry.get_agents_by_type("code")
        return agents[0] if agents else None

    def _get_fallback_agent(self) -> Optional[BaseAgent]:
        """获取兜底通用 Agent"""
        agents = self.registry.get_agents_by_type("general")
        return agents[0] if agents else None


# 全局路由器实例
_router: Optional[AgentRouter] = None


def get_router() -> AgentRouter:
    """获取全局路由器（单例模式）

    Returns:
        AgentRouter 实例
    """
    global _router
    if _router is None:
        _router = AgentRouter()
    return _router


def reset_router() -> None:
    """重置路由器（主要用于测试）"""
    global _router
    _router = None