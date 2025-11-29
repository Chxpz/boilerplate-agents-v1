# Async Task Pattern Specification

## Overview

This document specifies the implementation of the **Distributed Saga Pattern** for asynchronous task execution with backend services. The agent delegates long-running tasks to external services via Redis Streams while remaining responsive to user interactions.

## Use Case

**Scenario**: User requests an action that requires external service processing (e.g., report generation, data analysis, document processing).

**Requirements**:
1. Agent delegates task to external service asynchronously
2. Agent remains responsive during task execution
3. User can continue other interactions while task processes
4. Agent notifies user when task completes
5. User can retrieve results on-demand

## Architecture Pattern

### Distributed Saga with Orchestration

The agent acts as the **orchestrator** coordinating between user and backend services.

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interaction                         │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    User Request
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Agent (Orchestrator)                        │
│                                                                   │
│  Step 1: Receive Request                                        │
│  Step 2: Invoke Tool → Publish Event                            │
│  Step 3: Store Task Metadata                                    │
│  Step 4: Return Acknowledgment                                  │
│  Step 5: Continue Serving User                                  │
│                                                                   │
│  [Later] Step 6: Receive Completion Event                       │
│  [Later] Step 7: Update Task Status                             │
│  [Later] Step 8: Notify User                                    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    Redis Streams
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Service                             │
│                                                                   │
│  Step 1: Consume Task Event                                     │
│  Step 2: Process Task (Long-Running)                            │
│  Step 3: Publish Completion Event                               │
└─────────────────────────────────────────────────────────────────┘
```

## Component Specifications

### 1. Tool Layer (Abstraction)

**Purpose**: Provide clean interface for external service invocation.

**Responsibilities**:
- Validate input parameters
- Generate unique task ID
- Publish event to service stream
- Store task metadata
- Return immediate acknowledgment

**Tool Interface**:
```
Tool Name: {service_name}_task_tool
Input: task_type, parameters, session_id
Output: task_id, acknowledgment_message
Side Effects: 
  - Publishes to agent:stream:task.create
  - Stores task metadata in Redis
  - Updates session task list
```

**Example Tools**:
- `generate_report_tool` - Report generation
- `analyze_data_tool` - Data analysis
- `process_document_tool` - Document processing
- `export_data_tool` - Data export

### 2. Redis Streams Design

#### Stream Naming Convention

**Request Streams** (Agent → Service):
```
agent:stream:task.create
```

**Response Streams** (Service → Agent):
```
agent:stream:task.completed
agent:stream:task.failed
agent:stream:task.timeout
```

**Notification Streams** (Agent → User):
```
user:stream:notifications:{session_id}
```

#### Event Schemas

**Task Creation Event**:
```json
{
  "event_id": "uuid-v4",
  "event_type": "task.create",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "data": {
    "task_id": "task-uuid",
    "task_type": "report.generate",
    "params": {
      "quarter": "Q4",
      "year": 2024,
      "format": "pdf"
    },
    "session_id": "user-123",
    "timeout": 300,
    "priority": "normal",
    "created_by": "agent"
  }
}
```

**Task Completion Event**:
```json
{
  "event_id": "uuid-v4",
  "event_type": "task.completed",
  "timestamp": "2024-01-01T12:05:00.000Z",
  "data": {
    "task_id": "task-uuid",
    "status": "success",
    "result": {
      "file_url": "https://storage/report.pdf",
      "summary": "Report generated successfully",
      "metadata": {}
    },
    "duration_ms": 300000,
    "completed_by": "report-service"
  }
}
```

**Task Failure Event**:
```json
{
  "event_id": "uuid-v4",
  "event_type": "task.failed",
  "timestamp": "2024-01-01T12:05:00.000Z",
  "data": {
    "task_id": "task-uuid",
    "status": "failed",
    "error": {
      "code": "INSUFFICIENT_DATA",
      "message": "Not enough data for Q4 2024",
      "details": {}
    },
    "duration_ms": 120000,
    "failed_by": "report-service"
  }
}
```

### 3. Task State Management

#### State Machine

```
PENDING → PROCESSING → COMPLETED
                    ↓
                  FAILED
                    ↓
                  TIMEOUT
