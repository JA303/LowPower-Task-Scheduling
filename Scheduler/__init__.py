"""
Scheduler package - backward compatibility package forwarding to lowpower_scheduler.
"""

from lowpower_scheduler.models.task import Task
from lowpower_scheduler.models.assignment import TaskAssignment
from lowpower_scheduler.models.processor import ProcessorElement, DVFSLevel
from lowpower_scheduler.models.communication import CommunicationElement, CommunicationRequest, BusChannel
from lowpower_scheduler.core.timeline import Timeline, TimeInterval
from lowpower_scheduler.core.scheduler import TaskScheduler, DagTaskScheduler
from lowpower_scheduler.core.individual import Individual, IndividualGenerator, IndividualFactory, ScheduleGenerator
from lowpower_scheduler.core.energy import Fitness, FitnessEvaluator, EnergyModel, EnergyBreakdown

# Legacy spelling alias
ProccessorElement = ProcessorElement

__all__ = [
    "Task",
    "TaskAssignment",
    "ProcessorElement",
    "ProccessorElement",
    "DVFSLevel",
    "CommunicationElement",
    "CommunicationRequest",
    "BusChannel",
    "Timeline",
    "TimeInterval",
    "TaskScheduler",
    "DagTaskScheduler",
    "Individual",
    "IndividualGenerator",
    "IndividualFactory",
    "ScheduleGenerator",
    "Fitness",
    "FitnessEvaluator",
    "EnergyModel",
    "EnergyBreakdown",
]
