# MOTHER 3 OSV to MSGS

import os, shutil
from mido import MidiFile, Message

GM_EXTENSION = [0x41, 0x10, 0x42, 0x12, 0x40, 0x00, 0x7F, 0x00, 0x41]

INSTANT_CUT = True

def TOGGLE_DRUMS(chan, on):
    xx = 0x11 + chan
    if chan == 9: xx = 0x10
    if chan  > 9: xx -= 1
    yy = 0x1A - chan
    msg = [0x41, 0x10, 0x42, 0x12, 0x40, xx, 0x15, (1 if on else 0), yy]

    return msg

source_dir = "./OSV/"
target_dir = "./OSVMSGS/"
directory = os.fsencode(target_dir)

if os.path.exists(target_dir):
    print("MSGS exists! removing...")
    shutil.rmtree(target_dir)

shutil.copytree(source_dir, target_dir)

directory = os.fsencode(target_dir)

inst_replace = {
    2: (3, 123), # wind
    61: 60, # french horns
    69: 60, # french horns
    66: 65, # replace sax
     3: 88, # synth min
     6: 88, # synth maj
     7: (8, 80), # sine
     9: 8, # celesta
    82: (1, 80), # square
    83: (1, 80), # square
    84: (1, 80), # square
    85: (1, 80), # square
    86: (1, 80), # square
    87: (1, 80), # square
    31: 30, # DIST.guitar
    126: 17, # Organ (needs work)
}
class Chord:
    def __init__(self, *offsets):
        self.offsets = offsets

inst_tweaks = {
    3: Chord(12, 15, 19),
    6: Chord(15, 19, 22),
    7: Chord(17),
    9: Chord(12),
    31: Chord(-15, -8),
}

# TODO: convert chord instruments to proper instrument, keep track of channel and append chord notes
#       bank switching! for special instruments
#       swap 10th channel to next free (16th), move gunshot notes to 10th channel
#       or enable drums mode on the fly?
#
#       it seems that's causing some panic (sudden stops, certain instruments are set to piano??),
#       so maybe let's try rerouting all note events on program 127 to channel 10
#
#       the results are amazing
#       let's do something about those guitar chords
#       one down, a few to go: 11, 22, 67, 69, 109??

inst_name = {
    0: "Acoustic Grand Piano",
    1: "Bright Acoustic Piano",
    2: "Electric Grand Piano",
    3: "Honky-tonk Piano",
    4: "Electric Piano 1",
    5: "Electric Piano 2",
    6: "Harpsichord",
    7: "Clavi",
    8: "Celesta",
    9: "Glockenspiel",
    10: "Music Box",
    11: "Vibraphone",
    12: "Marimba",
    13: "Xylophone",
    14: "Tubular Bells",
    15: "Dulcimer",
    16: "Drawbar Organ",
    17: "Percussive Organ",
    18: "Rock Organ",
    19: "Church Organ",
    20: "Reed Organ",
    21: "Accordion",
    22: "Harmonica",
    23: "Tango Accordion",
    24: "Acoustic Guitar (nylon)",
    25: "Acoustic Guitar (steel)",
    26: "Electric Guitar (jazz)",
    27: "Electric Guitar (clean)",
    28: "Electric Guitar (muted)",
    29: "Overdriven Guitar",
    30: "Distortion Guitar",
    31: "Guitar harmonics",
    32: "Acoustic Bass",
    33: "Electric Bass (finger)",
    34: "Electric Bass (pick)",
    35: "Fretless Bass",
    36: "Slap Bass 1",
    37: "Slap Bass 2",
    38: "Synth Bass 1",
    39: "Synth Bass 2",
    40: "Violin",
    41: "Viola",
    42: "Cello",
    43: "Contrabass",
    44: "Tremolo Strings",
    45: "Pizzicato Strings",
    46: "Orchestral Harp",
    47: "Timpani",
    48: "String Ensemble 1",
    49: "String Ensemble 2",
    50: "SynthStrings 1",
    51: "SynthStrings 2",
    52: "Choir Aahs",
    53: "Voice Oohs",
    54: "Synth Voice",
    55: "Orchestra Hit",
    56: "Trumpet",
    57: "Trombone",
    58: "Tuba",
    59: "Muted Trumpet",
    60: "French Horn",
    61: "Brass Section",
    62: "SynthBrass 1",
    63: "SynthBrass 2",
    64: "Soprano Sax",
    65: "Alto Sax",
    66: "Tenor Sax",
    67: "Baritone Sax",
    68: "Oboe",
    69: "English Horn",
    70: "Bassoon",
    71: "Clarinet",
    72: "Piccolo",
    73: "Flute",
    74: "Recorder",
    75: "Pan Flute",
    76: "Blown Bottle",
    77: "Shakuhachi",
    78: "Whistle",
    79: "Ocarina",
    80: "Lead 1 (square)",
    81: "Lead 2 (sawtooth)",
    82: "Lead 3 (calliope)",
    83: "Lead 4 (chiff)",
    84: "Lead 5 (charang)",
    85: "Lead 6 (voice)",
    86: "Lead 7 (fifths)",
    87: "Lead 8 (bass + lead)",
    88: "Pad 1 (new age)",
    89: "Pad 2 (warm)",
    90: "Pad 3 (polysynth)",
    91: "Pad 4 (choir)",
    92: "Pad 5 (bowed)",
    93: "Pad 6 (metallic)",
    94: "Pad 7 (halo)",
    95: "Pad 8 (sweep)",
    96: "FX 1 (rain)",
    97: "FX 2 (soundtrack)",
    98: "FX 3 (crystal)",
    99: "FX 4 (atmosphere)",
    100: "FX 5 (brightness)",
    101: "FX 6 (goblins)",
    102: "FX 7 (echoes)",
    103: "FX 8 (sci-fi)",
    104: "Sitar",
    105: "Banjo",
    106: "Shamisen",
    107: "Koto",
    108: "Kalimba",
    109: "Bag pipe",
    110: "Fiddle",
    111: "Shanai",
    112: "Tinkle Bell",
    113: "Agogo",
    114: "Steel Drums",
    115: "Woodblock",
    116: "Taiko Drum",
    117: "Melodic Tom",
    118: "Synth Drum",
    119: "Reverse Cymbal",
    120: "Guitar Fret Noise",
    121: "Breath Noise",
    122: "Seashore",
    123: "Bird Tweet",
    124: "Telephone Ring",
    125: "Helicopter",
    126: "Applause",
    127: "Gunshot"
}

