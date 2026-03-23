"""
Project Memory - Project-specific memory and context.

项目记忆系统功能：
1. 项目事实记忆 - 存储项目中学习到的重要信息
2. 项目偏好设置 - 项目特定的配置和偏好
3. 项目工作流记录 - 常用操作流程
4. 项目关联文档 - 重要文档和知识库
5. 项目统计信息 - 数据处理历史和结果摘要
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
from datetime import datetime
import uuid


@dataclass
class ProjectFact:
    """项目事实"""
    id: str
    content: str
    category: str  # 例如: data, workflow, issue, solution
    importance: int = 1  # 1-5，重要性评分
    source: str = "user"  # user, system, tool
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "category": self.category,
            "importance": self.importance,
            "source": self.source,
            "created_at": self.created_at,
            "tags": self.tags
        }


@dataclass
class ProjectPreference:
    """项目偏好设置"""
    id: str
    key: str
    value: Any
    description: str = ""
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "updated_at": self.updated_at
        }


@dataclass
class ProjectWorkflow:
    """项目工作流"""
    id: str
    name: str
    description: str
    steps: List[Dict[str, Any]]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "created_at": self.created_at,
            "last_used": self.last_used
        }


@dataclass
class ProjectStats:
    """项目统计"""
    total_sessions: int = 0
    total_messages: int = 0
    tool_usage: Dict[str, int] = field(default_factory=dict)
    data_files: List[str] = field(default_factory=list)
    output_files: List[str] = field(default_factory=list)
    last_activity: str = ""

    def to_dict(self) -> dict:
        return {
            "total_sessions": self.total_sessions,
            "total_messages": self.total_messages,
            "tool_usage": self.tool_usage,
            "data_files": self.data_files,
            "output_files": self.output_files,
            "last_activity": self.last_activity
        }


class ProjectMemory:
    """项目记忆系统"""

    def __init__(self, project_id: str, storage_dir: Path):
        self.project_id = project_id
        self.storage_dir = storage_dir / project_id / ".memory"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self.facts: List[ProjectFact] = []
        self.preferences: Dict[str, ProjectPreference] = {}
        self.workflows: List[ProjectWorkflow] = []
        self.stats: ProjectStats = ProjectStats()

        # 加载持久化数据
        self._load()

    def _load(self):
        """加载记忆数据"""
        # 加载事实
        facts_file = self.storage_dir / "facts.json"
        if facts_file.exists():
            with open(facts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.facts = [ProjectFact(**item) for item in data]

        # 加载偏好
        prefs_file = self.storage_dir / "preferences.json"
        if prefs_file.exists():
            with open(prefs_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.preferences = {
                    k: ProjectPreference(**v) for k, v in data.items()
                }

        # 加载工作流
        workflows_file = self.storage_dir / "workflows.json"
        if workflows_file.exists():
            with open(workflows_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.workflows = [ProjectWorkflow(**item) for item in data]

        # 加载统计
        stats_file = self.storage_dir / "stats.json"
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.stats = ProjectStats(**data)

    def _save(self):
        """保存记忆数据"""
        # 保存事实
        facts_file = self.storage_dir / "facts.json"
        with open(facts_file, 'w', encoding='utf-8') as f:
            json.dump([f.to_dict() for f in self.facts], f, indent=2, ensure_ascii=False)

        # 保存偏好
        prefs_file = self.storage_dir / "preferences.json"
        with open(prefs_file, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.preferences.items()},
                f, indent=2, ensure_ascii=False
            )

        # 保存工作流
        workflows_file = self.storage_dir / "workflows.json"
        with open(workflows_file, 'w', encoding='utf-8') as f:
            json.dump([w.to_dict() for w in self.workflows], f, indent=2, ensure_ascii=False)

        # 保存统计
        stats_file = self.storage_dir / "stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats.to_dict(), f, indent=2, ensure_ascii=False)

    # ============ 事实记忆 ============

    def add_fact(
        self,
        content: str,
        category: str = "general",
        importance: int = 1,
        source: str = "user",
        tags: List[str] = None
    ) -> ProjectFact:
        """添加事实"""
        fact = ProjectFact(
            id=str(uuid.uuid4()),
            content=content,
            category=category,
            importance=importance,
            source=source,
            tags=tags or []
        )
        self.facts.append(fact)
        self._save()
        return fact

    def get_facts(
        self,
        category: Optional[str] = None,
        min_importance: int = 0,
        limit: int = 50
    ) -> List[ProjectFact]:
        """获取事实"""
        facts = self.facts

        if category:
            facts = [f for f in facts if f.category == category]

        facts = [f for f in facts if f.importance >= min_importance]
        facts = sorted(facts, key=lambda x: (x.importance, x.created_at), reverse=True)

        return facts[:limit]

    def search_facts(self, query: str, limit: int = 10) -> List[ProjectFact]:
        """搜索事实"""
        query_lower = query.lower()
        results = []

        for fact in self.facts:
            # 搜索内容、分类、标签
            search_text = f"{fact.content} {fact.category} {' '.join(fact.tags)}".lower()
            if query_lower in search_text:
                results.append(fact)
                if len(results) >= limit:
                    break

        # 按重要性排序
        results.sort(key=lambda x: x.importance, reverse=True)
        return results

    def delete_fact(self, fact_id: str) -> bool:
        """删除事实"""
        for i, fact in enumerate(self.facts):
            if fact.id == fact_id:
                del self.facts[i]
                self._save()
                return True
        return False

    # ============ 偏好设置 ============

    def set_preference(self, key: str, value: Any, description: str = ""):
        """设置偏好"""
        pref = ProjectPreference(
            id=str(uuid.uuid4()),
            key=key,
            value=value,
            description=description
        )
        self.preferences[key] = pref
        self._save()
        return pref

    def get_preference(self, key: str, default: Any = None) -> Any:
        """获取偏好"""
        if key in self.preferences:
            return self.preferences[key].value
        return default

    def get_all_preferences(self) -> Dict[str, ProjectPreference]:
        """获取所有偏好"""
        return self.preferences.copy()

    def delete_preference(self, key: str) -> bool:
        """删除偏好"""
        if key in self.preferences:
            del self.preferences[key]
            self._save()
            return True
        return False

    # ============ 工作流 ============

    def save_workflow(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]]
    ) -> ProjectWorkflow:
        """保存工作流"""
        workflow = ProjectWorkflow(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            steps=steps
        )
        self.workflows.append(workflow)
        self._save()
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[ProjectWorkflow]:
        """获取工作流"""
        for w in self.workflows:
            if w.id == workflow_id:
                return w
        return None

    def get_workflows_by_name(self, name: str) -> List[ProjectWorkflow]:
        """按名称获取工作流"""
        return [w for w in self.workflows if name in w.name]

    def list_workflows(self) -> List[ProjectWorkflow]:
        """列出所有工作流"""
        return self.workflows.copy()

    def delete_workflow(self, workflow_id: str) -> bool:
        """删除工作流"""
        for i, w in enumerate(self.workflows):
            if w.id == workflow_id:
                del self.workflows[i]
                self._save()
                return True
        return False

    # ============ 统计信息 ============

    def record_session(self):
        """记录会话"""
        self.stats.total_sessions += 1
        self.stats.last_activity = datetime.now().isoformat()
        self._save()

    def record_message(self, tool_used: Optional[str] = None):
        """记录消息"""
        self.stats.total_messages += 1
        if tool_used:
            self.stats.tool_usage[tool_used] = self.stats.tool_usage.get(tool_used, 0) + 1
        self.stats.last_activity = datetime.now().isoformat()
        self._save()

    def add_data_file(self, file_path: str):
        """添加数据文件记录"""
        if file_path not in self.stats.data_files:
            self.stats.data_files.append(file_path)
            self._save()

    def add_output_file(self, file_path: str):
        """添加输出文件记录"""
        if file_path not in self.stats.output_files:
            self.stats.output_files.append(file_path)
            self._save()

    def get_summary(self) -> Dict[str, Any]:
        """获取项目记忆摘要"""
        return {
            "project_id": self.project_id,
            "facts_count": len(self.facts),
            "high_importance_facts": len([f for f in self.facts if f.importance >= 4]),
            "preferences_count": len(self.preferences),
            "workflows_count": len(self.workflows),
            "stats": self.stats.to_dict()
        }

    def get_context_for_prompt(self, limit_facts: int = 10) -> str:
        """获取用于提示的上下文"""
        context_parts = []

        # 重要事实
        important_facts = self.get_facts(min_importance=4, limit=limit_facts)
        if important_facts:
            context_parts.append(f"## 项目重要事实")
            for fact in important_facts[:5]:
                context_parts.append(f"- [{fact.category}] {fact.content}")

        # 偏好设置
        if self.preferences:
            context_parts.append(f"\n## 项目偏好")
            for key, pref in self.preferences.items():
                context_parts.append(f"- {key}: {pref.value}")

        # 工作流提示
        if self.workflows:
            context_parts.append(f"\n## 项目工作流")
            for wf in self.workflows[:3]:
                context_parts.append(f"- {wf.name}: {wf.description}")

        return "\n".join(context_parts)


class ProjectMemoryManager:
    """项目记忆管理器"""

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._memories: Dict[str, ProjectMemory] = {}

    def get_memory(self, project_id: str) -> ProjectMemory:
        """获取项目记忆"""
        if project_id not in self._memories:
            self._memories[project_id] = ProjectMemory(project_id, self.storage_dir)
        return self._memories[project_id]

    def create_memory(self, project_id: str) -> ProjectMemory:
        """创建项目记忆"""
        if project_id in self._memories:
            return self._memories[project_id]
        memory = ProjectMemory(project_id, self.storage_dir)
        self._memories[project_id] = memory
        return memory

    def delete_memory(self, project_id: str) -> bool:
        """删除项目记忆"""
        if project_id in self._memories:
            del self._memories[project_id]

        memory_dir = self.storage_dir / project_id / ".memory"
        if memory_dir.exists():
            import shutil
            shutil.rmtree(memory_dir)
            return True
        return False

    def list_projects_with_memory(self) -> List[str]:
        """列出有记忆的项目"""
        return list(self._memories.keys())


# 全局单例
_memory_manager: Optional[ProjectMemoryManager] = None


def get_memory_manager() -> ProjectMemoryManager:
    """获取记忆管理器单例"""
    global _memory_manager
    if _memory_manager is None:
        from config import settings
        base_dir = Path(settings.WORKSPACE_DIR).resolve().parent / "projects"
        _memory_manager = ProjectMemoryManager(base_dir)
    return _memory_manager


def init_memory_manager(storage_dir: Optional[Path] = None):
    """初始化记忆管理器"""
    global _memory_manager
    if storage_dir is None:
        from config import settings
        storage_dir = Path(settings.WORKSPACE_DIR).resolve().parent / "projects"
    _memory_manager = ProjectMemoryManager(storage_dir)
    return _memory_manager