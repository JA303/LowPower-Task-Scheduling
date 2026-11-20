"""
Legacy compatibility wrapper for TaskScheduler.
"""

from lowpower_scheduler.core.scheduler import TaskScheduler, DagTaskScheduler

__all__ = ["TaskScheduler", "DagTaskScheduler"]
