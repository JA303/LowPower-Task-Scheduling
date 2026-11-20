"""
Example 3: Demonstrating SOLID & Strategy Pattern with Custom Operators.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lowpower_scheduler import (
    SystemBuilder,
    TaskGraphBuilder,
    GeneticAlgorithm,
)
from lowpower_scheduler.strategies.selection import RankSelection
from lowpower_scheduler.strategies.crossover import TwoPointCrossover
from lowpower_scheduler.strategies.mutation import SwapMutation
from lowpower_scheduler.strategies.arbiter import ShortestFirstArbiter


def main():
    print("=" * 65)
    print("  EXAMPLE 3: PLUGGING IN CUSTOM STRATEGIES (OPEN/CLOSED)")
    print("=" * 65)

    # 1. System with Shortest-Job-First (ShortestFirstArbiter) bus arbitration
    sys_config = (
        SystemBuilder()
        .add_processor("P0", [(1000, 5.0), (500, 3.0), (100, 1.0)])
        .add_processor("P1", [(1000, 5.0), (400, 3.0), (200, 1.0)])
        .set_bus(name="HIGH_SPEED_BUS", arbiter=ShortestFirstArbiter())
        .set_communication_power(8.0)
        .set_idle_power(5.0)
        .set_efficient_capacities([1.0, 1.5])
        .set_voltage_rail_capacities([2.0, 2.0])
        .build()
    )

    tasks = (
        TaskGraphBuilder()
        .add_task("T0", deadline=30.0, execution_times={"P0": 10.0, "P1": 10.0}, communications={"T1": 2.0})
        .add_task("T1", deadline=30.0, execution_times={"P0": 8.0, "P1": 16.0})
        .add_task("T2", deadline=30.0, execution_times={"P0": 3.0, "P1": 9.0})
        .build_task_list()
    )

    # 2. Inject custom operators into Genetic Algorithm (Strategy Pattern)
    ga = GeneticAlgorithm(
        task_list=tasks,
        pe_list=sys_config.processors,
        fitness_evaluator=sys_config.fitness_evaluator,
        population_size=20,
        generations=20,
        selection_strategy=RankSelection(),            # Rank-based selection
        crossover_strategy=TwoPointCrossover(),         # Two-point crossover
        mutation_strategy=SwapMutation(),               # Task-swap mutation
    )

    best_ind, best_sched, best_energy = ga.run()
    print(f"Optimization finished using custom strategies!")
    print(f"Optimal Energy: {best_energy:,.2f} | DNA: {best_ind}")


if __name__ == "__main__":
    main()
