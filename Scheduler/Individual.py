import random
from copy import deepcopy

from .ProccessorElement import *
from .TaskAssignment import *
from .TaskScheduler import *
from .Task import *

class Individual:
    def __init__(self, dna : list[int]) -> None:
        self.dna = dna
        self.task_count = len(dna) // 2

    def get_pe_index(self, index : int) -> int:
        return self.dna[index] if index <= self.task_count else self.dna[index - self.task_count]
    
    
    def get_freq_index(self, index : int) -> int:
        return self.dna[index + self.task_count] if index <= self.task_count else self.dna[index]

    def __str__(self) -> str:
        return ''.join(map(str, self.dna))


class IndividualGenerator:
    def __init__(self, list_frequencies_count : list[int], task_count : int) -> None:
        self.pe_count = len(list_frequencies_count)
        self.list_frequencies_count = list_frequencies_count
        self.task_count = task_count
    
    def generate_random(self) -> Individual:
        dna = [0] * (self.task_count * 2)
        for task_number in range(0, self.task_count):
            selcted_pe = random.randint(0, self.pe_count - 1)
            dna[task_number] = selcted_pe
            dna[task_number + self.task_count] = random.randint(0, self.list_frequencies_count[selcted_pe] - 1)

        return Individual(dna)
    
    def mutate(self, individual : Individual) -> Individual:
        mutate_individual = deepcopy(individual)
        random_index = random.randint(0, len(mutate_individual.dna))
        selected_value = mutate_individual.dna[random_index]
        new_value = selected_value
        if(random_index <= mutate_individual.task_count):
            choice_list = list(range(0, selected_value)) + list(range(selected_value + 1, self.pe_count))
        else:
            pe_index = mutate_individual.get_pe_index(random_index)
            choice_list = list(range(0, selected_value)) + list(range(selected_value + 1, self.list_frequencies_count[pe_index]))

        if len(choice_list) != 0 :
            new_value = random.choice(choice_list)

        mutate_individual.dna[random_index] = new_value
        return mutate_individual
    
class ScheduleGenerator:
    def __init__(self, task_list : list[Task], pe_list : list[ProccessorElement]) -> None:
        self.task_list = task_list
        self.pe_list = pe_list

    def generate_assigment_from_individual(self, individual : Individual) -> list[TaskAssignment]:
        assigment_list = []
        for task_index in range(0, individual.task_count):
            task = self.task_list[task_index]
            pe_freq_index = individual.get_freq_index(task_index)
            pe_name = self.pe_list[individual.get_pe_index(task_index)].name
            assigment_list.append(TaskAssignment(task, pe_name, pe_freq_index))
        return assigment_list
    
    def generate_scheduler_from_individual(self, individual : Individual) -> TaskScheduler:
        taskScheduler = TaskScheduler(self.pe_list)
        taskScheduler.assign(self.generate_assigment_from_individual(individual))
        taskScheduler.schedule()
        return taskScheduler
    
