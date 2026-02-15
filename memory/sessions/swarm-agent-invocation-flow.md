# How /swarm Invokes AI Agents Through agent_manager

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        /swarm Command                          │
│  (User types: `/swarm "Design a REST API" --mode design`)      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    tools/swarm_task.js                         │
│  JavaScript tool (OpenCode Plugin)                             │
│  - Receives `/swarm` command                                    │
│  - Returns immediately (non-blocking)                          │
│  - Spawns subprocess: `bun ... swarm-cli.py run ...`            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    swarm-cli.py                                 │
│  Python CLI (runs in background)                               │
│  - Parses args (task, mode, context)                           │
│  - Loads OpenCodeSwarmManager to get agent sequence            │
│  - Uses AgentManager to actually spawn agents                  │
│  - Saves results to .coordination/                             │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                 AgentManager.spawn_agent()                     │
│  emergent-learning/agents/agent_manager.py                       │
│  1. Creates/reuses OpenCode session                            │
│  2. Loads agent persona from .md file                          │
│  3. Calls SDK with noReply=True (async)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│            opencode_sdk_client.mjs                             │
│  JavaScript SDK for OpenCode server                            │
│  - Action: "session_prompt"                                    │
│  - Payload: session_id, agent, model, parts, noReply           │
│  - Executes via: `bun opencode_sdk_client.mjs <json>`          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              OpenCode Server (Port 4096)                        │
│  - Receives SDK request                                        │
│  - Creates session with agent binding                          │
│  - Sends message to AI model (via provider)                    │
│  - Returns session_id immediately (async)                      │
│  - AI model processes in background                            │
└─────────────────────────────────────────────────────────────────┘
```

## Detailed Flow

### 1. User Invokes `/swarm`

```bash
/swarm "Design a REST API for user management" --mode design
```

### 2. `tools/swarm_task.js` (OpenCode Tool)

```javascript
// File: /home/bamer/.opencode/tools/swarm_task.js

async execute(args) {
    const mode = args.mode || 'all';
    const context = args.context || '';

    // Return immediately - fire and forget
    let response = `🚀 SWARM EXECUTION STARTED\n\n`;
    response += `Task: ${args.task}\n`;
    response += `Mode: ${mode}\n`;
    response += `Status: Running agents in background...`;

    // Build command and run async
    const cmdArgs = [SWARM_CLI, 'run', args.task, '--mode', mode];
    if (context) cmdArgs.push('--context', context);

    // Execute via Bun subprocess (non-blocking, no await)
    Bun.$`python3 ${cmdArgs}`
        .then(result => console.log(`[SWARM] Execution complete`))
        .catch(error => console.error(`[SWARM] Execution failed`));

    return response; // Returns immediately
}
```

**Key Points:**
- Non-blocking: Uses Bun's `$` syntax without await
- Fire-and-forget: Returns immediately while subprocess runs in background
- Uses Bun runtime: Required for opencode_sdk_client.mjs

### 3. `swarm-cli.py` (Python CLI)

```python
# File: /home/bamer/.opencode/swarm-cli.py

def cmd_run(args):
    """Run a swarm task by spawning AI agents via agent_manager."""

    # 1. Load swarm manager to get agent sequence
    swarm_manager = OpenCodeSwarmManager()
    mode = SwarmMode(args.mode)
    agent_sequence = swarm_manager.get_recommended_sequence(mode.value)
    # => ['architect', 'creative', 'skeptic'] for design mode

    # 2. Get AgentManager for actual agent invocation
    agent_manager = get_agent_manager()

    # 3. Build context
    mission_context = {
        "task": args.task,
        "context": args.context,
        "mode": mode.value,
    }

    # 4. Spawn each agent (async!)
    for agent_name in agent_sequence:
        agent_result = agent_manager.spawn_agent(
            agent_name=agent_name,
            mission=args.task,
            context={
                "agent_role": agent_name,
                "swarm_context": mission_context,
            }
        )

        # Returns immediately with session_id, no AI processing wait
        if agent_result.get("success"):
            session_id = agent_result.get("session_id")
            print(f"✅ {agent_name} spawned (session: {session_id[:12]}...)")

    # 5. Save results
    coord_dir = EMERGENT_LEARNING_DIR / ".coordination"
    result_file = coord_dir / f"swarm_result_{timestamp}.json"
    # Contains: task, mode, agents with session_ids
