"""
Bus arbitration strategies using the Strategy design pattern.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from lowpower_scheduler.models.communication import CommunicationRequest


class ArbiterStrategy(ABC):
    """Abstract Strategy for shared bus communication arbitration."""

    @abstractmethod
    def select_request(self, requests: List[CommunicationRequest]) -> CommunicationRequest:
        """Select one communication request from candidates ready for transmission."""
        pass


class PriorityArbiter(ArbiterStrategy):
    """
    Selects the request with highest priority.
    Breaks ties by earliest arrival time (request_time), then shortest duration.
    """

    def select_request(self, requests: List[CommunicationRequest]) -> CommunicationRequest:
        if not requests:
            raise ValueError("Cannot select from empty requests list")
        return min(requests, key=lambda r: (-r.priority, r.request_time, r.duration))


class FCFSArbiter(ArbiterStrategy):
    """
    First-Come First-Served arbitration: selects request with earliest arrival time.
    Breaks ties by higher priority, then shortest duration.
    """

    def select_request(self, requests: List[CommunicationRequest]) -> CommunicationRequest:
        if not requests:
            raise ValueError("Cannot select from empty requests list")
        return min(requests, key=lambda r: (r.request_time, -r.priority, r.duration))


class ShortestFirstArbiter(ArbiterStrategy):
    """
    Shortest transmission time first.
    Breaks ties by earlier arrival time, then priority.
    """

    def select_request(self, requests: List[CommunicationRequest]) -> CommunicationRequest:
        if not requests:
            raise ValueError("Cannot select from empty requests list")
        return min(requests, key=lambda r: (r.duration, r.request_time, -r.priority))
