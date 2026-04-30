from mido import MidiTrack, Message
from utils import *

PIANO = ( 0,  0) # (  0,  0)
inst_replace = {
    (  0,  0) : ( PIANO ), # detuned (?)
    (  0, 11) : ( PIANO ),
    (  0, 22) : ( PIANO ),
    (  0,  1) : (  3,122), # wind
    (  0,  2) : (  0, 42), # "cello"
    (  0, 61) : (  0, 60), # french horns
    (  0, 66) : (  0, 65), # replace sax
    (  0,  3) : (  0, 88), # synth min
    (  0,  6) : (  0, 88), # synth maj
    (  0, 17) : (  5,122), # Percussion
    (  0,  7) : (  8, 80), # sine
    (  0,  9) : (  0,  8), # celesta
    (  0, 82) : (  1, 80), # square
    (  0, 83) : (  1, 80), # square
    (  0, 84) : (  1, 80), # square
    (  0, 85) : (  1, 80), # square
    (  0, 86) : (  1, 80), # square
    (  0, 87) : (  1, 80), # square
    (  0, 94) : (  8, 80), # "custom" sine-ish wave? very aliased though
    (  0, 31) : (  0, 30), # DIST.guitar
    (  0, 44) : (  0, 47), # timpani
    (  0, 67) : (  8, 27), # Guitar chord
    (  0, 69) : (  8, 27), # Guitar chord
    (  0,120) : (  0, 30), # Dist.Guitar
    (  0,126) : (  0, 18), # Rotary Organ
    (  0, 75) : (  8, 18), # Rotary Organ
    (  0,127) : (128,  0), # Percussion

    # JV-1080
    (  0,  5) : (  0,103), # Fantasia JV  (A-072) (stand-in)
    (  0, 10) : (  0,103), # Wave Bells   (A-084) (stand-in)
    (  0, 34) : (  0, 34), # Pick Bass    (B-009) (stand-in)
    (  0, 54) : (  0,103), # Raverborg    (B-059) (stand-in)
    (  0, 78) : (  0,103), # Fantasy Vox  (A-079) (stand-in)
    (  0, 79) : (  0,103), # Cyber Space  (C-122) (stand-in)
    (  0, 80) : (  0,103), # JP8Haunting  (C-072) (stand-in)
    (  0, 97) : (  0,103), # Heirborne    (C-073) (stand-in)
    (  0, 98) : (  0,103), # TeknoSoloVox (B-067) (stand-in)
    (  0, 99) : (  0,103), # Spaced Voxx  (C-026) (stand-in)
    (  0,103) : (  0, 91), # Night Shade  (C-117) (stand-in)
    (  0,109) : (  0,103), # Cyber Space  (C-122) (stand-in)
    (  0,110) : (  0,103), # Raggatronic  (B-051) (stand-in)
    (  0,111) : (  0,103), # Dunes        (C-120) (stand-in)
    (  0,112) : (  0,103), # Terminate    (C-128) (stand-in)

    (  4, 31) : (  0, 63), # Synth Brass 2
    (  4, 34) : (  0, 11), # Xylophone
}

class Transpose:
    def __init__(self, offset):
        self.offset = offset
    def process(self, queue):
        for msg in queue:
            if msg.type in ("note_on", "note_off"):
                msg.note += self.offset
        return queue

class Velocity:
    def __init__(self, mult):
        self.mult = mult
    def process(self, queue):
        for msg in queue:
            if msg.type in ("note_on", "note_off"):
                msg.velocity = int(msg.velocity * self.mult)
        return queue

class Chord:
    def __init__(self, *offsets):
        self.offsets = []
        for offset in offsets:
            if type(offset) is not tuple:
                offset = (offset, 1)
            self.offsets.append(offset)
    def process(self, queue):
        q = []
        for msg in queue:
            if msg.type in ("note_on", "note_off"):
                time = msg.time
                for offset in self.offsets:
                    note = clamp(msg.note + offset[0], 0, 127)
                    velocity = int(msg.velocity * offset[1])

                    q.append(msg.copy(note = note, velocity = velocity, time = time))
                    time = 0
            else: q.append(msg)
        return q

class InstantCut:
    def process(queue):
        q = []
        for msg in queue:
            if msg.type == "note_off":
                q.append(Message(type = "note_on", channel = msg.channel, note = msg.note, velocity = 1, time = msg.time))
                q.append(msg.copy(time = 0))
            else: q.append(msg)
        return queue

inst_tweaks = {
    (  0,  2): [Transpose(-12)], # "cello"
    (  0,  3): [Velocity(0.5), Chord(12, 15, 19)],
    (  0,  6): [Velocity(0.5), Chord(15, 19, 22)],
    (  0,  7): [Transpose(17)],
    (  0,  9): [Transpose(12)],
    (  0, 11): [Chord(-24, -12, (-5, .91), 0, (4, .94))], # Major
    (  0, 22): [Chord(-21, -15, (-3, .91), 0, (4, .82))], # Minor
    (  0, 31): [Chord(-15, -8)],
   #(  0, 34): [Transpose(24)],
    (  0, 41): [Transpose(12)],
    (  0, 60): [Velocity(0.50)], #, Chord(12)],
    (  0, 61): [Velocity(0.85)], #, Chord(12)],
    (  0, 67): [Velocity(0.5), Chord(0, 3,-5)], # Guitar chord
    (  0, 69): [Velocity(0.5), Chord(0, 4, 7)], # Guitar chord
    (  0, 75): [Transpose(12)],
    (  4, 34): [Transpose(24)],
    (  0, 97): [Transpose(5)],
    (  0,103): [Chord(0, 3, 6, 12)],
}

