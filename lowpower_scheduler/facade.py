"""
Facade pattern: LowPowerOptimizer providing a clean high-level API.
"""

from __future__ import annotations
from typing import List, Tuple, Optional, Dict, Any
from lowpower_scheduler.models.task import Task
from lowpower_scheduler.models.processor import ProcessorElement
from lowpower_scheduler.models.assignment import TaskAssignment
from lowpower_scheduler.core.scheduler import TaskScheduler, DagTaskScheduler
from lowpower_scheduler.core.energy import FitnessEvaluator, EnergyBreakdown
from lowpower_scheduler.core.individual import Individual
from lowpower_scheduler.ga.engine import GeneticAlgorithm
from lowpower_scheduler.ga.callbacks import ConsoleReporter, HistoryLogger


class OptimizationSummary:
    """Encapsulates before/after optimization metrics and energy savings."""

    def __init__(
        self,
        baseline_energy: float,
        optimized_energy: float,
        best_individual: Individual,
        best_scheduler: TaskScheduler,
        breakdown: EnergyBreakdown,
        history: HistoryLogger,
    ) -> None:
        self.baseline_energy: float = baseline_energy
        self.optimized_energy: float = optimized_energy
        self.energy_saved: float = max(0.0, baseline_energy - optimized_energy)
        self.savings_percentage: float = (
            (self.energy_saved / baseline_energy * 100.0) if baseline_energy > 0 else 0.0
        )
        self.best_individual: Individual = best_individual
        self.best_scheduler: TaskScheduler = best_scheduler
        self.breakdown: EnergyBreakdown = breakdown
        self.history: HistoryLogger = history

    def print_summary(self) -> None:
        print("\n" + "=" * 60)
        print("               OPTIMIZATION SUMMARY")
        print("=" * 60)
        print(f"Baseline (Max-Perf) Energy : {self.baseline_energy:,.2f}")
        print(f"Optimized (DVFS GA) Energy : {self.optimized_energy:,.2f}")
        print(f"Total Energy Saved         : {self.energy_saved:,.2f} ({self.savings_percentage:.2f}%)")
        print(f"Optimal Chromosome (DNA)   : {self.best_individual}")
        print(f"Deadline Compliance        : {'MET' if not self.best_scheduler.is_miss_deadline() else 'VIOLATED'}")
        print("=" * 60 + "\n")


class LowPowerOptimizer:
    """
    Facade providing a unified, simplified interface to optimize
    task scheduling and DVFS power states using Genetic Algorithms.
    """

    def __init__(
        self,
        tasks: List[Task],
        processors: List[ProcessorElement],
        fitness_evaluator: FitnessEvaluator,
        use_dag_scheduler: bool = False,
    ) -> None:
        self.tasks: List[Task] = list(tasks)
        self.processors: List[ProcessorElement] = list(processors)
        self.fitness_evaluator: FitnessEvaluator = fitness_evaluator
        self.scheduler_class = DagTaskScheduler if use_dag_scheduler else TaskScheduler

    def compute_baseline(self) -> float:
        """
        Evaluate baseline energy: tasks run at maximum frequency (index 0)
        distributed across processors in round-robin fashion.
        """
        pe_count = len(self.processors)
        assignments = []
        for i, task in enumerate(self.tasks):
            pe = self.processors[i % pe_count]
            assignments.append(TaskAssignment(task, pe.name, frequency_index=0))

        scheduler = self.scheduler_class(self.processors)
        scheduler.assign(assignments)
        scheduler.schedule()
        return self.fitness_evaluator.get_energy(scheduler)

    def optimize(
        self,
        generations: int = 50,
        population_size: int = 40,
        mutation_rate: float = 0.15,
        crossover_rate: float = 0.85,
        elitism_count: int = 2,
        verbose: bool = True,
    ) -> OptimizationSummary:
        """
        Run genetic algorithm optimization to find the lowest energy schedule.
        """
        baseline_energy = self.compute_baseline()

        ga = GeneticAlgorithm(
            task_list=self.tasks,
            pe_list=self.processors,
            fitness_evaluator=self.fitness_evaluator,
            population_size=population_size,
            generations=generations,
            mutation_rate=mutation_rate,
            crossover_rate=crossover_rate,
            elitism_count=elitism_count,
            scheduler_class=self.scheduler_class,
        )

        if verbose:
            ga.add_observer(ConsoleReporter(interval=max(1, generations // 5)))

        best_ind, best_sched, best_energy = ga.run()
        breakdown = self.fitness_evaluator.calculate_breakdown(best_sched)

        summary = OptimizationSummary(
            baseline_energy=baseline_energy,
            optimized_energy=best_energy,
            best_individual=best_ind,
            best_scheduler=best_sched,
            breakdown=breakdown,
            history=ga.history,
        )

        if verbose:
            summary.print_summary()

        return summary
