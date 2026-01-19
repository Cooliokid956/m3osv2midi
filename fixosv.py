# MOTHER 3 OSV to MIDI

import os, sys
if "--help" in sys.argv:
    nameLen = len(sys.argv[0])
    print(
f"""
Usage: {sys.argv[0]} [--in=PATH] [--out=PATH] [--loop[s=#]] [--drums=#]
       {' '*nameLen} [--mode=gm|gm2|gs|msgs|sc88] [--safe-name]
       {' '*nameLen} [--defer-drums] [--instant-cut] [--extra-patch]
       {' '*nameLen} [--skip-replace] [--skip-tweaks]
""" )
    sys.exit(0)

from collections.abc import Iterable
from mido import MidiFile, MidiTrack, Message, MetaMessage, merge_tracks # planned for use with guitar strum emulation
from mido.messages.checks import check_channel

# miscellaneous helpers
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

os.system('cls' if os.name == "nt" else 'clear')
print("MOTHER 3 OSV to MIDI\n")

source_dir = "OSV/"
target_dir = "OSVMIDI/"

# settings
SAFE_NAME    = "--safe-name"    in sys.argv
DEFER_DRUMS  = "--defer-drums"  in sys.argv
INSTANT_CUT  = "--instant-cut"  in sys.argv
EXTRA_PATCH  = "--extra-patch"  in sys.argv
SKIP_REPLACE = "--skip-replace" in sys.argv
SKIP_TWEAKS  = "--skip-tweaks"  in sys.argv

DEF_BANK = 0 # 16 for Power
LOOPS = 0
MODE = ""
for arg in sys.argv:
    if arg[:5] == "--in=":
        source_dir = os.path.normpath(arg[5:]) + "/"
    if arg[:6] == "--out=":
        target_dir = os.path.normpath(arg[6:]) + "/"
    elif arg[:6] == "--loop":
        LOOPS = 1
        if arg[6:8] == "s=": LOOPS = int(arg[8:])
    elif arg[:8] == "--drums=":
        DEF_BANK = int(arg[8])
    elif arg[:7] == "--mode=":
        MODE = arg[7:].lower()

if not os.path.exists(target_dir):
    os.mkdir(target_dir)

def SYSEX(data):
    if type(data) is str:
        data_list = []
        data = data.replace(" ", "").strip("0x")
        while len(data) > 0:
            try:
                data_list.append(int(data[:2], 16))
                data = data[2:]
            except ValueError: data = data[1:]

        data = data_list
    # print(data)
    return Message("sysex", data = data)
GM_SYSTEM_ON  = SYSEX("7E 7F 09 01")
GM2_SYSTEM_ON = SYSEX("7E 7F 09 03")
GS_RESET      = SYSEX("41 1042 12 40007F 0041")

def PC(chan, prog, **args):
    return Message("program_change", channel=chan, program=prog, **args)
def CC(chan, cont, val, **args):
    return Message("control_change", channel=chan, control=cont, value=val, **args)

CHANNEL_EVENTS = ('note_on', 'note_off', 'polytouch', 'control_change', 'program_change', 'aftertouch', 'pitchwheel')
ALTERED_EVENTS = ('note_on', 'note_off', 'control_change', 'program_change')

GM,GM2,GS,SC88=0,0,0,0
match MODE:
    case "gm"  : GM = 1; DEFER_DRUMS = 1
    case "gm2" : GM2 = 1
    case "sc88": GS = 1; SC88 = 1
    case "msgs": GS = 1; DEFER_DRUMS = 1
    case "gs"|_: GS = 1
CC_BANK = 32 if GM2 else 0

with open(target_dir + "ARGS.TXT", 'w') as f:
    f.write(" ".join(sys.argv[1:]))

def TOGGLE_DRUMS(chan, on):
    if GS:
        check_channel(chan)
        xx = 0x11 + chan
        if chan == 9: xx = 0x10
        if chan  > 9: xx -= 1
        yy = 0x1A - chan
        data = [0x41, 0x10,0x42, 0x12, 0x40,xx, 0x15, (1 if on else 0), yy]
                # 65,   16,  66,   18,   64,xx,   21, (off: 0, on:  1), yy

        return [SYSEX(data)]
    elif GM2:
        return [CC(chan, 0, (0x78 if on else 0x79)), CC(chan, 32, 0)]
    return [SYSEX([0])]