# auxiliary
class Auxiliary:
    track = MidiTrack()
    channel = 16
    def __init__(self): pass

    def part(self, part):
        return getattr(self, part.name, None)

    def fire(self, part, msg):
        return (part.init(self, msg) or []) + part.fire(self, msg)
            

class RevCymbal(Auxiliary):
    name = "revCymbal"
    def __init__(self): pass
    def init(self, aux, msg):
        if not aux.part(self):
            aux.channel -= 1
            aux.revCymbal = T(chan=aux.channel)
            return [PC(aux.channel, 119)]
    def fire(self, aux, msg):
        return [msg.copy(channel=aux.revCymbal.chan, note=60)]


class Strum:
    def __init__(self, *notes):
        self.notes = notes

STRUM_ABMAJ_DN = Strum(44, 48, 51, 56, 63)
STRUM_ABMAJ_UP = Strum(48, 51, 56, 63, 68)
STRUM_FMAJ_DN  = Strum(41, 45, 48, 53, 60)
STRUM_FMAJ_UP  = Strum(45, 48, 53, 60, 65)
STRUM_CMIN_DN  = Strum(36, 39, 43, 48, 55)
STRUM_CMIN_UP  = Strum(39, 43, 48, 55, 60)
STRUM_BB7TH_DN = Strum(46, 50, 53, 56, 65)
STRUM_BB7TH_UP = Strum(50, 53, 56, 65, 70)
STRUM_GBMIN_DN = Strum(42, 45, 49, 54, 61)
STRUM_GBMIN_UP = Strum(45, 49, 54, 61, 66)
STRUM_GAUG     = Strum(43, 47, 51, 55, 63)
STRUM_DBDIM    = Strum(49, 52, 55, 61, 67)

class Guitar(Auxiliary):
    name = "guitar"
    def __init__(self, strum):
        self.notes = strum.notes
    def init(self, aux, msg):
        if not aux.part(self):
            aux.guitar = array(T(
                on = None
            ), 16)
        
        if not aux.guitar[msg.channel].on:
            aux.guitar[msg.channel].on = array(0, 128)
            return [DRUMS(msg, False), PC(msg.channel, 25)]
        
    def fire(self, aux, msg):
        chan = aux.guitar[msg.channel].on
        q = []
        time = msg.time
        on = msg.type == "note_on"
        for note in self.notes:
            if on and chan[note]:
                q.append(Message("note_off", channel=msg.channel, note=note, time=time))
                time = 0
            if on or chan[note] == 1:
                q.append(msg.copy(note = note, time = time))
                time = 0
            aux.guitar[msg.channel].on[note] += 1 if on else -1
        return q
    
class Tom(Auxiliary):
    name = "tom"
    def __init__(self, note):
        self.note = note
    def init(self, aux, msg):
        if not aux.part(self):
            aux.tom = array(T(
                on = None
            ), 16)
        
        if not aux.tom[msg.channel].on:
            aux.tom[msg.channel].on = array(0, 128)
            return [DRUMS(msg, False), PC(msg.channel, 117)]
        
    def fire(self, aux, msg):
        return [msg.copy(note = self.note)]

OK, NG = -1, -2
drums_remap = {
    4: (0, 85), # SFX; Applause
    24: (56, 58), # SFX; Applause
    33: (48, 59), # Orchestra;
    34: NG, # "Bendy Hat", might be ethnic
    35: ( 0, 43), # reverse cymbal
    88: ( 0, 35), # kick
    122: (56, 78), # chirping
    123: (56, 55), # heartbeat

    # may reconsider
    117: ( 0, 42), # hi-hat closed
    118: ( 0, 46), # hi-hat open
    120: ( 0, 40), # snare

    14: Tom(45), # Note offset of -6 from sf to gm
    15: Tom(48), # inst root = 66
    16: Tom(52), # offset + split key - root
    17: Tom(56), # 
    18: Tom(60), # 
    19: Tom(63), # 

    56: RevCymbal(),
    60: Guitar(STRUM_ABMAJ_DN),
    61: Guitar(STRUM_ABMAJ_UP),
    71: Guitar(STRUM_FMAJ_DN),
    72: Guitar(STRUM_FMAJ_UP),
    76: Guitar(STRUM_CMIN_DN),
    77: Guitar(STRUM_CMIN_UP),
    78: Guitar(STRUM_BB7TH_DN),
    79: Guitar(STRUM_BB7TH_UP),
    124: Guitar(STRUM_GBMIN_DN),
    125: Guitar(STRUM_GBMIN_UP),
    126: Guitar(STRUM_GAUG),
    127: Guitar(STRUM_DBDIM)
}
