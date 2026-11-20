"""
Legacy compatibility wrapper for ProcessorElement (including legacy misspelled ProccessorElement).
"""

from lowpower_scheduler.models.processor import ProcessorElement, DVFSLevel

# Alias for legacy spelling
ProccessorElement = ProcessorElement

__all__ = ["ProcessorElement", "ProccessorElement", "DVFSLevel"]
