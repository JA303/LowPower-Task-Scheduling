"""
Parent selection strategies for Genetic Algorithm using Strategy pattern.
"""

from __future__ import annotations
import random
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from lowpower_scheduler.core.individual import Individual


class SelectionStrategy(ABC):
    """Abstract Strategy interface for mating selection."""

    @abstractmethod
    def select(self, population: List[Individual], fitnesses: List[float]) -> Individual:
        """Select one individual from population according to fitness values."""
        pass


class TournamentSelection(SelectionStrategy):
    """
    Tournament Selection: picks k individuals at random and selects the one
    with the highest fitness. Robust against fitness scaling and maintains diversity.
    """

    def __init__(self, tournament_size: int = 3) -> None:
        self.tournament_size: int = max(1, tournament_size)

    def select(self, population: List[Individual], fitnesses: List[float]) -> Individual:
        pop_size = len(population)
        sample_indices = random.sample(range(pop_size), min(self.tournament_size, pop_size))
        best_idx = max(sample_indices, key=lambda idx: fitnesses[idx])
        return population[best_idx]


class RouletteWheelSelection(SelectionStrategy):
    """
    Fitness-Proportionate (Roulette Wheel) Selection.
    Probability of selection is proportional to fitness score.
    """

    def select(self, population: List[Individual], fitnesses: List[float]) -> Individual:
        total_fitness = sum(fitnesses)
        if total_fitness <= 0:
            return random.choice(population)

        spin = random.uniform(0, total_fitness)
        accumulated = 0.0
        for ind, fit in zip(population, fitnesses):
            accumulated += fit
            if accumulated >= spin:
                return ind
        return population[-1]


class RankSelection(SelectionStrategy):
    """
    Rank-Based Selection: selection probability is proportional to sorted fitness rank.
    Eliminates stagnation when fitnesses are too close or extreme outliers exist.
    """

    def select(self, population: List[Individual], fitnesses: List[float]) -> Individual:
        pop_size = len(population)
        # Sort indices ascending by fitness so rank 1 is lowest, rank N is highest
        sorted_indices = sorted(range(pop_size), key=lambda idx: fitnesses[idx])
        total_ranks = pop_size * (pop_size + 1) // 2

        spin = random.randint(1, total_ranks)
        accumulated = 0
        for rank, idx in enumerate(sorted_indices, start=1):
            accumulated += rank
            if accumulated >= spin:
                return population[idx]
        return population[sorted_indices[-1]]


class RandomSelection(SelectionStrategy):
    """Uniform random selection (useful for baseline comparisons)."""

    def select(self, population: List[Individual], fitnesses: List[float]) -> Individual:
        return random.choice(population)
