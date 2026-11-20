"""
Energy models and fitness evaluation for low-power task scheduling.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Union, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from lowpower_scheduler.core.scheduler import TaskScheduler


@dataclass
class EnergyBreakdown:
    """Detailed energy consumption metrics per component."""
    dynamic_energy_by_pe: Dict[str, float] = field(default_factory=dict)
    transition_energy_by_pe: Dict[str, float] = field(default_factory=dict)
    idle_energy_by_pe: Dict[str, float] = field(default_factory=dict)
    communication_energy: float = 0.0
    total_energy: float = 0.0

    @property
    def total_dynamic(self) -> float:
        return sum(self.dynamic_energy_by_pe.values())

    @property
    def total_transition(self) -> float:
        return sum(self.transition_energy_by_pe.values())

    @property
    def total_idle(self) -> float:
        return sum(self.idle_energy_by_pe.values())


class EnergyModel:
    """
    Physical CMOS energy parameters for heterogeneous multi-core architectures.
    """

    def __init__(
        self,
        pe_count: int,
        communication_power: float,
        idle_power: Union[float, Sequence[float]],
        efficient_capacity: Union[float, Sequence[float]],
        voltage_rail_capacity: Union[float, Sequence[float]],
    ) -> None:
        if pe_count <= 0:
            raise ValueError(f"pe_count must be positive, got {pe_count}")

        self.pe_count: int = pe_count
        self.communication_power: float = float(communication_power)

        # Normalize scalar or sequence to per-PE lists
        self.idle_power: List[float] = self._normalize_parameter(
            idle_power, pe_count, "idle_power"
        )
        # Fix bug from original code where [idle_power] was assigned to efficient_capacity
        self.efficient_capacity: List[float] = self._normalize_parameter(
            efficient_capacity, pe_count, "efficient_capacity"
        )
        self.voltage_rail_capacity: List[float] = self._normalize_parameter(
            voltage_rail_capacity, pe_count, "voltage_rail_capacity"
        )

    @staticmethod
    def _normalize_parameter(value: Union[float, Sequence[float]], count: int, name: str) -> List[float]:
        if isinstance(value, (int, float)):
            return [float(value)] * count
        seq = list(value)
        if len(seq) != count:
            raise ValueError(f"Length of {name} ({len(seq)}) must equal pe_count ({count})")
        return [float(v) for v in seq]


class FitnessEvaluator:
    """
    Evaluates total energy and fitness score for a given schedule.
    Supports deadline violation penalty for real-time systems.
    """

    def __init__(
        self,
        communication_power: float,
        idle_power: Union[float, Sequence[float]],
        efficient_capacity: Union[float, Sequence[float]],
        voltage_rail_capacity: Union[float, Sequence[float]],
        pe_count: int,
        deadline_penalty_weight: float = 0.0,
    ) -> None:
        self.energy_model = EnergyModel(
            pe_count=pe_count,
            communication_power=communication_power,
            idle_power=idle_power,
            efficient_capacity=efficient_capacity,
            voltage_rail_capacity=voltage_rail_capacity,
        )
        self.pe_count = self.energy_model.pe_count
        self.communication_power = self.energy_model.communication_power
        self.idle_power = self.energy_model.idle_power
        self.efficient_capacity = self.energy_model.efficient_capacity
        self.voltage_rail_capacity = self.energy_model.voltage_rail_capacity
        self.deadline_penalty_weight: float = float(deadline_penalty_weight)

    def calculate_breakdown(self, scheduler: TaskScheduler) -> EnergyBreakdown:
        """Compute full energy breakdown across all PEs and communication channels."""
        breakdown = EnergyBreakdown()
        total = 0.0

        for index, pe in enumerate(scheduler.pe_list):
            dyn = pe.get_dynamic_energy(self.efficient_capacity[index])
            trans = pe.get_transition_energy(self.voltage_rail_capacity[index])
            idle = pe.get_idle_energy(self.idle_power[index], scheduler.end_time)

            breakdown.dynamic_energy_by_pe[pe.name] = dyn
            breakdown.transition_energy_by_pe[pe.name] = trans
            breakdown.idle_energy_by_pe[pe.name] = idle

            total += dyn + trans + idle

        comm_energy = scheduler.ce.get_energy(self.communication_power)
        breakdown.communication_energy = comm_energy
        breakdown.total_energy = total + comm_energy

        return breakdown

    def get_energy(self, scheduler: TaskScheduler) -> float:
        """Compute total energy consumption in Joules/arbitrary energy units."""
        return self.calculate_breakdown(scheduler).total_energy

    def get_fitness(self, scheduler: TaskScheduler) -> float:
        """
        Compute optimization fitness:
        Fitness = 1.0 / (E_total * (1 + penalty * missed_deadlines))
        """
        energy = self.get_energy(scheduler)
        if energy <= 0.0:
            return float("inf")

        penalty = 1.0
        if self.deadline_penalty_weight > 0.0:
            missed_count = len(scheduler.miss_deadline)
            penalty += self.deadline_penalty_weight * missed_count

        return 1.0 / (energy * penalty)

    def print(self, scheduler: TaskScheduler) -> None:
        """Print detailed energy analysis report to standard output."""
        breakdown = self.calculate_breakdown(scheduler)
        print("\n" + "=" * 50)
        print("                 ENERGY REPORT")
        print("=" * 50)
        for index, pe in enumerate(scheduler.pe_list):
            dyn = breakdown.dynamic_energy_by_pe[pe.name]
            trans = breakdown.transition_energy_by_pe[pe.name]
            idle = breakdown.idle_energy_by_pe[pe.name]
            pe_total = dyn + trans + idle
            print(f"Processor '{pe.name}':")
            print(f"  - Dynamic Energy    : {dyn:,.2f}")
            print(f"  - Transition Energy : {trans:,.2f}")
            print(f"  - Idle Energy       : {idle:,.2f}")
            print(f"  - PE Subtotal       : {pe_total:,.2f}")
            print(f"  - Parameters        : C_eff={self.efficient_capacity[index]}, "
                  f"C_rail={self.voltage_rail_capacity[index]}, P_idle={self.idle_power[index]}")
            print()

        print(f"Communication Bus '{scheduler.ce.name}':")
        print(f"  - Power Rate        : {self.communication_power}")
        print(f"  - Active Bus Energy : {breakdown.communication_energy:,.2f}")
        print("-" * 50)
        print(f"TOTAL SYSTEM ENERGY   : {breakdown.total_energy:,.2f}")
        print("=" * 50 + "\n")


# Alias for backward compatibility
Fitness = FitnessEvaluator
