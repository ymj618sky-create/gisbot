"""
LLM驱动的记忆系统

支持智能记忆合并、异步处理和增量更新
参考nanobot的记忆系统设计
"""
import asyncio
import weakref
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.agent.memory import MemoryStore


class LLMMemoryStore(MemoryStore):
    """
    LLM驱动的记忆存储

    扩展基础MemoryStore，添加：
    - 智能记忆合并（使用LLM）
    - 异步合并（不阻塞用户交互）
    - 防重复合并机制
    """

    def __init__(self, workspace: Path, provider):
        """
        初始化LLM记忆存储

        Args:
            workspace: 工作目录
            provider: LLM提供商，用于智能合并
        """
        super().__init__(workspace)
        self._provider = provider
        self._consolidating: set[str] = set()  # 正在合并的会话ID
        self._consolidation_locks: weakref.WeakValueDictionary[str, asyncio.Lock] = weakref.WeakValueDictionary()
        self._consolidation_lock = asyncio.Lock()  # 保护consolidating集合和lock字典

    async def consolidate_memory(
        self,
        session_id: str,
        history_entry: str,
        current_memory: str
    ) -> Optional[str]:
        """
        使用LLM智能合并记忆

        Args:
            session_id: 会话ID（用于防重复）
            history_entry: 历史条目（新内容）
            current_memory: 当前记忆内容

        Returns:
            合并后的记忆内容，合并中返回None
        """
        # 获取或创建会话特定的锁（受全局锁保护）
        async with self._consolidation_lock:
            # 如果正在合并，立即返回
            if session_id in self._consolidating:
                return None

            # 标记为正在合并
            self._consolidating.add(session_id)

            # 获取或创建锁
            lock = self._consolidation_locks.get(session_id)
            if lock is None:
                lock = asyncio.Lock()
                self._consolidation_locks[session_id] = lock

        # 执行合并（不持有全局锁）
        async with lock:
            try:
                # 使用LLM进行智能合并
                consolidated = await self._llm_consolidate(
                    history_entry,
                    current_memory
                )
                self.write_long_term(consolidated)
                return consolidated
            finally:
                # 清理标记
                self._consolidating.discard(session_id)

    async def _llm_consolidate(
        self,
        history_entry: str,
        current_memory: str
    ) -> str:
        """
        调用LLM执行智能合并

        Args:
            history_entry: 历史条目
            current_memory: 当前记忆

        Returns:
            合并后的记忆
        """
        if not current_memory:
            # 如果没有现有记忆，直接使用历史条目
            return history_entry

        # 构建合并提示
        prompt = self._build_consolidation_prompt(
            history_entry,
            current_memory
        )

        try:
            # 调用LLM
            response = await self._provider.chat(
                messages=[
                    {"role": "system", "content": "你是一个专业的记忆整理助手，负责合并和更新长期记忆。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # 低温度确保稳定性
            )

            # 提取合并结果
            if response and "content" in response:
                return response["content"]
            return current_memory

        except Exception as e:
            # 合并失败，保持原有记忆
            print(f"记忆合并失败: {e}")
            return current_memory

    def _build_consolidation_prompt(
        self,
        history_entry: str,
        current_memory: str
    ) -> str:
        """
        构建记忆合并提示

        Args:
            history_entry: 历史条目
            current_memory: 当前记忆

        Returns:
            合并提示文本
        """
        return f"""请合并以下两段内容，生成更精炼的长期记忆。

当前记忆：
---
{current_memory}
---

新内容（历史条目）：
---
{history_entry}
---

要求：
1. 提取新内容中的关键信息和事实
2. 避免重复，整合相似信息
3. 保持记忆的结构清晰（使用标题、列表等）
4. 保留重要细节，去除冗余内容
5. 输出Markdown格式

合并后的记忆："""

    async def save_memory(self, memory_update: str, source: str = "auto") -> None:
        """
        保存记忆更新

        Args:
            memory_update: 记忆更新内容
            source: 更新来源（auto/manual）
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"# Memory Update ({source}) - {timestamp}\n\n{memory_update}"

        # 追加到历史记录
        self.append_history(entry)

        # 如果来源是auto，触发智能合并
        if source == "auto":
            # 获取当前记忆
            current_memory = self.read_long_term()
            # 异步合并（不等待完成）
            asyncio.create_task(self.consolidate_memory(
                f"auto-{timestamp}",
                memory_update,
                current_memory
            ))

    def is_consolidating(self, session_id: str) -> bool:
        """检查指定会话是否正在合并记忆"""
        return session_id in self._consolidating
