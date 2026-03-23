"""System tools for file operations, script execution, and more."""

import asyncio
import difflib
import os
import re
from pathlib import Path
from typing import Any

from core.tools.base import Tool


# Helper function to get configured Python path
def get_python_path() -> str:
    """Get the configured Python path, falling back to system python."""
    # Try to get from environment variable first (loaded from .env)
    python_path = os.environ.get("ARCGIS_PRO_PYTHON", None)
    if python_path and Path(python_path).exists():
        return python_path
    # Try to get from config module
    try:
        from config import settings
        if hasattr(settings, 'ARCGIS_PRO_PYTHON') and settings.ARCGIS_PRO_PYTHON:
            check_path = Path(settings.ARCGIS_PRO_PYTHON)
            if check_path.exists():
                return str(check_path)
    except ImportError:
        pass
    # Fall back to python
    return "python"


class ListFilesTool(Tool):
    """Tool for listing files and directories in a given path."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "list_files"

    @property
    def description(self) -> str:
        return "List files and directories. Paths are relative to workspace directory. Use '.' to list workspace root."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list (relative to workspace, or absolute)"
                }
            },
            "required": ["path"]
        }

    async def execute(self, path: str, **kwargs) -> str:
        try:
            dir_path = Path(path)
            if not dir_path.is_absolute():
                dir_path = self.workspace / dir_path

            if not dir_path.exists():
                return f"Error: Path not found: {dir_path}"

            if not dir_path.is_dir():
                return f"Error: Not a directory: {dir_path}"

            items = []
            for item in sorted(dir_path.iterdir()):
                prefix = "📁 " if item.is_dir() else "📄 "
                # Show relative path if inside workspace
                display_name = item.name
                try:
                    rel = item.relative_to(self.workspace)
                    display_name = str(rel)
                except ValueError:
                    pass
                items.append(f"{prefix}{display_name}")

            if not items:
                return f"Directory {path} is empty"

            return "\n".join(items)

        except PermissionError:
            return f"Error: Permission denied accessing {path}"
        except Exception as e:
            return f"Error listing files: {str(e)}"


class ReadFileTool(Tool):
    """Tool for reading text file contents."""

    _MAX_CHARS = 128_000

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return "Read the contents of a file. Paths are relative to workspace unless absolute."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace, or absolute)"
                }
            },
            "required": ["path"]
        }

    async def execute(self, path: str, **kwargs) -> str:
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = self.workspace / file_path

            if not file_path.exists():
                return f"Error: File not found: {file_path}"

            if not file_path.is_file():
                return f"Error: Not a file: {file_path}"

            size = file_path.stat().st_size
            if size > self._MAX_CHARS * 4:
                return (
                    f"Error: File too large ({size:,} bytes). "
                    f"Use exec tool with head/tail/grep to read portions."
                )

            content = file_path.read_text(encoding="utf-8")
            if len(content) > self._MAX_CHARS:
                content = content[: self._MAX_CHARS] + f"\n\n... (truncated — file is {len(content):,} chars, limit {self._MAX_CHARS:,})"
            return content

        except PermissionError:
            return f"Error: Permission denied reading {path}"
        except Exception as e:
            return f"Error reading file: {str(e)}"


class WriteFileTool(Tool):
    """Tool for writing content to a text file."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "write_file"

    @property
    def description(self) -> str:
        return "Write content to a text file. Creates parent directories if needed. File paths are relative to the workspace directory (use absolute paths to write outside workspace). Example: write_file(path='myfile.txt', content='hello')"

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace, or absolute)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                }
            },
            "required": ["path", "content"]
        }

    async def execute(self, path: str, content: str, **kwargs) -> str:
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = self.workspace / file_path

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")

            # Show relative path if inside workspace
            display_path = path
            try:
                rel = file_path.relative_to(self.workspace)
                display_path = f"workspace/{rel}"
            except ValueError:
                pass

            return f"Successfully wrote {len(content)} bytes to {display_path}"

        except PermissionError:
            return f"Error: Permission denied writing to {path}"
        except Exception as e:
            return f"Error writing file: {str(e)}"