```

**Key Points:**
- Uses `AgentManager.spawn_agent()` which is async
- Does NOT wait for AI responses
- Returns session IDs immediately
- Saves results to `.coordination/` directory

### 4. `AgentManager.spawn_agent()` (The Core)

```python
# File: /home/bamer/.opencode/emergent-learning/agents/agent_manager.py

def spawn_agent(self, agent_name: str, mission: str, context: Dict = None) -> Dict:
    """
    Spawn an agent for a long-running async mission.
    Unlike ask_agent which waits for response, spawn_agent sends
    the mission asynchronously and returns immediately.
    """

    # Step 1: Load agent config from .md file
    agent_config = self.agents[agent_name]
    # Agent file: ~/.opencode/agents/OPC_ELF_System_Agents/architect.md
    # Parsed metadata: name, description, model, tags, etc.
    # System prompt: Full persona instruction text

    # Step 2: Ensure session exists
    session_id = self._ensure_session(agent_name)
    # - Checks if session in self.sessions[agent_name]
    # - If not, calls _create_session() to create new one
    # - Reuses existing session if title matches: "ELF Architect Session 14-02-2026"

    # Step 3: Build message
    message = mission
    if context:
        context_str = json.dumps(context, indent=2)
        message = f"Context:\n{context_str}\n\nMission:\n{mission}"

    # Step 4: Send via SDK (ASYNC!)
    provider_id, _, model_id = agent_config.model.partition("/")
    # provider_id = "model", model_id = "llamacpp/nemotron-v3-coder"

    prompt_result = self._sdk_request(
        "session_prompt",
        payload={
            "sessionId": session_id,
            "directory": str(self.workdir),  # "/home/bamer/.opencode/emergent-learning"
            "agent": agent_config.name,      # "architect"
            "model": {
                "providerID": provider_id,
                "modelID": model_id
            },
            "parts": [{"type": "text", "text": message}],
            "noReply": True,  # *** KEY: Don't wait for AI response ***
        },
    )

    # Step 5: Return immediately with session_id
    if prompt_result.get("success"):
        return {
            "success": True,
            "session_id": session_id,
            "agent": agent_name,
            "message": "Mission spawned successfully",
        }
    else:
        return {"success": False, "error": ...}
```

**Key Points:**
- **`noReply: True`** is the critical flag for async behavior
- Session management: Creates/reuses sessions per agent
- Agent loading: Parses `.md` files for system prompts
- Returns immediately after sending request

### 5. `_sdk_request()` (Communicates with OpenCode)

```python
def _sdk_request(self, action: str, payload: Dict) -> Dict:
    """
    Execute an OpenCode SDK CLI request via Bun subprocess.
    """

    # Build request JSON
    request_body = {
        "action": action,
        "baseUrl": "http://localhost:4096",
        "payload": payload,
    }

    # Execute SDK client via Bun
    result = subprocess.run(
        ["bun", str(SDK_CLIENT_PATH)],  # opencode_sdk_client.mjs
        input=json.dumps(request_body),
        capture_output=True,
        text=True,
        timeout=600,  # 10 minute timeout
    )

    # Parse response
    return json.loads(result.stdout)
```

**Key Points:**
- Uses Bun to execute JavaScript SDK client
- Sends JSON over stdin
- Reads JSON from stdout
- Handles timeouts and retries

### 6. `opencode_sdk_client.mjs` (The Bridge)

```javascript
// File: /home/bamer/.opencode/emergent-learning/agents/opencode_sdk_client.mjs

const input = await Bun.stdin.text();
const { action, baseUrl, payload } = JSON.parse(input);

