"""
Unit tests to guarantee 100% backward compatibility with legacy imports and API.
"""

import unittest
from Scheduler.Task import Task
from Scheduler.TaskAssignment import TaskAssignment
from Scheduler.ProccessorElement import ProccessorElement, ProcessorElement
from Scheduler.CommunicationElement import CommunicationElement
from Scheduler.CommunicationRequest import CommunicationRequest
from Scheduler.Timeline import Timeline
from Scheduler.TaskScheduler import TaskScheduler
from Scheduler.Individual import Individual, IndividualGenerator, ScheduleGenerator
from Scheduler.Fitness import Fitness


class TestBackwardCompatibility(unittest.TestCase):
    def test_legacy_classes_instantiation_and_methods(self):
        t0 = Task("T0", 30.0, {"P0": 10.0, "P1": 10.0}, {"T1": 2.0})
        t1 = Task("T1", 50.0, {"P0": 8.0, "P1": 16.0})

        # Test both ProcessorElement and legacy ProccessorElement spelling
        pe0 = ProccessorElement("P0", [(1000, 5), (500, 3), (100, 1)])
        pe1 = ProcessorElement("P1", [(1000, 5), (400, 3), (200, 1)])
        self.assertEqual(pe0.name, "P0")
        self.assertEqual(pe1.name, "P1")

        assignments = [
            TaskAssignment(t0, "P0", 0),
            TaskAssignment(t1, "P1", 1),
        ]

        scheduler = TaskScheduler([pe0, pe1])
        scheduler.assign(assignments)
        scheduler.schedule()

        self.assertFalse(scheduler.is_miss_deadline())

        fitness = Fitness(10.0, 10.0, [1.0, 2.0], 4.0, pe_count=2)
        energy = fitness.get_energy(scheduler)
        fit_score = fitness.get_fitness(scheduler)
        self.assertGreater(energy, 0.0)
        self.assertGreater(fit_score, 0.0)

    def test_legacy_generator_workflow(self):
        tasks = [
            Task("T0", 25.0, {"P0": 10.0, "P1": 10.0}),
            Task("T1", 25.0, {"P0": 8.0, "P1": 16.0}),
        ]
        pes = [
            ProcessorElement("P0", [(1000, 5), (500, 3)]),
            ProcessorElement("P1", [(1000, 5), (400, 3)]),
        ]

        gen = IndividualGenerator([len(p.frequency_list) for p in pes], len(tasks))
        ind_a = gen.generate_random()
        ind_b = gen.generate_random()

        self.assertEqual(ind_a.task_count, 2)
        self.assertEqual(len(ind_a.dna), 4)

        # Static call as in legacy main.py
        child_a, child_b = IndividualGenerator.crossover(ind_a, ind_b)
        self.assertEqual(len(child_a.dna), 4)

        # Instance call
        mutated = gen.mutate(child_a)
        self.assertEqual(len(mutated.dna), 4)

        # ScheduleGenerator
        sg = ScheduleGenerator(tasks, pes)
        sched = sg.generate_scheduler_from_individual(mutated)
        self.assertIsNotNone(sched)


if __name__ == "__main__":
    unittest.main()
