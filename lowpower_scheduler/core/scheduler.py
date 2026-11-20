"""
TaskScheduler implementations: standard independent/heuristic and DAG precedence-aware.
"""

from __future__ import annotations
from typing import List, Dict, Optional, TYPE_CHECKING
from lowpower_scheduler.models.communication import BusChannel, CommunicationRequest
from lowpower_scheduler.models.task import TaskGraph
from lowpower_scheduler.core.timeline import Timeline

if TYPE_CHECKING:
    from lowpower_scheduler.models.processor import ProcessorElement
    from lowpower_scheduler.models.assignment import TaskAssignment
    from lowpower_scheduler.models.task import Task


class TaskScheduler:
    """
    Coordinates task execution on heterogeneous ProcessorElements and cross-PE
    communication on a shared BusChannel.
    """

    def __init__(
        self,
        pe_list: List[ProcessorElement],
        ce: Optional[BusChannel] = None,
    ) -> None:
        self.pe_list: List[ProcessorElement] = list(pe_list)
        self.ce: BusChannel = ce if ce is not None else BusChannel("BUS")
        self.communication_requests: List[CommunicationRequest] = []
        self.miss_deadline: List[Task] = []
        self.end_time: float = 0.0

    def assign(self, assignment_list: List[TaskAssignment]) -> None:
        """Route task assignments to their designated processor elements."""
        for pe in self.pe_list:
            my_assign_list = [a for a in assignment_list if a.pe_name == pe.name]
            pe.assign(my_assign_list)

    def schedule(self) -> None:
        """
        Execute schedules on all PEs, generate communication requests,
        and arbitrate shared bus transmissions.
        """
        self.communication_requests = []
        self.miss_deadline = []
        self.end_time = 0.0

        for pe in self.pe_list:
            miss_tasks = pe.schedule()
            self.miss_deadline.extend(miss_tasks)
            self.communication_requests.extend(pe.get_communication_requests())

            pe_end_time = pe.task_timeline.timeline_length
            if pe_end_time > self.end_time:
                self.end_time = pe_end_time

        self.ce.schedule(self.communication_requests)

        ce_end_time = self.ce.timeline.timeline_length
        if ce_end_time > self.end_time:
            self.end_time = ce_end_time

    def is_miss_deadline(self) -> bool:
        """Check if any task failed to meet its deadline."""
        return len(self.miss_deadline) > 0

    def print(self) -> None:
        """Print formatted schedule execution summary."""
        print("\n" + "=" * 55)
        print("             PROCESSOR ELEMENTS TIMELINES")
        print("=" * 55)
        for pe in self.pe_list:
            print(f"PE Name: {pe.name}")
            print(f"  Timeline  : {pe.task_timeline}")
            freqs = [str(pe.frequency_list[a.frequency_index]) for a in pe.assignment_list]
            print(f"  Frequencies: {', '.join(freqs)} MHz\n")

        print("=" * 55)
        print("             DEADLINE COMPLIANCE REPORT")
        print("=" * 55)
        if self.miss_deadline:
            missed = [f"{m.name} (deadline={m.deadline})" for m in self.miss_deadline]
            print(f"Status: VIOLATED ({len(self.miss_deadline)} tasks missed deadlines)")
            print(f"Tasks : {', '.join(missed)}")
        else:
            print("Status: ALL DEADLINES MET (0 violations)")

        print("\n" + "=" * 55)
        print("             COMMUNICATION BUS TIMELINE")
        print("=" * 55)
        print(f"Channel '{self.ce.name}': {self.ce.timeline}")

        if self.communication_requests:
            print("\nCommunication Requests:")
            for req in self.communication_requests:
                print(f"  - {req}")
        print("=" * 55 + "\n")


class DagTaskScheduler(TaskScheduler):
    """
    DAG-Precedence-Aware Task Scheduler.
    Guarantees that no task starts before all its parent tasks have completed
    and required cross-processor communications have finished on the shared bus.
    """

    def schedule(self) -> None:
        """Schedule tasks respecting precedence and bus communication completion times."""
        self.communication_requests = []
        self.miss_deadline = []
        self.end_time = 0.0

        # Reset all timelines
        for pe in self.pe_list:
            pe.task_timeline = Timeline()
        self.ce.timeline = Timeline()

        # Map task name to assignment and PE
        all_assignments: Dict[str, TaskAssignment] = {}
        task_to_pe: Dict[str, ProcessorElement] = {}
        for pe in self.pe_list:
            for assignment in pe.assignment_list:
                all_assignments[assignment.task.name] = assignment
                task_to_pe[assignment.task.name] = pe

        if not all_assignments:
            return

        # Build dependency graph
        tasks = [a.task for a in all_assignments.values()]
        graph = TaskGraph(tasks)
        try:
            topo_order = graph.topological_sort()
        except ValueError:
            # Fall back to standard schedule if cycle or independent
            super().schedule()
            return

        task_finish_times: Dict[str, float] = {}
        pe_current_time: Dict[str, float] = {pe.name: 0.0 for pe in self.pe_list}
        bus_current_time: float = 0.0

        for task in topo_order:
            assignment = all_assignments[task.name]
            pe = task_to_pe[task.name]

            # Compute earliest time all dependencies and communications are satisfied
            ready_time = 0.0
            for pred_name in graph.get_predecessors(task.name):
                pred_pe = task_to_pe[pred_name]
                pred_end = task_finish_times[pred_name]

                if pred_pe.name == pe.name:
                    # Intra-PE: zero communication delay
                    ready_time = max(ready_time, pred_end)
                else:
                    # Inter-PE: requires bus transfer
                    pred_task = all_assignments[pred_name].task
                    comm_duration = pred_task.get_communication_time(task.name)
                    comm_req = CommunicationRequest(
                        source=pred_name,
                        destination=task.name,
                        duration=comm_duration,
                        request_time=pred_end,
                        priority=pred_task.priority,
                    )
                    self.communication_requests.append(comm_req)

                    # Schedule communication on bus
                    comm_start = max(bus_current_time, pred_end)
                    comm_delay = comm_start - self.ce.timeline.timeline_length
                    self.ce.timeline.append(comm_req, comm_duration, delay=max(0.0, comm_delay))
                    bus_current_time = comm_start + comm_duration
                    ready_time = max(ready_time, bus_current_time)

            # Schedule task on PE
            start_time = max(pe_current_time[pe.name], ready_time)
            delay = start_time - pe.task_timeline.timeline_length
            freq = pe.frequency_list[assignment.frequency_index]
            base_time = task.get_execution_time(pe.name)
            duration = (pe.base_frequency / freq) * base_time

            pe.task_timeline.append(task, duration, delay=max(0.0, delay))
            finish_time = start_time + duration
            task_finish_times[task.name] = finish_time
            pe_current_time[pe.name] = finish_time

            if finish_time > task.deadline:
                self.miss_deadline.append(task)

            if finish_time > self.end_time:
                self.end_time = finish_time

        if self.ce.timeline.timeline_length > self.end_time:
            self.end_time = self.ce.timeline.timeline_length
