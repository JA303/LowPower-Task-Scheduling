"""
Unit tests for Timeline and TimeInterval tracking.
"""

import unittest
from lowpower_scheduler.core.timeline import Timeline, TimeInterval


class TestTimeline(unittest.TestCase):
    def setUp(self):
        self.timeline = Timeline()

    def test_append_continuous(self):
        self.timeline.append("TaskA", duration=10.0)
        self.timeline.append("TaskB", duration=5.0)
        self.assertEqual(self.timeline.time(), 15.0)
        self.assertEqual(self.timeline.count(), 2)
        self.assertEqual(self.timeline.get_start_time("TaskA"), 0.0)
        self.assertEqual(self.timeline.get_end_time("TaskA"), 10.0)
        self.assertEqual(self.timeline.get_start_time("TaskB"), 10.0)
        self.assertEqual(self.timeline.get_end_time("TaskB"), 15.0)

    def test_append_with_delay(self):
        self.timeline.append("TaskA", duration=5.0, delay=2.0)
        self.assertEqual(self.timeline.get_start_time("TaskA"), 2.0)
        self.assertEqual(self.timeline.get_end_time("TaskA"), 7.0)
        self.assertEqual(self.timeline.time(), 7.0)

        # Append next task with delay 3
        self.timeline.append("TaskB", duration=4.0, delay=3.0)
        self.assertEqual(self.timeline.get_start_time("TaskB"), 10.0)
        self.assertEqual(self.timeline.get_end_time("TaskB"), 14.0)
        self.assertEqual(self.timeline.time(), 14.0)

    def test_clear(self):
        self.timeline.append("TaskA", duration=5.0)
        self.assertEqual(self.timeline.count(), 1)
        self.timeline.clear()
        self.assertEqual(self.timeline.count(), 0)
        self.assertEqual(self.timeline.time(), 0.0)

    def test_all_duration_time(self):
        self.timeline.append("TaskA", duration=5.0, delay=2.0)
        self.timeline.append("TaskB", duration=3.0, delay=4.0)
        # Busy time is 5 + 3 = 8, makespan is 2 + 5 + 4 + 3 = 14
        self.assertEqual(self.timeline.get_all_duration_time(), 8.0)
        self.assertEqual(self.timeline.time(), 14.0)


if __name__ == "__main__":
    unittest.main()
