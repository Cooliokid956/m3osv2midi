def clamp(x, a, b): return max(a,min(x, b))
def array(init, len): return [init for _ in range(len)]

class T:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

class Explosion(Exception): ...
class Bomb:
    def __init__(self, ticks):
        self.ticks = ticks
    def tick(self):
        self.ticks -= 1
        if not self.ticks: raise Explosion

from mido import Message

def PC(chan, prog, **args):
    return Message("program_change", channel=chan, program=prog, **args)
def CC(chan, cont, val, **args):
    return Message("control_change", channel=chan, control=cont, value=val, **args)
