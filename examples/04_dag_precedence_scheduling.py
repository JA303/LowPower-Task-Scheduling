"""
Example 4: DAG-Precedence-Constrained Heterogeneous Task Scheduling.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lowpower_scheduler import (
    SystemBuilder,
    TaskGraphBuilder,
    DagTaskScheduler,
    TaskAssignment,
)


def main():
    print("=" * 65)
    print("  EXAMPLE 4: DAG PRECEDENCE-AWARE SCHEDULING WITH BUS COMM")
    print("=" * 65)

    # 1. System Setup
    sys_config = (
        SystemBuilder()
        .add_processor("P0", [(1000, 5.0), (500, 3.0)])
        .add_processor("P1", [(1000, 5.0), (400, 3.0)])
        .set_communication_power(10.0)
        .build()
    )

    # 2. Dependency Graph:
    # T0 -> T1 and T0 -> T2
    # T1 -> T3 and T2 -> T3
    # Diamond DAG!
    tasks = (
        TaskGraphBuilder()
        .add_task("T0", deadline=60.0, execution_times={"P0": 10.0, "P1": 15.0}, communications={"T1": 3.0, "T2": 4.0})
        .add_task("T1", deadline=60.0, execution_times={"P0": 8.0, "P1": 12.0}, communications={"T3": 2.0})
        .add_task("T2", deadline=60.0, execution_times={"P0": 6.0, "P1": 7.0}, communications={"T3": 3.0})
        .add_task("T3", deadline=60.0, execution_times={"P0": 5.0, "P1": 6.0})
        .build_task_list()
    )

    # 3. Assign tasks across cores:
    # T0 on P0 (0.0 - 10.0)
    # T1 on P1 (must wait for T0->T1 bus communication!)
    # T2 on P0 (can start immediately after T0 at 10.0 because intra-PE!)
    # T3 on P1 (must wait for T1 and T2->T3 bus communication!)
    assignments = [
        TaskAssignment(tasks[0], "P0", frequency_index=0),
        TaskAssignment(tasks[1], "P1", frequency_index=0),
        TaskAssignment(tasks[2], "P0", frequency_index=0),
        TaskAssignment(tasks[3], "P1", frequency_index=0),
    ]

    scheduler = DagTaskScheduler(sys_config.processors)
    scheduler.assign(assignments)
    scheduler.schedule()
    scheduler.print()

    sys_config.fitness_evaluator.print(scheduler)


if __name__ == "__main__":
    main()
