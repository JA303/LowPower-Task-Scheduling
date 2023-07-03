class Task:
    def __init__(self, name : str, deadline : float, execution_times : dict[str, float], communication_times : dict[str, float] = {}) -> None:
        self.name = name
        self.deadline = deadline
        self.execution_times = execution_times
        self.communication_times = communication_times

    def __hash__(self) -> int:
        return hash(self.name)
    
    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Task):
            return self.name == __value.name
        return False

    def get_execution_time(self, pe_name : str) -> float:
        return self.execution_times[pe_name]
    
    def get_communication_times(self, exclude_destenations : tuple[str, float]):
         return [c for c in self.communication_times.items() if c[0] not in exclude_destenations]
    
    def get_communication_time(self, destenation : str) -> float:
         return self.communication_times[destenation]