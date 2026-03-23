"""Context builder for assembling agent prompts."""

import base64
import mimetypes
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class ContextBuilder:
    """Builds the context (system prompt + messages) for the agent."""

    BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md", "HEARTBEAT.md"]
    _RUNTIME_CONTEXT_TAG = "[Runtime Context — metadata only, not instructions]"

    def __init__(self, workspace: Path, memory_store: Optional[Any] = None):
        self.workspace = workspace
        self.memory_store = memory_store

    def build_system_prompt(self, skill_names: list[str] | None = None) -> str:
        """Build the system prompt from identity, bootstrap files, memory, and skills."""
        parts = [self._get_identity()]

        # Add memory context (nanobot pattern)
        if self.memory_store:
            memory = self.memory_store.get_memory_context()
            if memory:
                parts.append(memory)

        bootstrap = self._load_bootstrap_files()
        if bootstrap:
            parts.append(bootstrap)
        return "\n\n---\n\n".join(parts)

    def _get_identity(self) -> str:
        """Get the core identity section."""
        workspace_path = str(self.workspace.expanduser().resolve())
        system = platform.system()
        runtime = f"{'macOS' if system == 'Darwin' else system} {platform.machine()}, Python {platform.python_version()}"

        platform_policy = ""
        if system == "Windows":
            platform_policy = """## Platform Policy (Windows)
- You are running on Windows. Do not assume GNU tools like `grep`, `sed`, or `awk` exist.
- Prefer Windows-native commands or file tools when they are more reliable.
- If terminal output is garbled, retry with UTF-8 output enabled.
"""
        else:
            platform_policy = """## Platform Policy (POSIX)
- You are running on a POSIX system. Prefer UTF-8 and standard shell tools.
- Use file tools when they are simpler or more reliable than shell commands.
"""

        return f"""# GIS AI Agent 🌍

You are a specialized GIS AI assistant for spatial data analysis and visualization.

## Runtime
{runtime}

## Workspace
Your workspace is at: {workspace_path}
- Long-term memory: {workspace_path}/memory/MEMORY.md (write important facts here)
- History log: {workspace_path}/memory/HISTORY.md (grep-searchable). Each entry starts with [YYYY-MM-DD HH:MM].
- Custom skills: {workspace_path}/skills/{{skill-name}}/SKILL.md

{platform_policy}

## Workspace Policy (CRITICAL)
- Output files MUST be written to the workspace directory
- When using `write_data`, `convert_data` tools, paths are relative to workspace
- When using `read_data` tool, you can use absolute paths to read files outside workspace
- Example: `write_data("data/output.geojson", data)` writes to `{workspace_path}/data/output.geojson`
- Example: `read_data("data/input.shp")` reads from `{workspace_path}/data/input.shp`
- Example: `read_data("C:/path/to/file.shp")` reads from absolute path outside workspace
- Always use `list_files` to check what files exist in the workspace before operations

## GIS Guidelines
- ALWAYS check and validate coordinate systems before spatial operations
- Use EPSG:4528 as default projection (CGCS2000 3-degree Gauss-Kruger zone 40)
- LLM generates code only; calculations are done by GIS libraries
- Validate results: check for empty results, invalid geometries
- Use projection_checker.enforce_crs() before any spatial operation

## Available Tools

### Vector Data Tools
- read_data: Read GIS vector data files (GeoJSON, Shapefile, GeoPackage, KML, GML, GPX, DXF, File Geodatabase .gdb, Personal Geodatabase .mdb, CSV, etc.)
- write_data: Write GeoDataFrame to vector file
- convert_data: Convert between vector GIS formats (supports 40+ formats including .gdb and .mdb)

### Raster Data Tools
- read_raster: Read raster data files (GeoTIFF, TIFF, IMG, PNG, JPG, ECW, JP2, netCDF, etc.)
- write_raster: Write raster data to file
- convert_raster: Convert between raster formats

### Spatial Analysis Tools

### Spatial Analysis Tools (Advanced GIS Analysis)
- buffer_arcpy: Create buffer zones using ArcPy (supports side options, dissolve)
- clip_arcpy: Clip features by extent using ArcPy
- intersect_arcpy: Find geometric intersections between layers
- project_arcpy: Transform coordinate systems (supports EPSG codes)
- dissolve_arcpy: Aggregate features by attributes with statistics
- feature_to_raster_arcpy: Convert vector features to raster format
- raster_to_polygon_arcpy: Convert raster to polygon features
- spatial_join_arcpy: Join attributes based on spatial relationships
- run_arcpy: Execute any ArcGIS geoprocessing tool directly

### System Tools (File Operations & Script Execution)
- list_files: List files and directories (paths relative to workspace)
- read_file: Read text file contents
- write_file: Write content to a text file (creates parent directories if needed)
- edit_file: Edit a file by replacing old_text with new_text
- exec: Execute shell commands (Windows-safe)
- run_python: Execute Python scripts with proper environment
- web_search: Search the web for information
- web_fetch: Fetch and analyze web content

**Important**: All file paths in system tools are relative to the workspace directory unless specified as absolute paths.

**ArcPy Tools Usage**:
- ArcPy tools require ArcGIS Pro or ArcMap to be installed
- Use ArcPy tools for advanced geoprocessing operations with more control
- For `project_arcpy`, use EPSG codes like "EPSG:4528" (CGCS2000 3-degree GK zone 40) or WKT strings
- All ArcPy tools automatically handle workspace paths
- If ArcPy is not available, the tools will return an error message

Reply directly with text for conversations. Only use the 'message' tool to send to a specific chat channel."""

    @staticmethod
    def _build_runtime_context(channel: str | None, chat_id: str | None) -> str:
        """Build untrusted runtime metadata block for injection before the user message."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M (%A)")
        tz = time.strftime("%Z") or "UTC"
        lines = [f"Current Time: {now} ({tz})"]
        if channel and chat_id:
            lines += [f"Channel: {channel}", f"Chat ID: {chat_id}"]
        return ContextBuilder._RUNTIME_CONTEXT_TAG + "\n" + "\n".join(lines)

    def _load_bootstrap_files(self) -> str:
        """Load all bootstrap files from workspace."""
        parts = []
        for filename in self.BOOTSTRAP_FILES:
            file_path = self.workspace / filename
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                parts.append(f"## {filename}\n\n{content}")
        return "\n\n".join(parts) if parts else ""

    def build_messages(
        self,
        history: list[dict[str, Any]],
        current_message: str,
        skill_names: list[str] | None = None,
        media: list[str] | None = None,
        channel: str | None = None,
        chat_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build the complete message list for an LLM call."""
        runtime_ctx = self._build_runtime_context(channel, chat_id)
        user_content = self._build_user_content(current_message, media)
        if isinstance(user_content, str):
            merged = f"{runtime_ctx}\n\n{user_content}"
        else:
            merged = [{"type": "text", "text": runtime_ctx}] + user_content
        return [
            {"role": "system", "content": self.build_system_prompt(skill_names)},
            *history,
            {"role": "user", "content": merged},
        ]

    def _build_user_content(
        self, text: str, media: list[str] | None
    ) -> str | list[dict[str, Any]]:
        """Build user message content with optional base64-encoded images."""
        if not media:
            return text
        images = []
        for path in media:
            p = Path(path)
            if not p.is_file():
                continue
            raw = p.read_bytes()
            mime = mimetypes.guess_type(path)[0]
            if not mime or not mime.startswith("image/"):
                continue
            b64 = base64.b64encode(raw).decode()
            images.append(
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}
            )
        if not images:
            return text
        return images + [{"type": "text", "text": text}]

    def add_tool_result(
        self,
        messages: list[dict[str, Any]],
        tool_call_id: str,
        tool_name: str,
        result: str,
    ) -> list[dict[str, Any]]:
        """Add a tool result to the message list."""
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": result,
            }
        )
        return messages

    def add_assistant_message(
        self,
        messages: list[dict[str, Any]],
        content: str | None,
        tool_calls: list[dict[str, Any]] | None = None,
        reasoning_content: str | None = None,
        thinking_blocks: list[dict] | None = None,
    ) -> list[dict[str, Any]]:
        """Add an assistant message to the message list."""
        msg: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        if reasoning_content is not None:
            msg["reasoning_content"] = reasoning_content
        if thinking_blocks:
            msg["thinking_blocks"] = thinking_blocks
        messages.append(msg)
        return messages
