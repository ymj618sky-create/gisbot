"""
LLM记忆系统单元测试

测试LLM驱动的记忆合并功能
"""
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from core.agent.llm_memory import LLMMemoryStore


class TestLLMMemoryStore:
    """LLMMemoryStore核心功能测试"""

    @pytest.mark.asyncio
    async def test_consolidate_memory_empty(self, llm_memory_store):
        """测试空记忆合并"""
        # Given - 空记忆
        history_entry = "用户偏好使用Python进行GIS分析"
        current_memory = ""

        # When - 合并记忆
        result = await llm_memory_store.consolidate_memory(
            "test-session",
            history_entry,
            current_memory
        )

        # Then - 结果非空（直接使用history_entry）
        assert result is not None
        assert "用户偏好使用Python进行GIS分析" in result

    @pytest.mark.asyncio
    async def test_concurrent_consolidation_safe(self, llm_memory_store):
        """测试并发合并的安全性（不会导致冲突）"""
        # Given - 相同会话ID
        history_entry = "测试内容"
        current_memory = "现有记忆"

        # When - 并发执行两次合并
        task1 = asyncio.create_task(llm_memory_store.consolidate_memory(
            "test-session",
            history_entry,
            current_memory
        ))
        # 不等待第一个完成，立即开始第二个
        await asyncio.sleep(0.01)  # 确保第一个已经开始
        task2 = asyncio.create_task(llm_memory_store.consolidate_memory(
            "test-session",
            history_entry,
            current_memory
        ))

        # Then - 两个任务都能完成（锁机制确保顺序执行，不会崩溃）
        results = await asyncio.gather(task1, task2, return_exceptions=True)

        # 确保没有异常
        exceptions = [r for r in results if isinstance(r, Exception)]
        assert len(exceptions) == 0, f"Concurrent consolidation caused exceptions: {exceptions}"

        # 两个结果中至少有一个成功
        successful = [r for r in results if r is not None]
        assert len(successful) >= 1, "At least one consolidation should succeed"

    @pytest.mark.asyncio
    async def test_save_memory_auto_triggers_consolidation(self, llm_memory_store):
        """测试自动保存触发合并"""
        # Given - 新记忆内容
        memory_update = "用户偏好使用QGIS进行制图"

        # When - 保存记忆（auto模式）
        await llm_memory_store.save_memory(memory_update, source="auto")

        # Then - 追加到历史记录
        history = llm_memory_store.history_file.read_text(encoding="utf-8")
        assert "用户偏好使用QGIS进行制图" in history
        assert "Memory Update" in history

    @pytest.mark.asyncio
    async def test_save_memory_manual_no_consolidation(self, llm_memory_store):
        """测试手动保存不触发合并"""
        # Given - 新记忆内容
        memory_update = "手动添加的备注"

        # When - 保存记忆（manual模式）
        await llm_memory_store.save_memory(memory_update, source="manual")

        # Then - 追加到历史记录
        history = llm_memory_store.history_file.read_text(encoding="utf-8")
        assert "手动添加的备注" in history

    def test_build_consolidation_prompt(self, llm_memory_store):
        """测试合并提示构建"""
        # Given - 历史条目和当前记忆
        history_entry = "用户使用ArcPy"
        current_memory = "# 用户偏好\n- 使用Python"

        # When - 构建提示
        prompt = llm_memory_store._build_consolidation_prompt(
            history_entry,
            current_memory
        )

        # Then - 提示包含必要内容
        assert "用户使用ArcPy" in prompt
        assert "使用Python" in prompt
        assert "合并" in prompt.lower() or "consolidat" in prompt.lower()

    def test_is_consolidating(self, llm_memory_store):
        """测试合并状态检查"""
        # Then - 初始状态不合并
        assert not llm_memory_store.is_consolidating("test-session")