if (action === "session_prompt") {
    // Create URL
    const url = `${baseUrl}/sessions/${payload.sessionId}/prompt`;

    // Send request to OpenCode server
    const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            agent: payload.agent,
            model: payload.model,
            parts: payload.parts,
            noReply: payload.noReply  // Passed from python!
        }),
    });

    const data = await response.json();
    console.log(JSON.stringify({ success: response.ok, data }));
}
```

**Key Points:**
- Reads JSON from stdin
- Makes HTTP request to OpenCode server
- Forwards `noReply` flag
- Returns JSON to stdout

### 7. OpenCode Server (Port 4096)

When `noReply: true`:

1. **Receive Request:**
   ```
   POST /sessions/ses_xxx/prompt
   Content-Type: application/json

   {
     "agent": "architect",
     "model": {"providerID": "model", "modelID": "llamacpp/nemotron-v3-coder"},
     "parts": [{"type": "text", "text": "Mission: Design a REST API..."}],
     "noReply": true
   }
   ```

2. **Process:**
   - Create/reuse session with ID `ses_xxx`
   - Bind agent persona (load from `AGENTS.md` or agent-specific file)
   - Queue the message for AI processing
   - **Return immediately** (before AI responds):
     ```json
     {
       "success": true,
       "data": {"sessionId": "ses_xxx"}
     }
     ```

3. **Background:**
   - AI model processes the message
   - Response appears in session messages
   - User can check OpenCode UI for progress

## Agent Persona Loading

Agent personas are loaded from:

```
~/.opencode/agents/OPC_ELF_System_Agents/
  ├── architect.md          # System: "You are a system design architect..."
  ├── researcher.md         # System: "You are an investigator..."
  ├── skeptic.md            # System: "You are a critical analyst..."
  ├── creative.md           # System: "You are an innovation specialist..."
  └── learning-extractor.md # System: "You synthesize learnings..."
```

Format (YAML frontmatter + markdown):

```yaml
---
name: architect
description: System design architect
model: model/llamacpp/nemotron-v3-coder
---

# Persona

You are a system design architect with expertise in...

## Core Principles

1. ...

## Approach

...
```

## Session Management

Each agent maintains its own session:

- **Session Title:** `"ELF Architect Session 14-02-2026"`
- **Session ID:** `"ses_3a79f9940ffeKl0sXN9hIOECYD"`
- **Persistence:** Messages persist across requests
- **Reuse:** AgentManager reuses sessions on same day

When `noReply: true`:
- Session stores: User message → (AI processing...) → AI response
- Response appears later in session
- Can poll `/messages` endpoint to check status

## Result Files

Results saved to:

```
~/.opencode/emergent-learning/.coordination/
  └── swarm_result_2026-02-14T02-00-38.json
```

Content:
```json
{
  "task": "Design a REST API",
  "context": "Node.js, PostgreSQL",
  "mode": "design",
  "timestamp": "2026-02-14T02-00-38",
  "agents": [
    {
      "name": "architect",
      "status": "spawned",
      "session_id": "ses_3a79f9940ffeKl0sXN9hIOECYD"
    },
    {
      "name": "creative",
      "status": "spawned",
      "session_id": "ses_3a78a0a0..."}
    },
    {
      "name": "skeptic",
      "status": "spawned",
      "session_id": "ses_3a77b1b1..."}
    }
  ],
  "status": "spawned"
}
```

## Checking Agent Progress

### Via CLI:
```bash
python3 swarm-cli.py status
# Shows most recent swarm and session IDs

python3 swarm-cli.py status --file path/to/swarm_result_*.json
# Check specific swarm
```

### Via OpenCode Server API:
```bash
# Get session messages
curl http://localhost:4096/sessions/ses_xxx/messages

# Look for last "assistant" message
# That's the AI's response
```

### Via OpenCode UI:
1. Open http://localhost:4096
2. Find session: "ELF Architect Session 14-02-2026"
3. Read messages to see AI response

## Key Takeaways

1. **async = noReply: true:** The swarm returns immediately, agents run in background
2. **AgentManager does the work:** It loads personas, manages sessions, calls SDK
3. **SDK bridges to server:** `opencode_sdk_client.mjs` translates Python → HTTP
4. **Server handles AI:** OpenCode server manages model/provider/logic
5. **Results are saved:** Session IDs stored for checking progress later
6. **Non-blocking all the way:** From `/swarm` to server request, everything returns fast

This architecture allows the swarm to:
- Spawn multiple agents in parallel
- Not block the user interface
- Leverage OpenCode's full session management
- Scale to large agent pools (100+)
