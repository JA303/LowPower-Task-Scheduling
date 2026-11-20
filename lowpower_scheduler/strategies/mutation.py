"""
Mutation strategies for Genetic Algorithm chromosome variation.
"""

from __future__ import annotations
import random
from abc import ABC, abstractmethod
from copy import deepcopy
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from lowpower_scheduler.core.individual import Individual


class MutationStrategy(ABC):
    """Abstract Strategy interface for genetic mutation."""

    @abstractmethod
    def mutate(
        self,
        individual: Individual,
        pe_count: int,
        freq_counts: List[int],
    ) -> Individual:
        """Apply mutation operator to produce a mutated individual."""
        pass


class RandomResettingMutation(MutationStrategy):
    """
    Random Resetting Mutation: picks a random gene and replaces its value with
    another permissible value. Corrects boundary off-by-one errors and guarantees
    valid frequency levels for newly assigned PEs.
    """

    def __init__(self, mutation_rate: float = 0.15) -> None:
        self.mutation_rate: float = mutation_rate

    def mutate(
        self,
        individual: Individual,
        pe_count: int,
        freq_counts: List[int],
    ) -> Individual:
        mutated = deepcopy(individual)
        dna_len = len(mutated.dna)
        task_count = mutated.task_count

        if dna_len == 0:
            return mutated

        # Mutate at least one gene, plus additional genes with mutation_rate probability
        indices_to_mutate = [random.randint(0, dna_len - 1)]
        for i in range(dna_len):
            if i not in indices_to_mutate and random.random() < self.mutation_rate:
                indices_to_mutate.append(i)

        for gene_idx in indices_to_mutate:
            curr_val = mutated.dna[gene_idx]

            if gene_idx < task_count:
                # PE gene (0 to task_count - 1)
                task_idx = gene_idx
                available_pes = [p for p in range(pe_count) if p != curr_val]
                if available_pes:
                    new_pe = random.choice(available_pes)
                    mutated.dna[task_idx] = new_pe
                    # Ensure corresponding frequency gene is valid on the new PE
                    freq_gene_idx = task_count + task_idx
                    max_allowed_freq = freq_counts[new_pe] - 1
                    if mutated.dna[freq_gene_idx] > max_allowed_freq:
                        mutated.dna[freq_gene_idx] = random.randint(0, max_allowed_freq)
            else:
                # Frequency gene (task_count to 2 * task_count - 1)
                task_idx = gene_idx - task_count
                pe_idx = mutated.dna[task_idx]
                max_freq = freq_counts[pe_idx]
                available_freqs = [f for f in range(max_freq) if f != curr_val]
                if available_freqs:
                    mutated.dna[gene_idx] = random.choice(available_freqs)

        return mutated


class SwapMutation(MutationStrategy):
    """
    Swap Mutation: selects two tasks and exchanges their PE allocations
    or frequency levels.
    """

    def mutate(
        self,
        individual: Individual,
        pe_count: int,
        freq_counts: List[int],
    ) -> Individual:
        mutated = deepcopy(individual)
        task_count = mutated.task_count
        if task_count <= 1:
            return mutated

        task_a, task_b = random.sample(range(task_count), 2)

        if random.random() < 0.5:
            # Swap PEs
            mutated.dna[task_a], mutated.dna[task_b] = mutated.dna[task_b], mutated.dna[task_a]
            # Repair frequencies
            for t in (task_a, task_b):
                pe = mutated.dna[t]
                max_f = freq_counts[pe] - 1
                if mutated.dna[task_count + t] > max_f:
                    mutated.dna[task_count + t] = max_f
        else:
            # Re-sample frequency on one task
            pe = mutated.dna[task_a]
            mutated.dna[task_count + task_a] = random.randint(0, freq_counts[pe] - 1)

        return mutated
