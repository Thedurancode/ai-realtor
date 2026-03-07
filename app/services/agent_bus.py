"""Agent Bus — Redis-backed task coordination for multi-agent orchestration.

Agents communicate through Redis pub/sub + streams:
- Boss publishes tasks to a stream
- Workers consume tasks, execute them, publish results
- Boss reads results and makes decisions

Usage:
    # Boss side
    bus = AgentBus()
    await bus.connect()
    task_id = await bus.publish_task("research_property", {"address": "123 Main St"})
    result = await bus.wait_for_result(task_id, timeout=120)

    # Worker side
    bus = AgentBus(role="worker", worker_id="worker-1")
    await bus.connect()
    async for task in bus.consume_tasks():
        result = await do_work(task)
        await bus.publish_result(task["task_id"], result)
"""

import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

STREAM_TASKS = "agentbus:tasks"
STREAM_RESULTS = "agentbus:results"
KEY_TASK_STATUS = "agentbus:status:{task_id}"
KEY_TASK_RESULT = "agentbus:result:{task_id}"
CONSUMER_GROUP = "agentbus-workers"


class TaskStatus(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    task_id: str
    task_type: str
    payload: dict
    priority: int = 0
    created_at: float = 0
    created_by: str = ""
    goal_id: str = ""

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "payload": json.dumps(self.payload),
            "priority": str(self.priority),
            "created_at": str(self.created_at or time.time()),
            "created_by": self.created_by,
            "goal_id": self.goal_id,
        }

    @classmethod
    def from_stream(cls, data: dict) -> "AgentTask":
        return cls(
            task_id=data.get("task_id", ""),
            task_type=data.get("task_type", ""),
            payload=json.loads(data.get("payload", "{}")),
            priority=int(data.get("priority", 0)),
            created_at=float(data.get("created_at", 0)),
            created_by=data.get("created_by", ""),
            goal_id=data.get("goal_id", ""),
        )


@dataclass
class TaskResult:
    task_id: str
    status: TaskStatus
    result: Any = None
    error: str = ""
    worker_id: str = ""
    duration: float = 0

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": json.dumps(self.result),
            "error": self.error,
            "worker_id": self.worker_id,
            "duration": str(self.duration),
        }

    @classmethod
    def from_stream(cls, data: dict) -> "TaskResult":
        return cls(
            task_id=data.get("task_id", ""),
            status=TaskStatus(data.get("status", "completed")),
            result=json.loads(data.get("result", "null")),
            error=data.get("error", ""),
            worker_id=data.get("worker_id", ""),
            duration=float(data.get("duration", 0)),
        )


class AgentBus:
    """Redis-backed message bus for agent coordination."""

    def __init__(self, role: str = "boss", worker_id: str = ""):
        self.role = role
        self.worker_id = worker_id or f"{role}-{uuid.uuid4().hex[:8]}"
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> bool:
        try:
            self._redis = aioredis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                decode_responses=True,
            )
            await self._redis.ping()

            # Ensure consumer group exists
            try:
                await self._redis.xgroup_create(
                    STREAM_TASKS, CONSUMER_GROUP, id="0", mkstream=True
                )
            except aioredis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            try:
                await self._redis.xgroup_create(
                    STREAM_RESULTS, CONSUMER_GROUP, id="0", mkstream=True
                )
            except aioredis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

            logger.info("AgentBus connected as %s (%s)", self.role, self.worker_id)
            return True
        except Exception as e:
            logger.error("AgentBus failed to connect: %s", e)
            return False

    async def close(self):
        if self._redis:
            await self._redis.close()

    # --- Boss: publish tasks ---

    async def publish_task(
        self,
        task_type: str,
        payload: dict,
        goal_id: str = "",
        priority: int = 0,
    ) -> str:
        task = AgentTask(
            task_id=f"task-{uuid.uuid4().hex[:12]}",
            task_type=task_type,
            payload=payload,
            priority=priority,
            created_at=time.time(),
            created_by=self.worker_id,
            goal_id=goal_id,
        )

        await self._redis.xadd(STREAM_TASKS, task.to_dict())
        await self._redis.set(
            KEY_TASK_STATUS.format(task_id=task.task_id),
            TaskStatus.PENDING.value,
            ex=3600,
        )

        logger.info("Published task %s: %s", task.task_id, task_type)
        return task.task_id

    # --- Boss: wait for results ---

    async def wait_for_result(self, task_id: str, timeout: float = 120) -> TaskResult | None:
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = await self._redis.get(KEY_TASK_RESULT.format(task_id=task_id))
            if raw:
                return TaskResult.from_stream(json.loads(raw))
            await asyncio.sleep(0.5)
        return None

    async def wait_for_results(
        self, task_ids: list[str], timeout: float = 300
    ) -> dict[str, TaskResult]:
        results = {}
        deadline = time.time() + timeout
        pending = set(task_ids)

        while pending and time.time() < deadline:
            for tid in list(pending):
                raw = await self._redis.get(KEY_TASK_RESULT.format(task_id=tid))
                if raw:
                    results[tid] = TaskResult.from_stream(json.loads(raw))
                    pending.discard(tid)
            if pending:
                await asyncio.sleep(0.5)

        return results

    # --- Worker: consume tasks ---

    async def consume_tasks(self, block_ms: int = 5000) -> AsyncIterator[AgentTask]:
        while True:
            try:
                messages = await self._redis.xreadgroup(
                    CONSUMER_GROUP,
                    self.worker_id,
                    {STREAM_TASKS: ">"},
                    count=1,
                    block=block_ms,
                )
                if not messages:
                    continue

                for stream_name, entries in messages:
                    for msg_id, data in entries:
                        task = AgentTask.from_stream(data)
                        await self._redis.set(
                            KEY_TASK_STATUS.format(task_id=task.task_id),
                            TaskStatus.CLAIMED.value,
                            ex=3600,
                        )
                        yield task
                        # Acknowledge after yielding (caller processes it)
                        await self._redis.xack(STREAM_TASKS, CONSUMER_GROUP, msg_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error consuming tasks: %s", e)
                await asyncio.sleep(1)

    # --- Worker: publish results ---

    async def publish_result(self, task_id: str, result: Any = None, error: str = "", duration: float = 0):
        task_result = TaskResult(
            task_id=task_id,
            status=TaskStatus.FAILED if error else TaskStatus.COMPLETED,
            result=result,
            error=error,
            worker_id=self.worker_id,
            duration=duration,
        )

        # Store result for boss to poll
        await self._redis.set(
            KEY_TASK_RESULT.format(task_id=task_id),
            json.dumps(task_result.to_dict()),
            ex=3600,
        )
        await self._redis.set(
            KEY_TASK_STATUS.format(task_id=task_id),
            task_result.status.value,
            ex=3600,
        )

        # Also publish to results stream
        await self._redis.xadd(STREAM_RESULTS, task_result.to_dict())
        logger.info("Result for %s: %s", task_id, task_result.status.value)

    # --- Status ---

    async def get_task_status(self, task_id: str) -> str:
        return await self._redis.get(KEY_TASK_STATUS.format(task_id=task_id)) or "unknown"

    async def get_active_workers(self) -> list[dict]:
        info = await self._redis.xinfo_groups(STREAM_TASKS)
        workers = []
        for group in info:
            consumers = await self._redis.xinfo_consumers(STREAM_TASKS, group["name"])
            for c in consumers:
                workers.append({
                    "worker_id": c["name"],
                    "pending": c["pending"],
                    "idle_ms": c["idle"],
                })
        return workers

    async def get_queue_depth(self) -> int:
        length = await self._redis.xlen(STREAM_TASKS)
        return length
