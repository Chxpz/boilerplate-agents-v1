# Setup Guide

Complete guide for setting up the AI Agent from scratch.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Setup](#docker-setup)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Verification](#verification)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- **Python 3.12+** - [Download](https://www.python.org/downloads/)
- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop/)
- **Git** - [Download](https://git-scm.com/downloads)

### Required Accounts
- **OpenAI API Key** - [Get API Key](https://platform.openai.com/api-keys)
- **Supabase Account** - [Sign Up](https://supabase.com)

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Disk**: 2GB free space
- **OS**: macOS, Linux, or Windows with WSL2

## Local Development Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd AutonomaTreasuryAgent
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3.12 -m venv .venv-treasury

# Activate virtual environment
# On macOS/Linux:
source .venv-treasury/bin/activate

# On Windows:
.venv-treasury\Scripts\activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Expected output**:
```
Successfully installed langchain-1.1.0 langgraph-1.0.4 fastapi-0.122.0 ...
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

**Required Configuration**:
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# Redis Configuration (for local development)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=true

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### 5. Start Redis (Local Development)

**Option A: Using Docker**
```bash
docker run -d \
  --name redis-dev \
  -p 6379:6379 \
  redis:7-alpine
```

**Option B: Using Homebrew (macOS)**
```bash
brew install redis
brew services start redis
```

**Option C: Using APT (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

**Verify Redis**:
```bash
redis-cli ping
# Expected output: PONG
```

### 6. Setup Supabase Database

#### Get Supabase Credentials

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Create a new project or select existing
3. Navigate to **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon/public key** → `SUPABASE_KEY`

#### Run Database Migrations

```bash
python database/migrate.py
```

**Expected output**:
```
=== Database Migrations ===

Migration: 001_initial_schema.sql
CREATE TABLE IF NOT EXISTS conversation_history (
    ...
)
...
```

#### Apply Migrations

**Option A: Supabase Dashboard**
1. Copy the SQL output from migration script
2. Go to **SQL Editor** in Supabase Dashboard
3. Paste and click **Run**

**Option B: Supabase CLI**
```bash
# Install Supabase CLI
npm install -g supabase

# Link to your project
supabase link --project-ref your-project-ref

# Push migrations
supabase db push
```

### 7. Start the Application

```bash
python main.py
```

**Expected output**:
```
2024-01-01 12:00:00 - agent - INFO - Starting AI Agent API...
2024-01-01 12:00:00 - agent - INFO - Server running on 0.0.0.0:8000
2024-01-01 12:00:00 - agent - INFO - LLM initialized successfully
2024-01-01 12:00:00 - agent - INFO - Redis connected successfully
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 8. Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Expected response:
{
  "status": "healthy",
  "services": {
    "llm": "ok",
    "vectorstore": "ok",
    "redis": "ok"
  }
}
```

## Docker Setup

### 1. Prerequisites

Ensure Docker and Docker Compose are installed:
```bash
docker --version
docker-compose --version
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Build and Start Services

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

**Expected output**:
```
NAME          STATUS                    PORTS
agent-api     Up (healthy)             0.0.0.0:8000->8000/tcp
agent-redis   Up (healthy)             0.0.0.0:6379->6379/tcp
```

### 4. Verify Docker Deployment

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Check Redis
docker exec agent-redis redis-cli ping
# Expected: PONG

# View agent logs
docker-compose logs agent
```

### 5. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Configuration

### Environment Variables Reference

#### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-...` |
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJhbGc...` |

#### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_NAME` | `gpt-4-turbo-preview` | OpenAI model |
| `TEMPERATURE` | `0.7` | LLM temperature |
| `REDIS_HOST` | `localhost` | Redis hostname |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_ENABLED` | `true` | Enable Redis |
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |
| `RATE_LIMIT_PER_MINUTE` | `60` | Rate limit |

### Advanced Configuration

#### Custom System Prompt

Edit `agent/prompts.py`:
```python
SYSTEM_PROMPT = """
Your custom agent behavior here...
"""
```

#### Custom Tools

Add to `core/tools.py`:
```python
@tool
def my_custom_tool(param: str) -> str:
    """Tool description."""
    return f"Result: {param}"

# Register tool
tool_registry.register(my_custom_tool)
```

#### Redis Configuration

For production, configure Redis persistence:
```yaml
# docker-compose.yml
redis:
  command: redis-server --appendonly yes --save 60 1
  volumes:
    - redis-data:/data
```

## Database Setup

### Supabase Tables

The migration creates two main tables:

#### conversation_history
Stores all conversation messages with metadata.

**Schema**:
```sql
CREATE TABLE conversation_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes**:
- `idx_conversation_history_session_id` on `session_id`
- `idx_conversation_history_created_at` on `created_at`

#### documents
Stores documents for RAG with vector embeddings.

**Schema**:
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes**:
- `idx_documents_embedding` using ivfflat for vector search

### Row-Level Security (RLS)

All tables have RLS enabled with permissive policies for development:

```sql
-- Enable RLS
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;

-- Allow all operations (customize for production)
CREATE POLICY "Enable access for all users"
ON conversation_history FOR ALL USING (true);
```

**Production Note**: Customize RLS policies based on your authentication strategy.

## Verification

### 1. Health Check

```bash
curl http://localhost:8000/api/v1/health | jq
```

**Expected**:
```json
{
  "status": "healthy",
  "services": {
    "llm": "ok",
    "vectorstore": "ok",
    "redis": "ok"
  }
}
```

### 2. Test Chat Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, who are you?",
    "session_id": "test-session"
  }' | jq
```

### 3. Test CLI

```bash
python cli.py
```

**Expected**:
```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       🤖 AI Agent CLI - Interactive Session                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
  Session ID: abc12345
  Commands: exit, quit, clear

  ✓ Connected to agent

💬 You: 
```

### 4. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_redis.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Troubleshooting

### Common Issues

#### 1. Redis Connection Error

**Error**:
```
redis.exceptions.ConnectionError: Error connecting to localhost:6379
```

**Solution**:
```bash
# Check if Redis is running
redis-cli ping

# If not running, start Redis
docker run -d -p 6379:6379 redis:7-alpine

# Or check Redis host in .env
REDIS_HOST=localhost  # or 'redis' for Docker
```

#### 2. OpenAI API Error

**Error**:
```
openai.error.AuthenticationError: Incorrect API key provided
```

**Solution**:
```bash
# Verify API key in .env
echo $OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

#### 3. Supabase Connection Error

**Error**:
```
Failed to initialize services: Invalid API key
```

**Solution**:
1. Verify credentials in Supabase Dashboard
2. Ensure using **anon/public** key, not service_role
3. Check URL format: `https://xxx.supabase.co`

#### 4. Port Already in Use

**Error**:
```
OSError: [Errno 48] Address already in use
```

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in .env
API_PORT=8001
```

#### 5. Docker Build Fails

**Error**:
```
ERROR: failed to solve: process "/bin/sh -c pip install..." did not complete
```

**Solution**:
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check Docker resources (increase if needed)
```

### Getting Help

1. **Check Logs**:
   ```bash
   # Application logs
   tail -f logs/agent.log
   
   # Docker logs
   docker-compose logs -f agent
   ```

2. **Enable Debug Mode**:
   ```python
   # In config/settings.py
   LOG_LEVEL = "DEBUG"
   ```

3. **Verify Dependencies**:
   ```bash
   pip list | grep langchain
   pip list | grep redis
   ```

4. **Test Individual Components**:
   ```bash
   # Test Redis
   python -c "from core import redis_client; print(redis_client.get_sync_client().ping())"
   
   # Test OpenAI
   python -c "from core import ModelManager; print(ModelManager.get_llm())"
   ```

### Next Steps

- [User Guide](USER_GUIDE.md) - Learn how to use the agent
- [Admin Guide](ADMIN_GUIDE.md) - Deploy and maintain in production
- [Development Guide](DEVELOPMENT.md) - Extend and customize

---

**Need more help?** Open an issue on GitHub or check the [FAQ](FAQ.md).
