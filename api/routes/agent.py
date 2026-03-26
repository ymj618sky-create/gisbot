"""
Agent API Routes
使用 Agent Loop 架构的 API 端点
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
from core.tools.data.raster import ReadRasterTool, WriteRasterTool, ConvertRasterTool
from core.tools.gis.proximity import BufferTool
from core.tools.gis.clip import ClipTool
from core.tools.system import (
    ListFilesTool,
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    ExecuteCommandTool,
    RunPythonScriptTool,
    WebSearchTool,
    WebFetchTool,
    RunArcPyTool
)
from core.tools.arcpy import (
    BufferToolArcPy,
    ClipToolArcPy,
    IntersectToolArcPy,
    ProjectToolArcPy,
    DissolveToolArcPy,
    FeatureToRasterToolArcPy,
    RasterToPolygonToolArcPy,
    SpatialJoinToolArcPy
)
from core.tools.spawn import SpawnTool
from core.tools.message import MessageTool
from core.tools.file_analysis import ReadImageTool, ReadDocumentTool, ParseTableTool
from core.providers.factory import create_provider
from session.manager import SessionManager
from config import settings
from core.config import get_timeout_config

router = APIRouter()


# 全局实例
_agent_loop: Optional[AgentLoop] = None


def reset_agent_loop() -> None:
    """Reset the agent loop singleton. Call this when tools or configuration changes."""
    global _agent_loop
    _agent_loop = None


def get_agent_loop() -> AgentLoop:
    """获取 Agent Loop 实例（单例）"""
    global _agent_loop
    if _agent_loop is None:
        # Use workspace subdirectory as the main workspace
        project_root = Path.cwd()
        workspace = project_root / "workspace"
        # Ensure workspace directory exists
        workspace.mkdir(parents=True, exist_ok=True)
        data_dir = workspace / "data"
        # Ensure data directory exists
        data_dir.mkdir(parents=True, exist_ok=True)

        # 加载超时配置
        timeout_config = get_timeout_config()
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Loading Agent Loop with timeout config: {timeout_config}")

        # 获取默认 provider 和模型
        provider_name = getattr(settings, 'DEFAULT_PROVIDER', 'dashscope')
        model = None  # 使用 provider 默认模型

        # 判断是否使用 mock 模式
        api_key_env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "dashscope": "DASHSCOPE_API_KEY",
        }
        env_key = api_key_env_map.get(provider_name, "")
        api_key = getattr(settings, env_key, "")
        use_mock_mode = not api_key or api_key in [
            f"your_{provider_name}_api_key_here",
            "your_anthropic_api_key_here"
        ]

        # 创建 provider，传递超时配置
        provider = create_provider(
            provider_name=provider_name,
            model=model,
            api_key=api_key if not use_mock_mode else "mock_key_for_testing",
            timeout=timeout_config.llm_request,
            max_retries=timeout_config.provider_max_retries,
        )
        logger.info(f"Created {provider_name} provider with timeout={timeout_config.llm_request}s")

        tool_registry = ToolRegistry()
        # Register GIS tools with workspace parameter
        tool_registry.register(ReadDataTool(workspace))
        tool_registry.register(WriteDataTool(workspace))
        tool_registry.register(ConvertDataTool(workspace))
        tool_registry.register(BufferTool())
        tool_registry.register(ClipTool())

        # Register raster tools
        tool_registry.register(ReadRasterTool(workspace))
        tool_registry.register(WriteRasterTool(workspace))
        tool_registry.register(ConvertRasterTool(workspace))

        # Register system tools with workspace parameter and timeout config
        python_path = getattr(settings, 'ARCGIS_PRO_PYTHON', 'python')
        logger.info(f"Using Python path: {python_path}")
        tool_registry.register(ListFilesTool(workspace))
        tool_registry.register(ReadFileTool(workspace))
        tool_registry.register(WriteFileTool(workspace))
        tool_registry.register(EditFileTool(workspace))
        tool_registry.register(ExecuteCommandTool(workspace, timeout=timeout_config.exec_command))
        tool_registry.register(RunPythonScriptTool(workspace, timeout=timeout_config.run_python))
        tool_registry.register(WebSearchTool(provider="tavily"))  # Use Tavily as default
        tool_registry.register(WebFetchTool())
        tool_registry.register(RunArcPyTool(workspace))

        logger.info(f"Registered tools: exec(timeout={timeout_config.exec_command}s), run_python(timeout={timeout_config.run_python}s), python={python_path}")

        # Register ArcPy tools (always register, will show error if ArcPy unavailable)
        try:
            tool_registry.register(BufferToolArcPy(workspace))
            print("  - buffer_arcpy registered")
        except Exception as e:
            print(f"  - buffer_arcpy skipped: {e}")

        try:
            tool_registry.register(ClipToolArcPy(workspace))
            print("  - clip_arcpy registered")
        except Exception as e:
            print(f"  - clip_arcpy skipped: {e}")

        try:
            tool_registry.register(IntersectToolArcPy(workspace))
            print("  - intersect_arcpy registered")
        except Exception as e:
            print(f"  - intersect_arcpy skipped: {e}")

        try:
            tool_registry.register(ProjectToolArcPy(workspace))
            print("  - project_arcpy registered")
        except Exception as e:
            print(f"  - project_arcpy skipped: {e}")

        try:
            tool_registry.register(DissolveToolArcPy(workspace))
            print("  - dissolve_arcpy registered")
        except Exception as e:
            print(f"  - dissolve_arcpy skipped: {e}")

        try:
            tool_registry.register(FeatureToRasterToolArcPy(workspace))
            print("  - feature_to_raster_arcpy registered")
        except Exception as e:
            print(f"  - feature_to_raster_arcpy skipped: {e}")

        try:
            tool_registry.register(RasterToPolygonToolArcPy(workspace))
            print("  - raster_to_polygon_arcpy registered")
        except Exception as e:
            print(f"  - raster_to_polygon_arcpy skipped: {e}")

        try:
            tool_registry.register(SpatialJoinToolArcPy(workspace))
            print("  - spatial_join_arcpy registered")
        except Exception as e:
            print(f"  - spatial_join_arcpy skipped: {e}")

        # Register agent tools
        tool_registry.register(SpawnTool(workspace))
        tool_registry.register(MessageTool(workspace))

        # Register file analysis tools
        tool_registry.register(ReadImageTool())
        tool_registry.register(ReadDocumentTool())
        tool_registry.register(ParseTableTool())

        session_manager = SessionManager(data_dir=data_dir)

        _agent_loop = AgentLoop(
            workspace=workspace,
            provider=provider,
            tool_registry=tool_registry,
            session_manager=session_manager,
            max_iterations=timeout_config.max_iterations,
            memory_window=50
        )
        logger.info(f"Agent Loop created with max_iterations={timeout_config.max_iterations}")

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


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    """
    使用 Agent Loop 处理聊天消息

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