class EditFileTool(Tool):
    """Tool for editing a file by replacing text."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "edit_file"

    @property
    def description(self) -> str:
        return "Edit a file by replacing old_text with new_text. The old_text must exist exactly in the file. Paths are relative to workspace unless absolute."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file (relative to workspace, or absolute)"
                },
                "old_text": {
                    "type": "string",
                    "description": "The exact text to find and replace"
                },
                "new_text": {
                    "type": "string",
                    "description": "The text to replace with"
                }
            },
            "required": ["path", "old_text", "new_text"]
        }

    async def execute(self, path: str, old_text: str, new_text: str, **kwargs) -> str:
        try:
            file_path = Path(path)
            if not file_path.is_absolute():
                file_path = self.workspace / file_path

            if not file_path.exists():
                return f"Error: File not found: {path}"

            content = file_path.read_text(encoding="utf-8")

            if old_text not in content:
                return self._not_found_message(old_text, content, path)

            # Count occurrences
            count = content.count(old_text)
            if count > 1:
                return f"Warning: old_text appears {count} times. Please provide more context to make it unique."

            new_content = content.replace(old_text, new_text, 1)
            file_path.write_text(new_content, encoding="utf-8")

            # Show relative path if inside workspace
            display_path = path
            try:
                rel = file_path.relative_to(self.workspace)
                display_path = f"workspace/{rel}"
            except ValueError:
                pass

            return f"Successfully edited {display_path}"

        except PermissionError:
            return f"Error: Permission denied editing {path}"
        except Exception as e:
            return f"Error editing file: {str(e)}"

    @staticmethod
    def _not_found_message(old_text: str, content: str, path: str) -> str:
        """Build a helpful error when old_text is not found."""
        lines = content.splitlines(keepends=True)
        old_lines = old_text.splitlines(keepends=True)
        window = len(old_lines)

        best_ratio, best_start = 0.0, 0
        for i in range(max(1, len(lines) - window + 1)):
            ratio = difflib.SequenceMatcher(None, old_lines, lines[i : i + window]).ratio()
            if ratio > best_ratio:
                best_ratio, best_start = ratio, i

        if best_ratio > 0.5:
            diff = "\n".join(
                difflib.unified_diff(
                    old_lines,
                    lines[best_start : best_start + window],
                    fromfile="old_text (provided)",
                    tofile=f"{path} (actual, line {best_start + 1})",
                    lineterm="",
                )
            )
            return f"Error: old_text not found in {path}.\nBest match ({best_ratio:.0%} similar) at line {best_start + 1}:\n{diff}"
        return (
            f"Error: old_text not found in {path}. No similar text found. Verify the file content."
        )


class ExecuteCommandTool(Tool):
    """Tool for executing shell commands."""

    def __init__(self, workspace: Path | None = None, timeout: int = 60, working_dir: str | None = None):
        self.workspace = workspace or Path.cwd()
        self.timeout = timeout
        self.working_dir = working_dir
        # Get Python path for Windows
        self.python_path = get_python_path()
        self.deny_patterns = [
            r"\brm\s+-[rf]{1,2}\b",
            r"\bdel\s+/[fq]\b",
            r"\brmdir\s+/s\b",
            r"(?:^|[;&|]\s*)format\b",
            r"\b(mkfs|diskpart)\b",
            r"\bdd\s+if=",
            r">\s*/dev/sd",
            r"\b(shutdown|reboot|poweroff)\b",
            r":\(\)\s*\{.*\};\s*:",
        ]

    @property
    def name(self) -> str:
        return "exec"

    @property
    def description(self) -> str:
        return "Execute a shell command. Working directory defaults to workspace. Use with caution."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "working_dir": {
                    "type": "string",
                    "description": "Optional working directory (defaults to workspace)"
                }
            },
            "required": ["command"]
        }

    async def execute(self, command: str, working_dir: str | None = None, **kwargs) -> str:
        try:
            # Determine working directory
            if working_dir:
                if Path(working_dir).is_absolute():
                    cwd = working_dir
                else:
                    cwd = str(self.workspace / working_dir)
            else:
                cwd = str(self.working_dir or self.workspace)

            guard_error = self._guard_command(command, cwd)
            if guard_error:
                return guard_error

            # On Windows, handle encoding properly
            import sys
            if sys.platform == 'win32':
                # Replace 'python' in command with configured path
                import re
                command = re.sub(r'\bpython\b', f'"{self.python_path}"', command)

            # Run command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return f"Error: Command timed out after {self.timeout} seconds"

            output_parts = []

            # Decode with proper encoding
            def decode_output(data: bytes) -> str:
                if not data:
                    return ""
                # On Windows, try GBK (CP936) first for system commands, then UTF-8
                if sys.platform == 'win32':
                    try:
                        return data.decode("gbk", errors="replace")
                    except (UnicodeDecodeError, LookupError):
                        pass
                # Try UTF-8
                try:
                    return data.decode("utf-8", errors="replace")
                except UnicodeDecodeError:
                    # Fall back to system encoding
                    import locale
                    return data.decode(locale.getpreferredencoding(), errors="replace")

            if stdout:
                output_parts.append(decode_output(stdout))

            if stderr:
                stderr_text = decode_output(stderr)
                if stderr_text.strip():
                    output_parts.append(f"STDERR:\n{stderr_text}")

            if process.returncode != 0:
                output_parts.append(f"\nExit code: {process.returncode}")

            result = "\n".join(output_parts) if output_parts else "(no output)"

            # Truncate very long output
            max_len = 10000
            if len(result) > max_len:
                result = result[:max_len] + f"\n... (truncated, {len(result) - max_len} more chars)"

            return result

        except PermissionError:
            return "Error: Permission denied executing command"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    def _guard_command(self, command: str, cwd: str) -> str | None:
        """Best-effort safety guard for potentially destructive commands."""
        cmd = command.strip()
        lower = cmd.lower()

        for pattern in self.deny_patterns:
            if re.search(pattern, lower):
                return "Error: Command blocked by safety guard (dangerous pattern detected)"

        if "..\\" in cmd or "../" in cmd:
            return "Error: Command blocked by safety guard (path traversal detected)"

        return None

    @staticmethod
    def _extract_absolute_paths(command: str) -> list[str]:
        """Extract absolute paths from command."""
        win_paths = re.findall(r"[A-Za-z]:\\[^\s\"'|><;]+", command)
        posix_paths = re.findall(r"(?:^|[\s|>])(/[^\s\"'>]+)", command)
        return win_paths + posix_paths


class RunPythonScriptTool(Tool):
    """Tool for executing Python scripts."""

    def __init__(self, workspace: Path | None = None, timeout: int = 60):
        self.workspace = workspace or Path.cwd()
        self.timeout = timeout
        # Use configured Python path
        self.python_path = get_python_path()

    @property
    def name(self) -> str:
        return "run_python"

    @property
    def description(self) -> str:
        return "Execute a Python script file. Returns stdout and stderr. Paths are relative to workspace unless absolute."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the Python script (relative to workspace, or absolute)"
                },
                "args": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Command line arguments to pass to the script (optional)"
                }
            },
            "required": ["path"]
        }

    async def execute(self, path: str, args: list[str] | None = None, **kwargs) -> str:
        try:
            script = Path(path)
            if not script.is_absolute():
                script = self.workspace / path

            if not script.exists():
                return f"Error: Script not found: {script}"

            if not script.is_file():
                return f"Error: Not a file: {script}"

            # Verify Python path exists
            python_exec = Path(self.python_path)
            if not python_exec.exists():
                # Try to use system python as fallback
                self.python_path = "python"
                python_exec = Path(self.python_path)
                if not python_exec.exists():
                    return f"Error: Python interpreter not found at {self.python_path}. Please configure ARCGIS_PRO_PYTHON environment variable."

            # Prepare command - use configured Python path
            cmd = [self.python_path, str(script)]
            if args:
                cmd.extend(args)

            # Run script
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(script.parent)
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return f"Error: Script execution timed out after {self.timeout} seconds"

            stdout_text = stdout.decode("utf-8", errors="replace")
            stderr_text = stderr.decode("utf-8", errors="replace")

            # Show relative path if inside workspace
            display_path = path
            try:
                rel = script.relative_to(self.workspace)
                display_path = f"workspace/{rel}"
            except ValueError:
                pass

            result = [
                f"Script: {display_path}",
                f"Python: {self.python_path}",
                f"Exit code: {process.returncode}"
            ]

            if stdout_text:
                result.append(f"\n=== STDOUT ===\n{stdout_text}")

            if stderr_text:
                result.append(f"\n=== STDERR ===\n{stderr_text}")

            if process.returncode == 0:
                result.append("\n✓ Script executed successfully")
            else:
                result.append(f"\n✗ Script failed with exit code {process.returncode}")

            return "\n".join(result)

        except PermissionError:
            return f"Error: Permission denied executing {path}"
        except Exception as e:
            return f"Error running Python script: {str(e)}"


class WebSearchTool(Tool):
    """Tool for searching the web using Tavily or Brave Search API."""

    def __init__(self, api_key: str | None = None, max_results: int = 5, provider: str = "tavily"):
        # Load .env file to ensure API keys are available
        from dotenv import load_dotenv
        load_dotenv()

        self._init_api_key = api_key
        self.max_results = max_results
        self.provider = provider.lower()  # "tavily" or "brave"

        # Cache API keys at init time
        import os
        self._cached_tavily_key = self._init_api_key or os.environ.get("TAVILY_API_KEY", "")
        self._cached_brave_key = os.environ.get("BRAVE_API_KEY", "")

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web using Tavily or Brave Search. Returns titles, URLs, and snippets."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of results (1-10)",
                    "minimum": 1,
                    "maximum": 10
                },
                "provider": {
                    "type": "string",
                    "description": "Search provider (tavily or brave, default: tavily)",
                    "enum": ["tavily", "brave"]
                }
            },
            "required": ["query"]
        }

    @property
    def tavily_api_key(self) -> str:
        """Resolve Tavily API key at call time."""
        return self._cached_tavily_key

    @property
    def brave_api_key(self) -> str:
        """Resolve Brave API key at call time."""
        return self._cached_brave_key

    async def execute(self, query: str, count: int | None = None, provider: str | None = None, **kwargs) -> str:
        # Determine which provider to use
        use_provider = (provider or self.provider).lower()

        if use_provider == "tavily":
            return await self._search_tavily(query, count)
        elif use_provider == "brave":
            return await self._search_brave(query, count)
        else:
            return f"Error: Unknown provider '{provider}'. Use 'tavily' or 'brave'."

    async def _search_tavily(self, query: str, count: int | None = None) -> str:
        """Search using Tavily API."""
        api_key = self.tavily_api_key
        if not api_key:
            return "Error: Tavily API key not configured. Set TAVILY_API_KEY environment variable."

        try:
            import httpx
            n = min(max(count or self.max_results, 1), 10)

            async with httpx.AsyncClient() as client:
                r = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "max_results": n,
                        "search_depth": "basic",
                        "include_answer": False,
                        "include_raw_content": False
                    },
                    timeout=30.0
                )
                r.raise_for_status()

            data = r.json()
            results = data.get("results", [])

            if not results:
                return f"No results for: {query}"

            lines = [f"Results for: {query}\n"]
            for i, item in enumerate(results, 1):
                lines.append(f"{i}. {item.get('title', '')}")
                lines.append(f"   {item.get('url', '')}")
                if desc := item.get("content", ""):
                    # Truncate description if too long
                    if len(desc) > 200:
                        desc = desc[:200] + "..."
                    lines.append(f"   {desc}")
            return "\n".join(lines)

        except Exception as e:
            return f"Error searching with Tavily: {str(e)}"

    async def _search_brave(self, query: str, count: int | None = None) -> str:
        """Search using Brave Search API."""
        api_key = self.brave_api_key
        if not api_key:
            return "Error: Brave Search API key not configured. Set BRAVE_API_KEY environment variable."

        try:
            import httpx
            n = min(max(count or self.max_results, 1), 10)

            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": n},
                    headers={
                        "Accept": "application/json",
                        "X-Subscription-Token": api_key
                    },
                    timeout=10.0
                )
                r.raise_for_status()

            results = r.json().get("web", {}).get("results", [])[:n]
            if not results:
                return f"No results for: {query}"

            lines = [f"Results for: {query}\n"]
            for i, item in enumerate(results, 1):
                lines.append(f"{i}. {item.get('title', '')}")
                lines.append(f"   {item.get('url', '')}")
                if desc := item.get("description"):
                    lines.append(f"   {desc}")
            return "\n".join(lines)

        except Exception as e:
            return f"Error searching with Brave: {str(e)}"


class WebFetchTool(Tool):
    """Tool for fetching and extracting content from URLs."""

    def __init__(self, max_chars: int = 50000):
        self.max_chars = max_chars

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch URL and extract readable content (HTML → text)."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to fetch"
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Maximum characters to extract (default: 50000)"
                }
            },
            "required": ["url"]
        }

    async def execute(self, url: str, max_chars: int | None = None, **kwargs) -> str:
        try:
            import html
            import httpx

            max_chars = max_chars or self.max_chars

            # Validate URL
            from urllib.parse import urlparse
            p = urlparse(url)
            if p.scheme not in ('http', 'https'):
                return f"Error: Only http/https URLs allowed, got '{p.scheme}'"
            if not p.netloc:
                return "Error: Missing domain"

            async with httpx.AsyncClient(
                follow_redirects=True,
                max_redirects=5,
                timeout=30.0
            ) as client:
                r = await client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                )
                r.raise_for_status()

            ctype = r.headers.get("content-type", "")

            if "application/json" in ctype:
                return r.text

            if "text/html" in ctype or r.text[:256].lower().startswith(("<!doctype", "<html")):
                # Strip HTML tags
                content = re.sub(r'<script[\s\S]*?</script>', '', r.text, flags=re.I)
                content = re.sub(r'<style[\s\S]*?</style>', '', content, flags=re.I)
                content = re.sub(r'<[^>]+>', '', content)
                content = html.unescape(content).strip()

                # Get title
                title_match = re.search(r'<title>([^<]*)</title>', r.text, re.I)
                if title_match:
                    content = f"# {title_match.group(1)}\n\n{content}"
            else:
                content = r.text

            truncated = len(content) > max_chars
            if truncated:
                content = content[:max_chars]

            return content

        except Exception as e:
            return f"Error: {str(e)}"


class RunArcPyTool(Tool):
    """Tool for executing ArcGIS geoprocessing tools."""

    def __init__(self, workspace: Path | None = None):
        self.workspace = workspace or Path.cwd()

    @property
    def name(self) -> str:
        return "run_arcpy"

    @property
    def description(self) -> str:
        return "Execute an ArcGIS geoprocessing tool using ArcPy. Requires ArcGIS Pro/ArcMap."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "toolbox": {
                    "type": "string",
                    "description": "ArcGIS toolbox path or alias (e.g., 'analysis', 'management')"
                },
                "tool": {
                    "type": "string",
                    "description": "Name of the ArcPy tool to execute"
                },
                "parameters": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tool parameters as a list of strings"
                }
            },
            "required": ["toolbox", "tool"]
        }

    async def execute(self, toolbox: str, tool: str, parameters: list[str] | None = None, **kwargs) -> str:
        try:
            import arcpy

            # Add toolbox
            if arcpy.Exists(toolbox) and toolbox.endswith(".tbx"):
                arcpy.AddToolbox(toolbox)

            # Get parameters
            tool_params = parameters or []

            # Execute tool
            arcpy.ImportToolbox(toolbox, "")
            output = arcpy.__getattr__(toolbox).__getattr__(tool)(*tool_params)

            result = [
                f"ArcPy Tool: {tool}",
                f"Toolbox: {toolbox}",
                f"Parameters: {tool_params if tool_params else 'None'}",
                f"\n=== Result ===\n{output}",
                "\n✓ ArcPy tool executed successfully"
            ]

            return "\n".join(result)

        except ImportError:
            return "Error: ArcPy not installed. This tool requires ArcGIS Pro or ArcMap."
        except Exception as e:
            return f"Error executing ArcPy tool: {str(e)}"