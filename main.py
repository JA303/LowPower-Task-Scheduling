import sys

sys.path.append('..')

from Scheduler.Task import *
from Scheduler.TaskAssignment import *
from Scheduler.TaskScheduler import *
from Scheduler.ProccessorElement import *
from Scheduler.Individual import *

def get_tasks_pes():
    test_list = []
    global_deadline = 25
    test_list.append(Task('T0', global_deadline, {'P0':10 , 'P1':10}, {'T1':2, 'T2':5, 'T3':10}))
    test_list.append(Task('T1', global_deadline, {'P0':8 , 'P1':16}, {'T3':2}))
    test_list.append(Task('T2', global_deadline, {'P0':3 , 'P1':9}, {'T3':6}))
    test_list.append(Task('T3', global_deadline, {'P0':5 , 'P1':6}))
    test_list.append(Task('T4', global_deadline, {'P0':2.5 , 'P1':3}))
    test_list.append(Task('T5', global_deadline + 25, {'P0':3 , 'P1':2.5}))
    test_list.append(Task('T6', global_deadline + 10, {'P0':4 , 'P1':4}, {'T5':3}))

    pe_list = []
    pe_list.append(ProccessorElement('P0', [1, 0.5, 0.5]))
    pe_list.append(ProccessorElement('P1', [1, 0.5, 0.4]))

    return (test_list, pe_list)

def test_scheduler():
    tasks , pe_list = get_tasks_pes()
    
    assignt_list = [TaskAssignment(tasks[0], pe_list[0].name, 0), TaskAssignment(tasks[1], pe_list[0].name, 1), TaskAssignment(tasks[2], pe_list[1].name, 0), TaskAssignment(tasks[3], pe_list[1].name, 0), TaskAssignment(tasks[4], pe_list[1].name, 0)]
    
    t_s = TaskScheduler(pe_list)
    t_s.assign(assignt_list)
    t_s.schedule()
    t_s.print()

def test_random_individual():
    tasks , pe_list = get_tasks_pes()
    individualGenerator = IndividualGenerator([len(p.frequency_list) for p in pe_list], len(tasks))
    individual = individualGenerator.generate_random()
    print(individual)
    return individual

def test_schedule_generator():
    tasks , pe_list = get_tasks_pes()
    schedule_generator = ScheduleGenerator(tasks, pe_list)
    individualGenerator = IndividualGenerator([len(p.frequency_list) for p in pe_list], len(tasks))

    individual_a = individualGenerator.generate_random()
    print(f"\n individual_a = {individual_a}")
    schedule_generator.generate_scheduler_from_individual(individual_a).print()

    individual_b = individualGenerator.generate_random()
    print(f"\n individual_b = {individual_b}")
    schedule_generator.generate_scheduler_from_individual(individual_b).print()

    cross_individual_a , cross_individual_b = IndividualGenerator.crossover(individual_a, individual_b)
    
    print(f"\n cross_individual_a = {cross_individual_a}")
    schedule_generator.generate_scheduler_from_individual(cross_individual_a).print()

    print(f"\n cross_individual_b = {cross_individual_b}")
    schedule_generator.generate_scheduler_from_individual(cross_individual_b).print()

    mutate_cross_individual_b = individualGenerator.mutate(cross_individual_b)
    print(f"\n mutate_cross_individual_b = {mutate_cross_individual_b}")
    schedule_generator.generate_scheduler_from_individual(mutate_cross_individual_b).print()

def main():
    # test_scheduler()
    # test_genetic_algorithm()
    test_schedule_generator()

if __name__ == '__main__':
    main()