converts = 0
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".mid"): 
        mid = MidiFile(target_dir + filename)

        for track in mid.tracks:
            extended = False
            
            og_chan_prog = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
            chan_prog    = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
            chan_msb     = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]

            tweaked = False
            skip_msg = 0

            for msg in track:
                if not extended:
                    track.insert(0, Message("sysex", data = GM_EXTENSION))
                    # track.insert(track.index(msg), Message("sysex", data = TOGGLE_DRUMS(9, True)))
                    extended = True
                    skip_msg += 1
                    continue
                
                if skip_msg > 0:
                    skip_msg -= 1
                    continue

                if msg.type == "sysex": track.remove(msg)
                if msg.type in ('note_on', 'note_off', 'polytouch', 'control_change', 'program_change', 'aftertouch', 'pitchwheel') and msg.channel == 9: msg.channel = 15

                if msg.type == 'program_change':
                    # if msg.program == 127 and chan_prog[msg.channel] != 127:
                    #     track.insert(track.index(msg), Message("sysex", data = TOGGLE_DRUMS(msg.channel, True)))
                    #     chan_prog[msg.channel] = 127
                    #     print("channel", msg.channel, "has drums!!")
                    #     skip_msg += 1
                    #     continue
                    # elif msg.program != 127 and chan_prog[msg.channel] == 127:
                    #     track.insert(track.index(msg), Message("sysex", data = TOGGLE_DRUMS(msg.channel, False)))
                    #     print("channel", msg.channel, "lost drums..")
                    #     skip_msg += 1

                    if msg.program == 127:
                        chan_prog[msg.channel] = 127
                        continue

                    og_chan_prog[msg.channel] = msg.program
                    replace = inst_replace.get(msg.program)
                    if replace is not None:
                        if type(replace) is tuple:
                            print("special instrument:", replace[0], replace[1])
                            track.insert(track.index(msg), Message("control_change", channel = msg.channel, control = 0, value = replace[0]))
                            chan_msb[msg.channel] = replace[0]
                            replace = replace[1]
                            skip_msg += 1
                        elif chan_msb[msg.channel] != 0:
                            track.insert(track.index(msg), Message("control_change", channel = msg.channel, control = 0, value = 0))
                            chan_msb[msg.channel] = 0
                        
                        print("%s %i %s -> %s %s converts"
                            % (filename[11:-4].ljust(52), msg.channel,
                                inst_name[msg.program].ljust(23),
                                inst_name[replace].ljust(23),
                                str(converts).rjust(3)))
                        
                        msg.program = replace
                        converts += 1
                    
                    chan_prog[msg.channel] = msg.program

                if msg.type in ('note_on', 'note_off'):
                    if chan_prog[msg.channel] == 127:
                        msg.channel = 9
                        continue
                    tweak = inst_tweaks.get(og_chan_prog[msg.channel])
                    if type(tweak) is Chord:
                        insert_index = track.index(msg)
                        if not tweaked:
                            print("Tweaked a", inst_name[chan_prog[msg.channel]], ".", insert_index)
                            tweaked = True

                        og_note = msg.note
                        for offset in tweak.offsets:
                            if tweak.offsets.index(offset) == 0:
                                msg.note = min(og_note + offset, 127)
                                if msg.type == "note_off":
                                    track.remove(msg)
                                    track.insert(insert_index, Message(type = "note_on", channel = msg.channel, note = min(og_note + offset, 127), velocity = 1, time = msg.time))
                            else:
                                track.insert(insert_index, Message(type = msg.type, channel = msg.channel, note = min(og_note + offset, 127), velocity = msg.velocity if msg.type == "note_on" else 1, time = 0))
                        skip_msg = len(tweak.offsets) - 1
                        

        mid.save(target_dir + filename)
        continue
    else:
        continue



