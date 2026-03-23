"""
Workspace Manager - Multi-project and multi-process workspace isolation.

架构说明：

1. Project Isolation（项目隔离）
   - 每个项目有独立的 workspace 目录
   - 结构: workspace/projects/{project_id}/
   - 项目内文件完全隔离

2. Session Association（会话关联）
   - Session 可以关联到特定 project
   - 未关联的会话使用 default project

3. Workspace Structure（目录结构）
   workspace/
   ├── projects/
   │   ├── default/           # 默认项目（未指定 project_id 的会话）
   │   ├── project_abc123/     # 项目 A
   │   │   ├── data/          # 项目数据
   │   │   ├── outputs/       # 输出文件
   │   │   └── temp/          # 临时文件
   │   └── project_xyz789/     # 项目 B
   │       ├── data/
   │       ├── outputs/
   │       └── temp/
   ├── shared/                # 共享资源（跨项目）
   │   ├── templates/         # 模板文件
   │   └── libs/             # 共享库
   └── sessions/             # 会话数据

4. API Design
   - 创建会话时可选指定 project_id
   - 工具自动使用项目的 workspace
   - 支持项目列表、切换、删除等管理功能
"""

from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import json
from datetime import datetime
import shutil


@dataclass
class Project:
    """项目配置"""
    id: str
    name: str
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)

    @property
    def workspace_dir(self) -> Path:
        """项目工作目录"""
        from .config import get_workspace_manager
        manager = get_workspace_manager()
        return manager.get_project_workspace(self.id)


class WorkspaceManager:
    """工作空间管理器"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.projects_dir = base_dir / "projects"
        self.shared_dir = base_dir / "shared"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.shared_dir.mkdir(parents=True, exist_ok=True)
        self._projects: Dict[str, Project] = {}
        self._project_index_file = base_dir / "projects" / ".index.json"

        self._load_project_index()

    def _load_project_index(self):
        """加载项目索引"""
        if self._project_index_file.exists():
            try:
                with open(self._project_index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pid, p_data in data.items():
                        self._projects[pid] = Project(
                            id=pid,
                            name=p_data["name"],
                            description=p_data.get("description", ""),
                            created_at=p_data.get("created_at"),
                            metadata=p_data.get("metadata", {})
                        )
            except Exception as e:
                print(f"Warning: Failed to load project index: {e}")

        # 确保默认项目存在
        if "default" not in self._projects:
            self.create_project("default", "默认项目")

    def _save_project_index(self):
        """保存项目索引"""
        data = {
            pid: {
                "name": p.name,
                "description": p.description,
                "created_at": p.created_at,
                "metadata": p.metadata
            }
            for pid, p in self._projects.items()
        }
        self._project_index_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def create_project(
        self,
        project_id: str,
        name: str,
        description: str = ""
    ) -> Project:
        """创建新项目"""
        if project_id in self._projects:
            raise ValueError(f"Project {project_id} already exists")

        # 创建项目目录结构
        project_dir = self.projects_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "data").mkdir(exist_ok=True)
        (project_dir / "outputs").mkdir(exist_ok=True)
        (project_dir / "temp").mkdir(exist_ok=True)

        project = Project(
            id=project_id,
            name=name,
            description=description
        )
        self._projects[project_id] = project
        self._save_project_index()

        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        return self._projects.get(project_id)

    def get_project_workspace(self, project_id: str) -> Path:
        """获取项目工作目录"""
        if project_id not in self._projects:
            raise ValueError(f"Project {project_id} not found")
        return self.projects_dir / project_id

    def list_projects(self) -> List[Project]:
        """列出所有项目"""
        return list(self._projects.values())

    def delete_project(self, project_id: str, delete_files: bool = False):
        """删除项目"""
        if project_id not in self._projects:
            raise ValueError(f"Project {project_id} not found")

        if project_id == "default":
            raise ValueError("Cannot delete default project")

        if delete_files:
            project_dir = self.projects_dir / project_id
            if project_dir.exists():
                shutil.rmtree(project_dir)

        del self._projects[project_id]
        self._save_project_index()

    def get_default_workspace(self) -> Path:
        """获取默认工作目录"""
        return self.get_project_workspace("default")


# 全局单例
_workspace_manager: Optional[WorkspaceManager] = None


def get_workspace_manager() -> WorkspaceManager:
    """获取工作空间管理器单例"""
    global _workspace_manager
    if _workspace_manager is None:
        from config import settings
        base_dir = Path(settings.WORKSPACE_DIR).resolve().parent
        _workspace_manager = WorkspaceManager(base_dir)
    return _workspace_manager


def init_workspace_manager(base_dir: Optional[Path] = None):
    """初始化工作空间管理器"""
    global _workspace_manager
    if base_dir is None:
        from config import settings
        base_dir = Path(settings.WORKSPACE_DIR).resolve().parent
    _workspace_manager = WorkspaceManager(base_dir)
    return _workspace_manager