"""
Processor Element model with Dynamic Voltage and Frequency Scaling (DVFS).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Sequence, Optional, TYPE_CHECKING
from lowpower_scheduler.core.timeline import Timeline
from lowpower_scheduler.models.communication import CommunicationRequest

if TYPE_CHECKING:
    from lowpower_scheduler.models.assignment import TaskAssignment
    from lowpower_scheduler.models.task import Task


@dataclass(frozen=True)
class DVFSLevel:
    """Represents an operating frequency and voltage state of a processor."""
    frequency: float
    voltage: float

    def __repr__(self) -> str:
        return f"DVFSLevel(f={self.frequency}MHz, v={self.voltage}V)"


class ProcessorElement:
    """
    Heterogeneous Processing Element (PE) supporting discrete DVFS operating points.
    Computes dynamic, transition, and idle energy consumption based on CMOS power models.
    """

    def __init__(
        self,
        name: str,
        frequency_voltage_list: Sequence[Tuple[float, float]],
    ) -> None:
        if not frequency_voltage_list:
            raise ValueError(f"Processor '{name}' must have at least one (frequency, voltage) operating point.")

        self.name: str = name
        self.task_timeline: Timeline = Timeline()
        self.assignment_list: List[TaskAssignment] = []

        # Sort descending by frequency so index 0 is max performance
        sorted_points = sorted(frequency_voltage_list, key=lambda t: t[0], reverse=True)
        self.dvfs_levels: List[DVFSLevel] = [DVFSLevel(f, v) for f, v in sorted_points]

        # Convenience lists for backward compatibility
        self.frequency_list: List[float] = [lvl.frequency for lvl in self.dvfs_levels]
        self.voltage_list: List[float] = [lvl.voltage for lvl in self.dvfs_levels]
        self.base_frequency: float = self.frequency_list[0]
        self.base_voltage: float = self.voltage_list[0]

    def assign(self, assignment_list: List[TaskAssignment]) -> None:
        """Assign tasks to this processor and verify ownership."""
        self.verify_assignments(self.name, assignment_list)
        self.assignment_list = list(assignment_list)

    @staticmethod
    def verify_assignments(pe_name: str, assignment_list: List[TaskAssignment]) -> None:
        """Ensure all assignments in list are allocated to pe_name."""
        for assignment in assignment_list:
            if assignment.pe_name != pe_name:
                raise ValueError(
                    f"Processor '{pe_name}' received invalid assignment for task '{assignment.task.name}' "
                    f"targeted to '{assignment.pe_name}'"
                )

    def schedule(self, sort_by_deadline: bool = True) -> List[Task]:
        """
        Execute scheduled task assignments on this PE's timeline.
        Returns list of tasks that missed their deadlines.
        """
        if sort_by_deadline:
            # Sort by frequency index, then task deadline (EDF within frequency class)
            self.assignment_list.sort(key=lambda t: (t.frequency_index, t.task.deadline))

        self.task_timeline = Timeline()
        miss_deadline_tasks: List[Task] = []

        for assignment in self.assignment_list:
            if assignment.frequency_index >= len(self.frequency_list):
                raise IndexError(
                    f"Task '{assignment.task.name}' assigned invalid frequency_index {assignment.frequency_index} "
                    f"on PE '{self.name}' (available: {len(self.frequency_list)})"
                )
            execution_frequency = self.frequency_list[assignment.frequency_index]
            base_time = assignment.task.get_execution_time(self.name)
            # DVFS scaled execution duration
            execution_time = (self.base_frequency / execution_frequency) * base_time
            self.task_timeline.append(assignment.task, execution_time)

            if self.task_timeline.timeline_length > assignment.task.deadline:
                miss_deadline_tasks.append(assignment.task)

        return miss_deadline_tasks

    def task_names(self) -> List[str]:
        """Return list of names of tasks assigned to this PE."""
        return [a.task.name for a in self.assignment_list]

    def get_communication_requests(self) -> List[CommunicationRequest]:
        """
        Generate communication requests for data transferred to tasks
        on other processors (cross-PE communications).
        """
        my_tasks = set(self.task_names())
        requests: List[CommunicationRequest] = []

        for assignment in self.assignment_list:
            task = assignment.task
            for dest, duration in task.get_communication_times(my_tasks):
                task_end_time = self.task_timeline.get_end_time(task)
                requests.append(
                    CommunicationRequest(
                        source=task.name,
                        destination=dest,
                        duration=duration,
                        request_time=task_end_time,
                        priority=task.priority,
                    )
                )

        return requests

    def get_dynamic_energy(self, efficient_capacity: float) -> float:
        """
        Compute dynamic energy consumption:
        E_dynamic = sum(C_eff * f * V^2 * duration)
        """
        energy = 0.0
        for assignment in self.assignment_list:
            freq = self.frequency_list[assignment.frequency_index]
            voltage = self.voltage_list[assignment.frequency_index]
            duration = self.task_timeline.get_duration_time(assignment.task)
            energy += (efficient_capacity * freq * (voltage ** 2)) * duration
        return energy

    def get_transition_energy(self, voltage_rail_capacity: float) -> float:
        """
        Compute energy lost due to voltage transitions between consecutive tasks:
        E_transition = C_rail * sum((V_prev - V_curr)^2) + return to base voltage.
        """
        if not self.assignment_list:
            return 0.0

        energy = 0.0
        prev_voltage = self.base_voltage

        for assignment in self.assignment_list:
            curr_voltage = self.voltage_list[assignment.frequency_index]
            energy += voltage_rail_capacity * ((abs(prev_voltage - curr_voltage)) ** 2)
            prev_voltage = curr_voltage

        # Return voltage rail to nominal/base voltage at end of schedule
        energy += voltage_rail_capacity * ((abs(prev_voltage - self.base_voltage)) ** 2)
        return energy

    def get_idle_energy(self, idle_power: float, end_time: float) -> float:
        """
        Compute idle energy consumed when PE has completed all tasks
        before system makespan:
        E_idle = P_idle * (end_time - busy_time)
        """
        idle_time = max(0.0, end_time - self.task_timeline.timeline_length)
        return idle_time * idle_power

    def __repr__(self) -> str:
        return f"ProcessorElement(name='{self.name}', levels={len(self.dvfs_levels)})"

    def __str__(self) -> str:
        levels_str = ", ".join([f"{lvl.frequency}MHz@{lvl.voltage}V" for lvl in self.dvfs_levels])
        return f"ProcessorElement '{self.name}': [{levels_str}] | Timeline: {self.task_timeline}"
