"""
LowPower Task Scheduling - Main Demonstration Script.

Showcases heterogeneous multi-core task scheduling with Dynamic Voltage and
Frequency Scaling (DVFS), CMOS energy modeling, and Genetic Algorithm optimization.
"""

import sys
import os

sys.path.append(os.path.dirname(__file__))

from Scheduler.Task import Task
from Scheduler.TaskAssignment import TaskAssignment
from Scheduler.TaskScheduler import TaskScheduler, DagTaskScheduler
from Scheduler.ProcessorElement import ProcessorElement
from Scheduler.Individual import Individual, IndividualGenerator, ScheduleGenerator
from Scheduler.Fitness import Fitness, FitnessEvaluator
from lowpower_scheduler.facade import LowPowerOptimizer


def get_tasks_pes():
    """Build the benchmark task workload and heterogeneous processor platform."""
    test_list = []
    global_deadline = 25.0
    test_list.append(Task('T0', global_deadline, {'P0': 10.0, 'P1': 10.0}, {'T1': 2.0, 'T2': 5.0, 'T3': 10.0}))
    test_list.append(Task('T1', global_deadline, {'P0': 8.0, 'P1': 16.0}, {'T3': 2.0}))
    test_list.append(Task('T2', global_deadline, {'P0': 3.0, 'P1': 9.0}, {'T3': 6.0}))
    test_list.append(Task('T3', global_deadline, {'P0': 5.0, 'P1': 6.0}))
    test_list.append(Task('T4', global_deadline, {'P0': 2.5, 'P1': 3.0}))
    test_list.append(Task('T5', global_deadline + 25.0, {'P0': 3.0, 'P1': 2.5}))
    test_list.append(Task('T6', global_deadline + 10.0, {'P0': 4.0, 'P1': 4.0}, {'T5': 3.0}))

    pe_list = []
    pe_list.append(ProcessorElement('P0', [(1000, 5.0), (500, 3.0), (100, 1.0)]))
    pe_list.append(ProcessorElement('P1', [(1000, 5.0), (400, 3.0), (200, 1.0)]))

    return test_list, pe_list


def test_scheduler():
    """Test manual static task assignment and schedule generation."""
    print("\n--- Running test_scheduler ---")
    tasks, pe_list = get_tasks_pes()

    assignt_list = [
        TaskAssignment(tasks[0], pe_list[0].name, 0),
        TaskAssignment(tasks[1], pe_list[0].name, 1),
        TaskAssignment(tasks[2], pe_list[1].name, 0),
        TaskAssignment(tasks[3], pe_list[1].name, 0),
        TaskAssignment(tasks[4], pe_list[1].name, 0),
    ]

    t_s = TaskScheduler(pe_list)
    t_s.assign(assignt_list)
    t_s.schedule()
    t_s.print()


def test_random_individual():
    """Test random chromosome generation."""
    print("\n--- Running test_random_individual ---")
    tasks, pe_list = get_tasks_pes()
    individualGenerator = IndividualGenerator([len(p.frequency_list) for p in pe_list], len(tasks))
    individual = individualGenerator.generate_random()
    print(f"Generated Random Individual: {individual}")
    return individual


def test_schedule_generator():
    """Test schedule generation, crossover, and mutation operators."""
    print("\n--- Running test_schedule_generator ---")
    tasks, pe_list = get_tasks_pes()
    schedule_generator = ScheduleGenerator(tasks, pe_list)
    individualGenerator = IndividualGenerator([len(p.frequency_list) for p in pe_list], len(tasks))

    individual_a = individualGenerator.generate_random()
    print(f"\nIndividual A: {individual_a}")
    schedule_generator.generate_scheduler_from_individual(individual_a).print()

    individual_b = individualGenerator.generate_random()
    print(f"\nIndividual B: {individual_b}")
    schedule_generator.generate_scheduler_from_individual(individual_b).print()

    cross_individual_a, cross_individual_b = IndividualGenerator.crossover(individual_a, individual_b)

    print(f"\nCrossover Offspring A: {cross_individual_a}")
    schedule_generator.generate_scheduler_from_individual(cross_individual_a).print()

    print(f"\nCrossover Offspring B: {cross_individual_b}")
    schedule_generator.generate_scheduler_from_individual(cross_individual_b).print()

    mutate_cross_individual_b = individualGenerator.mutate(cross_individual_b)
    print(f"\nMutated Offspring B: {mutate_cross_individual_b}")
    schedule_generator.generate_scheduler_from_individual(mutate_cross_individual_b).print()


def test_energy_calcutation():
    """Test energy evaluation and breakdown reporting."""
    print("\n--- Running test_energy_calculation ---")
    tasks, pe_list = get_tasks_pes()
    schedule_generator = ScheduleGenerator(tasks, pe_list)
    individualGenerator = IndividualGenerator([len(p.frequency_list) for p in pe_list], len(tasks))
    fitness = Fitness(10.0, 10.0, [1.0, 2.0], 4.0, pe_count=2)

    individual_random = individualGenerator.generate_random()
    schedule = schedule_generator.generate_scheduler_from_individual(individual_random)
    print(f"Random Schedule Individual: {individual_random}")
    schedule.print()
    fitness.print(schedule)


def test_genetic_algorithm():
    """Test full Genetic Algorithm optimization and report energy savings."""
    print("\n--- Running test_genetic_algorithm ---")
    tasks, pe_list = get_tasks_pes()
    fitness = Fitness(10.0, 10.0, [1.0, 2.0], 4.0, pe_count=2, deadline_penalty_weight=2.0)

    optimizer = LowPowerOptimizer(tasks, pe_list, fitness)
    summary = optimizer.optimize(
        generations=30,
        population_size=25,
        mutation_rate=0.15,
        crossover_rate=0.85,
        elitism_count=2,
        verbose=True,
    )
    return summary


def main():
    print("=" * 70)
    print("   LOW-POWER HETEROGENEOUS MULTI-CORE TASK SCHEDULING")
    print("=" * 70)

    # 1. Test schedule generation with crossover & mutation
    test_schedule_generator()

    # 2. Test physical energy breakdown calculation
    test_energy_calcutation()

    # 3. Test Genetic Algorithm optimization loop
    test_genetic_algorithm()


if __name__ == '__main__':
    main()
