from .Task import *

class TaskAssignment:    
    def __init__(self, task : Task, pe_name : str, frequency_index : int):
        self.task = task
        self.pe_name = pe_name
        self.frequency_index = frequency_index