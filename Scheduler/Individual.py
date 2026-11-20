"""
Legacy compatibility wrapper for Individual, IndividualGenerator, and ScheduleGenerator.
"""

from lowpower_scheduler.core.individual import (
    Individual,
    IndividualGenerator,
    IndividualFactory,
    ScheduleGenerator,
)

__all__ = [
    "Individual",
    "IndividualGenerator",
    "IndividualFactory",
    "ScheduleGenerator",
]
