from .TaskScheduler import *

class Fitness:
    def __init__(self, communication_power : float, idle_power, efficient_capacity, voltage_rail_capacity, pe_count) -> None:
        
        if(pe_count == 0): raise Exception("pe_count is zero")
        self.pe_count = pe_count
        self.communication_power = communication_power

        if(isinstance(idle_power, (float, int))):
            self.idle_power = [idle_power] * pe_count
        else:
            if(len(idle_power) != pe_count): raise Exception("len(idle_power) not equal with pe_count")
            self.idle_power = idle_power

        if(isinstance(efficient_capacity, (float, int))):
            self.efficient_capacity = [idle_power] * pe_count
        else:
            if(len(efficient_capacity) != pe_count): raise Exception("len(efficient_capacity) not equal with pe_count")
            self.efficient_capacity = efficient_capacity

        if(isinstance(voltage_rail_capacity, (float, int))):
            self.voltage_rail_capacity = [voltage_rail_capacity] * pe_count
        else:
            if(len(voltage_rail_capacity) != pe_count): raise Exception("len(voltage_rail_capacity) not equal with pe_count")
            self.voltage_rail_capacity = voltage_rail_capacity


    def get_energy(self, scheduler : TaskScheduler) -> float:
        total_energy = 0.0
        for index, pe in enumerate(scheduler.pe_list):
            dynamic_energy = pe.get_dynamic_energy(self.efficient_capacity[index])
            transition_energy = pe.get_transition_energy(self.voltage_rail_capacity[index])
            idle_energy = pe.get_idle_energy(self.idle_power[index], scheduler.end_time)
            total_energy += dynamic_energy + transition_energy + idle_energy
            
        total_energy += scheduler.ce.get_energy(self.communication_power)
        return total_energy

    def get_fitness(self, scheduler : TaskScheduler) -> float:
        return 1.0 / self.get_energy(scheduler)
    
    def print(self, scheduler : TaskScheduler) -> None:
        total_energy = 0.0
        print("\n****** Energy Report ******")
        for index, pe in enumerate(scheduler.pe_list):
            dynamic_energy = pe.get_dynamic_energy(self.efficient_capacity[index])
            transition_energy = pe.get_transition_energy(self.voltage_rail_capacity[index])
            idle_energy = pe.get_idle_energy(self.idle_power[index], scheduler.end_time)
            total_energy += dynamic_energy + transition_energy + idle_energy
            print(f"PE name : {pe.name}")
            print(f"dynamic_energy = {dynamic_energy}, transition_energy = {transition_energy}, idle_energy = {idle_energy}")
            print(f"efficient_capacity = {self.efficient_capacity[index]}, voltage_rail_capacity = {self.voltage_rail_capacity[index]}, idle_power = {self.idle_power[index]}")

            print("\n")
          
        ce_energy = scheduler.ce.get_energy(self.communication_power)
        print(f"communication_power = {self.communication_power}")
        print(f"communication_energy = {ce_energy}")
        print(f"\ntotal_energy = {total_energy + ce_energy}\n")