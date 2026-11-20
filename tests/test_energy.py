"""
Unit tests for EnergyModel and FitnessEvaluator, including bug fix verification.
"""

import unittest
from lowpower_scheduler.core.energy import EnergyModel, FitnessEvaluator
from lowpower_scheduler.models.processor import ProcessorElement
from lowpower_scheduler.models.task import Task
from lowpower_scheduler.models.assignment import TaskAssignment
from lowpower_scheduler.core.scheduler import TaskScheduler


class TestEnergyAndFitness(unittest.TestCase):
    def test_efficient_capacity_scalar_bug_fix(self):
        """
        Verify that passing a scalar efficient_capacity sets efficient_capacity
        to [efficient_capacity]*pe_count and does NOT overwrite it with idle_power!
        (Fixes critical bug in original code).
        """
        idle_power = 10.0
        eff_cap = 2.5
        v_rail = 4.0
        comm_power = 5.0
        pe_count = 3

        model = EnergyModel(
            pe_count=pe_count,
            communication_power=comm_power,
            idle_power=idle_power,
            efficient_capacity=eff_cap,
            voltage_rail_capacity=v_rail,
        )

        self.assertEqual(model.efficient_capacity, [2.5, 2.5, 2.5])
        self.assertEqual(model.idle_power, [10.0, 10.0, 10.0])
        self.assertEqual(model.voltage_rail_capacity, [4.0, 4.0, 4.0])

    def test_mismatched_sequence_length_raises(self):
        with self.assertRaises(ValueError):
            EnergyModel(
                pe_count=2,
                communication_power=10.0,
                idle_power=[1.0, 2.0, 3.0],  # 3 items for 2 PEs
                efficient_capacity=1.0,
                voltage_rail_capacity=1.0,
            )

    def test_transition_energy_calculation(self):
        """
        P0 with levels (1000MHz, 5V) and (500MHz, 3V).
        If tasks run at 3V, transition from 5V to 3V: Delta V = 2V.
        E_trans = C_rail * (2^2) = 4 * 4 = 16.
        Return to base 5V: Delta V = 2V -> 16. Total = 32.
        """
        pe = ProcessorElement("P0", [(1000, 5), (500, 3)])
        t1 = Task("T1", 50.0, {"P0": 5.0})
        # Freq index 1 is 500MHz @ 3V
        pe.assign([TaskAssignment(t1, "P0", 1)])
        pe.schedule()
        trans_energy = pe.get_transition_energy(voltage_rail_capacity=4.0)
        self.assertEqual(trans_energy, 32.0)

    def test_fitness_deadline_penalty(self):
        pe = ProcessorElement("P0", [(1000, 5)])
        # Task with deadline 5.0 but execution time 10.0 -> deadline miss!
        t = Task("T0", deadline=5.0, execution_times={"P0": 10.0})
        scheduler = TaskScheduler([pe])
        scheduler.assign([TaskAssignment(t, "P0", 0)])
        scheduler.schedule()
        self.assertTrue(scheduler.is_miss_deadline())

        evaluator_no_penalty = FitnessEvaluator(10, 10, 1, 4, pe_count=1, deadline_penalty_weight=0.0)
        evaluator_with_penalty = FitnessEvaluator(10, 10, 1, 4, pe_count=1, deadline_penalty_weight=2.0)

        fit_no_pen = evaluator_no_penalty.get_fitness(scheduler)
        fit_with_pen = evaluator_with_penalty.get_fitness(scheduler)

        # Penalized fitness must be significantly lower
        self.assertLess(fit_with_pen, fit_no_pen)


if __name__ == "__main__":
    unittest.main()