HEADER_GS = [GS_RESET] + TOGGLE_DRUMS(9, False)
headers = {
    "gm"  : [GM_SYSTEM_ON],
    "gm2" : [GM2_SYSTEM_ON] + TOGGLE_DRUMS(9, False),
    "sc88": [GS_RESET, PC(9, DEF_BANK)] + TOGGLE_DRUMS(9, False)
}
HEADER = headers.get(MODE, HEADER_GS)

def DRUMS(msg, on):
    return MetaMessage("marker", text="drums"+("O" if on else "X")+str(msg.channel)) \
        if DEFER_DRUMS else TOGGLE_DRUMS(msg.channel, on)

PIANO = ( 16,  0) # (  0,  0)
inst_replace = {
    (  0,  0) : ( PIANO ), # detuned (?)
    (  0, 11) : ( PIANO ),
    (  0, 22) : ( PIANO ),
    (  0,  1) : (  3,122), # wind
    (  0, 61) : (  0, 60), # french horns
    (  0, 66) : (  0, 65), # replace sax
    (  0,  3) : (  0, 88), # synth min
    (  0,  6) : (  0, 88), # synth maj
    (  0,  7) : (  8, 80), # sine
    (  0,  9) : (  0,  8), # celesta
    (  0, 82) : (  1, 80), # square
    (  0, 83) : (  1, 80), # square
    (  0, 84) : (  1, 80), # square
    (  0, 85) : (  1, 80), # square
    (  0, 86) : (  1, 80), # square
    (  0, 87) : (  1, 80), # square
    (  0, 31) : (  0, 30), # DIST.guitar
    (  0, 44) : (  0, 47), # timpani
    (  0, 67) : (  8, 27), # Guitar chord
    (  0, 69) : (  8, 27), # Guitar chord
    (  0,120) : (  0, 30), # Dist.Guitar
    (  0,126) : (  0, 18), # Rotary Organ
    (  0, 75) : (  8, 18), # Rotary Organ
    (  0,127) : (128,  0), # Percussion
    (  4, 31) : (  0, 63), # Synth Brass 2
    (  4, 34) : (  0, 11), # Xylophone
}
def get_inst(inst):
    replace = inst_replace.get(inst)
    if replace is None: return inst, False
    else: return replace, True

# tweaks
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
    (  0,  3): [Velocity(0.5), Chord(12, 15, 19)],
    (  0,  6): [Velocity(0.5), Chord(15, 19, 22)],
    (  0,  7): [Transpose(17)],
    (  0,  9): [Transpose(12)],
    (  0, 11): [Velocity(0.7), Chord(0-12, 4-12, 7-12)], # Major
    (  0, 22): [Velocity(0.7), Chord(-3, 0, 4-12)], # Minor
    (  0, 31): [Chord(-15, -8)],
   #(  0, 34): [Transpose(24)],
    (  0, 41): [Transpose(12)],
    (  0, 60): [Velocity(0.50)], #, Chord(12)],
    (  0, 61): [Velocity(0.85)], #, Chord(12)],
    (  0, 67): [Chord(0, 3,-5)], # Guitar chord
    (  0, 69): [Chord(0, 4, 7)], # Guitar chord
    (  0, 75): [Transpose(12)],
    (  4, 34): [Transpose(24)],
    (  0, 94): [Transpose(5)],
    (  0, 97): [Transpose(5)],
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

