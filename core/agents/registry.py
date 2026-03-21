"""
Agent 注册表
管理所有可用的 Agent 实例
"""
import logging
from typing import Dict, List, Optional, Any
from collections import defaultdict

from core.agents.base import BaseAgent, AgentType, AgentCapability

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Agent 注册表

    管理所有 Agent 实例的注册、查询和路由。
    """

    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
        self._agents_by_type: Dict[AgentType, List[BaseAgent]] = defaultdict(list)
        self._agent_ranking: Dict[str, int] = {}  # Agent 使用频率统计

    def register(self, agent: BaseAgent) -> None:
        """注册 Agent

        Args:
            agent: Agent 实例
        """
        agent_key = f"{agent.agent_type.value}:{agent.name}"

        if agent_key in self._agents:
            logger.warning(f"Agent {agent_key} already registered, overwriting")

        self._agents[agent_key] = agent
        self._agents_by_type[agent.agent_type].append(agent)
        self._agent_ranking[agent_key] = 0

        logger.info(f"Registered agent: {agent_key} v{agent.version} with {len(agent.capabilities)} capabilities")

    def unregister(self, agent_type: AgentType, name: str) -> bool:
        """注销 Agent

        Args:
            agent_type: Agent 类型
            name: Agent 名称

        Returns:
            是否成功注销
        """
        agent_key = f"{agent_type.value}:{name}"

        if agent_key in self._agents:
            agent = self._agents[agent_key]
            self._agents_by_type[agent.agent_type].remove(agent)
            del self._agents[agent_key]
            del self._agent_ranking[agent_key]

            logger.info(f"Unregistered agent: {agent_key}")
            return True

        logger.warning(f"Agent not found: {agent_key}")
        return False

    def get_agent(self, agent_type: AgentType, name: str) -> Optional[BaseAgent]:
        """获取指定 Agent

        Args:
            agent_type: Agent 类型
            name: Agent 名称

        Returns:
            Agent 实例或 None
        """
        agent_key = f"{agent_type.value}:{name}"
        return self._agents.get(agent_key)

    def get_all_agents(self) -> List[BaseAgent]:
        """获取所有已注册的 Agent

        Returns:
            Agent 列表
        """
        return list(self._agents.values())

    def get_agents_by_type(self, agent_type: AgentType) -> List[BaseAgent]:
        """获取指定类型的所有 Agent

        Args:
            agent_type: Agent 类型

        Returns:
            Agent 列表
        """
        return self._agents_by_type.get(agent_type, [])

    async def route(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None,
        require_data: bool = False
    ) -> Optional[BaseAgent]:
        """路由请求到最合适的 Agent

        Args:
            user_query: 用户查询
            context: 上下文信息
            require_data: 是否需要 Agent 支持数据处理

        Returns:
            最合适的 Agent 实例，如果没有合适的则返回 None
        """
        best_agent: Optional[BaseAgent] = None
        best_score = 0.0

        for agent in self._agents.values():
            # 如果需要数据处理能力，跳过不支持数据的 Agent
            if require_data:
                has_data_capability = any(c.requires_data for c in agent.capabilities)
                if not has_data_capability:
                    continue

            # 获取 Agent 处理该请求的置信度
            score = await agent.can_handle(user_query, context)

            # 考虑使用频率（增加一些探索性）
            usage_factor = 1.0
            agent_key = f"{agent.agent_type.value}:{agent.name}"
            if agent_key in self._agent_ranking:
                usage_factor = 1.0 - (self._agent_ranking[agent_key] * 0.01)

            final_score = score * usage_factor

            if final_score > best_score:
                best_score = final_score
                best_agent = agent

        if best_agent:
            logger.info(f"Routed query to agent: {best_agent.agent_type.value}:{best_agent.name} (score={best_score:.2f})")
        else:
            logger.warning(f"No suitable agent found for query: {user_query[:50]}...")

        return best_agent

    def record_usage(self, agent: BaseAgent) -> None:
        """记录 Agent 使用情况

        Args:
            agent: Agent 实例
        """
        agent_key = f"{agent.agent_type.value}:{agent.name}"
        if agent_key in self._agent_ranking:
            self._agent_ranking[agent_key] += 1

    def get_all_capabilities(self) -> List[AgentCapability]:
        """获取所有 Agent 的能力列表

        Returns:
            能力列表
        """
        capabilities = []
        for agent in self._agents.values():
            capabilities.extend(agent.capabilities)
        return capabilities

    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息

        Returns:
            统计信息字典
        """
        return {
            "total_agents": len(self._agents),
            "agents_by_type": {
                agent_type.value: len(agents)
                for agent_type, agents in self._agents_by_type.items()
            },
            "agent_ranking": dict(sorted(
                self._agent_ranking.items(),
                key=lambda x: x[1],
                reverse=True
            ))
        }


# 全局 Agent 注册表实例
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """获取全局 Agent 注册表（单例模式）

    Returns:
        AgentRegistry 实例
    """
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry


def reset_registry() -> None:
    """重置注册表（主要用于测试）"""
    global _registry
    _registry = None