```

**State Transitions**:
- `PENDING`: Task created, waiting for service pickup
- `PROCESSING`: Service acknowledged and processing
- `COMPLETED`: Task finished successfully
- `FAILED`: Task failed with error
- `TIMEOUT`: Task exceeded timeout threshold

#### Redis Storage Schema

**Task Metadata**:
```
Key: task:{task_id}
TTL: 86400 (24 hours)
Value: {
  "task_id": "task-uuid",
  "task_type": "report.generate",
  "status": "processing",
  "session_id": "user-123",
  "params": {},
  "result": null,
  "error": null,
  "created_at": "2024-01-01T12:00:00.000Z",
  "updated_at": "2024-01-01T12:00:00.000Z",
  "completed_at": null,
  "timeout": 300,
  "priority": "normal"
}
```

**Session Task Index**:
```
Key: session:{session_id}:tasks
Type: Set
TTL: 86400 (24 hours)
Members: [task_id_1, task_id_2, task_id_3]
```

**Task Result Cache**:
```
Key: task:{task_id}:result
TTL: 86400 (24 hours)
Value: {
  "result": {},
  "cached_at": "2024-01-01T12:05:00.000Z"
}
```

### 4. Consumer Groups

#### Agent Consumer Group

**Purpose**: Process task completion events from backend services.

**Configuration**:
```
Group Name: agent-group
Consumers: agent-1, agent-2, agent-3 (auto-scaled)
Streams: 
  - agent:stream:task.completed
  - agent:stream:task.failed
  - agent:stream:task.timeout
Block Time: 1000ms
Batch Size: 10 messages
```

**Consumer Responsibilities**:
1. Read events from streams
2. Update task status in Redis
3. Store results
4. Trigger user notifications
5. Acknowledge processed messages

#### Service Consumer Groups

**Purpose**: Process task creation events from agent.

**Configuration** (Per Service):
```
Group Name: {service-name}-group
Consumers: {service}-worker-1, {service}-worker-2
Streams: agent:stream:task.create
Filter: task_type == "{service-type}"
Block Time: 1000ms
Batch Size: 5 messages
```

### 5. Notification Strategy (Hybrid Approach)

#### Notification Methods

**Method 1: Next Interaction (Default)**
- Store notification flag in session
- Display on user's next message
- Simple, no infrastructure needed

**Method 2: WebSocket Push (If Active)**
- Check if user has active WebSocket connection
- Push real-time notification
- Better UX for active users

**Method 3: Polling Endpoint**
- User can query: "Show my pending tasks"
- Agent retrieves from session task index
- Always available fallback

#### Notification Flow

```
Task Completed
    │
    ▼
Check User Status
    │
    ├─ Active (WebSocket) ──→ Push Notification
    │                              │
    │                              ▼
    │                         User Receives
    │
    └─ Inactive ──→ Set Notification Flag
                         │
                         ▼
                    Show on Next Interaction
```

#### Notification Message Format

```json
{
  "notification_id": "notif-uuid",
  "type": "task_completed",
  "task_id": "task-uuid",
  "task_type": "report.generate",
  "message": "Your Q4 2024 report is ready!",
  "action": "retrieve_result",
  "timestamp": "2024-01-01T12:05:00.000Z",
  "priority": "normal"
}
```

### 6. Timeout Handling

#### Timeout Detection

**Background Job** (Runs every 60 seconds):
```
1. Query all tasks with status = "processing"
2. Check if (current_time - created_at) > timeout
3. For timed-out tasks:
   - Update status to "timeout"
   - Publish task.timeout event
   - Notify user
```

#### Timeout Event

```json
{
  "event_id": "uuid-v4",
  "event_type": "task.timeout",
  "timestamp": "2024-01-01T12:10:00.000Z",
  "data": {
    "task_id": "task-uuid",
    "status": "timeout",
    "message": "Task exceeded timeout of 300 seconds",
    "elapsed_ms": 600000
  }
}
```

#### User Communication

**Timeout Message**:
```
"Your report generation is taking longer than expected. 
The task is still running. I'll notify you when it completes, 
or you can check status with: 'Show task status for {task_id}'"
```

### 7. Error Handling & Retry Strategy

#### Error Categories

**Transient Errors** (Retry):
- Network timeouts
- Service temporarily unavailable
- Rate limit exceeded

**Permanent Errors** (Fail):
- Invalid parameters
- Insufficient permissions
- Resource not found

#### Retry Configuration

```
Max Retries: 3
Backoff Strategy: Exponential
Initial Delay: 1 second
Max Delay: 60 seconds
Jitter: ±20%
```

#### Retry Logic

```
Attempt 1: Immediate
Attempt 2: 1 second delay
Attempt 3: 2 seconds delay
Attempt 4: 4 seconds delay
Final: Mark as failed
```

#### Dead Letter Queue

**Purpose**: Store permanently failed tasks for manual review.

```
Stream: agent:stream:task.dlq
TTL: 7 days
Contains: Tasks that failed after max retries
```

### 8. Result Retrieval

#### Retrieval Tool

**Tool Name**: `get_task_result_tool`

**Input**:
- `task_id`: Task identifier

**Output**:
- Task status
- Result (if completed)
- Error (if failed)
- Progress (if processing)

**Behavior**:
```
1. Fetch task metadata from Redis
2. Check status:
   - COMPLETED: Return result
   - FAILED: Return error details
   - PROCESSING: Return progress/ETA
   - PENDING: Return queue position
   - TIMEOUT: Return timeout message
