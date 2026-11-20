"""
Legacy compatibility wrapper for CommunicationElement.
"""

from lowpower_scheduler.models.communication import CommunicationElement, BusChannel
from lowpower_scheduler.strategies.arbiter import PriorityArbiter

__all__ = ["CommunicationElement", "BusChannel", "PriorityArbiter"]
