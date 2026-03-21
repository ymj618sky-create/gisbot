"""
Nanobot Agent API Routes
使用新的 Agent Loop 架构的 API 端点
"""
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from core.agent.loop import AgentLoop
from core.tools.registry import ToolRegistry
from core.tools.data.read import ReadDataTool
from core.tools.data.write import WriteDataTool
from core.tools.data.convert import ConvertDataTool
from core.tools.gis.proximity import BufferTool
from core.providers.anthropic import AnthropicProvider
from core.providers.openai import OpenAIProvider
from session.manager import SessionManager
from config import settings

router = APIRouter()


# 全局实例
_agent_loop: Optional[AgentLoop] = None


def get_agent_loop() -> AgentLoop:
    """获取 Agent Loop 实例（单例）"""
    global _agent_loop
    if _agent_loop is None:
        workspace = Path(settings.WORKSPACE_DIR) if hasattr(settings, 'WORKSPACE_DIR') else Path.cwd()
        data_dir = workspace / "data"

        # Initialize components
        provider = AnthropicProvider(
            api_key=getattr(settings, 'ANTHROPIC_API_KEY', ''),
            model=getattr(settings, 'ANTHROPIC_MODEL', None)
        )

        tool_registry = ToolRegistry()
        # Register core tools
        tool_registry.register(ReadDataTool())
        tool_registry.register(WriteDataTool())
        tool_registry.register(ConvertDataTool())
        tool_registry.register(BufferTool())

        session_manager = SessionManager(data_dir=data_dir)

        _agent_loop = AgentLoop(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager,
            max_iterations=getattr(settings, 'MAX_ITERATIONS', 15),
            memory_window=getattr(settings, 'MEMORY_WINDOW', 50)
        )

    return _agent_loop


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    channel: str = Field(default="web", description="渠道名称")
    chat_id: str = Field(..., description="聊天 ID")
    media: Optional[List[str]] = Field(default=None, description="媒体文件路径列表")


class ChatResponse(BaseModel):
    """聊天响应"""
    response: str
    session_id: str


@router.post("/nanobot/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    """
    使用新的 Agent Loop 处理聊天消息

    这是一个统一的聊天端点，支持：
    - 多轮对话
    - 工具调用
    - 会话管理
    - 进度回调
    """
    agent_loop = get_agent_loop()

    try:
        # 处理消息
        response = await agent_loop.process_direct(
            content=body.message,
            channel=body.channel,
            chat_id=body.chat_id,
            media=body.media
        )

        # 获取会话 ID
        session = agent_loop.session_manager.get_by_channel_chat_id(
            body.channel, body.chat_id
        )
        session_id = session.id if session else ""

        return ChatResponse(
            response=response,
            session_id=session_id
        )

    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/nanobot/tools")
async def list_tools():
    """获取所有已注册的工具"""
    agent_loop = get_agent_loop()
    tools = agent_loop.tool_registry.get_definitions()

    return {
        "tools": [
            {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "parameters": tool["function"]["parameters"]
            }
            for tool in tools
        ],
        "count": len(tools)
    }


@router.get("/nanobot/session/{channel}/{chat_id}")
async def get_session(channel: str, chat_id: str):
    """获取会话信息"""
    agent_loop = get_agent_loop()
    session = agent_loop.session_manager.get_by_channel_chat_id(channel, chat_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return {
        "id": session.id,
        "channel": session.channel,
        "chat_id": session.chat_id,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "message_count": len(session.messages),
        "metadata": session.metadata
    }


@router.delete("/nanobot/session/{channel}/{chat_id}")
async def delete_session(channel: str, chat_id: str):
    """删除会话"""
    agent_loop = get_agent_loop()
    session = agent_loop.session_manager.get_by_channel_chat_id(channel, chat_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    agent_loop.session_manager.delete_session(session.id)

    return {"success": True, "message": "Session deleted"}


@router.get("/nanobot/sessions")
async def list_sessions(limit: int = 50):
    """列出所有会话"""
    agent_loop = get_agent_loop()
    sessions = agent_loop.session_manager.list_sessions(limit=limit)

    return {
        "sessions": [
            {
                "id": s.id,
                "channel": s.channel,
                "chat_id": s.chat_id,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.messages)
            }
            for s in sessions
        ],
        "count": len(sessions)
    }


@router.get("/nanobot/skills")
async def list_skills():
    """获取所有可用的技能"""
    agent_loop = get_agent_loop()
    skills = agent_loop.skills_loader.list_skills(filter_unavailable=True)

    return {
        "skills": [
            {
                "name": skill["name"],
                "path": skill["path"],
                "source": skill["source"]
            }
            for skill in skills
        ],
        "count": len(skills)
    }


@router.post("/nanobot/stream/{channel}/{chat_id}")
async def chat_stream(channel: str, chat_id: str, request: Request):
    """
    Server-Sent Events (SSE) 流式聊天

    支持实时推送 Agent 处理进度。
    """
    from fastapi.responses import StreamingResponse

    async def event_generator():
        """生成 SSE 事件"""
        try:
            import json

            # 读取请求体
            body = await request.json()
            message = body.get("message", "")
            media = body.get("media", [])

            agent_loop = get_agent_loop()

            # 进度回调
            progress_messages = []

            def on_progress(progress: str):
                progress_messages.append(progress)

            # 处理消息
            response = await agent_loop.process_direct(
                content=message,
                channel=channel,
                chat_id=chat_id,
                media=media,
                on_progress=on_progress
            )

            # 发送进度事件
            for progress in progress_messages:
                yield f"data: {json.dumps({'type': 'progress', 'message': progress}, ensure_ascii=False)}\n\n"

            # 发送最终响应
            yield f"data: {json.dumps({'type': 'response', 'content': response}, ensure_ascii=False)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )