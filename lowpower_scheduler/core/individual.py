"""
Chromosome representation, factory, and schedule mapping.
"""

from __future__ import annotations
import random
from copy import deepcopy
from typing import List, Tuple, Sequence, Optional, TYPE_CHECKING
from lowpower_scheduler.models.assignment import TaskAssignment
from lowpower_scheduler.core.scheduler import TaskScheduler
from lowpower_scheduler.strategies.crossover import CrossoverStrategy, SinglePointCrossover
from lowpower_scheduler.strategies.mutation import MutationStrategy, RandomResettingMutation

if TYPE_CHECKING:
    from lowpower_scheduler.models.processor import ProcessorElement
    from lowpower_scheduler.models.task import Task


class Individual:
    """
    Genetic Algorithm chromosome representing task-to-PE mapping and DVFS levels.
    Chromosome encoding:
      - First half [0 : task_count]: PE index for each task.
      - Second half [task_count : 2 * task_count]: DVFS frequency index for each task.
    """

    def __init__(self, dna: Sequence[int]) -> None:
        self.dna: List[int] = list(dna)
        self.task_count: int = len(self.dna) // 2

    def get_pe_index(self, index: int) -> int:
        """
        Return PE index for the given gene position or task index.
        Fixes bug where index == task_count accessed wrong half.
        """
        return self.dna[index] if index < self.task_count else self.dna[index - self.task_count]

    def get_freq_index(self, index: int) -> int:
        """
        Return Frequency index for the given gene position or task index.
        Fixes bug where index == task_count caused out-of-bounds error.
        """
        return self.dna[index + self.task_count] if index < self.task_count else self.dna[index]

    def get_pe_for_task(self, task_idx: int) -> int:
        """Explicitly return the PE index for task_idx."""
        if not 0 <= task_idx < self.task_count:
            raise IndexError(f"task_idx {task_idx} out of range [0, {self.task_count - 1}]")
        return self.dna[task_idx]

    def get_freq_for_task(self, task_idx: int) -> int:
        """Explicitly return the frequency index for task_idx."""
        if not 0 <= task_idx < self.task_count:
            raise IndexError(f"task_idx {task_idx} out of range [0, {self.task_count - 1}]")
        return self.dna[self.task_count + task_idx]

    def clone(self) -> Individual:
        return Individual(self.dna.copy())

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Individual):
            return self.dna == other.dna
        return False

    def __hash__(self) -> int:
        return hash(tuple(self.dna))

    def __str__(self) -> str:
        return "".join(map(str, self.dna))

    def __repr__(self) -> str:
        pe_part = "".join(map(str, self.dna[:self.task_count]))
        freq_part = "".join(map(str, self.dna[self.task_count:]))
        return f"Individual(PE=[{pe_part}], Freq=[{freq_part}])"


class IndividualFactory:
    """
    Factory for initializing, mutating, and recombining Individuals.
    """

    def __init__(
        self,
        list_frequencies_count: List[int],
        task_count: int,
        crossover_strategy: Optional[CrossoverStrategy] = None,
        mutation_strategy: Optional[MutationStrategy] = None,
    ) -> None:
        self.pe_count: int = len(list_frequencies_count)
        self.list_frequencies_count: List[int] = list(list_frequencies_count)
        self.task_count: int = task_count
        self.crossover_strategy: CrossoverStrategy = (
            crossover_strategy if crossover_strategy is not None else SinglePointCrossover()
        )
        self.mutation_strategy: MutationStrategy = (
            mutation_strategy if mutation_strategy is not None else RandomResettingMutation()
        )

    def generate_random(self) -> Individual:
        """Generate a random valid chromosome satisfying PE DVFS level constraints."""
        dna = [0] * (self.task_count * 2)
        for task_idx in range(self.task_count):
            selected_pe = random.randint(0, self.pe_count - 1)
            dna[task_idx] = selected_pe
            max_freq = self.list_frequencies_count[selected_pe]
            dna[task_idx + self.task_count] = random.randint(0, max_freq - 1)

        return Individual(dna)

    def mutate(self, individual: Individual) -> Individual:
        """Mutate an individual using the injected mutation strategy."""
        return self.mutation_strategy.mutate(
            individual=individual,
            pe_count=self.pe_count,
            freq_counts=self.list_frequencies_count,
        )

    @staticmethod
    def crossover(
        individual_a: Individual,
        individual_b: Individual,
        crossover_strategy: Optional[CrossoverStrategy] = None,
        freq_counts: Optional[List[int]] = None,
    ) -> Tuple[Individual, Individual]:
        """
        Recombine two individuals. Can be called on class or instance.
        """
        strategy = crossover_strategy if crossover_strategy is not None else SinglePointCrossover()
        return strategy.crossover(
            parent_a=individual_a,
            parent_b=individual_b,
            freq_counts=freq_counts,
        )

    def repair(self, individual: Individual) -> Individual:
        """Ensure all frequency indices conform to their assigned PE's available levels."""
        repaired = individual.clone()
        for t in range(self.task_count):
            pe = repaired.dna[t]
            max_freq = self.list_frequencies_count[pe] - 1
            if repaired.dna[self.task_count + t] > max_freq:
                repaired.dna[self.task_count + t] = max_freq
        return repaired


# Alias for backward compatibility
IndividualGenerator = IndividualFactory


class ScheduleGenerator:
    """
    Transforms an Individual's genetic encoding into an executable TaskScheduler.
    """

    def __init__(
        self,
        task_list: List[Task],
        pe_list: List[ProcessorElement],
        scheduler_class=None,
    ) -> None:
        self.task_list: List[Task] = list(task_list)
        self.pe_list: List[ProcessorElement] = list(pe_list)
        self.scheduler_class = scheduler_class if scheduler_class is not None else TaskScheduler

    def generate_assigment_from_individual(self, individual: Individual) -> List[TaskAssignment]:
        """Convert chromosome genes into TaskAssignment objects."""
        assignment_list: List[TaskAssignment] = []
        for task_index in range(individual.task_count):
            task = self.task_list[task_index]
            pe_freq_index = individual.get_freq_index(task_index)
            pe_name = self.pe_list[individual.get_pe_index(task_index)].name
            assignment_list.append(TaskAssignment(task, pe_name, pe_freq_index))
        return assignment_list

    # Alias for legacy typo
    generate_assignment_from_individual = generate_assigment_from_individual

    def generate_scheduler_from_individual(self, individual: Individual) -> TaskScheduler:
        """Build and execute a TaskScheduler corresponding to individual's genes."""
        scheduler = self.scheduler_class(self.pe_list)
        assignments = self.generate_assigment_from_individual(individual)
        scheduler.assign(assignments)
        scheduler.schedule()
        return scheduler