@router.post("/reset")
async def reset_agent():
    """Reset the agent loop singleton. Use when tools or configuration changes."""
    from core.config import reset_timeout_config
    reset_agent_loop()
    reset_timeout_config()
    return {"success": True, "message": "Agent loop and timeout config reset. Next chat request will create a new instance."}


@router.get("/config")
async def get_config_status():
    """获取当前配置状态，包括超时配置和工具信息。"""
    from core.config import get_timeout_config
    agent_loop = get_agent_loop()

    timeout_config = get_timeout_config()
    tools = agent_loop.tool_registry.get_definitions()

    return {
        "timeout": timeout_config.to_dict(),
        "tools": {
            "count": len(tools),
            "names": [tool["function"]["name"] for tool in tools]
        },
        "agent": {
            "max_iterations": agent_loop.max_iterations,
            "memory_window": agent_loop.memory_window,
            "provider": agent_loop.provider.name,
            "model": agent_loop.provider.model
        }
    }


@router.get("/tools")
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


@router.get("/session/{channel}/{chat_id}")
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


@router.delete("/session/{channel}/{chat_id}")
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


@router.get("/sessions")
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
                "title": s.title,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
                "message_count": len(s.messages)
            }
            for s in sessions
        ],
        "count": len(sessions)
    }


@router.get("/skills")
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


