"""
Communication modeling: CommunicationRequest and BusChannel (CommunicationElement).
"""

from __future__ import annotations
from typing import List, Optional
from lowpower_scheduler.core.timeline import Timeline
from lowpower_scheduler.strategies.arbiter import ArbiterStrategy, PriorityArbiter


class CommunicationRequest:
    """Represents a message or data transfer over a shared communication channel."""

    def __init__(
        self,
        source: str,
        destination: str,
        duration: float,
        request_time: float,
        priority: int = 0,
    ) -> None:
        self.source: str = source
        self.destination: str = destination
        self.duration: float = float(duration)
        self.request_time: float = float(request_time)
        self.priority: int = int(priority)
        self.name: str = f"{source}->{destination}"

    def __str__(self) -> str:
        return (
            f"(CommunicationRequest: time {self.request_time:.1f} from {self.source} "
            f"to {self.destination}, d={self.duration:.1f}, p={self.priority})"
        )

    def __repr__(self) -> str:
        return f"CommunicationRequest({self.name}, t={self.request_time}, d={self.duration}, p={self.priority})"

    def __hash__(self) -> int:
        return hash((self.name, self.request_time, self.duration, self.priority))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CommunicationRequest):
            return (
                self.name == other.name
                and self.request_time == other.request_time
                and self.duration == other.duration
                and self.priority == other.priority
            )
        return False


class BusChannel:
    """
    Simulates a shared half-duplex communication bus with contention and arbitration.
    """

    # Backward compatibility alias for the legacy nested Arbiter class
    Arbiter = PriorityArbiter

    def __init__(
        self,
        name: str = "BUS",
        arbiter: Optional[ArbiterStrategy] = None,
    ) -> None:
        self.name: str = name
        self.arbiter: ArbiterStrategy = arbiter if arbiter is not None else PriorityArbiter()
        self.timeline: Timeline = Timeline()

    def schedule(self, communication_requests: List[CommunicationRequest]) -> None:
        """
        Schedule all communication requests onto the bus timeline according to the arbiter policy.
        Resets previous timeline state before scheduling.
        """
        self.timeline = Timeline()
        if not communication_requests:
            return

        unserved = list(communication_requests)
        current_time = min(r.request_time for r in unserved)
        delay = current_time

        while unserved:
            ready_reqs = [r for r in unserved if r.request_time <= current_time]

            if not ready_reqs:
                # Bus is idle waiting for next request arrival
                next_arrival = min(r.request_time for r in unserved)
                delay = next_arrival - current_time
                current_time = next_arrival
                ready_reqs = [r for r in unserved if r.request_time <= current_time]

            selected = self.arbiter.select_request(ready_reqs)
            unserved.remove(selected)

            self.timeline.append(selected, selected.duration, delay)
            delay = 0.0
            current_time += selected.duration

    def get_energy(self, communication_power: float) -> float:
        """Calculate bus transmission energy: E_comm = P_comm * total_active_time."""
        return self.timeline.get_all_duration_time() * communication_power

    def __repr__(self) -> str:
        return f"BusChannel(name='{self.name}', arbiter={self.arbiter.__class__.__name__})"


# Alias for backward compatibility
CommunicationElement = BusChannel
