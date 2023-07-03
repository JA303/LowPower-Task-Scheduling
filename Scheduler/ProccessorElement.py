from .TaskAssignment import *
from .Timeline import *
from .CommunicationRequest import *

class ProccessorElement:
    def __init__(self, name : str, frequency_list : list[float]):
        self.name = name
        self.frequency_list = frequency_list
        self.base_frequency = frequency_list[0]
        self.task_timeline = Timeline()

    def assign(self, assignment_list : list[TaskAssignment]):
        self.verify_assignments(self.name, assignment_list)
        self.assignment_list = assignment_list

    def verify_assignments(self, pe_name : str, assignment_list : list[TaskAssignment]):
        for assignment in assignment_list:
            if assignment.pe_name != pe_name: raise Exception(f"{pe_name}:Invalid assignment for task {assignment.task.name}")


    def schedule(self) -> list[Task]:
        self.assignment_list.sort(key=lambda t: t.frequency_index)
        self.task_timeline = Timeline()
        miss_deadline_tasks = []
        
        for assignment in self.assignment_list:
            executuin_frequency = self.frequency_list[assignment.frequency_index]
            task_base_exection_time = assignment.task.get_execution_time(self.name)
            exection_time = (self.base_frequency / executuin_frequency) * task_base_exection_time
            self.task_timeline.append(assignment.task, exection_time)

            if(self.task_timeline.timeline_length > assignment.task.deadline):
                miss_deadline_tasks.append(assignment.task)

        return miss_deadline_tasks

    def task_names(self) -> list[str]:
        return [a.task.name for a in self.assignment_list]

    def get_communication_requests(self) -> list[CommunicationRequest]:
        my_task_names = self.task_names()
        result = []

        for assignment in self.assignment_list:
            task = assignment.task
            for comm in  task.get_communication_times(my_task_names):
                task_end_time = self.task_timeline.get_end_time(task)
                newReq = CommunicationRequest(task.name, comm[0], comm[1], task_end_time, priority=0)
                result.append(newReq)
        
        return result
    
    def __str__(self) -> str:
        pass