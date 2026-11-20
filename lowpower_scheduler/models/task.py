"""
Task and TaskGraph representations for heterogeneous real-time task scheduling.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, deque


class Task:
    """
    Represents an atomic task with heterogeneous execution times,
    deadline constraint, and communication dependencies.
    """

    def __init__(
        self,
        name: str,
        deadline: float,
        execution_times: Dict[str, float],
        communication_times: Optional[Dict[str, float]] = None,
        priority: int = 0,
    ) -> None:
        self.name: str = name
        self.deadline: float = float(deadline)
        self.execution_times: Dict[str, float] = {k: float(v) for k, v in execution_times.items()}
        # Avoid mutable default argument
        self.communication_times: Dict[str, float] = (
            {k: float(v) for k, v in communication_times.items()} if communication_times else {}
        )
        self.priority: int = priority

    def get_execution_time(self, pe_name: str) -> float:
        """Return base execution time on given processor element."""
        if pe_name not in self.execution_times:
            raise KeyError(f"Task '{self.name}' has no execution time specified for PE '{pe_name}'")
        return self.execution_times[pe_name]

    def get_communication_times(self, exclude_destinations: tuple[str, ...] | list[str] | set[str] = ()) -> List[Tuple[str, float]]:
        """Return communication requirements excluding tasks in exclude_destinations."""
        exclude_set = set(exclude_destinations)
        return [(dest, duration) for dest, duration in self.communication_times.items() if dest not in exclude_set]

    def get_communication_time(self, destination: str) -> float:
        """Return communication duration to destination task."""
        if destination not in self.communication_times:
            raise KeyError(f"No communication defined from task '{self.name}' to '{destination}'")
        return self.communication_times[destination]

    # Backward compatibility aliases for typos in legacy code
    def get_communication_time_legacy(self, destenation: str) -> float:
        return self.get_communication_time(destenation)

    exclude_destenations = get_communication_times

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Task):
            return self.name == other.name
        return False

    def __repr__(self) -> str:
        return f"Task(name='{self.name}', deadline={self.deadline}, priority={self.priority})"


class TaskGraph:
    """
    Represents a Directed Acyclic Graph (DAG) of tasks with dependencies.
    Provides validation, topological sort, and predecessor/successor lookups.
    """

    def __init__(self, tasks: Optional[List[Task]] = None) -> None:
        self._tasks: Dict[str, Task] = {}
        self._predecessors: Dict[str, Set[str]] = defaultdict(set)
        self._successors: Dict[str, Set[str]] = defaultdict(set)

        if tasks:
            for task in tasks:
                self.add_task(task)

    def add_task(self, task: Task) -> None:
        """Add a task and register its directed dependency edges."""
        self._tasks[task.name] = task
        for dest in task.communication_times.keys():
            self._successors[task.name].add(dest)
            self._predecessors[dest].add(task.name)

    def get_task(self, name: str) -> Task:
        """Retrieve task by name."""
        return self._tasks[name]

    @property
    def tasks(self) -> List[Task]:
        """Return list of all tasks in insertion order."""
        return list(self._tasks.values())

    def __len__(self) -> int:
        return len(self._tasks)

    def __iter__(self):
        return iter(self._tasks.values())

    def get_predecessors(self, task_name: str) -> Set[str]:
        """Return names of tasks that must execute before task_name."""
        return self._predecessors[task_name]

    def get_successors(self, task_name: str) -> Set[str]:
        """Return names of tasks that depend on task_name."""
        return self._successors[task_name]

    def topological_sort(self) -> List[Task]:
        """
        Return tasks ordered by dependency precedence.
        Raises ValueError if a cycle is detected (not a DAG).
        """
        in_degree: Dict[str, int] = {name: len(self._predecessors[name]) for name in self._tasks}
        queue = deque([name for name, deg in in_degree.items() if deg == 0])
        sorted_tasks: List[Task] = []

        while queue:
            node = queue.popleft()
            sorted_tasks.append(self._tasks[node])
            for succ in self._successors[node]:
                if succ in in_degree:
                    in_degree[succ] -= 1
                    if in_degree[succ] == 0:
                        queue.append(succ)

        if len(sorted_tasks) != len(self._tasks):
            missing = set(self._tasks.keys()) - {t.name for t in sorted_tasks}
            raise ValueError(f"Task graph contains cycles involving tasks: {missing}")

        return sorted_tasks