@router.get("/sse/{channel}/{chat_id}")
async def chat_stream_sse(channel: str, chat_id: str, request: Request):
    """
    Server-Sent Events (SSE) 流式聊天 (GET 版本，用于 EventSource)
    支持实时推送 Agent 处理进度和思考过程。

    使用查询参数:
    - message: 用户消息内容
    - media: 媒体文件路径 (可选，逗号分隔)
    """
    import json
    import time
    from fastapi.responses import StreamingResponse
    import asyncio

    # 从查询参数获取消息
    message = request.query_params.get("message", "")
    if not message:
        # 返回空事件而不是错误
        async def empty_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Missing message parameter'}, ensure_ascii=False)}\n\n"
        return StreamingResponse(empty_generator(), media_type="text/event-stream")

    async def event_generator():
        """生成 SSE 事件，带心跳机制和增强的错误处理"""
        import time
        try:
            agent_loop = get_agent_loop()

            # 加载超时配置
            from core.config import get_timeout_config
            timeout_config = get_timeout_config()

            # 使用队列来传递进度消息
            progress_queue = asyncio.Queue()

            def on_progress(progress: str):
                # 非阻塞地将进度消息放入队列
                try:
                    progress_queue.put_nowait(progress)
                except asyncio.QueueFull:
                    pass

            # 在后台运行 agent_loop
            async def run_agent():
                try:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info("Starting agent task for SSE stream")

                    response = await agent_loop.process_direct(
                        content=message,
                        channel=channel,
                        chat_id=chat_id,
                        media=None,
                        on_progress=on_progress
                    )
                    progress_queue.put_nowait({"type": "response", "content": response})
                    logger.info("Agent task completed successfully")
                except Exception as e:
                    import logging
                    import traceback
                    logger = logging.getLogger(__name__)
                    logger.error(f"Agent task failed: {e}", exc_info=True)
                    error_details = f"{str(e)}\n\n{traceback.format_exc()}"
                    progress_queue.put_nowait({"type": "error", "message": error_details})
                finally:
                    progress_queue.put_nowait(None)  # 标记结束

            # 启动 agent 任务
            agent_task = asyncio.create_task(run_agent())

            # 心跳任务
            async def heartbeat():
                heartbeat_interval = timeout_config.sse_heartbeat
                while not agent_task.done():
                    yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': time.time()}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(heartbeat_interval)

            heartbeat_task = asyncio.create_task(heartbeat().__anext__())

            # 发送初始连接消息
            yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE stream connected'}, ensure_ascii=False)}\n\n"

            # 发送进度事件
            while True:
                try:
                    # 使用较长的超时时间，允许长时间运行的任务
                    queue_timeout = min(timeout_config.sse_queue_wait, 600.0)
                    progress = await asyncio.wait_for(progress_queue.get(), timeout=queue_timeout)

                    if progress is None:
                        # Agent 完成，结束流
                        yield f"data: {json.dumps({'type': 'done', 'message': 'Processing complete'}, ensure_ascii=False)}\n\n"
                        break

                    if isinstance(progress, dict):
                        # 这是一个最终响应或错误
                        yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"
                    else:
                        # 这是一个进度消息
                        yield f"data: {json.dumps({'type': 'progress', 'message': progress}, ensure_ascii=False)}\n\n"

                except asyncio.TimeoutError:
                    # 队列为空，发送心跳表示连接仍然活跃
                    heartbeat_msg = {'type': 'heartbeat', 'timestamp': time.time(), 'status': 'waiting'}
                    yield f"data: {json.dumps(heartbeat_msg, ensure_ascii=False)}\n\n"
                    continue

            # 等待 agent 任务完成并检查是否有错误
            try:
                await asyncio.wait_for(agent_task, timeout=5.0)
            except asyncio.TimeoutError:
                import logging
                logging.getLogger(__name__).warning("Agent task did not complete within 5s after stream end")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Agent task error after stream end: {e}")

        except Exception as e:
            import logging
            import traceback
            logging.getLogger(__name__).error(f"SSE stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'Stream error: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            "Content-Type": "text/event-stream; charset=utf-8",
        }
    )


