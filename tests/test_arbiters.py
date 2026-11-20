"""
Unit tests for Bus arbitration strategies, verifying arbitration logic and bug fixes.
"""

import unittest
from lowpower_scheduler.models.communication import CommunicationRequest, BusChannel
from lowpower_scheduler.strategies.arbiter import (
    PriorityArbiter,
    FCFSArbiter,
    ShortestFirstArbiter,
)


class TestBusArbiters(unittest.TestCase):
    def test_priority_arbiter_selection(self):
        """
        Req A: priority 1, time 5.0, duration 4.0
        Req B: priority 2, time 5.0, duration 4.0 (same time and duration, higher priority)
        In the original buggy code, 'r.request_time < selected.request_time' was required,
        so Req B would NOT be selected despite higher priority!
        The fixed PriorityArbiter must correctly select Req B.
        """
        req_a = CommunicationRequest("T0", "T1", duration=4.0, request_time=5.0, priority=1)
        req_b = CommunicationRequest("T2", "T3", duration=4.0, request_time=5.0, priority=2)

        arbiter = PriorityArbiter()
        selected = arbiter.select_request([req_a, req_b])
        self.assertEqual(selected, req_b)

    def test_fcfs_arbiter_selection(self):
        req_earlier = CommunicationRequest("T0", "T1", duration=5.0, request_time=2.0, priority=1)
        req_later = CommunicationRequest("T2", "T3", duration=1.0, request_time=6.0, priority=10)

        arbiter = FCFSArbiter()
        selected = arbiter.select_request([req_later, req_earlier])
        self.assertEqual(selected, req_earlier)

    def test_shortest_first_arbiter(self):
        req_long = CommunicationRequest("T0", "T1", duration=10.0, request_time=1.0)
        req_short = CommunicationRequest("T2", "T3", duration=2.0, request_time=1.0)

        arbiter = ShortestFirstArbiter()
        selected = arbiter.select_request([req_long, req_short])
        self.assertEqual(selected, req_short)

    def test_bus_channel_resets_timeline_on_reschedule(self):
        """Verify BusChannel resets timeline on repeated schedule calls."""
        bus = BusChannel("BUS")
        req = CommunicationRequest("T0", "T1", duration=2.0, request_time=0.0)
        bus.schedule([req])
        self.assertEqual(bus.timeline.count(), 1)
        self.assertEqual(bus.timeline.time(), 2.0)

        # Schedule again: should not accumulate items
        bus.schedule([req])
        self.assertEqual(bus.timeline.count(), 1)
        self.assertEqual(bus.timeline.time(), 2.0)


if __name__ == "__main__":
    unittest.main()
