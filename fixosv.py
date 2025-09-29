# MOTHER 3 OSV to MSGS

import os, shutil
from mido import MidiFile, Message, open_output, get_output_names

os.system('cls')
print("MOTHER 3 OSV to MSGS\n")

GM_EXTENSION = [0x41, 0x10, 0x42, 0x12, 0x40, 0x00, 0x7F, 0x00, 0x41]

CHANNEL_EVENTS = ('note_on', 'note_off', 'polytouch', 'control_change', 'program_change', 'aftertouch', 'pitchwheel')
ALTERED_EVENTS = ('note_on', 'note_off', 'control_change', 'program_change')

# flags
INSTANT_CUT = False

# def TOGGLE_DRUMS(chan, on):
#     xx = 0x11 + chan
#     if chan == 9: xx = 0x10
#     if chan  > 9: xx -= 1
#     yy = 0x1A - chan
#     msg = [0x41, 0x10, 0x42, 0x12, 0x40, xx, 0x15, (1 if on else 0), yy]

#     return msg

source_dir = "./OSV/"
target_dir = "./OSVMSGS/"
directory = os.fsencode(target_dir)

if os.path.exists(target_dir):
    print("MSGS exists! removing...")
    shutil.rmtree(target_dir)

shutil.copytree(source_dir, target_dir)

inst_replace = {
    0: (16, 0), # detuned (?)
    11: 0,
    1: (3, 122), # wind
    61: 60, # french horns
    # 69: 60, # french horns WHAT?? don't know what this is doing here, this is supposed to be a guitar chord
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
    126: 18, # Organ (needs work) 18 or 17
}
class Chord:
    def __init__(self, *offsets):
        self.offsets = offsets
class Velocity:
    def __init__(self, mult):
        self.mult = mult

inst_tweaks = {
     3: [Chord(12, 15, 19)],
     6: [Chord(15, 19, 22)],
     7: [Chord(17)],
     9: [Chord(12)],
    11: [Chord(0, 4, 7)], # Major
    31: [Chord(-15, -8)],
  # 34: [Chord(24)],
    41: [Chord(12)],
  #126: [Chord(0, -12)],
    60: [Velocity(0.50)], #, Chord(12)],
    61: [Velocity(0.85)], #, Chord(12)],
}

