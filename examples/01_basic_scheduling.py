"""
Example 1: Basic Heterogeneous Task Scheduling with DVFS and Energy Analysis.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lowpower_scheduler import (
    SystemBuilder,
    TaskGraphBuilder,
    TaskAssignment,
    TaskScheduler,
)


def main():
    print("=" * 60)
    print("  EXAMPLE 1: BASIC HETEROGENEOUS TASK SCHEDULING")
    print("=" * 60)

    # 1. Build a heterogeneous dual-core processor platform with DVFS
    sys_config = (
        SystemBuilder()
        .add_processor("P0", [(1000, 5.0), (500, 3.0), (100, 1.0)])  # High-performance PE
        .add_processor("P1", [(1000, 5.0), (400, 3.0), (200, 1.0)])  # Energy-efficient PE
        .set_communication_power(10.0)
        .set_idle_power(10.0)
        .set_efficient_capacities([1.0, 2.0])
        .set_voltage_rail_capacities([4.0, 4.0])
        .build()
    )

    # 2. Define a workload with real-time deadlines and communication requirements
    tasks = (
        TaskGraphBuilder()
        .add_task("T0", deadline=25.0, execution_times={"P0": 10.0, "P1": 10.0}, communications={"T1": 2.0, "T2": 5.0})
        .add_task("T1", deadline=25.0, execution_times={"P0": 8.0, "P1": 16.0})
        .add_task("T2", deadline=25.0, execution_times={"P0": 3.0, "P1": 9.0})
        .build_task_list()
    )

    # 3. Create a schedule assignment
    assignments = [
        TaskAssignment(tasks[0], "P0", frequency_index=0),
        TaskAssignment(tasks[1], "P0", frequency_index=1),
        TaskAssignment(tasks[2], "P1", frequency_index=0),
    ]

    # 4. Schedule and print results
    scheduler = TaskScheduler(sys_config.processors)
    scheduler.assign(assignments)
    scheduler.schedule()
    scheduler.print()

    # 5. Evaluate energy breakdown
    sys_config.fitness_evaluator.print(scheduler)


if __name__ == "__main__":
    main()
