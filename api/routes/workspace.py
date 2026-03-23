"""
Workspace API Routes - Multi-project management endpoints.

提供项目管理、会话关联项目、项目记忆等功能。
"""
from typing import List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.workspace import get_workspace_manager, get_memory_manager, WorkspaceManager, Project
from core.workspace.memory import ProjectMemory, ProjectFact

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


# Models
class ProjectCreateRequest(BaseModel):
    """创建项目请求"""
    id: str = Field(..., description="项目ID（仅字母、数字、下划线、短横线）", pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(..., description="项目名称")
    description: str = Field(default="", description="项目描述")


class ProjectResponse(BaseModel):
    """项目响应"""
    id: str
    name: str
    description: str
    created_at: str
    workspace_dir: str


class FactAddRequest(BaseModel):
    """添加事实请求"""
    content: str = Field(..., description="事实内容")
    category: str = Field(default="general", description="分类")
    importance: int = Field(default=1, ge=1, le=5, description="重要性 1-5")
    source: str = Field(default="user", description="来源")
    tags: List[str] = Field(default_factory=list, description="标签")


class FactResponse(BaseModel):
    """事实响应"""
    id: str
    content: str
    category: str
    importance: int
    source: str
    created_at: str
    tags: List[str]


class PreferenceSetRequest(BaseModel):
    """设置偏好请求"""
    key: str = Field(..., description="偏好键")
    value: Any = Field(..., description="偏好值")
    description: str = Field(default="", description="描述")


class WorkflowSaveRequest(BaseModel):
    """保存工作流请求"""
    name: str = Field(..., description="工作流名称")
    description: str = Field(..., description="描述")
    steps: List[dict] = Field(..., description="步骤列表")


# Endpoints
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects():
    """列出所有项目"""
    manager = get_workspace_manager()
    projects = manager.list_projects()
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            description=p.description,
            created_at=p.created_at,
            workspace_dir=str(p.workspace_dir)
        )
        for p in projects
    ]


@router.post("/projects", response_model=ProjectResponse)
async def create_project(request: ProjectCreateRequest):
    """创建新项目"""
    manager = get_workspace_manager()
    try:
        project = manager.create_project(
            project_id=request.id,
            name=request.name,
            description=request.description
        )
        # 初始化项目记忆
        memory_manager = get_memory_manager()
        memory_manager.create_memory(request.id)
        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            workspace_dir=str(project.workspace_dir)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """获取项目详情"""
    manager = get_workspace_manager()
    project = manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        workspace_dir=str(project.workspace_dir)
    )


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, delete_files: bool = Query(False, description="是否删除项目文件")):
    """删除项目"""
    manager = get_workspace_manager()
    memory_manager = get_memory_manager()
    try:
        # 删除项目记忆
        memory_manager.delete_memory(project_id)
        # 删除项目
        manager.delete_project(project_id, delete_files=delete_files)
        return {"message": f"Project {project_id} deleted"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects/{project_id}/files")
async def list_project_files(project_id: str, path: str = Query("", description="相对路径（相对于项目工作目录）")):
    """列出项目目录中的文件"""
    manager = get_workspace_manager()
    project = manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    import os
    from pathlib import Path

    workspace = project.workspace_dir
    target_dir = workspace / path if path else workspace

    if not target_dir.exists():
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    files = []
    for item in target_dir.iterdir():
        files.append({
            "name": item.name,
            "is_dir": item.is_dir(),
            "size": item.stat().st_size if item.is_file() else None,
            "modified": item.stat().st_mtime
        })

    return {"project_id": project_id, "path": path, "files": files}


# ============ 项目记忆端点 ============

@router.get("/projects/{project_id}/memory/summary")
async def get_project_memory_summary(project_id: str):
    """获取项目记忆摘要"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    return memory.get_summary()


@router.get("/projects/{project_id}/memory/context")
async def get_project_memory_context(
    project_id: str,
    limit_facts: int = Query(10, description="事实数量限制")
):
    """获取项目记忆上下文（用于提示）"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    context = memory.get_context_for_prompt(limit_facts)
    return {"project_id": project_id, "context": context}


@router.get("/projects/{project_id}/memory/facts", response_model=List[FactResponse])
async def get_project_facts(
    project_id: str,
    category: Optional[str] = Query(None, description="筛选分类"),
    min_importance: int = Query(0, description="最小重要性"),
    limit: int = Query(50, description="数量限制")
):
    """获取项目事实"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    facts = memory.get_facts(category=category, min_importance=min_importance, limit=limit)
    return [FactResponse(**f.to_dict()) for f in facts]


@router.post("/projects/{project_id}/memory/facts", response_model=FactResponse)
async def add_project_fact(project_id: str, request: FactAddRequest):
    """添加项目事实"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    fact = memory.add_fact(
        content=request.content,
        category=request.category,
        importance=request.importance,
        source=request.source,
        tags=request.tags
    )
    return FactResponse(**fact.to_dict())


@router.delete("/projects/{project_id}/memory/facts/{fact_id}")
async def delete_project_fact(project_id: str, fact_id: str):
    """删除项目事实"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    if memory.delete_fact(fact_id):
        return {"message": "Fact deleted"}
    raise HTTPException(status_code=404, detail="Fact not found")


@router.get("/projects/{project_id}/memory/preferences")
async def get_project_preferences(project_id: str):
    """获取项目偏好设置"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    prefs = memory.get_all_preferences()
    return {
        key: {
            "value": pref.value,
            "description": pref.description,
            "updated_at": pref.updated_at
        }
        for key, pref in prefs.items()
    }


@router.post("/projects/{project_id}/memory/preferences")
async def set_project_preference(project_id: str, request: PreferenceSetRequest):
    """设置项目偏好"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    pref = memory.set_preference(request.key, request.value, request.description)
    return {"message": "Preference set", "preference": pref.to_dict()}


@router.get("/projects/{project_id}/memory/workflows")
async def list_project_workflows(project_id: str):
    """列出项目工作流"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    return {"workflows": [w.to_dict() for w in memory.list_workflows()]}


@router.post("/projects/{project_id}/memory/workflows")
async def save_project_workflow(project_id: str, request: WorkflowSaveRequest):
    """保存项目工作流"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    workflow = memory.save_workflow(request.name, request.description, request.steps)
    return {"message": "Workflow saved", "workflow": workflow.to_dict()}


@router.delete("/projects/{project_id}/memory/workflows/{workflow_id}")
async def delete_project_workflow(project_id: str, workflow_id: str):
    """删除项目工作流"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    if memory.delete_workflow(workflow_id):
        return {"message": "Workflow deleted"}
    raise HTTPException(status_code=404, detail="Workflow not found")


@router.get("/projects/{project_id}/memory/stats")
async def get_project_stats(project_id: str):
    """获取项目统计"""
    manager = get_workspace_manager()
    if not manager.get_project(project_id):
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    memory_manager = get_memory_manager()
    memory = memory_manager.get_memory(project_id)
    return memory.stats.to_dict()


# ============ 其他端点 ============

@router.get("/default-workspace")
async def get_default_workspace():
    """获取默认工作目录"""
    manager = get_workspace_manager()
    workspace = manager.get_default_workspace()
    return {"workspace_dir": str(workspace)}


@router.get("/shared")
async def list_shared_files():
    """列出共享资源目录中的文件"""
    manager = get_workspace_manager()
    files = []
    if manager.shared_dir.exists():
        for item in manager.shared_dir.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(manager.shared_dir)
                files.append({
                    "path": str(rel_path),
                    "size": item.stat().st_size,
                    "modified": item.stat().st_mtime
                })
    return {"files": files}