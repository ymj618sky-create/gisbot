"""
通用对话 Agent
处理一般的对话、问答和辅助任务
"""
import logging
from typing import Dict, Any, Optional, List

from core.agents.base import BaseAgent, AgentType, AgentCapability, AgentResponse
from agent.llm_integration import get_llm

logger = logging.getLogger(__name__)


class GeneralAgent(BaseAgent):
    """通用对话 Agent

    处理非 GIS 相关的对话、问答、文本生成等通用任务。
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.GENERAL,
            name="general_conversation",
            version="1.0.0"
        )
        self._capabilities = self._init_capabilities()

    def _init_capabilities(self) -> List[AgentCapability]:
        """初始化能力列表"""
        return [
            AgentCapability(
                name="general_chat",
                description="通用对话和聊天",
                keywords=["你好", "hello", "hi", "聊天", "对话", "say"],
                priority=1
            ),
            AgentCapability(
                name="question_answering",
                description="回答一般问题",
                keywords=["问题", "问题", "什么是", "如何", "how", "what", "explain"],
                priority=2
            ),
            AgentCapability(
                name="text_generation",
                description="文本生成和摘要",
                keywords=["生成", "写", "写一段", "摘要", "总结", "generate", "summary"],
                priority=1
            ),
            AgentCapability(
                name="translation",
                description="文本翻译",
                keywords=["翻译", "translate", "翻译成"],
                priority=1
            ),
            AgentCapability(
                name="code_explanation",
                description="代码解释",
                keywords=["解释代码", "explain code", "代码说明"],
                priority=1
            )
        ]

    @property
    def capabilities(self) -> List[AgentCapability]:
        return self._capabilities

    async def can_handle(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> float:
        """判断是否能处理该请求"""
        # 检查关键词匹配
        keyword_score = self.matches_keywords(user_query)

        # 如果有关键词匹配，返回较高分数
        if keyword_score > 0:
            return keyword_score

        # 对于一般查询，总是返回一个基础分数
        # 这样 General Agent 可以作为兜底选项
        return 0.3

    async def execute(
        self,
        user_query: str,
        data_paths: List[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """执行任务"""
        try:
            logger.info(f"[GeneralAgent] Processing query: {user_query[:50]}...")

            # 使用 LLM 处理一般查询
            llm = get_llm()

            # 构建提示词
            system_prompt = """你是一个乐于助人的 AI 助手，专门处理一般的对话和问答。

你的能力包括：
1. 日常对话和聊天
2. 回答各种问题
3. 文本生成和摘要
4. 翻译
5. 代码解释

对于用户的问题，请提供准确、有帮助的回答。
如果涉及到 GIS 或空间数据分析，请建议用户使用相关的 GIS 分析工具。"""

            # 调用 LLM
            response_text = await llm.generate_chat_response(
                system_prompt=system_prompt,
                user_message=user_query,
                conversation_history=context.get("conversation_history") if context else None
            )

            return AgentResponse(
                success=True,
                content=response_text,
                status="completed",
                metadata={
                    "agent": self.name,
                    "agent_type": self.agent_type.value,
                    "version": self.version
                }
            )

        except Exception as e:
            logger.error(f"[GeneralAgent] Error processing query: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                content="抱歉，处理您的请求时出现了错误。",
                status="failed",
                errors=[str(e)]
            )

    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "version": self.version,
            "description": "通用对话 Agent，处理一般的对话、问答和辅助任务",
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description
                }
                for c in self.capabilities
            ]
        }


class CodeAgent(BaseAgent):
    """代码生成 Agent

    专门处理代码生成、代码审查、代码解释等任务。
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.CODE,
            name="code_generator",
            version="1.0.0"
        )
        self._capabilities = self._init_capabilities()

    def _init_capabilities(self) -> List[AgentCapability]:
        """初始化能力列表"""
        return [
            AgentCapability(
                name="code_generation",
                description="生成各种编程语言的代码",
                keywords=["生成代码", "写代码", "generate code", "写一个", "实现"],
                priority=2
            ),
            AgentCapability(
                name="code_explanation",
                description="解释代码逻辑",
                keywords=["解释代码", "explain", "这是什么代码"],
                priority=1
            ),
            AgentCapability(
                name="code_review",
                description="代码审查和优化建议",
                keywords=["代码审查", "优化", "review", "refactor"],
                priority=1
            ),
            AgentCapability(
                name="debug_help",
                description="调试帮助",
                keywords=["调试", "bug", "错误", "debug", "fix"],
                priority=1
            )
        ]

    @property
    def capabilities(self) -> List[AgentCapability]:
        return self._capabilities

    async def can_handle(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> float:
        """判断是否能处理该请求"""
        return self.matches_keywords(user_query)

    async def execute(
        self,
        user_query: str,
        data_paths: List[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """执行任务"""
        try:
            logger.info(f"[CodeAgent] Processing query: {user_query[:50]}...")

            llm = get_llm()

            system_prompt = """你是一个专业的代码助手，擅长各种编程语言的代码生成、解释和优化。

你的能力包括：
1. 根据需求生成高质量代码
2. 解释代码逻辑和原理
3. 提供代码审查和优化建议
4. 帮助调试和修复 bug

生成代码时，请：
- 添加必要的注释
- 遵循最佳实践
- 考虑边界情况
- 提供使用示例

如果用户请求涉及 GIS 或空间数据处理，请使用 geopandas、shapely 等 GIS 库。"""

            response_text = await llm.generate_chat_response(
                system_prompt=system_prompt,
                user_message=user_query,
                conversation_history=context.get("conversation_history") if context else None
            )

            return AgentResponse(
                success=True,
                content=response_text,
                status="completed",
                metadata={
                    "agent": self.name,
                    "agent_type": self.agent_type.value,
                    "version": self.version
                }
            )

        except Exception as e:
            logger.error(f"[CodeAgent] Error: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                content="抱歉，生成代码时出现了错误。",
                status="failed",
                errors=[str(e)]
            )

    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "version": self.version,
            "description": "代码生成 Agent，处理代码生成、解释和优化",
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description
                }
                for c in self.capabilities
            ]
        }