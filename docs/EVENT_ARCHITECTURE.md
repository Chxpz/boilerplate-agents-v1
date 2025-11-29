# Event-Driven Architecture

Complete guide to the Redis Streams-based event-driven architecture for inter-service communication.

## Overview

The agent uses **Redis Streams** for asynchronous, reliable communication with backend services. This enables:
- Loose coupling between services
- Scalable event processing
- Reliable message delivery
- Event sourcing and replay

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Backend Services                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Service A  │  │   Service B  │  │   Service C  │      │
│  │  (Tasks)     │  │  (Documents) │  │  (Analytics) │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          │ Publish Events   │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Redis Streams                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agent:stream:task.created                           │   │
│  │  agent:stream:document.processed                     │   │
│  │  agent:stream:query.completed                        │   │
│  │  agent:stream:notification.sent                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
          │ Subscribe        │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Agent Service                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Consumer 1  │  │  Consumer 2  │  │  Consumer 3  │      │
│  │  (Instance)  │  │  (Instance)  │  │  (Instance)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Stream Naming Convention

### Pattern
```
agent:stream:{event_type}
```

### Examples
- `agent:stream:task.created` - New task events
- `agent:stream:document.processed` - Document processing complete
- `agent:stream:query.completed` - Query execution finished
- `agent:stream:notification.sent` - Notification delivery
- `agent:stream:response:{correlation_id}` - Response streams

### Naming Rules
1. Use lowercase with dots for hierarchy
2. Use present tense for actions
3. Use past tense for completed events
4. Include entity type in name

## Event Structure

### Standard Event Format

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "task.created",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "task_id": "task-123",
    "priority": "high",
    "payload": {},
    "response_stream": "agent:stream:response:550e8400"
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | UUID | Yes | Unique event identifier (correlation ID) |
| `event_type` | String | Yes | Event type (matches stream name) |
| `timestamp` | ISO8601 | Yes | Event creation time (UTC) |
| `data` | Object | Yes | Event-specific payload |
| `data.response_stream` | String | No | Stream for response (request/response pattern) |

## Usage Patterns

### 1. Fire-and-Forget (Pub/Sub)

**Use Case**: Notifications, logging, analytics

**Publisher (Backend Service)**:
```python
import redis
import json
import uuid
from datetime import datetime, timezone

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

def publish_event(event_type, data):
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": json.dumps(data)
    }
    
    stream_name = f"agent:stream:{event_type}"
    redis_client.xadd(stream_name, event)
```

**Consumer (Agent)**:
```python
from core import event_bus

@event_bus.subscribe("task.created")
async def handle_task_created(data):
    task_id = data.get("task_id")
    print(f"Processing task: {task_id}")
    # Process task...
```

### 2. Request/Response

**Use Case**: Synchronous operations, RPC-style calls

**Requester (Backend Service)**:
```python
async def request_agent_action(action_type, params):
    correlation_id = str(uuid.uuid4())
    response_stream = f"agent:stream:response:{correlation_id}"
    
    # Publish request
    event = {
        "event_id": correlation_id,
        "event_type": action_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": json.dumps({
            **params,
            "response_stream": response_stream
        })
    }
    
    redis_client.xadd(f"agent:stream:{action_type}", event)
    
    # Wait for response (with timeout)
    start_time = time.time()
    timeout = 30
    
    while time.time() - start_time < timeout:
        messages = redis_client.xread({response_stream: "0"}, count=1, block=1000)
        if messages:
            for stream, msg_list in messages:
                for msg_id, msg_data in msg_list:
                    redis_client.delete(response_stream)
                    return json.loads(msg_data["data"])
        await asyncio.sleep(0.1)
    
    raise TimeoutError("No response received")
```

**Responder (Agent)**:
```python
from core import event_bus

@event_bus.subscribe("document.process")
async def handle_document_process(data):
    doc_id = data.get("doc_id")
    response_stream = data.get("response_stream")
    
    # Process document
    result = await process_document(doc_id)
    
    # Send response
    if response_stream:
        await event_bus.publish(
            response_stream.split(":")[-1],
            {"result": result, "status": "success"}
        )
```

### 3. Event Sourcing

**Use Case**: Audit trail, event replay, debugging

```python
# Read all events from a stream
def get_event_history(event_type, start_id="0"):
    stream_name = f"agent:stream:{event_type}"
    events = []
    
    messages = redis_client.xrange(stream_name, min=start_id)
    for msg_id, msg_data in messages:
        events.append({
            "id": msg_id,
            **msg_data
        })
    
    return events

# Replay events
async def replay_events(event_type, from_timestamp):
    events = get_event_history(event_type)
    
    for event in events:
        if event["timestamp"] >= from_timestamp:
            await process_event(event)
```

## Consumer Groups

### Purpose
- Load balancing across multiple consumers
- Guaranteed message processing
- Fault tolerance

### Setup

```python
# Create consumer group
redis_client.xgroup_create(
    "agent:stream:task.created",
    "agent-group",
    id="0",
    mkstream=True
)

# Read as consumer
messages = redis_client.xreadgroup(
    "agent-group",
    "agent-1",  # Consumer name
    {"agent:stream:task.created": ">"},
    count=10,
    block=1000
)

# Process and acknowledge
for stream, msg_list in messages:
    for msg_id, msg_data in msg_list:
        try:
            await process_message(msg_data)
            redis_client.xack(stream, "agent-group", msg_id)
        except Exception as e:
            logger.error(f"Failed to process {msg_id}: {e}")
            # Message will be redelivered
```

### Consumer Group Benefits

