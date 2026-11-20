"""
Unit tests for Genetic Algorithm operators and chromosome bug fixes.
"""

import unittest
from lowpower_scheduler.core.individual import Individual, IndividualFactory
from lowpower_scheduler.strategies.crossover import SinglePointCrossover, TwoPointCrossover, UniformCrossover
from lowpower_scheduler.strategies.mutation import RandomResettingMutation, SwapMutation
from lowpower_scheduler.strategies.selection import TournamentSelection, RouletteWheelSelection, RankSelection


class TestGAOperators(unittest.TestCase):
    def test_individual_indexing_bug_fix(self):
        """
        For task_count = 3, DNA has length 6:
        PE genes: indices 0, 1, 2
        Frequency genes: indices 3, 4, 5
        Verify get_pe_index and get_freq_index at boundary index 3 (task_count).
        """
        # dna: PE=[0, 1, 0], Freq=[2, 1, 0]
        ind = Individual([0, 1, 0, 2, 1, 0])
        self.assertEqual(ind.task_count, 3)

        # Boundary index 3 is first frequency gene
        self.assertEqual(ind.get_pe_index(3), 0)    # dna[3 - 3] = dna[0] = 0
        self.assertEqual(ind.get_freq_index(3), 2)  # dna[3] = 2

        # Explicit task helpers
        self.assertEqual(ind.get_pe_for_task(0), 0)
        self.assertEqual(ind.get_pe_for_task(1), 1)
        self.assertEqual(ind.get_pe_for_task(2), 0)
        self.assertEqual(ind.get_freq_for_task(0), 2)
        self.assertEqual(ind.get_freq_for_task(1), 1)
        self.assertEqual(ind.get_freq_for_task(2), 0)

    def test_mutation_bounds_no_index_error(self):
        """
        Run 200 mutations to ensure random_index does not exceed len(dna) - 1.
        (Fixes randint(0, len(dna)) IndexError bug).
        """
        factory = IndividualFactory(list_frequencies_count=[3, 2], task_count=5)
        for _ in range(200):
            ind = factory.generate_random()
            mutated = factory.mutate(ind)
            self.assertEqual(len(mutated.dna), 10)
            # Verify PE valid
            for t in range(5):
                pe = mutated.dna[t]
                self.assertIn(pe, [0, 1])
                # Verify Frequency valid for assigned PE
                freq = mutated.dna[5 + t]
                max_freq = 3 if pe == 0 else 2
                self.assertLess(freq, max_freq)

    def test_crossover_reaches_last_gene(self):
        """
        Verify single point crossover can swap the tail including the last gene.
        (Fixes dna[cut : -1] off-by-one bug).
        """
        # Parent A: all 0s, Parent B: all 1s
        parent_a = Individual([0, 0, 0, 0])
        parent_b = Individual([1, 1, 1, 1])
        crossover = SinglePointCrossover()

        # Over multiple runs, offspring should receive parent B's last gene
        received_last_gene_from_b = False
        for _ in range(50):
            child_a, child_b = crossover.crossover(parent_a, parent_b)
            if child_a.dna[-1] == 1:
                received_last_gene_from_b = True
                break
        self.assertTrue(received_last_gene_from_b)

    def test_selection_strategies(self):
        pop = [Individual([0, 0]), Individual([1, 1]), Individual([0, 1])]
        fitnesses = [1.0, 10.0, 5.0]  # Ind 1 is best

        tourn = TournamentSelection(tournament_size=3)
        selected = tourn.select(pop, fitnesses)
        self.assertEqual(selected, pop[1])

        rank = RankSelection()
        selected_rank = rank.select(pop, fitnesses)
        self.assertIn(selected_rank, pop)

        rw = RouletteWheelSelection()
        selected_rw = rw.select(pop, fitnesses)
        self.assertIn(selected_rw, pop)


if __name__ == "__main__":
    unittest.main()