# Acoustic Grand Piano
# Bright Acoustic Piano
# Electric Grand Piano
# Honky-tonk Piano
# Electric Piano 1
# Electric Piano 2
# Harpsichord
# Clavi
# Celesta
# Glockenspiel
# Music Box
# Vibraphone
# Marimba
# Xylophone
# Tubular Bells
# Dulcimer
# Drawbar Organ
# Percussive Organ
# Rock Organ
# Church Organ
# Reed Organ
# Accordion
# Harmonica
# Tango Accordion
# Acoustic Guitar (nylon)
# Acoustic Guitar (steel)
# Electric Guitar (jazz)
# Electric Guitar (clean)
# Electric Guitar (muted)
# Overdriven Guitar
# Distortion Guitar
# Guitar harmonics
# Acoustic Bass
# Electric Bass (finger)
# Electric Bass (pick)
# Fretless Bass
# Slap Bass 1
# Slap Bass 2
# Synth Bass 1
# Synth Bass 2
# Violin
# Viola
# Cello
# Contrabass
# Tremolo Strings
# Pizzicato Strings
# Orchestral Harp
# Timpani
# String Ensemble 1
# String Ensemble 2
# SynthStrings 1
# SynthStrings 2
# Choir Aahs
# Voice Oohs
# Synth Voice
# Orchestra Hit
# Trumpet
# Trombone
# Tuba
# Muted Trumpet
# French Horn
# Brass Section
# SynthBrass 1
# SynthBrass 2
# Soprano Sax
# Alto Sax
# Tenor Sax
# Baritone Sax
# Oboe
# English Horn
# Bassoon
# Clarinet
# Piccolo
# Flute
# Recorder
# Pan Flute
# Blown Bottle
# Shakuhachi
# Whistle
# Ocarina
# Lead 1 (square)
# Lead 2 (sawtooth)
# Lead 3 (calliope)
# Lead 4 (chiff)
# Lead 5 (charang)
# Lead 6 (voice)
# Lead 7 (fifths)
# Lead 8 (bass + lead)
# Pad 1 (new age)
# Pad 2 (warm)
# Pad 3 (polysynth)
# Pad 4 (choir)
# Pad 5 (bowed)
# Pad 6 (metallic)
# Pad 7 (halo)
# Pad 8 (sweep)
# FX 1 (rain)
# FX 2 (soundtrack)
# FX 3 (crystal)
# FX 4 (atmosphere)
# FX 5 (brightness)
# FX 6 (goblins)
# FX 7 (echoes)
# FX 8 (sci-fi)
# Sitar
# Banjo
# Shamisen
# Koto
# Kalimba
# Bag pipe
# Fiddle
# Shanai
# Tinkle Bell
# Agogo
# Steel Drums
# Woodblock
# Taiko Drum
# Melodic Tom
# Synth Drum
# Reverse Cymbal
# Guitar Fret Noise
# Breath Noise
# Seashore
# Bird Tweet
# Telephone Ring
# Helicopter
# Applause
# Gunshot