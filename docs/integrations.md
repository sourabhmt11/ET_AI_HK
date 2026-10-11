# Integrations

cosmac integrates with popular Python web frameworks and LLM orchestration libraries. Each integration is available as an optional dependency.

## FastAPI / Starlette

```bash
pip install cosmac[fastapi]
```

Add `CosmacASGIMiddleware` to scan all POST/PUT/PATCH request bodies:

```python
from fastapi import FastAPI
from cosmac.integrations.fastapi_middleware import CosmacASGIMiddleware

app = FastAPI()
app.add_middleware(
    CosmacASGIMiddleware,
    config_path="cosmac.yaml",  # Optional
    mode="block",                       # "block", "monitor", or "flag"
    scan_fields=["body.prompt", "body.messages.*.content"],
)
```

Blocked requests receive HTTP 400 with a JSON body:

```json
{
  "error": "Prompt injection detected",
  "scan_id": "...",
  "risk_score": 0.92
}
```

The `scan_fields` parameter uses dot notation with `*` for array wildcards. Defaults are `body.prompt` and `body.messages.*.content`.

An optional `on_detection` async callback receives `(request, report)` for custom logging.

## Flask

```bash
pip install cosmac[flask]
```

Wrap the WSGI app:

```python
from flask import Flask
from cosmac.integrations.flask_middleware import CosmacFlaskMiddleware

app = Flask(__name__)
app.wsgi_app = CosmacFlaskMiddleware(
    app.wsgi_app,
    config_path="cosmac.yaml",
    scan_fields=["prompt", "messages.*.content"],
)
```

Blocked requests receive HTTP 400 with JSON containing `error` and `scan_id`.

## Django

```bash
pip install cosmac[django]
```

Add the middleware to `settings.py`:

```python
MIDDLEWARE = [
    "cosmac.integrations.django_middleware.CosmacDjangoMiddleware",
    # ... other middleware
]
```

The middleware scans `prompt` and `messages.*.content` fields in JSON request bodies. Blocked requests return `JsonResponse` with status 400.

## LangChain

```bash
pip install cosmac[langchain]
```

Attach `CosmacCallback` to any LangChain LLM, ChatModel, or AgentExecutor:

```python
from cosmac import CosmacEngine
from cosmac.integrations.langchain_callback import CosmacCallback

engine = CosmacEngine()
callback = CosmacCallback(
    engine=engine,
    mode="block",              # Raises ValueError on detection
    scan_tool_results=True,    # Scan tool output for indirect injection
    enable_canary=False,       # Check LLM output for canary leakage
)

# Attach to any LangChain component
llm = ChatOpenAI(callbacks=[callback])
agent = AgentExecutor(agent=agent, tools=tools, callbacks=[callback])
```

Lifecycle hooks:

| Hook | Gate | Behavior |
|---|---|---|
| `on_llm_start` | Input | Scans prompts; raises `ValueError` on detection |
| `on_tool_end` | Data | Scans tool output; raises `ValueError` in block mode |
| `on_llm_end` | Output | Checks for canary token leakage |
| `on_chain_error` | -- | Logs cosmac block events |

## LlamaIndex

```bash
pip install cosmac[llamaindex]
```

Use `CosmacHandler` to scan queries and retrieved nodes:

```python
from cosmac.integrations.llamaindex_handler import CosmacHandler

handler = CosmacHandler(mode="block", scan_retrieved=True)

# Scan user query
handler.scan_query("What is the company revenue?")

# Scan retrieved nodes (filters out poisoned content)
safe_nodes = handler.scan_retrieved_nodes(retrieved_nodes)

# Scan final response
handler.scan_response(response_text)
```

In block mode, `scan_query` raises `ValueError` if injection is detected. `scan_retrieved_nodes` silently drops poisoned nodes from the list.

## MCP (Model Context Protocol)

```bash
pip install cosmac[mcp]
```

Wrap any MCP server with `CosmacMCPFilter`:

```python
from cosmac.integrations.mcp import CosmacMCPFilter

protected = CosmacMCPFilter(
    server=mcp_server,
    engine=engine,
    mode="sanitize",
    exempt_tools=["get_time"],
)

result = await protected.call_tool("search", {"query": "test"})
```

See [Agentic Security](agentic-security.md) for details on the MCP filter.

## Direct Use

For maximum control, use the engine directly:

```python
from cosmac import CosmacEngine

engine = CosmacEngine()

# Single scan
report = engine.scan(user_input, context={"source": "api"})

# Batch scan
reports = engine.scan_batch(["input1", "input2", "input3"])

# Check results
if report.action.value == "block":
    reject_request()
elif report.action.value == "flag":
    log_for_review(report)
```

## AgentGuard

For agentic applications, use `AgentGuard` which implements the 3-gate pattern:

```python
from cosmac.integrations.agent_guard import AgentGuard

guard = AgentGuard(engine=engine)
input_result = guard.scan_input(user_message)
data_result = guard.scan_tool_result("tool_name", tool_output)
```

See [Agentic Security](agentic-security.md) for the full 3-gate pattern.
