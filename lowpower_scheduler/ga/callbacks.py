"""
Observer pattern callbacks for monitoring Genetic Algorithm optimization.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from lowpower_scheduler.core.individual import Individual


class GAObserver(ABC):
    """Abstract Observer for receiving lifecycle events during GA execution."""

    def on_optimization_start(self, total_generations: int, population_size: int) -> None:
        pass

    def on_generation_end(
        self,
        generation: int,
        best_individual: Individual,
        best_fitness: float,
        avg_fitness: float,
        best_energy: float,
        missed_deadlines: int,
    ) -> bool:
        """
        Invoked at the end of each generation.
        Return True to request early termination of the optimization loop.
        """
        return False

    def on_optimization_end(self, best_individual: Individual, best_fitness: float, best_energy: float) -> None:
        pass


class HistoryLogger(GAObserver):
    """
    Logs generation-by-generation optimization history for metrics tracking and plotting.
    """

    def __init__(self) -> None:
        self.generations: List[int] = []
        self.best_fitness: List[float] = []
        self.avg_fitness: List[float] = []
        self.best_energy: List[float] = []
        self.missed_deadlines: List[int] = []

    def on_generation_end(
        self,
        generation: int,
        best_individual: Individual,
        best_fitness: float,
        avg_fitness: float,
        best_energy: float,
        missed_deadlines: int,
    ) -> bool:
        self.generations.append(generation)
        self.best_fitness.append(best_fitness)
        self.avg_fitness.append(avg_fitness)
        self.best_energy.append(best_energy)
        self.missed_deadlines.append(missed_deadlines)
        return False


class EarlyStopping(GAObserver):
    """
    Stops optimization early if best fitness does not improve for `patience` consecutive generations.
    """

    def __init__(self, patience: int = 15, min_delta: float = 1e-8) -> None:
        self.patience: int = patience
        self.min_delta: float = min_delta
        self.best_score: float = -float("inf")
        self.wait: int = 0

    def on_generation_end(
        self,
        generation: int,
        best_individual: Individual,
        best_fitness: float,
        avg_fitness: float,
        best_energy: float,
        missed_deadlines: int,
    ) -> bool:
        if best_fitness > self.best_score + self.min_delta:
            self.best_score = best_fitness
            self.wait = 0
        else:
            self.wait += 1
            if self.wait >= self.patience:
                return True  # Request early stop
        return False


class ConsoleReporter(GAObserver):
    """
    Prints a formatted status line every `interval` generations.
    """

    def __init__(self, interval: int = 10) -> None:
        self.interval: int = max(1, interval)

    def on_optimization_start(self, total_generations: int, population_size: int) -> None:
        print(f"\n[GA] Starting optimization: {total_generations} gens, population {population_size}")
        print(f"{'Gen':>5} | {'Best Fitness':>14} | {'Avg Fitness':>14} | {'Best Energy':>14} | {'Missed':>6}")
        print("-" * 65)

    def on_generation_end(
        self,
        generation: int,
        best_individual: Individual,
        best_fitness: float,
        avg_fitness: float,
        best_energy: float,
        missed_deadlines: int,
    ) -> bool:
        if generation % self.interval == 0 or generation == 1:
            print(
                f"{generation:>5} | {best_fitness:>14.6e} | {avg_fitness:>14.6e} | "
                f"{best_energy:>14,.2f} | {missed_deadlines:>6}"
            )
        return False

    def on_optimization_end(self, best_individual: Individual, best_fitness: float, best_energy: float) -> None:
        print("-" * 65)
        print(f"[GA] Finished! Optimal Energy: {best_energy:,.2f} | Best DNA: {best_individual}\n")
