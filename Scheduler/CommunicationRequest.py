
class CommunicationRequest:
    def __init__(self, source : str, destination : str, duration : float, request_time : float, priority : int = 0) -> None:
        self.name = f"{source}->{destination}"
        self.source = source
        self.destination = destination
        self.duration = duration
        self.request_time = request_time
        self.priority = priority

    def __str__(self) -> str:
        return f"(CommunicationRequest: time {self.request_time} from {self.source} to {self.destination}, d={self.duration}, p={self.priority})"
    
    def __hash__(self) -> int:
        return hash(self.name)
    
    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, CommunicationRequest):
            return self.name == __value.name
        return False
