from .TaskAssignment import *
from .Timeline import *
from .CommunicationRequest import *

class ProcessorElement:
    def __init__(self, name : str, frequency_voltage_list : list[tuple[float, float]]):
        self.name = name
        self.task_timeline = Timeline()

        frequency_voltage_list.sort(key= lambda t: t[0], reverse=True)
        self.frequency_list, self.voltage_list = list(map(list, zip(*frequency_voltage_list)))
        self.base_frequency = self.frequency_list[0]
        

    def assign(self, assignment_list : list[TaskAssignment]):
        self.verify_assignments(self.name, assignment_list)
        self.assignment_list = assignment_list

    def verify_assignments(self, pe_name : str, assignment_list : list[TaskAssignment]):
        for assignment in assignment_list:
            if assignment.pe_name != pe_name: raise Exception(f"{pe_name}:Invalid assignment for task {assignment.task.name}")


    def schedule(self) -> list[Task]:
        self.assignment_list.sort(key=lambda t: (t.frequency_index, t.task.deadline))
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
    
    def get_dynamic_energy(self, efficient_capacity : float) -> float:
        energy = 0.0
        for i, assignment in enumerate(self.assignment_list):
            executuin_frequency = self.frequency_list[assignment.frequency_index]
            executuin_voltage = self.voltage_list[assignment.frequency_index]
            duration =  self.task_timeline.get_duration_time(assignment.task)
            energy = energy + (efficient_capacity * executuin_frequency * pow(executuin_voltage, 2)) * duration
        return energy
    
    def get_transition_energy(self, voltage_rail_capacity : float) -> float:
        energy = 0.0
        previous_voltage = self.voltage_list[0]
        for i, assignment in enumerate(self.assignment_list):
            executuin_voltage = self.voltage_list[assignment.frequency_index]
            energy = energy + (voltage_rail_capacity * pow(abs(previous_voltage - executuin_voltage) , 2))
            previous_voltage = executuin_voltage

        return energy + (voltage_rail_capacity * pow(abs(previous_voltage - self.voltage_list[0]) , 2))
    
    def get_idle_energy(self, idle_power : float, end_time : float) -> float:
        return (end_time - self.task_timeline.timeline_length) * idle_power
    
    def __str__(self) -> str:
        pass