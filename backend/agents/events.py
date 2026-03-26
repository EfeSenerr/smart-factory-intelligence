"""Global agent activity event bus — stores recent events for the Agent Hub."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Any

MAX_EVENTS = 200


@dataclass
class AgentEvent:
    timestamp: float
    event_type: str  # agent_start, agent_end, tool_call, tool_result, error
    agent: str
    detail: str
    elapsed: float | None = None
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["time_str"] = time.strftime("%H:%M:%S", time.localtime(self.timestamp))
        return d


# Shared event store
_events: deque[AgentEvent] = deque(maxlen=MAX_EVENTS)
_subscribers: list[asyncio.Queue] = []


def push_event(event: AgentEvent):
    """Push an event to the store and notify all subscribers."""
    _events.append(event)
    for q in _subscribers:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            pass


def get_recent_events(n: int = 50) -> list[dict]:
    """Get the last N events."""
    items = list(_events)[-n:]
    return [e.to_dict() for e in items]


async def subscribe() -> asyncio.Queue:
    """Subscribe to new events. Returns a queue that receives events."""
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers.append(q)
    return q


def unsubscribe(q: asyncio.Queue):
    """Remove a subscriber."""
    if q in _subscribers:
        _subscribers.remove(q)
