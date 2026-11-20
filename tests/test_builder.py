"""
Unit tests for Fluent Builders and LowPowerOptimizer facade.
"""

import unittest
from lowpower_scheduler.builder.system_builder import SystemBuilder, TaskGraphBuilder
from lowpower_scheduler.facade import LowPowerOptimizer


class TestBuilderAndFacade(unittest.TestCase):
    def test_system_and_task_builders(self):
        sys_config = (
            SystemBuilder()
            .add_processor("P0", [(1000, 5), (500, 3)])
            .add_processor("P1", [(1000, 5), (400, 3)])
            .set_communication_power(10.0)
            .set_idle_power(10.0)
            .set_efficient_capacities([1.0, 2.0])
            .set_voltage_rail_capacities([4.0, 4.0])
            .build()
        )

        self.assertEqual(len(sys_config.processors), 2)
        self.assertEqual(sys_config.fitness_evaluator.pe_count, 2)
        self.assertEqual(sys_config.fitness_evaluator.efficient_capacity, [1.0, 2.0])

        graph = (
            TaskGraphBuilder()
            .add_task("T0", deadline=25.0, execution_times={"P0": 10.0, "P1": 10.0}, communications={"T1": 2.0})
            .add_task("T1", deadline=25.0, execution_times={"P0": 8.0, "P1": 16.0})
            .build()
        )

        self.assertEqual(len(graph), 2)
        order = graph.topological_sort()
        self.assertEqual([t.name for t in order], ["T0", "T1"])

    def test_facade_optimization(self):
        sys_config = (
            SystemBuilder()
            .add_processor("P0", [(1000, 5), (500, 3)])
            .add_processor("P1", [(1000, 5), (400, 3)])
            .set_communication_power(10.0)
            .set_idle_power(10.0)
            .set_efficient_capacities(1.0)
            .set_voltage_rail_capacities(4.0)
            .build()
        )

        tasks = (
            TaskGraphBuilder()
            .add_task("T0", deadline=30.0, execution_times={"P0": 10.0, "P1": 12.0})
            .add_task("T1", deadline=30.0, execution_times={"P0": 5.0, "P1": 6.0})
            .build_task_list()
        )

        optimizer = LowPowerOptimizer(tasks, sys_config.processors, sys_config.fitness_evaluator)
        summary = optimizer.optimize(generations=10, population_size=15, verbose=False)

        self.assertGreater(summary.baseline_energy, 0.0)
        self.assertGreater(summary.optimized_energy, 0.0)
        self.assertIsNotNone(summary.best_individual)


if __name__ == "__main__":
    unittest.main()
