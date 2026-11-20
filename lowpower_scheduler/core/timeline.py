"""
Timeline and TimeInterval tracking for scheduled tasks and communication events.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TimeInterval:
    """Represents a continuous execution window [start_time, end_time]."""
    start_time: float
    end_time: float

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def __repr__(self) -> str:
        return f"[{self.start_time:.2f} - {self.end_time:.2f}]"


class Timeline:
    """
    Manages non-overlapping execution intervals on a processor or communication channel.
    """

    # Backward compatibility alias
    TimePeriod = TimeInterval

    def __init__(self) -> None:
        self.timeline: Dict[Any, TimeInterval] = {}
        self.timeline_length: float = 0.0
        self.item_count: int = 0

    def append(self, item: Any, duration: float, delay: float = 0.0) -> TimeInterval:
        """Append an item to the timeline after optional delay."""
        start_time = self.timeline_length + delay
        end_time = start_time + duration
        interval = TimeInterval(start_time, end_time)
        self.timeline[item] = interval
        self.timeline_length = end_time
        self.item_count += 1
        return interval

    def insert_at(self, item: Any, start_time: float, duration: float) -> TimeInterval:
        """Insert an item starting at specific time, updating timeline length if needed."""
        end_time = start_time + duration
        interval = TimeInterval(start_time, end_time)
        self.timeline[item] = interval
        if end_time > self.timeline_length:
            self.timeline_length = end_time
        self.item_count += 1
        return interval

    def clear(self) -> None:
        """Reset timeline state."""
        self.timeline.clear()
        self.timeline_length = 0.0
        self.item_count = 0

    def count(self) -> int:
        return self.item_count

    def time(self) -> float:
        return self.timeline_length

    def get_end_time(self, item: Any) -> float:
        return self.timeline[item].end_time

    def get_start_time(self, item: Any) -> float:
        return self.timeline[item].start_time

    def get_duration_time(self, item: Any) -> float:
        return self.timeline[item].duration

    def get_all_duration_time(self) -> float:
        """Sum of busy execution time across all scheduled items."""
        return sum(interval.duration for interval in self.timeline.values())

    def get_sorted_intervals(self) -> List[Tuple[Any, TimeInterval]]:
        """Return chronological list of (item, interval) tuples."""
        return sorted(self.timeline.items(), key=lambda x: x[1].start_time)

    def __len__(self) -> int:
        return self.item_count

    def __contains__(self, item: Any) -> bool:
        return item in self.timeline

    def __str__(self) -> str:
        intervals = self.get_sorted_intervals()
        parts = []
        for item, interval in intervals:
            name = getattr(item, "name", str(item))
            parts.append(f"{name}: {interval.start_time:.1f}-{interval.end_time:.1f}")
        return f"(TimeLine= {' , '.join(parts)})" if parts else "(TimeLine= empty)"

    def __repr__(self) -> str:
        return f"Timeline(items={self.item_count}, length={self.timeline_length:.2f})"
