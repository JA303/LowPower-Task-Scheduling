"""
Domain models for tasks, processors, communication, and assignments.
"""

from lowpower_scheduler.models.task import Task, TaskGraph
from lowpower_scheduler.models.processor import ProcessorElement, DVFSLevel
from lowpower_scheduler.models.communication import CommunicationRequest, BusChannel, CommunicationElement
from lowpower_scheduler.models.assignment import TaskAssignment, ScheduleResult

__all__ = [
    "Task",
    "TaskGraph",
    "ProcessorElement",
    "DVFSLevel",
    "CommunicationRequest",
    "BusChannel",
    "CommunicationElement",
    "TaskAssignment",
    "ScheduleResult",
]
