# User Guide

Complete guide for using the AI Agent as an end user.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Using the CLI](#using-the-cli)
3. [Using the API](#using-the-api)
4. [Features](#features)
5. [Best Practices](#best-practices)
6. [Examples](#examples)

## Getting Started

### Prerequisites
- Agent is running (see [Setup Guide](SETUP.md))
- You have a session ID (or use default)

### Quick Start

**CLI**:
```bash
python cli.py
```

**API**:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "session_id": "my-session"}'
```

## Using the CLI

### Starting the CLI

```bash
python cli.py
```

**Welcome Screen**:
```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                       🤖 AI Agent CLI - Interactive Session                   ║
╚═══════════════════════════════════════════════════════════════════════════════╝
  Session ID: abc12345
  Commands: exit, quit, clear

  ✓ Connected to agent


💬 You: 
```

### CLI Features

#### 1. Interactive Chat

Simply type your message and press Enter:

```
💬 You: What is the capital of France?

🤖 Agent
────────────────────────────────────────────────────────────────────────────────
The capital of France is Paris.
────────────────────────────────────────────────────────────────────────────────
```

#### 2. Streaming Responses

Responses appear character-by-character in Matrix-style green text for better UX.

#### 3. Session Management

Each CLI session has a unique ID. All messages in the same session maintain context:

```
💬 You: My name is John

🤖 Agent: Nice to meet you, John!

💬 You: What's my name?

🤖 Agent: Your name is John.
```

#### 4. Commands

| Command | Description |
|---------|-------------|
| `exit`, `quit`, `q` | End session and exit |
| `clear` | Clear screen |
| `Ctrl+C` | Interrupt current request |

### CLI Tips

1. **Long Messages**: Type multi-line messages naturally
2. **Copy/Paste**: Works seamlessly
3. **History**: Use ↑/↓ arrows for command history
4. **Interruption**: Press Ctrl+C to stop agent mid-response

## Using the API

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

Currently no authentication required (add in production).

### Endpoints

#### 1. Chat (Non-Streaming)

**Endpoint**: `POST /chat`

**Request**:
```json
{
  "message": "What is machine learning?",
  "session_id": "user-123"
}
```

**Response**:
```json
{
  "response": "Machine learning is...",
  "context": "Retrieved context from RAG",
  "session_id": "user-123"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain quantum computing",
    "session_id": "user-123"
  }'
```

#### 2. Chat (Streaming)

**Endpoint**: `POST /chat/stream`

**Request**: Same as non-streaming

**Response**: Server-Sent Events (SSE)

```
data: {"chunk": "Q", "done": false, "progress": 0.01, "session_id": "user-123"}
data: {"chunk": "u", "done": false, "progress": 0.02, "session_id": "user-123"}
...
data: {"chunk": ".", "done": true, "progress": 1.0, "session_id": "user-123"}
```

**Example (Python)**:
```python
import requests
import json

response = requests.post(
    "http://localhost:8000/api/v1/chat/stream",
    json={"message": "Hello", "session_id": "user-123"},
    stream=True
)

for line in response.iter_lines():
    if line.startswith(b"data: "):
        data = json.loads(line[6:])
        print(data["chunk"], end="", flush=True)
```

**Example (JavaScript)**:
```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/v1/chat/stream',
  {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      message: 'Hello',
      session_id: 'user-123'
    })
  }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.chunk);
};
```

#### 3. Add Documents

**Endpoint**: `POST /documents`

**Request**:
```json
{
  "texts": [
    "Document content 1",
    "Document content 2"
  ],
  "metadatas": [
    {"source": "file1.txt"},
    {"source": "file2.txt"}
  ]
}
```

**Response**:
```json
{
  "count": 5,
  "message": "Successfully added 5 document chunks"
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["AI is transforming industries"],
    "metadatas": [{"source": "article.txt"}]
  }'
```

#### 4. Clear Memory

**Endpoint**: `DELETE /memory/{session_id}`

**Response**:
```json
{
  "message": "Memory cleared for session: user-123"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/memory/user-123
```

#### 5. Health Check

**Endpoint**: `GET /health`

**Response**:
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

## Features

### 1. Conversational Memory

The agent remembers context within a session:

```
User: My favorite color is blue
Agent: I'll remember that your favorite color is blue.

User: What's my favorite color?
Agent: Your favorite color is blue.
```

**Session Management**:
- Each `session_id` maintains separate context
- Sessions persist across restarts (with Redis/Supabase)
- Clear memory with DELETE endpoint

### 2. RAG (Retrieval-Augmented Generation)

Add documents to enhance agent knowledge:

```bash
# Add company documentation
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["Company policy: Remote work allowed 3 days/week"],
    "metadatas": [{"source": "hr-policy.pdf"}]
  }'

# Query with context
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the remote work policy?",
    "session_id": "employee-456"
  }'
