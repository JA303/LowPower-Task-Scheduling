"""
Builder design pattern for fluent construction of systems, processors, and task graphs.
"""

from __future__ import annotations
from typing import Dict, List, Tuple, Sequence, Optional, Union
from lowpower_scheduler.models.processor import ProcessorElement
from lowpower_scheduler.models.task import Task, TaskGraph
from lowpower_scheduler.models.communication import BusChannel
from lowpower_scheduler.core.energy import EnergyModel, FitnessEvaluator
from lowpower_scheduler.strategies.arbiter import ArbiterStrategy, PriorityArbiter


class SystemConfiguration:
    """Encapsulates a fully configured multi-core system with energy parameters."""

    def __init__(
        self,
        processors: List[ProcessorElement],
        bus: BusChannel,
        fitness_evaluator: FitnessEvaluator,
    ) -> None:
        self.processors: List[ProcessorElement] = processors
        self.bus: BusChannel = bus
        self.fitness_evaluator: FitnessEvaluator = fitness_evaluator

    @property
    def pe_list(self) -> List[ProcessorElement]:
        return self.processors


class SystemBuilder:
    """
    Fluent builder for configuring heterogeneous multi-core architectures,
    DVFS states, communication buses, and CMOS energy models.
    """

    def __init__(self) -> None:
        self._processors: List[ProcessorElement] = []
        self._bus_name: str = "BUS"
        self._arbiter: ArbiterStrategy = PriorityArbiter()
        self._comm_power: float = 10.0
        self._idle_power: Union[float, List[float]] = 10.0
        self._efficient_capacity: Union[float, List[float]] = 1.0
        self._voltage_rail_capacity: Union[float, List[float]] = 4.0
        self._deadline_penalty: float = 0.0

    def add_processor(self, name: str, dvfs_table: Sequence[Tuple[float, float]]) -> SystemBuilder:
        """Add a heterogeneous processor element with DVFS (freq, voltage) pairs."""
        self._processors.append(ProcessorElement(name, dvfs_table))
        return self

    def set_bus(self, name: str = "BUS", arbiter: Optional[ArbiterStrategy] = None) -> SystemBuilder:
        """Configure shared communication bus and arbitration strategy."""
        self._bus_name = name
        if arbiter is not None:
            self._arbiter = arbiter
        return self

    def set_communication_power(self, power: float) -> SystemBuilder:
        """Set dynamic power consumption rate for active bus communications."""
        self._comm_power = float(power)
        return self

    def set_idle_power(self, power: Union[float, Sequence[float]]) -> SystemBuilder:
        """Set static/idle power rate (scalar for uniform, or sequence per PE)."""
        self._idle_power = power if isinstance(power, (int, float)) else list(power)
        return self

    def set_efficient_capacities(self, capacities: Union[float, Sequence[float]]) -> SystemBuilder:
        """Set CMOS switching capacitance C_eff (scalar or sequence per PE)."""
        self._efficient_capacity = capacities if isinstance(capacities, (int, float)) else list(capacities)
        return self

    def set_voltage_rail_capacities(self, capacities: Union[float, Sequence[float]]) -> SystemBuilder:
        """Set power rail capacitance C_rail for DVFS transition energy."""
        self._voltage_rail_capacity = capacities if isinstance(capacities, (int, float)) else list(capacities)
        return self

    def set_deadline_penalty(self, penalty_weight: float) -> SystemBuilder:
        """Set penalty weight factor for schedules that miss real-time deadlines."""
        self._deadline_penalty = float(penalty_weight)
        return self

    def build(self) -> SystemConfiguration:
        """Validate and construct the SystemConfiguration."""
        if not self._processors:
            raise ValueError("SystemBuilder requires at least one processor element.")

        bus = BusChannel(name=self._bus_name, arbiter=self._arbiter)
        evaluator = FitnessEvaluator(
            communication_power=self._comm_power,
            idle_power=self._idle_power,
            efficient_capacity=self._efficient_capacity,
            voltage_rail_capacity=self._voltage_rail_capacity,
            pe_count=len(self._processors),
            deadline_penalty_weight=self._deadline_penalty,
        )

        return SystemConfiguration(
            processors=self._processors,
            bus=bus,
            fitness_evaluator=evaluator,
        )


class TaskGraphBuilder:
    """
    Fluent builder for constructing tasks, execution profiles, deadlines,
    and dependency communication matrices.
    """

    def __init__(self) -> None:
        self._tasks: List[Task] = []

    def add_task(
        self,
        name: str,
        deadline: float,
        execution_times: Dict[str, float],
        communications: Optional[Dict[str, float]] = None,
        priority: int = 0,
    ) -> TaskGraphBuilder:
        """Add a task with heterogeneous execution times and communications."""
        task = Task(
            name=name,
            deadline=deadline,
            execution_times=execution_times,
            communication_times=communications,
            priority=priority,
        )
        self._tasks.append(task)
        return self

    def build(self) -> TaskGraph:
        """Build and return validated TaskGraph."""
        if not self._tasks:
            raise ValueError("TaskGraphBuilder requires at least one task.")
        return TaskGraph(self._tasks)

    def build_task_list(self) -> List[Task]:
        """Return list of constructed Task objects."""
        return list(self._tasks)
