"""
Example 2: Genetic Algorithm Optimization of Task-to-PE Allocation & DVFS States.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lowpower_scheduler import (
    SystemBuilder,
    TaskGraphBuilder,
    LowPowerOptimizer,
)


def main():
    print("=" * 65)
    print("  EXAMPLE 2: GENETIC ALGORITHM LOW-POWER OPTIMIZATION")
    print("=" * 65)

    # 1. System architecture with heterogeneous PEs
    sys_config = (
        SystemBuilder()
        .add_processor("P0", [(1000, 5.0), (500, 3.0), (100, 1.0)])
        .add_processor("P1", [(1000, 5.0), (400, 3.0), (200, 1.0)])
        .set_communication_power(10.0)
        .set_idle_power(10.0)
        .set_efficient_capacities([1.0, 2.0])
        .set_voltage_rail_capacities([4.0, 4.0])
        .set_deadline_penalty(2.0)
        .build()
    )

    # 2. 7-task benchmark workload
    global_deadline = 25.0
    tasks = (
        TaskGraphBuilder()
        .add_task("T0", deadline=global_deadline, execution_times={"P0": 10.0, "P1": 10.0}, communications={"T1": 2.0, "T2": 5.0, "T3": 10.0})
        .add_task("T1", deadline=global_deadline, execution_times={"P0": 8.0, "P1": 16.0}, communications={"T3": 2.0})
        .add_task("T2", deadline=global_deadline, execution_times={"P0": 3.0, "P1": 9.0}, communications={"T3": 6.0})
        .add_task("T3", deadline=global_deadline, execution_times={"P0": 5.0, "P1": 6.0})
        .add_task("T4", deadline=global_deadline, execution_times={"P0": 2.5, "P1": 3.0})
        .add_task("T5", deadline=global_deadline + 25.0, execution_times={"P0": 3.0, "P1": 2.5})
        .add_task("T6", deadline=global_deadline + 10.0, execution_times={"P0": 4.0, "P1": 4.0}, communications={"T5": 3.0})
        .build_task_list()
    )

    # 3. Optimize with the LowPowerOptimizer Facade
    optimizer = LowPowerOptimizer(
        tasks=tasks,
        processors=sys_config.processors,
        fitness_evaluator=sys_config.fitness_evaluator,
    )

    summary = optimizer.optimize(
        generations=40,
        population_size=30,
        mutation_rate=0.15,
        crossover_rate=0.85,
        elitism_count=2,
        verbose=True,
    )

    # Print the resulting optimal schedule
    summary.best_scheduler.print()
    sys_config.fitness_evaluator.print(summary.best_scheduler)


if __name__ == "__main__":
    main()