@router.get("/stream/{channel}/{chat_id}")
async def chat_stream_get(channel: str, chat_id: str, request: Request):
    """
    Server-Sent Events (SSE) 流式聊天 (GET 版本，用于 EventSource)
    支持实时推送 Agent 处理进度和思考过程。

    使用查询参数:
    - message: 用户消息内容
    - media: 媒体文件路径 (可选，逗号分隔)
    """
    import json
    import time
    from fastapi.responses import StreamingResponse
    import asyncio

    # 从查询参数获取消息
    message = request.query_params.get("message", "")
    if not message:
        # 返回空事件而不是错误
        async def empty_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Missing message parameter'}, ensure_ascii=False)}\n\n"
        return StreamingResponse(empty_generator(), media_type="text/event-stream")

    # 从查询参数获取媒体文件路径
    media_param = request.query_params.get("media", "")
    media = None
    if media_param:
        media = [p.strip() for p in media_param.split(",") if p.strip()]
        import logging
        logging.getLogger(__name__).info(f"Received media parameter: {media_param}, parsed as: {media}")
    else:
        import logging
        logging.getLogger(__name__).info("No media parameter received")

    async def event_generator():
        """生成 SSE 事件，带心跳机制和增强的错误处理"""
        try:
            agent_loop = get_agent_loop()

            # 加载超时配置
            from core.config import get_timeout_config
            timeout_config = get_timeout_config()

            # 使用队列来传递进度消息
            progress_queue = asyncio.Queue()

            def on_progress(progress: str):
                # 非阻塞地将进度消息放入队列
                try:
                    progress_queue.put_nowait(progress)
                except asyncio.QueueFull:
                    pass

            # 在后台运行 agent_loop
            async def run_agent():
                try:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.info("Starting agent task for SSE stream")

                    response = await agent_loop.process_direct(
                        content=message,
                        channel=channel,
                        chat_id=chat_id,
                        media=media,
                        on_progress=on_progress
                    )
                    progress_queue.put_nowait({"type": "response", "content": response})
                    logger.info("Agent task completed successfully")
                except Exception as e:
                    import logging
                    import traceback
                    logger = logging.getLogger(__name__)
                    logger.error(f"Agent task failed: {e}", exc_info=True)
                    error_details = f"{str(e)}\n\n{traceback.format_exc()}"
                    progress_queue.put_nowait({"type": "error", "message": error_details})
                finally:
                    progress_queue.put_nowait(None)  # 标记结束

            # 启动 agent 任务
            agent_task = asyncio.create_task(run_agent())

            # 发送初始连接消息
            yield f"data: {json.dumps({'type': 'connected', 'message': 'SSE stream connected'}, ensure_ascii=False)}\n\n"

            # 发送进度事件
            while True:
                try:
                    # 使用较长的超时时间，允许长时间运行的任务
                    queue_timeout = min(timeout_config.sse_queue_wait, 600.0)
                    progress = await asyncio.wait_for(progress_queue.get(), timeout=queue_timeout)

                    if progress is None:
                        # Agent 完成，结束流
                        yield f"data: {json.dumps({'type': 'done', 'message': 'Processing complete'}, ensure_ascii=False)}\n\n"
                        break

                    if isinstance(progress, dict):
                        # 这是一个最终响应或错误
                        yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"
                    else:
                        # 这是一个进度消息
                        yield f"data: {json.dumps({'type': 'progress', 'message': progress}, ensure_ascii=False)}\n\n"

                except asyncio.TimeoutError:
                    # 队列为空，发送心跳表示连接仍然活跃
                    heartbeat_msg = {'type': 'heartbeat', 'timestamp': time.time(), 'status': 'waiting'}
                    yield f"data: {json.dumps(heartbeat_msg, ensure_ascii=False)}\n\n"
                    continue

            # 等待 agent 任务完成并检查是否有错误
            try:
                await asyncio.wait_for(agent_task, timeout=5.0)
            except asyncio.TimeoutError:
                import logging
                logging.getLogger(__name__).warning("Agent task did not complete within 5s after stream end")
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Agent task error after stream end: {e}")

        except Exception as e:
            import logging
            import traceback
            logging.getLogger(__name__).error(f"SSE stream error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'Stream error: {str(e)}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            "Content-Type": "text/event-stream; charset=utf-8",
        }
    )


@router.post("/stream/{channel}/{chat_id}")
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