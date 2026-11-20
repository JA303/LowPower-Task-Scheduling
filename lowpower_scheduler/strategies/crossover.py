"""
Crossover strategies for Genetic Algorithm chromosome recombination.
"""

from __future__ import annotations
import random
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Tuple, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from lowpower_scheduler.core.individual import Individual


class CrossoverStrategy(ABC):
    """Abstract Strategy interface for genetic crossover."""

    @abstractmethod
    def crossover(
        self,
        parent_a: Individual,
        parent_b: Individual,
        freq_counts: Optional[List[int]] = None,
    ) -> Tuple[Individual, Individual]:
        """Perform crossover between parent_a and parent_b, returning two offspring."""
        pass

    @staticmethod
    def repair(individual: Individual, freq_counts: Optional[List[int]]) -> None:
        """Ensure frequency genes are valid for their mapped PE after crossover."""
        if not freq_counts:
            return
        task_count = individual.task_count
        for i in range(task_count):
            pe_idx = individual.dna[i]
            max_freq = freq_counts[pe_idx] - 1
            if individual.dna[task_count + i] > max_freq:
                individual.dna[task_count + i] = max_freq


class SinglePointCrossover(CrossoverStrategy):
    """
    Single-point crossover: picks a cut point and swaps tails.
    Fixes the legacy off-by-one bug where the last gene was excluded.
    """

    def crossover(
        self,
        parent_a: Individual,
        parent_b: Individual,
        freq_counts: Optional[List[int]] = None,
    ) -> Tuple[Individual, Individual]:
        dna_len = len(parent_a.dna)
        if dna_len <= 1:
            return deepcopy(parent_a), deepcopy(parent_b)

        # Cut point strictly between 1 and dna_len - 1
        cut = random.randint(1, dna_len - 1)
        child_a_dna = parent_a.dna[:cut] + parent_b.dna[cut:]
        child_b_dna = parent_b.dna[:cut] + parent_a.dna[cut:]

        from lowpower_scheduler.core.individual import Individual
        offspring_a = Individual(child_a_dna)
        offspring_b = Individual(child_b_dna)

        self.repair(offspring_a, freq_counts)
        self.repair(offspring_b, freq_counts)
        return offspring_a, offspring_b


class TwoPointCrossover(CrossoverStrategy):
    """
    Two-point crossover: selects two cut points and swaps the enclosed segment.
    """

    def crossover(
        self,
        parent_a: Individual,
        parent_b: Individual,
        freq_counts: Optional[List[int]] = None,
    ) -> Tuple[Individual, Individual]:
        dna_len = len(parent_a.dna)
        if dna_len <= 2:
            return SinglePointCrossover().crossover(parent_a, parent_b, freq_counts)

        cut1 = random.randint(1, dna_len - 2)
        cut2 = random.randint(cut1 + 1, dna_len - 1)

        child_a_dna = parent_a.dna[:cut1] + parent_b.dna[cut1:cut2] + parent_a.dna[cut2:]
        child_b_dna = parent_b.dna[:cut1] + parent_a.dna[cut1:cut2] + parent_b.dna[cut2:]

        from lowpower_scheduler.core.individual import Individual
        offspring_a = Individual(child_a_dna)
        offspring_b = Individual(child_b_dna)

        self.repair(offspring_a, freq_counts)
        self.repair(offspring_b, freq_counts)
        return offspring_a, offspring_b


class UniformCrossover(CrossoverStrategy):
    """
    Uniform crossover: for each gene, independently choose with probability 0.5
    from parent A or parent B.
    """

    def __init__(self, swap_prob: float = 0.5) -> None:
        self.swap_prob: float = swap_prob

    def crossover(
        self,
        parent_a: Individual,
        parent_b: Individual,
        freq_counts: Optional[List[int]] = None,
    ) -> Tuple[Individual, Individual]:
        dna_len = len(parent_a.dna)
        child_a_dna = []
        child_b_dna = []

        for i in range(dna_len):
            if random.random() < self.swap_prob:
                child_a_dna.append(parent_b.dna[i])
                child_b_dna.append(parent_a.dna[i])
            else:
                child_a_dna.append(parent_a.dna[i])
                child_b_dna.append(parent_b.dna[i])

        from lowpower_scheduler.core.individual import Individual
        offspring_a = Individual(child_a_dna)
        offspring_b = Individual(child_b_dna)

        self.repair(offspring_a, freq_counts)
        self.repair(offspring_b, freq_counts)
        return offspring_a, offspring_b
