"""Decorator to push tool-call events to the activity feed."""

import functools
import time

from backend.agents.events import AgentEvent, push_event


def tracked_tool(agent_label: str):
    """Decorator that emits start/end events for tool functions."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Build a readable summary of the call args
            arg_parts = []
            for v in args:
                arg_parts.append(repr(v)[:60])
            for k, v in kwargs.items():
                if v is not None:
                    arg_parts.append(f"{k}={repr(v)[:40]}")
            args_str = ", ".join(arg_parts)[:120]
            tool_name = func.__name__

            push_event(AgentEvent(
                timestamp=time.time(),
                event_type="tool_call",
                agent=agent_label,
                detail=f"🔧 {tool_name}({args_str})",
            ))

            t0 = time.time()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - t0

                # Summarize result
                result_str = str(result)
                if len(result_str) > 100:
                    result_str = result_str[:100] + "…"

                push_event(AgentEvent(
                    timestamp=time.time(),
                    event_type="tool_result",
                    agent=agent_label,
                    detail=f"✅ {tool_name} → {result_str}",
                    elapsed=round(elapsed, 2),
                ))
                return result
            except Exception as e:
                elapsed = time.time() - t0
                push_event(AgentEvent(
                    timestamp=time.time(),
                    event_type="error",
                    agent=agent_label,
                    detail=f"❌ {tool_name} failed: {e}",
                    elapsed=round(elapsed, 2),
                ))
                raise

        return wrapper
    return decorator
