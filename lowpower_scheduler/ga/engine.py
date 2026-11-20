"""
Genetic Algorithm optimization engine using Template Method and Strategy patterns.
"""

from __future__ import annotations
import random
from typing import List, Tuple, Optional, Type
from lowpower_scheduler.models.processor import ProcessorElement
from lowpower_scheduler.models.task import Task
from lowpower_scheduler.core.individual import Individual, IndividualFactory, ScheduleGenerator
from lowpower_scheduler.core.scheduler import TaskScheduler
from lowpower_scheduler.core.energy import FitnessEvaluator
from lowpower_scheduler.strategies.selection import SelectionStrategy, TournamentSelection
from lowpower_scheduler.strategies.crossover import CrossoverStrategy, SinglePointCrossover
from lowpower_scheduler.strategies.mutation import MutationStrategy, RandomResettingMutation
from lowpower_scheduler.ga.callbacks import GAObserver, HistoryLogger


class GeneticAlgorithm:
    """
    Genetic Algorithm engine for low-power heterogeneous task scheduling.
    Optimizes task-to-processor allocation and DVFS frequency selection
    to minimize total system energy while satisfying real-time deadlines.
    """

    def __init__(
        self,
        task_list: List[Task],
        pe_list: List[ProcessorElement],
        fitness_evaluator: FitnessEvaluator,
        population_size: int = 40,
        generations: int = 60,
        crossover_rate: float = 0.85,
        mutation_rate: float = 0.15,
        elitism_count: int = 2,
        selection_strategy: Optional[SelectionStrategy] = None,
        crossover_strategy: Optional[CrossoverStrategy] = None,
        mutation_strategy: Optional[MutationStrategy] = None,
        scheduler_class: Type[TaskScheduler] = TaskScheduler,
        observers: Optional[List[GAObserver]] = None,
    ) -> None:
        self.task_list: List[Task] = list(task_list)
        self.pe_list: List[ProcessorElement] = list(pe_list)
        self.fitness_evaluator: FitnessEvaluator = fitness_evaluator
        self.population_size: int = max(4, population_size)
        self.generations: int = max(1, generations)
        self.crossover_rate: float = float(crossover_rate)
        self.mutation_rate: float = float(mutation_rate)
        self.elitism_count: int = max(0, min(elitism_count, self.population_size // 2))

        # Pluggable Strategies (DIP / OCP)
        self.selection_strategy: SelectionStrategy = (
            selection_strategy if selection_strategy is not None else TournamentSelection(3)
        )
        self.crossover_strategy: CrossoverStrategy = (
            crossover_strategy if crossover_strategy is not None else SinglePointCrossover()
        )
        self.mutation_strategy: MutationStrategy = (
            mutation_strategy if mutation_strategy is not None else RandomResettingMutation(self.mutation_rate)
        )
        self.scheduler_class: Type[TaskScheduler] = scheduler_class

        # Observers
        self.observers: List[GAObserver] = list(observers) if observers else []
        self.history: HistoryLogger = HistoryLogger()
        self.observers.insert(0, self.history)

        # Helpers
        freq_counts = [len(p.frequency_list) for p in self.pe_list]
        self.factory = IndividualFactory(
            list_frequencies_count=freq_counts,
            task_count=len(self.task_list),
            crossover_strategy=self.crossover_strategy,
            mutation_strategy=self.mutation_strategy,
        )
        self.schedule_generator = ScheduleGenerator(
            task_list=self.task_list,
            pe_list=self.pe_list,
            scheduler_class=self.scheduler_class,
        )

    def add_observer(self, observer: GAObserver) -> None:
        """Register an observer to track optimization events."""
        self.observers.append(observer)

    def _evaluate(self, individual: Individual) -> Tuple[float, float, int, TaskScheduler]:
        """Compute (fitness, total_energy, missed_deadline_count, executed_scheduler)."""
        scheduler = self.schedule_generator.generate_scheduler_from_individual(individual)
        energy = self.fitness_evaluator.get_energy(scheduler)
        fitness = self.fitness_evaluator.get_fitness(scheduler)
        missed = len(scheduler.miss_deadline)
        return fitness, energy, missed, scheduler

    def run(self) -> Tuple[Individual, TaskScheduler, float]:
        """
        Execute the genetic optimization loop.
        Returns:
            Tuple of (best_individual, best_scheduler, best_energy_in_joules)
        """
        for obs in self.observers:
            obs.on_optimization_start(self.generations, self.population_size)

        # 1. Initialize random population
        population: List[Individual] = [
            self.factory.generate_random() for _ in range(self.population_size)
        ]

        # 2. Initial evaluation
        eval_results = [self._evaluate(ind) for ind in population]
        fitnesses = [r[0] for r in eval_results]

        best_idx = max(range(self.population_size), key=lambda i: fitnesses[i])
        best_individual: Individual = population[best_idx].clone()
        best_fitness, best_energy, best_missed, best_scheduler = eval_results[best_idx]

        # 3. Evolution loop
        for gen in range(1, self.generations + 1):
            # Sort population descending by fitness for elitism
            sorted_indices = sorted(range(self.population_size), key=lambda i: fitnesses[i], reverse=True)
            new_population: List[Individual] = []

            # Preserve elite individuals
            for e in range(self.elitism_count):
                new_population.append(population[sorted_indices[e]].clone())

            # Generate offspring
            while len(new_population) < self.population_size:
                parent_a = self.selection_strategy.select(population, fitnesses)
                parent_b = self.selection_strategy.select(population, fitnesses)

                if random.random() < self.crossover_rate:
                    child_a, child_b = self.factory.crossover(parent_a, parent_b)
                else:
                    child_a, child_b = parent_a.clone(), parent_b.clone()

                child_a = self.factory.mutate(child_a)
                new_population.append(child_a)

                if len(new_population) < self.population_size:
                    child_b = self.factory.mutate(child_b)
                    new_population.append(child_b)

            population = new_population

            # Evaluate new generation
            eval_results = [self._evaluate(ind) for ind in population]
            fitnesses = [r[0] for r in eval_results]

            current_best_idx = max(range(self.population_size), key=lambda i: fitnesses[i])
            curr_fit, curr_eng, curr_miss, curr_sched = eval_results[current_best_idx]

            if curr_fit > best_fitness:
                best_individual = population[current_best_idx].clone()
                best_fitness = curr_fit
                best_energy = curr_eng
                best_missed = curr_miss
                best_scheduler = curr_sched

            avg_fit = sum(fitnesses) / self.population_size

            # Notify observers and check early stopping
            stop_requested = False
            for obs in self.observers:
                if obs.on_generation_end(gen, best_individual, best_fitness, avg_fit, best_energy, best_missed):
                    stop_requested = True

            if stop_requested:
                break

        for obs in self.observers:
            obs.on_optimization_end(best_individual, best_fitness, best_energy)

        return best_individual, best_scheduler, best_energy
