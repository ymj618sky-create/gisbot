# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Server
```bash
# Run with auto-reload
python main.py

# Or with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Testing
```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/unit/agent/test_loop.py

# Run e2e tests only
pytest -m e2e

# Run with verbose output
pytest -v
```

### Linting
```bash
# The project uses ruff for linting
ruff check .
ruff format .
```

## Architecture Overview

### Agent Loop Pattern
The system uses an **Agent Loop** architecture (`core/agent/loop.py`) that orchestrates conversations:
1. `AgentLoop.process_direct()` - Entry point for user messages
2. `_run_agent_loop()` - Main iteration loop with max_iterations limit
3. Calls LLM via `provider.chat()` with tools
4. Executes tools via `tool_registry.execute()`
5. Manages session history and memory consolidation

### Configuration System
- **Environment-based** (`config.py`): Loads from `.env`, provides `Settings` class
- **JSON-based** (`core/config/`): Loads `config.json` for models, tools, timeout configs
- **TimeoutConfig** (`core/config/timeout.py`): Centralized timeout management (LLM, exec, SSE, max_iterations)

### Key Components

| Module | Purpose |
|--------|---------|
| `core/agent/loop.py` | Main agent conversation loop orchestration |
| `core/agent/context.py` | System prompt and message history builder |
| `core/providers/factory.py` | Creates LLM provider instances (Dashscope, Anthropic, OpenAI) |
| `core/tools/registry.py` | Dynamic tool registration and execution |
| `session/manager.py` | Session persistence with context memory |
| `api/routes/agent.py` | FastAPI routes (chat, SSE streaming, tools, sessions) |

### Tool System
Tools inherit from `core/tools/base.py::Tool`:
- Each tool defines `name`, `description`, `parameters` (JSON schema), and `execute()`
- Registered with `ToolRegistry` and exposed to LLM via OpenAI function schema
- Tool parameters are automatically validated and cast before execution

### Session Management
- Sessions are stored as JSON files in `workspace/data/sessions/`
- Each session has: messages, metadata, title, tags, context_memory
- Memory consolidation automatically extracts facts/patterns from assistant messages

## Configuration

### Environment Variables (.env)
Required for running:
- `DASHSCOPE_API_KEY` - Default provider API key
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` - Alternative providers
- `DEFAULT_PROVIDER` - Provider selection (dashscope, anthropic, openai)
- `WORKSPACE_DIR`, `DATA_DIR` - Paths for data storage

See `.env.example` for full configuration options.

### JSON Config (config.json)
- Models: Defines available models per provider
- Tools: Lists enabled tools and supported formats
- Timeout: LLM request, exec, SSE, max_iterations settings
- Defaults: CRS (EPSG:4528), workspace paths

## API Endpoints

- `POST /api/chat` - Standard chat endpoint
- `GET /api/stream/{channel}/{chat_id}` - SSE streaming chat (for EventSource)
- `POST /api/stream/{channel}/{chat_id}` - POST-based SSE streaming
- `GET /api/tools` - List registered tools
- `GET /api/sessions` - List sessions
- `GET /api/config` - Get current configuration status

## Important Patterns

### Timeout Configuration
All timeouts are centrally managed via `TimeoutConfig`:
```python
from core.config import get_timeout_config
timeout = get_timeout_config()
# timeout.llm_request, timeout.exec_command, timeout.run_python, etc.
```

### Provider Creation
```python
from core.providers.factory import create_provider
provider = create_provider(
    provider_name="dashscope",
    api_key="...",
    timeout=300
)
```

### Tool Registration
```python
from core.tools.registry import ToolRegistry
from core.tools.data.read import ReadDataTool

registry = ToolRegistry()
registry.register(ReadDataTool(workspace))
```

## Workspace Structure

- `workspace/` - Main working directory (data files go here)
- `workspace/data/` - GIS data files and session storage
- `workspace/data/sessions/` - Session JSON files
- `memory/` - Long-term memory (MEMORY.md, HISTORY.md)
- `static/` - Web UI files
- `skills/` - Custom skills (each has SKILL.md)

## Testing Notes

- E2E tests mock the `get_agent_loop()` function in `api/routes/agent.py`
- Use `pytest-asyncio` for async test support
- Coverage is configured for `core`, `api`, and `session` modules
- Session tests use temporary workspaces via `tmp_path` fixture