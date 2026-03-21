"""
GIS Agent 适配器
将现有的 GIS Agent 工作流包装成统一接口
"""
import logging
from typing import Dict, Any, Optional, List

from core.agents.base import BaseAgent, AgentType, AgentCapability, AgentResponse
from agent.workflow import GISAgentWorkflow

logger = logging.getLogger(__name__)


class GISAgentAdapter(BaseAgent):
    """GIS Agent 适配器

    将现有的 GISAgentWorkflow 包装成统一的 BaseAgent 接口。
    """

    def __init__(self, workflow: Optional[GISAgentWorkflow] = None, project_crs: str = "EPSG:4326"):
        super().__init__(
            agent_type=AgentType.GIS,
            name="gis_analyzer",
            version="2.0.0"
        )
        self._workflow = workflow or GISAgentWorkflow(project_crs=project_crs)
        self._capabilities = self._init_capabilities()

    def _init_capabilities(self) -> List[AgentCapability]:
        """初始化能力列表"""
        return [
            AgentCapability(
                name="spatial_analysis",
                description="空间数据分析",
                keywords=["空间分析", "缓冲区", "buffer", "相交", "intersect", "空间"],
                requires_data=True,
                priority=3
            ),
            AgentCapability(
                name="data_loading",
                description="加载和处理空间数据",
                keywords=["加载", "导入", "数据", "shp", "geojson", "kml"],
                requires_data=True,
                priority=2
            ),
            AgentCapability(
                name="map_generation",
                description="生成地图和可视化",
                keywords=["地图", "生成地图", "可视化", "map", "visualization"],
                requires_data=True,
                priority=2
            ),
            AgentCapability(
                name="coordinate_conversion",
                description="坐标系转换",
                keywords=["坐标系", "投影", "转换", "crs", "coordinate"],
                requires_data=True,
                priority=2
            ),
            AgentCapability(
                name="gis_query",
                description="GIS 空间查询",
                keywords=["查询", "查找", "search", "query", "附近"],
                requires_data=True,
                priority=2
            ),
            AgentCapability(
                name="statistics_analysis",
                description="统计分析",
                keywords=["统计", "分析", "count", "sum", "average"],
                requires_data=True,
                priority=2
            )
        ]

    @property
    def capabilities(self) -> List[AgentCapability]:
        return self._capabilities

    async def can_handle(self, user_query: str, context: Optional[Dict[str, Any]] = None) -> float:
        """判断是否能处理该请求"""
        # 检查关键词匹配
        keyword_score = self.matches_keywords(user_query)

        # 检查是否有数据文件（从 context 或作为参数）
        has_data = context and context.get("has_data_files", False)
        if has_data and keyword_score > 0:
            return 0.95  # 有数据文件且有关键词匹配，非常高置信度

        # 检查是否涉及 GIS 相关词汇
        gis_terms = ["gis", "地图", "空间", "地理", "坐标", "投影", "choropleth",
                     "热力图", "等值线", "多边形", "点", "线", "面"]
        query_lower = user_query.lower()
        gis_score = sum(1 for term in gis_terms if term in query_lower) / len(gis_terms)

        # 综合评分
        final_score = keyword_score * 0.6 + gis_score * 0.4
        return min(final_score, 1.0)

    async def execute(
        self,
        user_query: str,
        data_paths: List[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> AgentResponse:
        """执行 GIS 分析任务"""
        try:
            logger.info(f"[GISAgentAdapter] Processing query: {user_query[:50]}...")

            # 设置会话 ID（用于 SSE 推送）
            if session_id:
                self._workflow.set_session_id(session_id)

            # 执行工作流
            import uuid
            task_id = context.get("task_id") if context else None
            if not task_id:
                task_id = str(uuid.uuid4())

            # 调用 GIS 工作流
            final_state = self._workflow.execute_task(
                task_id=task_id,
                user_query=user_query,
                data_paths=data_paths or [],
                context=context or {}
            )

            # 转换为统一响应格式
            status = final_state.get("status", "unknown")
            is_success = status == "completed"

            # 构建响应内容
            if is_success:
                content = "GIS 分析任务已完成。"
            elif status == "failed":
                content = f"GIS 分析任务失败。"
            else:
                content = f"GIS 分析任务状态: {status}"

            # 获取结果
            result = final_state.get("analysis_result")
            errors = final_state.get("errors", [])
            warnings = final_state.get("warnings", [])

            return AgentResponse(
                success=is_success,
                content=content,
                data=result,
                status=status,
                errors=errors,
                metadata={
                    "agent": self.name,
                    "agent_type": self.agent_type.value,
                    "version": self.version,
                    "task_id": task_id,
                    "warnings": warnings
                }
            )

        except Exception as e:
            logger.error(f"[GISAgentAdapter] Error: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                content="GIS 分析过程中发生错误。",
                status="failed",
                errors=[str(e)]
            )

    def get_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            "name": self.name,
            "type": self.agent_type.value,
            "version": self.version,
            "description": "GIS 空间数据分析 Agent",
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description,
                    "requires_data": c.requires_data
                }
                for c in self.capabilities
            ],
            "workflow_info": {
                "nodes": self._workflow.get_node_names() if hasattr(self._workflow, "get_node_names") else []
            }
        }

    def get_workflow(self) -> GISAgentWorkflow:
        """获取底层工作流实例"""
        return self._workflow