drums_remap = {
    35: 43 # cymbal
}
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
"""
inst_name = (
    "Acoustic Grand Piano",
    "Bright Acoustic Piano",
    "Electric Grand Piano",
    "Honky-tonk Piano",
    "Electric Piano 1",
    "Electric Piano 2",
    "Harpsichord",
    "Clavi",
    "Celesta",
    "Glockenspiel",
    "Music Box",
    "Vibraphone",
    "Marimba",
    "Xylophone",
    "Tubular Bells",
    "Dulcimer",
    "Drawbar Organ",
    "Percussive Organ",
    "Rock Organ",
    "Church Organ",
    "Reed Organ",
    "Accordion",
    "Harmonica",
    "Tango Accordion",
    "Acoustic Guitar (nylon)",
    "Acoustic Guitar (steel)",
    "Electric Guitar (jazz)",
    "Electric Guitar (clean)",
    "Electric Guitar (muted)",
    "Overdriven Guitar",
    "Distortion Guitar",
    "Guitar harmonics",
    "Acoustic Bass",
    "Electric Bass (finger)",
    "Electric Bass (pick)",
    "Fretless Bass",
    "Slap Bass 1",
    "Slap Bass 2",
    "Synth Bass 1",
    "Synth Bass 2",
    "Violin",
    "Viola",
    "Cello",
    "Contrabass",
    "Tremolo Strings",
    "Pizzicato Strings",
    "Orchestral Harp",
    "Timpani",
    "String Ensemble 1",
    "String Ensemble 2",
    "SynthStrings 1",
    "SynthStrings 2",
    "Choir Aahs",
    "Voice Oohs",
    "Synth Voice",
    "Orchestra Hit",
    "Trumpet",
    "Trombone",
    "Tuba",
    "Muted Trumpet",
    "French Horn",
    "Brass Section",
    "SynthBrass 1",
    "SynthBrass 2",
    "Soprano Sax",
    "Alto Sax",
    "Tenor Sax",
    "Baritone Sax",
    "Oboe",
    "English Horn",
    "Bassoon",
    "Clarinet",
    "Piccolo",
    "Flute",
    "Recorder",
    "Pan Flute",
    "Blown Bottle",
    "Shakuhachi",
    "Whistle",
    "Ocarina",
    "Lead 1 (square)",
    "Lead 2 (sawtooth)",
    "Lead 3 (calliope)",
    "Lead 4 (chiff)",
    "Lead 5 (charang)",
    "Lead 6 (voice)",
    "Lead 7 (fifths)",
    "Lead 8 (bass + lead)",
    "Pad 1 (new age)",
    "Pad 2 (warm)",
    "Pad 3 (polysynth)",
    "Pad 4 (choir)",
    "Pad 5 (bowed)",
    "Pad 6 (metallic)",
    "Pad 7 (halo)",
    "Pad 8 (sweep)",
    "FX 1 (rain)",
    "FX 2 (soundtrack)",
    "FX 3 (crystal)",
    "FX 4 (atmosphere)",
    "FX 5 (brightness)",
    "FX 6 (goblins)",
    "FX 7 (echoes)",
    "FX 8 (sci-fi)",
    "Sitar",
    "Banjo",
    "Shamisen",
    "Koto",
    "Kalimba",
    "Bag pipe",
    "Fiddle",
    "Shanai",
    "Tinkle Bell",
    "Agogo",
    "Steel Drums",
    "Woodblock",
    "Taiko Drum",
    "Melodic Tom",
    "Synth Drum",
    "Reverse Cymbal",
    "Guitar Fret Noise",
    "Breath Noise",
    "Seashore",
    "Bird Tweet",
    "Telephone Ring",
    "Helicopter",
    "Applause",
    "Gunshot"
)

converts = 0
special  = 0
ntweaks  = 0

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".mid"): 
        mid = MidiFile(target_dir + filename)

        for track in mid.tracks:
            altered = False
            extended = False
            bank_switch = False
            
            og_chan_prog = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
            chan_prog    = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]
            chan_bank    = [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ]

            tweaked = False
            skip_msg = 0

            for msg in track:
                if not extended:
                    track.insert(0, Message("sysex", data = GM_EXTENSION))
                    extended = True
                    skip_msg += 1
                    continue
                
                if skip_msg > 0:
                    skip_msg -= 1
                    continue

                # Altered; begin file entry
                if not altered and msg.type in ALTERED_EVENTS:
                    altered = True; print(filename[11:-4].ljust(52))

                if msg.type == 'sysex': track.remove(msg)
                if msg.type in CHANNEL_EVENTS and msg.channel == 9: msg.channel = 15

                if not bank_switch and msg.type == 'control_change' and msg.control == 0:
                    bank_switch = True; print("WARNING: bank switch")

                if msg.type == 'program_change':
                    # dump song's instruments
                    if "Welcome!" in filename:
                        print("%i %s"
                             % (msg.channel,
                                inst_name[msg.program]))
                    # END dumping

                    if msg.program == 127: chan_prog[msg.channel] = 127; continue

                    og_chan_prog[msg.channel] = msg.program
                    replace = inst_replace.get(msg.program)
                    if replace is not None:
                        if type(replace) is tuple:
                            # print("special instrument:", replace[0], replace[1])
                            special += 1
                            track.insert(track.index(msg), Message("control_change", channel = msg.channel, control = 0, value = replace[0]))
                            chan_bank[msg.channel] = replace[0]
                            replace = replace[1]
                            skip_msg += 1
                        elif chan_bank[msg.channel] != 0:
                            track.insert(track.index(msg), Message("control_change", channel = msg.channel, control = 0, value = 0))
                            chan_bank[msg.channel] = 0
                        
                        print("%s %s -> %s"
                             % (str(msg.channel).rjust(2),
                                inst_name[msg.program].ljust(23),
                                inst_name[replace].ljust(23)))
                        
                        msg.program = replace
                        converts += 1
                    
                    chan_prog[msg.channel] = msg.program

                if msg.type in ('note_on', 'note_off'):
                    if chan_prog[msg.channel] == 127:
                        msg.channel = 9
                        if msg.note == 35:
                            msg.channel = 14
                            track.insert(track.index(msg)-1, Message(type = "program_change", channel = 14, program = 119, time = 0))
                            msg.note = 60
                            skip_msg += 1
                            continue
                            
                        remap = drums_remap.get(msg.note)
                        if remap is not None:
                            msg.note = remap
                        continue

                    tweaks = inst_tweaks.get(og_chan_prog[msg.channel])
                    if tweaks is not None:
                        ntweaks += 1

                        for tweak in tweaks:
                            if type(tweak) is Chord:
                                insert_index = track.index(msg)
                                if not tweaked:
                                    print("Tweaked a", inst_name[chan_prog[msg.channel]], ".", insert_index)
                                    tweaked = True

                                og_note = msg.note
                                for offset in tweak.offsets:
                                    if tweak.offsets.index(offset) == 0:
                                        msg.note = min(og_note + offset, 127)
                                        if msg.type == "note_off" and INSTANT_CUT:
                                            track.remove(msg)
                                            track.insert(insert_index,
                                                        Message(type = "note_on", channel = msg.channel, note = min(og_note + offset, 127), 
                                                                velocity = 1, time = msg.time))
                                    else:
                                        track.insert(insert_index,
                                                    Message(type = "note_on" if INSTANT_CUT else msg.type, channel = msg.channel, note = min(og_note + offset, 127),
                                                            velocity = 1 if (msg.type == "note_off" and INSTANT_CUT) else msg.velocity, time = 0))
                                skip_msg = len(tweak.offsets) - 1
                            elif type(tweak) is Velocity:
                                msg.velocity = int(msg.velocity * tweak.mult)
                    continue
                
                if msg.type == "note_off" and INSTANT_CUT:
                    insert_index = track.index(msg)
                    track.remove(msg)
                    track.insert(insert_index,
                                 Message(type = "note_on", channel = msg.channel, note = msg.note, 
                                         velocity = 1, time = msg.time))
                        

        mid.save(target_dir + filename)
        continue
    else:
        continue

print()
print("Program Overrides:", converts)
print("Special Overrides:", special)
print("Tweaks:", ntweaks)

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