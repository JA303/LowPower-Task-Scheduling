"""
Unit tests for domain models (Task, TaskGraph, ProcessorElement, CommunicationRequest).
"""

import unittest
from lowpower_scheduler.models.task import Task, TaskGraph
from lowpower_scheduler.models.processor import ProcessorElement, DVFSLevel
from lowpower_scheduler.models.assignment import TaskAssignment
from lowpower_scheduler.models.communication import CommunicationRequest, BusChannel


class TestTask(unittest.TestCase):
    def test_task_creation_and_attributes(self):
        task = Task("T0", deadline=25.0, execution_times={"P0": 10.0, "P1": 12.0}, communication_times={"T1": 4.0})
        self.assertEqual(task.name, "T0")
        self.assertEqual(task.deadline, 25.0)
        self.assertEqual(task.get_execution_time("P0"), 10.0)
        self.assertEqual(task.get_execution_time("P1"), 12.0)
        self.assertEqual(task.get_communication_time("T1"), 4.0)

    def test_missing_execution_time_raises(self):
        task = Task("T0", deadline=10.0, execution_times={"P0": 5.0})
        with self.assertRaises(KeyError):
            task.get_execution_time("P1")

    def test_communication_times_exclusion(self):
        task = Task("T0", 20.0, {"P0": 5.0}, {"T1": 2.0, "T2": 3.0, "T3": 4.0})
        # Exclude T1 and T3
        filtered = task.get_communication_times(exclude_destinations=("T1", "T3"))
        self.assertEqual(filtered, [("T2", 3.0)])

    def test_task_equality_and_hash(self):
        t1 = Task("T0", 10.0, {"P0": 5.0})
        t2 = Task("T0", 20.0, {"P0": 8.0})
        t3 = Task("T1", 10.0, {"P0": 5.0})
        self.assertEqual(t1, t2)
        self.assertNotEqual(t1, t3)
        self.assertEqual(hash(t1), hash(t2))


class TestTaskGraph(unittest.TestCase):
    def test_topological_sort_linear(self):
        t0 = Task("T0", 10.0, {"P0": 2.0}, {"T1": 1.0})
        t1 = Task("T1", 20.0, {"P0": 3.0}, {"T2": 1.0})
        t2 = Task("T2", 30.0, {"P0": 4.0})
        graph = TaskGraph([t0, t1, t2])
        order = graph.topological_sort()
        names = [t.name for t in order]
        self.assertEqual(names, ["T0", "T1", "T2"])

    def test_cycle_detection(self):
        t0 = Task("T0", 10.0, {"P0": 2.0}, {"T1": 1.0})
        t1 = Task("T1", 20.0, {"P0": 3.0}, {"T0": 1.0})  # Cycle T0 -> T1 -> T0
        graph = TaskGraph([t0, t1])
        with self.assertRaises(ValueError):
            graph.topological_sort()


class TestProcessorElement(unittest.TestCase):
    def setUp(self):
        # 3 DVFS points: 1000MHz@5V, 500MHz@3V, 100MHz@1V
        self.pe = ProcessorElement("P0", [(1000, 5), (500, 3), (100, 1)])

    def test_dvfs_levels_sorted_descending(self):
        self.assertEqual(self.pe.frequency_list, [1000, 500, 100])
        self.assertEqual(self.pe.voltage_list, [5, 3, 1])
        self.assertEqual(self.pe.base_frequency, 1000)
        self.assertEqual(self.pe.base_voltage, 5)

    def test_invalid_empty_dvfs_raises(self):
        with self.assertRaises(ValueError):
            ProcessorElement("Empty", [])

    def test_invalid_assignment_pe_name_raises(self):
        t = Task("T0", 10.0, {"P0": 5.0, "P1": 6.0})
        with self.assertRaises(ValueError):
            self.pe.assign([TaskAssignment(t, "P1", 0)])

    def test_dynamic_energy_calculation(self):
        t = Task("T0", 50.0, {"P0": 10.0})
        # Assign at base frequency (index 0: 1000MHz, 5V)
        self.pe.assign([TaskAssignment(t, "P0", 0)])
        self.pe.schedule()
        # duration = 10.0. E_dyn = C_eff * f * V^2 * duration = 1.0 * 1000 * 25 * 10 = 250,000
        dyn = self.pe.get_dynamic_energy(efficient_capacity=1.0)
        self.assertEqual(dyn, 250000.0)

    def test_str_representation(self):
        s = str(self.pe)
        self.assertIn("P0", s)
        self.assertIn("1000", s)


if __name__ == "__main__":
    unittest.main()
