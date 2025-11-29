# Development Guide

Guide for developers extending and customizing the AI Agent.

## Table of Contents
1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Adding Features](#adding-features)
4. [Testing](#testing)
5. [Code Style](#code-style)
6. [Contributing](#contributing)

## Development Setup

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- Git
- IDE (VS Code, PyCharm recommended)

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd AutonomaTreasuryAgent

# Create virtual environment
python3.12 -m venv .venv-treasury
source .venv-treasury/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov black flake8 mypy

# Setup pre-commit hooks
pip install pre-commit
pre-commit install

# Copy environment file
cp .env.example .env
# Edit .env with your credentials

# Start services
docker-compose up -d redis

# Run application
python main.py
```

## Project Structure

```
AutonomaTreasuryAgent/
├── agent/                  # Agent workflow and execution
│   ├── __init__.py
│   ├── executor.py        # Agent execution logic
│   ├── graph.py           # LangGraph workflow definition
│   ├── nodes.py           # Workflow nodes (retrieval, agent, tools)
│   ├── prompts.py         # System prompts
│   └── state.py           # Agent state definition
│
├── api/                    # FastAPI application
│   ├── __init__.py
│   ├── routes.py          # API endpoints
│   └── schemas.py         # Pydantic models
│
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py        # Environment settings
│
├── core/                   # Core infrastructure
│   ├── __init__.py
│   ├── cache.py           # Redis caching
│   ├── events.py          # Event bus (Redis Streams)
│   ├── logger.py          # Logging configuration
│   ├── mcp.py             # Model Context Protocol client
│   ├── memory.py          # Conversation memory
│   ├── middleware.py      # FastAPI middleware
│   ├── models.py          # LLM and embeddings
│   ├── rag.py             # RAG system
│   ├── redis_client.py    # Redis client
│   └── tools.py           # Tool registry
│
├── database/               # Database layer
│   ├── __init__.py
│   ├── client.py          # Supabase client
│   ├── migrate.py         # Migration runner
│   ├── models.py          # Database models
│   ├── repository.py      # Data access layer
│   └── migrations/        # SQL migrations
│       └── 001_initial_schema.sql
│
├── docs/                   # Documentation
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   ├── USER_GUIDE.md
│   ├── ADMIN_GUIDE.md
│   ├── EVENT_ARCHITECTURE.md
│   └── DEVELOPMENT.md
│
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_memory.py
│   ├── test_redis.py
│   └── test_tools.py
│
├── cli.py                  # Interactive CLI
├── main.py                 # Application entry point
├── Dockerfile              # Multi-stage Docker build
├── docker-compose.yml      # Service orchestration
├── .gitlab-ci.yml          # CI/CD pipeline
├── requirements.txt        # Python dependencies
└── README.md               # Project overview
```

## Adding Features

### 1. Adding a New Tool

**Step 1**: Define the tool in `core/tools.py`

```python
from langchain_core.tools import tool

@tool
def weather_tool(location: str) -> str:
    \"\"\"Get weather information for a location.\"\"\"
    # Implementation
    return f"Weather in {location}: Sunny, 72°F"

# Register tool
tool_registry.register(weather_tool)
```

**Step 2**: Test the tool

```python
# tests/test_tools.py
def test_weather_tool():
    result = weather_tool.invoke({"location": "New York"})
    assert "New York" in result
```

### 2. Adding a New API Endpoint

**Step 1**: Define schema in `api/schemas.py`

```python
from pydantic import BaseModel

class AnalyticsRequest(BaseModel):
    session_id: str
    metric: str

class AnalyticsResponse(BaseModel):
    value: float
    timestamp: str
```

**Step 2**: Add route in `api/routes.py`

```python
@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(request: AnalyticsRequest):
    \"\"\"Get analytics for a session.\"\"\"
    # Implementation
    return AnalyticsResponse(
        value=42.0,
        timestamp=datetime.now().isoformat()
    )
```

**Step 3**: Test the endpoint

```python
# tests/test_api.py
def test_analytics_endpoint():
    response = client.get("/api/v1/analytics?session_id=test&metric=count")
    assert response.status_code == 200
    assert "value" in response.json()
```

### 3. Adding a New Agent Node

**Step 1**: Define node in `agent/nodes.py`

```python
def validation_node(state: AgentState) -> AgentState:
    \"\"\"Validate user input before processing.\"\"\"
    messages = state["messages"]
    last_message = messages[-1].content
    
    # Validation logic
    if len(last_message) < 3:
        return {
            "messages": [AIMessage(content="Message too short")],
            "next_action": "end"
        }
    
    return {"next_action": "continue"}
```

**Step 2**: Add to workflow in `agent/graph.py`

```python
def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("validation", validation_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("agent", agent_node)
    
    # Add edges
    workflow.set_entry_point("validation")
    workflow.add_edge("validation", "retrieval")
    workflow.add_edge("retrieval", "agent")
    
    return workflow.compile()
```

### 4. Adding Event Handlers

**Step 1**: Define handler in your module

```python
from core import event_bus

@event_bus.subscribe("user.registered")
async def handle_user_registered(data):
    user_id = data.get("user_id")
    # Send welcome message
    await send_welcome_message(user_id)
```

**Step 2**: Start consumer in `main.py`

```python
@app.on_event("startup")
async def startup():
    asyncio.create_task(
        event_bus.start_consumer(
            consumer_group="agent-group",
            consumer_name=f"agent-{os.getpid()}"
        )
    )
```

### 5. Adding Database Models

**Step 1**: Define model in `database/models.py`

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserPreference(BaseModel):
    id: Optional[str] = None
    user_id: str
    key: str
    value: str
    created_at: Optional[datetime] = None
```

**Step 2**: Create migration in `database/migrations/`

```sql
-- 002_user_preferences.sql
CREATE TABLE IF NOT EXISTS user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, key)
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
```

**Step 3**: Add repository methods in `database/repository.py`

```python
class UserPreferenceRepository:
    def __init__(self):
        self.client = supabase_client.get_client()
    
    def save_preference(self, user_id: str, key: str, value: str):
        data = {"user_id": user_id, "key": key, "value": value}
        return self.client.table("user_preferences").upsert(data).execute()
    
    def get_preference(self, user_id: str, key: str):
        result = self.client.table("user_preferences")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("key", key)\
            .execute()
        return result.data[0] if result.data else None
```

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_tools.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test
pytest tests/test_tools.py::test_calculator_tool -v
```

### Writing Tests

**Unit Test Example**:
```python
# tests/test_tools.py
import pytest
from core.tools import calculator_tool

def test_calculator_addition():
    result = calculator_tool.invoke({"expression": "2+2"})
    assert result == "4"

def test_calculator_invalid():
    result = calculator_tool.invoke({"expression": "invalid"})
    assert "Error" in result
```

**Async Test Example**:
```python
# tests/test_redis.py
import pytest
from core.cache import cache_manager

@pytest.mark.asyncio
async def test_cache_set_get():
    await cache_manager.set("test_key", {"data": "value"}, ttl=60)
    result = await cache_manager.get("test_key")
    assert result == {"data": "value"}
```

**API Test Example**:
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Test Fixtures

```python
# tests/conftest.py
import pytest
from core.redis_client import redis_client

@pytest.fixture
async def redis_conn():
    client = redis_client.get_async_client()
    yield client
    await redis_client.close()

@pytest.fixture
def sample_data():
    return {"key": "value", "number": 42}
```

## Code Style

### Python Style Guide

Follow PEP 8 with these additions:

**Formatting**:
```bash
# Format code with black
black .

# Check with flake8
flake8 .

# Type checking with mypy
mypy .
```

**Naming Conventions**:
- Classes: `PascalCase`
- Functions/Variables: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Private: `_leading_underscore`

**Example**:
```python
from typing import Optional, Dict, Any

class CacheManager:
    \"\"\"Manages caching operations.\"\"\"
    
    DEFAULT_TTL = 3600
    
    def __init__(self, prefix: str = "cache"):
        self._prefix = prefix
        self._client = redis_client.get_async_client()
    
    async def get(self, key: str) -> Optional[Any]:
        \"\"\"Get value from cache.\"\"\"
        full_key = f"{self._prefix}:{key}"
        return await self._client.get(full_key)
```

### Documentation

**Docstrings**:
```python
def process_document(doc_id: str, options: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"
    Process a document with given options.
    
    Args:
        doc_id: Unique document identifier
        options: Processing options
            - chunk_size: Size of text chunks (default: 1000)
            - overlap: Chunk overlap (default: 200)
    
    Returns:
        Dictionary containing:
            - chunks: Number of chunks created
            - status: Processing status
    
    Raises:
        ValueError: If doc_id is invalid
        ProcessingError: If processing fails
    
    Example:
        >>> result = process_document("doc-123", {"chunk_size": 500})
        >>> print(result["chunks"])
        10
    \"\"\"
    pass
```

### Type Hints

Always use type hints:

```python
from typing import List, Dict, Optional, Union

def get_documents(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    \"\"\"Get documents matching query.\"\"\"
    pass
```

## Contributing

### Workflow

1. **Fork & Clone**
   ```bash
   git clone <your-fork-url>
   cd AutonomaTreasuryAgent
   ```

2. **Create Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Write code
   - Add tests
   - Update documentation

4. **Test**
   ```bash
   pytest tests/ -v
   black .
   flake8 .
   ```

5. **Commit**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

6. **Push & PR**
   ```bash
   git push origin feature/your-feature-name
   # Create Pull Request on GitHub/GitLab
   ```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add weather tool
fix: resolve memory leak in cache manager
docs: update API documentation
test: add tests for event bus
refactor: simplify agent workflow
chore: update dependencies
```

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### Code Review

**Reviewers check for**:
- Code quality and style
- Test coverage
- Documentation
- Performance implications
- Security considerations

## Debugging

### Enable Debug Logging

```python
# config/settings.py
LOG_LEVEL = "DEBUG"
```

### Debug Agent Workflow

```python
# Add breakpoints in nodes
def agent_node(state: AgentState) -> AgentState:
    import pdb; pdb.set_trace()  # Debugger
    # ... rest of code
```

### Debug Redis Events

```bash
# Monitor Redis commands
redis-cli MONITOR

# Check stream contents
redis-cli XRANGE agent:stream:task.created - + COUNT 10
```

### Debug API Requests

```python
# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response: {response.status_code}")
    return response
```

## Performance Profiling

```python
# Profile function
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
result = agent_executor.execute("test")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## Resources

- [LangChain Docs](https://python.langchain.com/)
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Redis Streams](https://redis.io/docs/data-types/streams/)
- [Supabase Docs](https://supabase.com/docs)

---

**Questions?** Open an issue or discussion on GitHub/GitLab.
