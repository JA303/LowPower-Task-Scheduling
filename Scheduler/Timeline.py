class Timeline:

    class TimePeriod:
        def __init__(self, start_time : float, end_time : float) -> None:
            self.start_time = start_time
            self.end_time = end_time
    
    def __init__(self) -> None:
        
        self.timeline = {}
        self.timeline_length = 0
        self.item_count = 0

    def append(self, task, duration : float, delay : float = 0) -> None:
        start_time = self.timeline_length + delay
        end_time = self.timeline_length + delay + duration
        self.timeline[task] = self.TimePeriod(start_time, end_time)
        self.timeline_length = end_time
        self.item_count += 1

    def count(self) -> int:
        return self.item_count

    def time(self) -> float:
        return self.timeline_length
    
    def get_end_time(self, t) -> float:
        return self.timeline[t].end_time
    
    def get_start_time(self, t) -> float:
        return self.timeline[t].start_time
    
    def get_duration_time(self, t) -> float:
        time_p = self.timeline[t]
        return time_p.end_time - time_p.start_time
    
    
    def __str__(self) -> str:
        str = "(TimeLine="
        timeline = sorted(self.timeline.items(), key=lambda item: item[1].start_time)
        for t in timeline:
            str += f" {t[0].name}: {t[1].start_time}-{t[1].end_time}, "
        return str + ')'
