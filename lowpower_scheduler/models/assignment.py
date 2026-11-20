"""
Task assignment and schedule result value objects.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from lowpower_scheduler.models.task import Task


class TaskAssignment:
    """Represents the mapping of a Task to a ProcessorElement at a specific DVFS frequency level."""

    def __init__(self, task: Task, pe_name: str, frequency_index: int) -> None:
        self.task: Task = task
        self.pe_name: str = pe_name
        self.frequency_index: int = int(frequency_index)

    def __repr__(self) -> str:
        return f"TaskAssignment({self.task.name} -> {self.pe_name} @ freq[{self.frequency_index}])"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TaskAssignment):
            return (
                self.task == other.task
                and self.pe_name == other.pe_name
                and self.frequency_index == other.frequency_index
            )
        return False


@dataclass
class ScheduleResult:
    """Encapsulates the complete outcome of a scheduled task graph."""
    makespan: float
    missed_deadlines: List[Task] = field(default_factory=list)
    total_energy: float = 0.0
    energy_breakdown: Optional[Any] = None
    is_valid: bool = True

    def __post_init__(self):
        self.is_valid = len(self.missed_deadlines) == 0