drums_remap = {
    24: (56, 58), # SFX; Applause
    33: (48, 59), # Orchestra;
    35: ( 0, 43), # reverse cymbal
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

if SC88 or EXTRA_PATCH:
    inst_replace.update({
        (  0,  3) : (  2, 88), # New Age
        (  0,  6) : (  2, 88), # New Age
        (  0, 62) : (  2, 63), # Warm Brass
        (  0, 73) : (  1, 73), # Flute 2
        (  0,126) : ( 24, 18), # Rotary Organ
        (  4, 34) : (  9, 11), # Xylophone
    })
    drums_remap.update({
        20: ( 0, 17), # One!
        21: ( 0, 18), # Two!
        22: ( 0, 19), # Three!
        23: (25,126), # Tah!
        24: (56, 91), # Small Club
        25: (56, 38), # pick scrape
    })


"""
  TODO: convert chord instruments to proper instrument, keep track of channel and append chord notes
        bank switching! for special instruments
        swap 10th channel to next free (16th), move gunshot notes to 10th channel
        or enable drums mode on the fly?

        it seems that's causing some panic (sudden stops, certain instruments are set to piano??),
        so maybe let's try rerouting all note events on program 127 to channel 10

        the results are amazing
        let's do something about those guitar chords
        one down, a few to go: 11, 22, 67, 69, 109??

        "Welcome!" needs a lot of instruments fixed

        haven't been writing this down but I've been reworking the event skip system and
        have decided on dropping it altogether in favor of altered track reconstruction

        there's slowdowns near chords now?
        No longer! :D

        let's keep working on those chords ..zZz
        11, |> 22, 67, 69, 109

        I should probably add GM Level 2 instrument names as well

        Add more chords and introduce auxiliary channels (keep track of unused channels, begin airing before school open backstor ) 

        10/22/2023, 6:12:15 PM
        Those auxiliary channels exist in a certain way (dynamic drum channel allocation) but I'll still need to find a solution for things like the guitar chords
"""

inst_name = {
    (  0,  0): "Piano 1",
    (  8,  0): "Piano 1",
    ( 16,  0): "Piano 1d",
    (  0,  1): "Piano 2",
    (  8,  1): "Piano 2",
    (  0,  2): "Piano 3",
    (  8,  2): "Piano 3",
    (  0,  3): "Honky-tonk",
    (  8,  3): "Honky-tonk",
    (  0,  4): "E.Piano 1",
    (  8,  4): "Detuned EP 1",
    ( 16,  4): "E.Piano 1v",
    ( 24,  4): "60's E.Piano",
    (  0,  5): "E.Piano 2",
    (  8,  5): "Detuned EP 2",
    ( 16,  5): "E.Piano 2v",
    (  0,  6): "Harpsichord",
    (  8,  6): "Coupled Hps.",
    ( 16,  6): "Harpsichord",
    ( 24,  6): "Harpsi.o",
    (  0,  7): "Clav.",
    (  0,  8): "Celesta",
    (  0,  9): "Glockenspiel",
    (  0, 10): "Music Box",
    (  0, 11): "Vibraphone",
    (  8, 11): "Vibraphone",
    (  0, 12): "Marimba",
    (  8, 12): "Marimba",
    (  0, 13): "Xylophone",
    (  0, 14): "Tubular-bell",
    (  8, 14): "Church Bell",
    (  9, 14): "Carillon",
    (  0, 15): "Santur",
    (  0, 16): "Organ 1",
    (  8, 16): "Detuned Or.1",
    ( 16, 16): "60's Organ 1",
    ( 32, 16): "Organ 4",
    (  0, 17): "Organ 2",
    (  8, 17): "Detuned Or.2",
    ( 32, 17): "Organ 5",
    (  0, 18): "Organ 3",
    (  0, 19): "Church Org.1",
    (  8, 19): "Church Org.2",
    ( 16, 19): "Church Org.3",
    (  0, 20): "Reed Organ",
    (  0, 21): "Accordion Fr",
    (  8, 21): "Accordion It",
    (  0, 22): "Harmonica",
    (  0, 23): "Bandoneon",
    (  0, 24): "Nylon-str.Gt",
    (  8, 24): "Ukulele",
    ( 16, 24): "Nylon Gt.o",
    ( 32, 24): "Nylon Gt.2",
    (  0, 25): "Steel-str.Gt",
    (  8, 25): "12-str.Gt",
    ( 16, 25): "Mandolin",
    (  0, 26): "Jazz Gt.",
    (  8, 26): "Hawaiian Gt.",
    (  0, 27): "Clean Gt.",
    (  8, 27): "Chorus Gt.",
    (  0, 28): "Muted Gt.",
    (  8, 28): "Funk Gt.",
    ( 16, 28): "Funk Gt.2",
    (  0, 29): "Overdrive Gt",
    (  0, 30): "DistortionGt",
    (  8, 30): "Feedback Gt.",
    (  0, 31): "Gt.Harmonics",
    (  8, 31): "Gt. Feedback",
    (  0, 32): "Acoustic Bs.",
    (  0, 33): "Fingered Bs.",
    (  0, 34): "Picked Bs.",
    (  0, 35): "Fretless Bs.",
    (  0, 36): "Slap Bass 1",
    (  0, 37): "Slap Bass 2",
    (  0, 38): "Synth Bass 1",
    (  1, 38): "SynthBass101",
    (  8, 38): "Synth Bass 3",
    (  0, 39): "Synth Bass 2",
    (  8, 39): "Synth Bass 4",
    ( 16, 39): "Rubber Bass",
    (  0, 40): "Violin",
    (  8, 40): "Slow Violin",
    (  0, 41): "Viola",
    (  0, 42): "Cello",
    (  0, 43): "Contrabass",
    (  0, 44): "Tremolo Str",
    (  0, 45): "PizzicatoStr",
    (  0, 46): "Harp",
    (  0, 47): "Timpani",
    (  0, 48): "Strings",
    (  8, 48): "Orchestra",
    (  0, 49): "Slow Strings",
    (  0, 50): "Syn.Strings1",
    (  8, 50): "Syn.Strings3",
    (  0, 51): "Syn.Strings2",
    (  0, 52): "Choir Aahs",
    ( 32, 52): "Choir Aahs 2",
    (  0, 53): "Voice Oohs",
    (  0, 54): "SynVox",
    (  0, 55): "OrchestraHit",
    (  0, 56): "Trumpet",
    (  0, 57): "Trombone",
    (  1, 57): "Trombone 2",
    (  0, 58): "Tuba",
    (  0, 59): "MutedTrumpet",
    (  0, 60): "French Horns",
    (  1, 60): "Fr.Horn 2",
    (  0, 61): "Brass 1",
    (  8, 61): "Brass 2",
    (  0, 62): "Synth Brass1",
    (  8, 62): "Synth Brass3",
    ( 16, 62): "AnalogBrass1",
    (  0, 63): "Synth Brass2",
    (  8, 63): "Synth Brass4",
    ( 16, 63): "AnalogBrass2",
    (  0, 64): "Soprano Sax",
    (  0, 65): "Alto Sax",
    (  0, 66): "Tenor Sax",
    (  0, 67): "Baritone Sax",
    (  0, 68): "Oboe",
    (  0, 69): "English Horn",
    (  0, 70): "Bassoon",
    (  0, 71): "Clarinet",
    (  0, 72): "Piccolo",
    (  0, 73): "Flute",
    (  0, 74): "Recorder",
    (  0, 75): "Pan Flute",
    (  0, 76): "Bottle Blow",
    (  0, 77): "Shakuhachi",
    (  0, 78): "Whistle",
    (  0, 79): "Ocarina",
    (  0, 80): "Square Wave",
    (  1, 80): "Square",
    (  8, 80): "Sine Wave",
    (  0, 81): "Saw Wave",
    (  1, 81): "Saw",
    (  8, 81): "Doctor Solo",
    (  0, 82): "Syn.Calliope",
    (  0, 83): "Chiffer Lead",
    (  0, 84): "Charang",
    (  0, 85): "Solo Vox",
    (  0, 86): "5th Saw Wave",
    (  0, 87): "Bass & Lead",
    (  0, 88): "Fantasia",
    (  0, 89): "Warm Pad",
    (  0, 90): "Polysynth",
    (  0, 91): "Space Voice",
    (  0, 92): "Bowed Glass",
    (  0, 93): "Metal Pad",
    (  0, 94): "Halo Pad",
    (  0, 95): "Sweep Pad",
    (  0, 96): "Ice Rain",
    (  0, 97): "Soundtrack",
    (  0, 98): "Crystal",
    (  1, 98): "Syn Mallet",
    (  0, 99): "Atmosphere",
    (  0,100): "Brightness",
    (  0,101): "Goblin",
    (  0,102): "Echo Drops",
    (  1,102): "Echo Bell",
    (  2,102): "Echo Pan",
    (  0,103): "Star Theme",
    (  0,104): "Sitar",
    (  1,104): "Sitar 2",
    (  0,105): "Banjo",
    (  0,106): "Shamisen",
    (  0,107): "Koto",
    (  8,107): "Taisho Koto",
    (  0,108): "Kalimba",
    (  0,109): "Bagpipe",
    (  0,110): "Fiddle",
    (  0,111): "Shanai",
    (  0,112): "Tinkle Bell",
    (  0,113): "Agogo",
    (  0,114): "Steel Drums",
    (  0,115): "Woodblock",
    (  8,115): "Castanets",
    (  0,116): "Taiko",
    (  8,116): "Concert BD",
    (  0,117): "Melo. Tom 1",
    (  8,117): "Melo. Tom 2",
    (  0,118): "Synth Drum",
    (  8,118): "808 Tom",
    (  9,118): "Elec Perc.",
    (  0,119): "Reverse Cym.",
    (  0,120): "Gt.FretNoise",
    (  1,120): "Gt.Cut Noise",
    (  2,120): "String Slap",
    (  0,121): "Breath Noise",
    (  1,121): "Fl.Key Click",
    (  0,122): "Seashore",
    (  1,122): "Rain",
    (  2,122): "Thunder",
    (  3,122): "Wind",
    (  4,122): "Stream",
    (  5,122): "Bubble",
    (  0,123): "Bird",
    (  1,123): "Dog",
    (  2,123): "Horse-Gallop",
    (  3,123): "Bird 2",
    (  0,124): "Telephone 1",
    (  1,124): "Telephone 2",
    (  2,124): "DoorCreaking",
    (  3,124): "Door",
    (  4,124): "Scratch",
    (  5,124): "Wind Chimes",
    (  0,125): "Helicopter",
    (  1,125): "Car-Engine",
    (  2,125): "Car-Stop",
    (  3,125): "Car-Pass",
    (  4,125): "Car-Crash",
    (  5,125): "Siren",
    (  6,125): "Train",
    (  7,125): "Jetplane",
    (  8,125): "Starship",
    (  9,125): "Burst Noise",
    (  0,126): "Applause",
    (  1,126): "Laughing",
    (  2,126): "Screaming",
    (  3,126): "Punch",
    (  4,126): "Heart Beat",
    (  5,126): "Footsteps",
    (  0,127): "Gun Shot",
    (  1,127): "Machine Gun",
    (  2,127): "Lasergun",
    (  3,127): "Explosion",

    # SC-88
    (  2, 88): "New Age",
    (  1, 73): "Flute 2",
    (  2, 63): "Warm Brass",
    (  8, 27): "Chorus Gt.",
    (  9, 11): "Vibraphones",
    ( 24, 18): "RotaryOrg.F"
}
def get_inst_name(prog):
    return inst_name.get(prog, f"Unknown ({prog[0]:03.0f}:{prog[1]:03.0f})")

def main():
    converts = 0
    ntweaks  = 0
    perc_counts = {}
    total_og_len = 0
    total_len = 0

    bomb = Bomb(999)

    for file in os.listdir(os.fsencode(source_dir)):
        filename = os.fsdecode(file)
        if filename.endswith(".mid"):
            mid = MidiFile(source_dir + filename)
            og_track = merge_tracks(mid.tracks, True) if len(mid.tracks) > 1 else mid.tracks[0]
            og_track.name = (filename[11:-4] or filename[:-4]).replace("┐", "?")

            header = HEADER.copy()
            track = MidiTrack()
            altered = False
            bank_switch = False

            orig_prog = array((0, 0), 16)
            chan_prog = array((0, 0), 16)
            drum_bank = DEF_BANK
            rev_cym = False
            aux = Auxiliary()
            prog_record = array([], 16)
            rest_time = 0

            tweaked = False

            pre_loop_track = None

            perc_count = 0
            peak_chan = 0

            # pass 1
            for msg in og_track:
                msg_queue = []
                def suppress(msg):
                    nonlocal rest_time
                    rest_time += msg.time
                def queue(msg, ignore_rest=False):
                    if isinstance(msg, Iterable):
                        if len(msg) > 0:
                            for m in msg: queue(m)
                            return msg_queue[-1]
                        else: return
                    if not ignore_rest:
                        nonlocal rest_time; msg.time += rest_time; rest_time = 0
                    msg_queue.append(msg)
                    return msg
                def flush():
                    if len(msg_queue) > 0:
                        track.extend(msg_queue)
                        msg_queue.clear()
                    else: suppress(msg)
                def queue_and_flush(msg):
                    queue(msg); flush()
                def pop_time(msg):
                    time = msg.time
                    msg.time = 0
                    return time

                # Altered; begin file entry
                if not altered and msg.type in ALTERED_EVENTS:
                    altered = True; print(filename[11:-4] or filename[:-4])

                if GM and msg.type in CHANNEL_EVENTS and msg.channel > 8: msg.channel += 1

                # looping
                if msg.type == 'marker':
                    queue_and_flush(msg)
                    if LOOPS > 0:
                        match msg.text:
                            case "loopStart":
                                pre_loop_track = track
                                track = MidiTrack()
                                # pre_loop_perc_bank = perc_bank
                                # queue_and_flush(PC(9, perc_bank)) # find a better way to do this
                            case "loopEnd":
                                pre_loop_track.extend(track * (LOOPS + 1))
                                track = pre_loop_track
                    continue

                if msg.type == 'sysex': suppress(msg); continue

                if msg.is_cc(0):
                    if not bank_switch and msg.value != 0: bank_switch = True; print("Contains special instruments")
                    orig_prog[msg.channel] = (msg.value, orig_prog[msg.channel][1])
                    queue_and_flush(msg) if SKIP_REPLACE else suppress(msg)
                    continue

                if msg.type == 'program_change':
                    orig_prog[msg.channel] = (orig_prog[msg.channel][0], msg.program)

                    if SKIP_REPLACE: queue_and_flush(msg); continue
                    # dump song's instruments
                    if "Welcome!" in filename:
                        print("%i %s"
                             % (msg.channel,
                                get_inst_name(orig_prog[msg.channel])))
                    # END dumping

                    new_prog, replaced = get_inst(orig_prog[msg.channel])
                    if chan_prog[msg.channel] != new_prog:
                        # static perc count test
                        prog_record[msg.channel].append(new_prog)
                        if orig_prog[msg.channel] == (0, 127):
                            new_perc_count = 0
                            for prog in orig_prog:
                                if prog == (0, 127):
                                    new_perc_count += 1
                            if new_perc_count > perc_count:
                                perc_count = new_perc_count

                            chan_prog[msg.channel] = new_prog
                            queue(DRUMS(msg, True), True)
                            queue_and_flush(msg.copy(program=drum_bank if SC88 else DEF_BANK))
                            continue
                        elif chan_prog[msg.channel][0] == 128:
                            queue(DRUMS(msg, False), True)

                        if chan_prog[msg.channel][0] != new_prog[0]:
                            queue(CC(msg.channel, CC_BANK, new_prog[0], time = pop_time(msg)))
                        chan_prog[msg.channel] = new_prog
                        msg.program = new_prog[1]
                        if replaced:
                            converts += 1
                            print("%s %s -> %s"
                                 % (str(msg.channel).rjust(2),
                                    get_inst_name(orig_prog[msg.channel]).ljust(23),
                                    get_inst_name(new_prog).ljust(23)))

                        queue_and_flush(msg)
                    else: suppress(msg)
                    continue

                is_drums = msg.type in CHANNEL_EVENTS and chan_prog[msg.channel][0] == 128

                if msg.type in ('note_on', 'note_off'):
                    if is_drums:
                        channel = 9 if GM else msg.channel
                        remap = drums_remap.get(msg.note)
                        bank = DEF_BANK
                        if remap is not None:
                            if isinstance(remap, Auxiliary):
                                queue_and_flush(aux.fire(remap, msg))
                                continue
                            else:
                                bank = remap[0]
                                msg.note = remap[1]
                        if bank != drum_bank if SC88 else chan_prog[channel][1]:
                            queue(PC(msg.channel, bank, time = pop_time(msg)))
                            chan_prog[channel] = (128, bank)
                            drum_bank = bank
                        queue_and_flush(msg)
                        continue

                    tweaks = inst_tweaks.get(orig_prog[msg.channel])
                    queue(msg)
                    if tweaks and not SKIP_TWEAKS:
                        ntweaks += 1
                        if not tweaked:
                            tweaked = True; print(get_inst_name(orig_prog[msg.channel]), "tweaked")

                        for tweak in tweaks:
                            msg_queue = tweak.process(msg_queue)

                    if INSTANT_CUT: InstantCut.process(msg_queue)

                    flush()
                    continue

                queue_and_flush(msg) # flush default message

                if msg.type in CHANNEL_EVENTS and msg.channel > peak_chan:
                    peak_chan = msg.channel

            # pass 2: deferred percussion
            if DEFER_DRUMS:
                peak_chan += 1
                static_perc = 0
                dyn_perc = []
                for i, prog_list in enumerate(prog_record):
                    if len(prog_list) > 0:
                        if (128, 0) in prog_list:
                            if len(prog_list) == 1:
                                static_perc += 1
                                header += TOGGLE_DRUMS(i, True)
                                print("Channel %i: static percussion allocated" % i)
                            else:
                                dyn_perc.append(i)
                
                perc_count -= static_perc
                print(perc_count)
                for i in range(perc_count):
                    header += TOGGLE_DRUMS(peak_chan+i, True)
                    print("Channel %i: dynamic percussion allocated" % (peak_chan+i))

                if perc_counts.get(perc_count) is None: perc_counts[perc_count] = [] # debug
                perc_counts[perc_count].append(filename) # debug

                if static_perc + len(dyn_perc) > 0:
                    dyn_perc_chan = {}
                    if GM and peak_chan == 9: peak_chan = 10

                    i = 0
                    while i < len(track):
                        msg = track[i]

                        if msg.type == "marker" and msg.text[:5] == "drums":
                            on = msg.text[5] == 'O'
                            channel = int(msg.text[6:])
                            if channel in dyn_perc or GM:
                                if on:
                                    for j in range(peak_chan, 16):
                                        if GM: dyn_perc_chan[channel] = 9; break
                                        if j not in dyn_perc_chan.values():
                                            dyn_perc_chan[channel] = j
                                            print("drums on channel %i allocated to %i" % (channel, j))
                                            break
                                else:
                                    print("drums off channel %i deallocated %i" % (channel, dyn_perc_chan.get(channel) or -1))
                                    dyn_perc_chan[channel] = None
                            else: print("drums", ("on" if on else "off"), "channel %i" % channel)
                            del track[i]; msg = track[i]

                        if msg.type in CHANNEL_EVENTS:
                            msg.channel = dyn_perc_chan.get(msg.channel) or msg.channel
                        i += 1

            header.extend(track)
            mid.tracks = [header]

            # if "Welcome" in filename:
            #     for msg in header: #.MSGDUMP
            #         print(msg, end=",  \n") #.MSGDUMP
            #     raise NameError

            bomb.tick()

            print("Message reduction:", f"{(len(track) / len(og_track)):.2%}", "(%i/%i)" % (len(track), len(og_track)))
            total_og_len += len(og_track)
            total_len += len(track)
                
            if SAFE_NAME:
                filename = filename.replace("┐", "").strip("!")
            mid.save(target_dir + filename)

    print()
    print("Program Overrides:", converts)
    print("Tweaks:", ntweaks)
    print("Message reduction:", f"{(total_len / total_og_len):.2%}", "(%i/%i)" % (total_len, total_og_len))
    # print("Peak dynamic percussion channel counts:", perc_counts)

    print("Conversion success!")

if __name__ == "__main__": main()
