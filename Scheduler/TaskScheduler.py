from .ProccessorElement import *
from .CommunicationElement import *
from .TaskAssignment import *

class TaskScheduler:
    def __init__(self, pe_list : list[ProccessorElement]) -> None:
        self.pe_list = pe_list
        self.ce = CommunicationElement()

    def assign(self, assignment_list : list[TaskAssignment]):
        for pe in self.pe_list:
            my_assign_list = [a for a in assignment_list if a.pe_name == pe.name]
            pe.assign(my_assign_list)
    
    def schedule(self):
        self.communication_requests = []
        self.miss_deadline = []

        for pe in self.pe_list:
            miss_tasks = pe.schedule()
            self.miss_deadline.extend(miss_tasks)
            self.communication_requests.extend(pe.get_communication_requests())
            
        self.ce.schedule(self.communication_requests)
    
    def is_miss_deadline(self) -> bool:
        return len(self.miss_deadline) > 0

    def print(self):
        print("\n****** Proccessor Elements ******")
        for pe in self.pe_list:
            print(f"PE name : {pe.name}")
            print(pe.task_timeline)
            print("execute frequancy list:" + ''.join([ str(pe.frequency_list[a.frequency_index]) + ', ' for a in pe.assignment_list]) + "\n")
            
        print("\n****** Miss Deadline Tasks ******")
        print(''.join([f"{m.name}(deadline={m.deadline}), " for m in self.miss_deadline]))

        print("\n****** Communication Element ******")
        print(f"CE {self.ce.name}: {self.ce.timeline}")
        
        if hasattr(self, 'communication_requests'):
            print("\n****** Communication Requests ******")
            print(*self.communication_requests, sep='\n')
        