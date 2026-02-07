import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


@dataclass
class AgentSpec:
    name: str
    dependencies: set[str] = field(default_factory=set)


class MultiAgentOrchestrator:
    """
    Dependency-aware scheduler for agent tasks.

    - Executes ready agents in parallel batches.
    - Preserves deterministic order within each batch from the original plan order.
    - Stops when max_steps is reached.
    """

    def __init__(self, max_parallel_agents: int = 3):
        self.max_parallel_agents = max(1, int(max_parallel_agents))

    async def run(
        self,
        specs: list[AgentSpec],
        run_agent: Callable[[str], Awaitable[Any]],
        max_steps: int | None = None,
    ) -> list[tuple[str, Any]]:
        if not specs:
            return []

        ordered_names = [spec.name for spec in specs]
        deps_by_name = {spec.name: set(spec.dependencies) for spec in specs}
        pending = list(ordered_names)
        completed: set[str] = set()
        executions: list[tuple[str, Any]] = []
        allowed_steps = max_steps if max_steps is None else max(0, int(max_steps))

        while pending:
            if allowed_steps is not None and len(executions) >= allowed_steps:
                break

            ready = [name for name in pending if deps_by_name[name].issubset(completed)]
            if not ready:
                blocked = ", ".join(sorted(pending))
                raise RuntimeError(f"No runnable agents left; unresolved dependencies for: {blocked}")

            remaining = len(pending) if allowed_steps is None else max(0, allowed_steps - len(executions))
            batch_size = min(self.max_parallel_agents, len(ready), remaining)
            if batch_size <= 0:
                break

            batch = ready[:batch_size]
            results = await asyncio.gather(*(run_agent(name) for name in batch))

            for name, result in zip(batch, results):
                pending.remove(name)
                completed.add(name)
                executions.append((name, result))

        return executions
