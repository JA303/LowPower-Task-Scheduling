from .Timeline import *
from .CommunicationRequest import *

class CommunicationElement:

    class Arbiter:
        def select_request(self, reqs : list[CommunicationRequest]) -> CommunicationRequest:
            selected = reqs[0]
            for r in reqs:
                if(r.priority >= selected.priority and r.request_time < selected.request_time and r.duration < selected.duration):
                    selected = r

            return selected

    def __init__(self):
        self.name = "BUS"
        self.timeline = Timeline()
        self.arbiter = self.Arbiter()
    
    def schedule(self, communication_requests : list[CommunicationRequest]) -> None:
        if(len(communication_requests) == 0) : return
        current_time = min(communication_requests, key=lambda r : r.request_time).request_time
        not_selected_reqs = communication_requests.copy()
        delay = current_time
        curr_req_list = [r for r in communication_requests if r.request_time <= current_time]

        while(len(not_selected_reqs) != 0):
            selected_req = self.arbiter.select_request(curr_req_list)
            curr_req_list.remove(selected_req)
            not_selected_reqs.remove(selected_req)
            self.timeline.append(selected_req, selected_req.duration ,delay)
            delay = 0

            current_time += selected_req.duration
            curr_req_list = [r for r in not_selected_reqs if r.request_time <= current_time]
            
            if(len(curr_req_list) <= 0 and len(not_selected_reqs) != 0):
                new_time = min(not_selected_reqs, key=lambda r : r.request_time).request_time
                delay = new_time - current_time
                current_time = new_time
                curr_req_list = [r for r in not_selected_reqs if r.request_time <= current_time]
    