3. If result not in cache, fetch from Supabase
```

#### Bulk Retrieval

**Tool Name**: `list_user_tasks_tool`

**Input**:
- `session_id`: User session
- `status_filter`: Optional (all, pending, completed, failed)

**Output**:
- List of tasks with status and summary

### 9. Monitoring & Observability

#### Metrics to Track

**Task Metrics**:
- Tasks created per minute
- Tasks completed per minute
- Tasks failed per minute
- Average task duration
- Task timeout rate

**Queue Metrics**:
- Queue depth (pending tasks)
- Consumer lag
- Message processing rate
- Dead letter queue size

**User Metrics**:
- Active tasks per user
- Task completion rate
- User notification delivery rate

#### Logging Requirements

**Task Lifecycle Logs**:
```
[INFO] Task created: task_id={id}, type={type}, session={session}
[INFO] Task processing: task_id={id}, service={service}
[INFO] Task completed: task_id={id}, duration={ms}
[ERROR] Task failed: task_id={id}, error={error}
[WARN] Task timeout: task_id={id}, elapsed={ms}
```

**Event Processing Logs**:
```
[DEBUG] Event published: stream={stream}, event_id={id}
[DEBUG] Event consumed: stream={stream}, event_id={id}, consumer={name}
[DEBUG] Event acknowledged: stream={stream}, event_id={id}
```

### 10. Security Considerations

#### Task Authorization

**Validation**:
- Verify session_id owns task_id before retrieval
- Validate task parameters before publishing
- Sanitize user input in task params

**Access Control**:
```
Rule: User can only access tasks created in their session
Implementation: Check session:{session_id}:tasks contains task_id
```

#### Data Privacy

**Sensitive Data Handling**:
- Never log sensitive parameters
- Encrypt task results if containing PII
- Set appropriate TTLs for data retention

**Stream Security**:
- Use Redis ACLs to restrict stream access
- Separate streams per service for isolation
- Monitor for unauthorized access attempts

## Implementation Phases

### Phase 1: Core Infrastructure
1. Implement task state management in Redis
2. Create task creation tool template
3. Setup consumer group for task completion
4. Implement basic notification (next interaction)

### Phase 2: Event Processing
1. Implement event bus handlers
2. Add timeout detection background job
3. Create task retrieval tools
4. Add error handling and retries

### Phase 3: Enhanced Notifications
1. Implement WebSocket support
2. Add push notifications for active users
3. Create notification preferences
4. Add bulk task listing

### Phase 4: Monitoring & Optimization
1. Add metrics collection
2. Implement monitoring dashboard
3. Optimize consumer performance
4. Add dead letter queue processing

## Testing Strategy

### Unit Tests
- Tool invocation and validation
- Event publishing and consumption
- State transitions
- Timeout detection

### Integration Tests
- End-to-end task flow
- Multiple concurrent tasks
- Service failure scenarios
- Timeout handling

### Load Tests
- 100 concurrent tasks
- 1000 tasks per minute
- Consumer group scaling
- Redis performance under load

## Success Criteria

1. **Responsiveness**: Agent responds within 200ms to user requests
2. **Reliability**: 99.9% task completion rate
3. **Notification**: 95% notification delivery within 5 seconds
4. **Scalability**: Handle 1000+ concurrent tasks
5. **Observability**: Full task lifecycle visibility

## Future Enhancements

### Priority Queue
- Implement task prioritization
- High-priority tasks processed first
- User-based priority levels

### Task Dependencies
- Support task chains (Task B after Task A)
- Parallel task execution
- Conditional task execution

### Scheduled Tasks
- Cron-like task scheduling
- Recurring tasks
- Delayed task execution

### Task Cancellation
- User can cancel pending tasks
- Graceful service shutdown
- Compensation actions

## References

- [Event-Driven Architecture](EVENT_ARCHITECTURE.md)
- [Redis Streams Documentation](https://redis.io/docs/data-types/streams/)
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)
- [Development Guide](DEVELOPMENT.md)

---

**Status**: Specification Complete - Ready for Implementation  
**Version**: 1.0  
**Last Updated**: 2024-01-01