```

**Benefits**:
- Reduces hallucinations
- Provides source attribution
- Updates knowledge without retraining

### 3. Tool Usage

The agent can use tools for specific tasks:

**Calculator**:
```
User: What is 15% of 250?
Agent: Let me calculate that... 15% of 250 is 37.5
```

**Search**:
```
User: Search for latest AI news
Agent: [Uses search tool] Here are the latest developments...
```

### 4. Streaming Responses

Real-time response generation for better UX:

- Immediate feedback
- Lower perceived latency
- Can interrupt long responses

## Best Practices

### 1. Session Management

**Do**:
- Use meaningful session IDs: `user-{user_id}`, `chat-{chat_id}`
- Clear sessions when done: `DELETE /memory/{session_id}`
- Reuse sessions for continued conversations

**Don't**:
- Share session IDs across users
- Use sensitive data in session IDs
- Keep sessions indefinitely

### 2. Document Management

**Do**:
- Chunk large documents before uploading
- Include metadata for source tracking
- Update documents when content changes

**Don't**:
- Upload duplicate content
- Exceed rate limits (10 req/min for documents)
- Upload without metadata

### 3. Query Optimization

**Do**:
- Be specific in questions
- Provide context when needed
- Use follow-up questions

**Don't**:
- Ask multiple unrelated questions at once
- Expect real-time data (unless tools provide it)
- Rely on memory across different sessions

### 4. Error Handling

**Do**:
- Check response status codes
- Implement retry logic with exponential backoff
- Handle rate limit errors (429)

**Don't**:
- Ignore error responses
- Retry immediately on failure
- Exceed rate limits

## Examples

### Example 1: Customer Support Bot

```python
import requests

def ask_support(question, user_id):
    response = requests.post(
        "http://localhost:8000/api/v1/chat",
        json={
            "message": question,
            "session_id": f"support-{user_id}"
        }
    )
    return response.json()["response"]

# Usage
answer = ask_support("How do I reset my password?", "user123")
print(answer)
```

### Example 2: Document Q&A

```python
# 1. Upload documents
documents = [
    "Product X costs $99 and includes free shipping",
    "Product Y costs $149 and has a 2-year warranty"
]

requests.post(
    "http://localhost:8000/api/v1/documents",
    json={"texts": documents}
)

# 2. Query
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "message": "Which product has free shipping?",
        "session_id": "product-qa"
    }
)

print(response.json()["response"])
# Output: Product X includes free shipping
```

### Example 3: Multi-Turn Conversation

```python
session_id = "conversation-001"

# Turn 1
response1 = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "message": "I'm planning a trip to Japan",
        "session_id": session_id
    }
)

# Turn 2 (with context)
response2 = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "message": "What's the best time to visit?",
        "session_id": session_id
    }
)
# Agent knows you're asking about Japan
```

### Example 4: Streaming Chat UI

```python
import requests
import json

def stream_chat(message, session_id):
    response = requests.post(
        "http://localhost:8000/api/v1/chat/stream",
        json={"message": message, "session_id": session_id},
        stream=True
    )
    
    full_response = ""
    for line in response.iter_lines():
        if line.startswith(b"data: "):
            data = json.loads(line[6:])
            chunk = data.get("chunk", "")
            print(chunk, end="", flush=True)
            full_response += chunk
    
    print()  # New line
    return full_response

# Usage
stream_chat("Tell me a story", "user-456")
```

### Example 5: Batch Processing

```python
questions = [
    "What is AI?",
    "What is ML?",
    "What is DL?"
]

for i, question in enumerate(questions):
    response = requests.post(
        "http://localhost:8000/api/v1/chat",
        json={
            "message": question,
            "session_id": f"batch-{i}"
        }
    )
    print(f"Q: {question}")
    print(f"A: {response.json()['response']}\n")
```

## Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/chat` | 60 requests | per minute |
| `/chat/stream` | 60 requests | per minute |
| `/documents` | 10 requests | per minute |
| `/memory/*` | Unlimited | - |
| `/health` | Unlimited | - |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1640000000
```

**Rate Limit Error**:
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 30
}
```

## Troubleshooting

### Common Issues

**1. No Response**
- Check if agent is running: `curl http://localhost:8000/api/v1/health`
- Verify network connectivity
- Check logs: `docker-compose logs agent`

**2. Slow Responses**
- Normal for first request (cold start)
- Check OpenAI API status
- Consider using streaming endpoint

**3. Context Not Maintained**
- Verify using same `session_id`
- Check if session was cleared
- Ensure Redis is running

**4. Rate Limit Errors**
- Implement exponential backoff
- Reduce request frequency
- Contact admin to increase limits

## Next Steps

- [Admin Guide](ADMIN_GUIDE.md) - Deploy and manage the agent
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Development Guide](DEVELOPMENT.md) - Extend functionality

---

**Questions?** Check the [FAQ](FAQ.md) or open an issue.
