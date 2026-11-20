"""
Unit tests for the Genetic Algorithm optimization engine.
"""

import unittest
from lowpower_scheduler.models.processor import ProcessorElement
from lowpower_scheduler.models.task import Task
from lowpower_scheduler.core.energy import FitnessEvaluator
from lowpower_scheduler.ga.engine import GeneticAlgorithm
from lowpower_scheduler.ga.callbacks import EarlyStopping


class TestGeneticAlgorithm(unittest.TestCase):
    def setUp(self):
        self.tasks = [
            Task("T0", deadline=50.0, execution_times={"P0": 10.0, "P1": 12.0}, communication_times={"T1": 2.0}),
            Task("T1", deadline=50.0, execution_times={"P0": 8.0, "P1": 15.0}),
            Task("T2", deadline=50.0, execution_times={"P0": 5.0, "P1": 6.0}),
        ]
        self.pes = [
            ProcessorElement("P0", [(1000, 5), (500, 3)]),
            ProcessorElement("P1", [(1000, 5), (400, 3)]),
        ]
        self.evaluator = FitnessEvaluator(
            communication_power=10.0,
            idle_power=10.0,
            efficient_capacity=1.0,
            voltage_rail_capacity=4.0,
            pe_count=2,
        )

    def test_ga_runs_and_improves_or_maintains_fitness(self):
        ga = GeneticAlgorithm(
            task_list=self.tasks,
            pe_list=self.pes,
            fitness_evaluator=self.evaluator,
            population_size=20,
            generations=15,
            elitism_count=2,
        )
        best_ind, best_sched, best_energy = ga.run()

        self.assertIsNotNone(best_ind)
        self.assertIsNotNone(best_sched)
        self.assertGreater(best_energy, 0.0)

        # Check history was recorded
        history = ga.history
        self.assertEqual(len(history.generations), 15)
        # Verify elitism: best fitness across generations must be non-decreasing
        for i in range(1, len(history.best_fitness)):
            self.assertGreaterEqual(history.best_fitness[i], history.best_fitness[i - 1] - 1e-9)

    def test_early_stopping_observer(self):
        early_stop = EarlyStopping(patience=3)
        ga = GeneticAlgorithm(
            task_list=self.tasks,
            pe_list=self.pes,
            fitness_evaluator=self.evaluator,
            population_size=10,
            generations=50,
            observers=[early_stop],
        )
        best_ind, _, _ = ga.run()
        # Should stop before 50 generations due to small problem size
        self.assertLessEqual(len(ga.history.generations), 50)


if __name__ == "__main__":
    unittest.main()
