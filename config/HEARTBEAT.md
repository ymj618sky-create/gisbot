# HEARTBEAT.md

## Memory & Heartbeat System

### Memory Architecture

The GIS Agent uses a **dual-layer memory system** for optimal performance and persistence.

#### Short-Term Memory (Session)
- **Location**: `workspace/data/sessions/{session_id}.json`
- **Scope**: Current conversation only
- **Capacity**: Last 50 messages (configurable via `MEMORY_WINDOW`)
- **Lifecycle**: Persists across multiple interactions within same session
- **Content**: User messages, assistant responses, tool calls, results

#### Long-Term Memory (Persistent)
- **Location**: `workspace/memory/MEMORY.md`
- **Scope**: Across all sessions and conversations
- **Structure**: Markdown with timestamped entries
- **Purpose**: Store important facts, user preferences, learned patterns
- **Update**: Written when agent learns something valuable for future use

#### History Log (Audit Trail)
- **Location**: `workspace/memory/HISTORY.md`
- **Structure**: Timestamped entries in format `[YYYY-MM-DD HH:MM]`
- **Purpose**: Complete audit trail of all operations
- **Usage**: Debugging, analysis review, workflow reconstruction

### Memory Operations

#### Writing to Long-Term Memory

The agent should write to MEMORY.md when:
- Learning about a user's preferred data formats
- Discovering common workflows or patterns
- Remembering data quality issues with specific sources
- Storing coordinate system preferences for regions
- Noting successful analysis approaches

**Format**:
```markdown
## [YYYY-MM-DD HH:MM]

### Learned: [Topic]

[Description of what was learned and why it matters]
```

#### Reading from Long-Term Memory

The agent reads MEMORY.md at startup and should:
- Reference stored preferences when making decisions
- Apply learned patterns to similar problems
- Warn about known data quality issues
- Use previously successful approaches

### Session State Management

Each session maintains:
- **Session ID**: Unique identifier (UUID)
- **Channel**: Communication channel (web, cli, etc.)
- **Chat ID**: User identifier within channel
- **Messages**: Conversation history
- **Metadata**: Additional session properties

### Heartbeat Signals

The agent sends heartbeat signals to indicate:
- **Processing**: Agent is actively working on a task
- **Thinking**: LLM is reasoning or generating response
- **Tool Execution**: Tool is running (may take time)
- **Idle**: Waiting for user input
- **Error**: Something went wrong

#### Heartbeat Types

1. **Building context...** - Gathering session history and tools
2. **Processing (iteration N/M)...** - Agent loop iteration in progress
3. **Executing N tool(s)...** - Tools are being called
4. **Response generated** - Final answer ready
5. **Error occurred** - Something failed

### Memory Quality Guidelines

**What to Store**:
- User preferences (CRS, formats, output styles)
- Data source characteristics
- Common analysis patterns
- Error prevention tips
- Successful workflow templates

**What NOT to Store**:
- Transient conversation details
- Temporary file locations (unless significant)
- Single-use queries
- Failed experiments (unless informative)

### Memory Maintenance

**Automatic Cleanup**:
- Old sessions are archived after extended inactivity
- History.md can grow indefinitely - consider rotation for long-running systems

**Manual Cleanup**:
- Review MEMORY.md periodically for outdated information
- Consolidate redundant entries
- Update changed facts or preferences

### Memory-Augmented Responses

When responding, the agent should:
1. Check MEMORY.md for relevant context
2. Reference stored preferences when applicable
3. Note when it's applying learned patterns
4. Update MEMORY.md after learning something new

**Example**:
> Based on your previous analysis [see MEMORY.md 2024-03-15], you prefer EPSG:4528 for China data. I've used that CRS for this analysis.

---

*Good memory makes the agent smarter over time.*