from setuptools import setup, find_packages

setup(
    name="lowpower-task-scheduling",
    version="1.0.0",
    packages=find_packages(include=["lowpower_scheduler*", "Scheduler*"]),
    python_requires=">=3.8",
)
