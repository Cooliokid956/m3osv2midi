msg_types = (
    "inst",
    "note",
    "bend",
)

class Msg:
    type = "none"

class Note(Msg):
    type = "note"

    def __init__(self, chan, inst, note):
        chan = chan
        inst = inst
        note = note

class Note(Msg):
    type = "note"

class Track:
    data = []

class State:
    pass