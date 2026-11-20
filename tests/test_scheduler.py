"""
Unit tests for TaskScheduler and DagTaskScheduler.
"""

import unittest
from lowpower_scheduler.models.processor import ProcessorElement
from lowpower_scheduler.models.task import Task
from lowpower_scheduler.models.assignment import TaskAssignment
from lowpower_scheduler.core.scheduler import TaskScheduler, DagTaskScheduler


class TestSchedulers(unittest.TestCase):
    def setUp(self):
        self.p0 = ProcessorElement("P0", [(1000, 5), (500, 3)])
        self.p1 = ProcessorElement("P1", [(1000, 5), (400, 3)])

    def test_standard_scheduler_execution(self):
        t0 = Task("T0", deadline=50.0, execution_times={"P0": 10.0, "P1": 12.0})
        t1 = Task("T1", deadline=50.0, execution_times={"P0": 8.0, "P1": 15.0})

        scheduler = TaskScheduler([self.p0, self.p1])
        scheduler.assign([
            TaskAssignment(t0, "P0", 0),
            TaskAssignment(t1, "P1", 0),
        ])
        scheduler.schedule()

        self.assertFalse(scheduler.is_miss_deadline())
        self.assertEqual(self.p0.task_timeline.timeline_length, 10.0)
        self.assertEqual(self.p1.task_timeline.timeline_length, 15.0)
        self.assertEqual(scheduler.end_time, 15.0)

    def test_dag_scheduler_respects_dependencies_and_bus_comm(self):
        """
        T0 executes on P0 (duration = 10).
        T1 executes on P1, but depends on T0 with communication duration = 4.
        Therefore, on P1, T1 CANNOT start until:
        T0 end time (10.0) + Bus transfer duration (4.0) = 14.0!
        """
        t0 = Task("T0", deadline=100.0, execution_times={"P0": 10.0, "P1": 20.0}, communication_times={"T1": 4.0})
        t1 = Task("T1", deadline=100.0, execution_times={"P0": 20.0, "P1": 5.0})

        dag_scheduler = DagTaskScheduler([self.p0, self.p1])
        dag_scheduler.assign([
            TaskAssignment(t0, "P0", 0),  # T0 on P0 at 1000MHz -> duration 10
            TaskAssignment(t1, "P1", 0),  # T1 on P1 at 1000MHz -> duration 5
        ])
        dag_scheduler.schedule()

        # Check P0 timeline: T0 starts at 0, ends at 10
        self.assertEqual(self.p0.task_timeline.get_start_time(t0), 0.0)
        self.assertEqual(self.p0.task_timeline.get_end_time(t0), 10.0)

        # Check Bus timeline: communication request starts at 10.0, ends at 14.0
        self.assertEqual(dag_scheduler.ce.timeline.count(), 1)
        self.assertEqual(dag_scheduler.ce.timeline.time(), 14.0)

        # Check P1 timeline: T1 starts at 14.0 (after bus comm finishes!)
        self.assertGreaterEqual(self.p1.task_timeline.get_start_time(t1), 14.0)
        self.assertEqual(self.p1.task_timeline.get_duration_time(t1), 5.0)
        self.assertEqual(self.p1.task_timeline.get_end_time(t1), 19.0)


if __name__ == "__main__":
    unittest.main()