1. **Load Balancing**: Messages distributed across consumers
2. **Fault Tolerance**: Unacknowledged messages redelivered
3. **Scalability**: Add consumers without code changes
4. **Ordering**: Per-consumer ordering guaranteed

## Event Bus API

### Publishing Events

```python
from core import event_bus

# Simple publish
event_id = await event_bus.publish(
    "task.created",
    {"task_id": "123", "priority": "high"}
)

# With correlation ID
event_id = await event_bus.publish(
    "task.created",
    {"task_id": "123"},
    correlation_id="my-correlation-id"
)
```

### Request/Response

```python
# Send request and wait for response
response = await event_bus.request(
    "document.process",
    {"doc_id": "456"},
    timeout=30  # seconds
)

if response:
    print(f"Result: {response}")
else:
    print("Request timed out")
```

### Subscribing to Events

```python
@event_bus.subscribe("task.created")
async def handle_task(data):
    task_id = data.get("task_id")
    # Process task...

@event_bus.subscribe("document.processed")
async def handle_document(data):
    doc_id = data.get("doc_id")
    # Handle processed document...
```

### Starting Consumer

```python
# In main.py
@app.on_event("startup")
async def startup():
    # Start event consumer
    asyncio.create_task(
        event_bus.start_consumer(
            consumer_group="agent-group",
            consumer_name=f"agent-{os.getpid()}"
        )
    )

@app.on_event("shutdown")
async def shutdown():
    await event_bus.stop_consumer()
```

## Event Types

### Standard Events

#### task.created
```json
{
  "event_type": "task.created",
  "data": {
    "task_id": "string",
    "type": "string",
    "priority": "low|medium|high",
    "payload": {}
  }
}
```

#### document.processed
```json
{
  "event_type": "document.processed",
  "data": {
    "doc_id": "string",
    "status": "success|failed",
    "chunks": 10,
    "error": "string (if failed)"
  }
}
```

#### query.completed
```json
{
  "event_type": "query.completed",
  "data": {
    "query_id": "string",
    "session_id": "string",
    "response": "string",
    "duration_ms": 1234
  }
}
```

#### notification.sent
```json
{
  "event_type": "notification.sent",
  "data": {
    "user_id": "string",
    "type": "email|sms|push",
    "status": "sent|failed"
  }
}
```

## Best Practices

### 1. Event Design

**Do**:
- Keep events small and focused
- Include all necessary context
- Use consistent naming
- Version your events

**Don't**:
- Include sensitive data
- Make events too large (>1MB)
- Use events for synchronous operations
- Couple events to specific consumers

### 2. Error Handling

```python
@event_bus.subscribe("task.created")
async def handle_task(data):
    try:
        await process_task(data)
    except RetryableError as e:
        # Let it be redelivered
        raise
    except FatalError as e:
        # Log and acknowledge to prevent retry loop
        logger.error(f"Fatal error: {e}")
        # Don't raise - message will be acknowledged
```

### 3. Idempotency

```python
processed_events = set()

@event_bus.subscribe("task.created")
async def handle_task(data):
    event_id = data.get("event_id")
    
    # Check if already processed
    if event_id in processed_events:
        return
    
    # Process
    await process_task(data)
    
    # Mark as processed
    processed_events.add(event_id)
```

### 4. Monitoring

```python
from prometheus_client import Counter, Histogram

events_processed = Counter(
    'events_processed_total',
    'Total events processed',
    ['event_type', 'status']
)

event_processing_time = Histogram(
    'event_processing_seconds',
    'Event processing time',
    ['event_type']
)

@event_bus.subscribe("task.created")
async def handle_task(data):
    with event_processing_time.labels("task.created").time():
        try:
            await process_task(data)
            events_processed.labels("task.created", "success").inc()
        except Exception:
            events_processed.labels("task.created", "error").inc()
            raise
```

## Performance Considerations

### Stream Trimming

Prevent unbounded growth:

```python
# Trim to last 10000 messages
redis_client.xtrim("agent:stream:task.created", maxlen=10000, approximate=True)

# Trim by age (keep last 7 days)
# Use external job with XDEL based on timestamp
```

### Batch Processing

```python
# Read multiple messages at once
messages = redis_client.xreadgroup(
    "agent-group",
    "agent-1",
    {"agent:stream:task.created": ">"},
    count=100,  # Process in batches
    block=1000
)
```

### Connection Pooling

```python
# Use connection pool
pool = redis.ConnectionPool(
    host='redis',
    port=6379,
    max_connections=50
)
redis_client = redis.Redis(connection_pool=pool)
```

## Troubleshooting

### Check Stream Status

```bash
# List all streams
redis-cli KEYS "agent:stream:*"

# Get stream length
redis-cli XLEN agent:stream:task.created

# View pending messages
redis-cli XPENDING agent:stream:task.created agent-group

# View consumer info
redis-cli XINFO CONSUMERS agent:stream:task.created agent-group
```

### Debug Events

```python
# Read last 10 events
messages = redis_client.xrevrange("agent:stream:task.created", count=10)
for msg_id, msg_data in messages:
    print(f"{msg_id}: {msg_data}")
```

### Reset Consumer Group

```bash
# Delete and recreate
redis-cli XGROUP DESTROY agent:stream:task.created agent-group
redis-cli XGROUP CREATE agent:stream:task.created agent-group 0
```

## Examples

See [examples/events/](../examples/events/) for complete working examples:
- `publisher.py` - Publishing events
- `consumer.py` - Consuming events
- `request_response.py` - Request/response pattern
- `event_sourcing.py` - Event replay

---

**Next**: [API Reference](API_REFERENCE.md) | [Admin Guide](ADMIN_GUIDE.md)
