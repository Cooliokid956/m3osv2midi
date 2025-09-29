# MOTHER 3 OSV to MIDI

import os, shutil
from mido import MidiFile, MidiTrack, Message

os.system('cls')
print("MOTHER 3 OSV to MIDI\n")

GM_EXTENSION = [0x41, 0x10,0x42, 0x12, 0x40,0x00,0x7F, 0x00,0x41]

CHANNEL_EVENTS = ('note_on', 'note_off', 'polytouch', 'control_change', 'program_change', 'aftertouch', 'pitchwheel')
ALTERED_EVENTS = ('note_on', 'note_off', 'control_change', 'program_change')

# settings
LOOPS = 1

SKIP_REPLACE = False
SKIP_TWEAKS  = False
GM_EXTEND    = True
INSTANT_CUT  = False

# def TOGGLE_DRUMS(chan, on):
#     xx = 0x11 + chan
#     if chan == 9: xx = 0x10
#     if chan  > 9: xx -= 1
#     yy = 0x1A - chan
#     msg = [0x41, 0x10,0x42, 0x12, 0x40,xx, 0x15, (1 if on else 0), yy]

#     return msg

source_dir = "./OSV/"
target_dir = "./OSVMIDI/"
directory = os.fsencode(target_dir)

if os.path.exists(target_dir):
    print("Removing old converts...")
    shutil.rmtree(target_dir)

shutil.copytree(source_dir, target_dir)

inst_replace = {
      0: (16, 0), # detuned (?)
     11: (16, 0),
      1: (3, 122), # wind
     61: 60,# french horns
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
     44: 47, # timpani
     67: 27, # Guitar chord
     69: 27, # Guitar chord
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
    11: [Chord(0-12, 4-12, 7-12)], # Major
    31: [Chord(-15, -8)],
  # 34: [Chord(24)],
    41: [Chord(12)],
  #126: [Chord(0,-12)],
    60: [Velocity(0.50)], #, Chord(12)],
    61: [Velocity(0.85)], #, Chord(12)],
    67: [Chord(0, 3, -5)], # Guitar chord
    69: [Chord(0, 4, 7)], # Guitar chord
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

        haven't been writing this down but I've been reworking the event skip system and
        have decided on dropping it altogether in favor of altered track reconstruction

        there's slowdowns near chords now?
        No longer! :D

        let's keep working on those chords ..zZz
        11, |> 22, 67, 69, 109

        I should probably add GM Level 2 instrument names as well
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

        for og_track in mid.tracks:
            track = MidiTrack()
            altered = False
            extended = not GM_EXTEND
            bank_switch = False
            
            orig_prog = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            chan_prog = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
            chan_bank = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

            tweaked = False

            loop_start = None

            for msg in og_track:
                msg_queue = []
                def queue(msg):
                    msg_queue.append(msg)
                    return msg
                def flush():
                    track.extend(msg_queue)
                    msg_queue.clear()
                def queue_and_flush(msg):
                    queue(msg); flush()

                if not extended:
                    extended = True; queue_and_flush(Message("sysex", data = GM_EXTENSION))

                # Altered; begin file entry
                if not altered and msg.type in ALTERED_EVENTS:
                    altered = True; print(filename[11:-4].ljust(52))

                # looping
                if LOOPS > 0:
                    if msg.type == 'marker' and msg.text == "loopStart":
                        queue_and_flush(msg)
                        loop_start = track.copy()
                        track = MidiTrack()
                        continue
                    if msg.type == 'marker' and msg.text == "loopEnd":
                        queue_and_flush(msg)
                        loop_start.extend(track * (LOOPS + 1))
                        track = loop_start.copy()
                        continue

                if msg.type == 'sysex': continue
                if msg.type in CHANNEL_EVENTS and msg.channel == 9: msg.channel = 15

                if not bank_switch and msg.is_cc(0):
                    bank_switch = True; print("WARNING: bank switch")

                if msg.type == 'program_change':
                    if SKIP_REPLACE: continue
                    # dump song's instruments
                    if "Welcome!" in filename:
                        print("%i %s"
                             % (msg.channel,
                                inst_name[msg.program]))
                    # END dumping

                    if msg.program == 127: chan_prog[msg.channel] = 127; queue_and_flush(msg); continue

                    orig_prog[msg.channel] = msg.program
                    replace = inst_replace.get(msg.program)
                    if replace is not None:
                        if type(replace) is tuple:
                            special += 1
                            queue(Message("control_change", channel = msg.channel, control = 0,value = replace[0]))
                            chan_bank[msg.channel] = replace[0]
                            replace = replace[1]
                        elif chan_bank[msg.channel] != 0:
                            queue(Message("control_change", channel = msg.channel, control = 0,value = 0))
                            chan_bank[msg.channel] = 0
                        
                        print("%s %s -> %s"
                             % (str(msg.channel).rjust(2),
                                inst_name[msg.program].ljust(23),
                                inst_name[replace].ljust(23)))
                        
                        msg.program = replace
                        converts += 1
                    
                    chan_prog[msg.channel] = msg.program

                    queue_and_flush(msg)
                    continue

                if msg.type in ('note_on', 'note_off'):
                    if chan_prog[msg.channel] == 127:
                        msg.channel = 9
                        if msg.note == 35:
                            queue(Message(type = "program_change", channel = 14, program = 119, time = 0))
                            queue_and_flush(msg.copy(channel=14, note=60))
                            continue
                            
                        remap = drums_remap.get(msg.note)
                        if remap is not None: msg.note = remap
                        queue_and_flush(msg)
                        continue

                    tweaks = inst_tweaks.get(orig_prog[msg.channel])
                    cut = False
                    def_queue = True
                    if tweaks is not None and not SKIP_TWEAKS:
                        ntweaks += 1

                        for tweak in tweaks:
                            if type(tweak) is Chord:
                                if not tweaked:
                                    tweaked = True; print(inst_name[chan_prog[msg.channel]], "tweaked")

                                for offset in tweak.offsets:
                                    if type(offset) is tuple:
                                        note = max(0,min(msg.note + offset[0], 127))
                                        velocity = int(msg.velocity * offset[1])
                                    else:
                                        note = max(0,min(msg.note + offset, 127))
                                        velocity = msg.velocity

                                    if msg.type == "note_off" and INSTANT_CUT:
                                        mtype = "note_on"
                                        velocity = 1
                                        cut = True
                                    else: mtype = msg.type

                                    queue(Message(type = mtype, channel = msg.channel, note = note, velocity = velocity, time = msg.time if tweak.offsets.index(offset) == 0 else 0))
                                    if msg.type == "note_off" and INSTANT_CUT: queue(Message(type = "note_off", channel = msg.channel, note = note, velocity = 0,time = 0))
                                def_queue = False

                            elif type(tweak) is Velocity:
                                msg.velocity = int(msg.velocity * tweak.mult)
                
                    if not cut and msg.type == "note_off" and INSTANT_CUT:
                        queue(Message(type = "note_on", channel = msg.channel, note = msg.note, velocity = 1, time = msg.time))
                        queue_and_flush(Message(type = "note_off", channel = msg.channel, note = msg.note, velocity = 0,time = 0))
                        continue

                    if def_queue: queue(msg)
                    flush()
                    continue
                
                queue_and_flush(msg) # flush default message
            
            mid.tracks[mid.tracks.index(og_track)] = track

        mid.save(target_dir + filename)
        continue
    else:
        continue

print()
print("Program Overrides:", converts)
print("Special Overrides:", special)
print("Tweaks:", ntweaks)

input("Conversion success! Press ENTER to continue...")
"""
Acoustic Grand Piano
Bright Acoustic Piano
Electric Grand Piano
Honky-tonk Piano
Electric Piano 1
Electric Piano 2
Harpsichord
Clavi
Celesta
Glockenspiel
Music Box
Vibraphone
Marimba
Xylophone
Tubular Bells
Dulcimer
Drawbar Organ
Percussive Organ
Rock Organ
Church Organ
Reed Organ
Accordion
Harmonica
Tango Accordion
Acoustic Guitar (nylon)
Acoustic Guitar (steel)
Electric Guitar (jazz)
Electric Guitar (clean)
Electric Guitar (muted)
Overdriven Guitar
Distortion Guitar
Guitar harmonics
Acoustic Bass
Electric Bass (finger)
Electric Bass (pick)
Fretless Bass
Slap Bass 1
Slap Bass 2
Synth Bass 1
Synth Bass 2
Violin
Viola
Cello
Contrabass
Tremolo Strings
Pizzicato Strings
Orchestral Harp
Timpani
String Ensemble 1
String Ensemble 2
SynthStrings 1
SynthStrings 2
Choir Aahs
Voice Oohs
Synth Voice
Orchestra Hit
Trumpet
Trombone
Tuba
Muted Trumpet
French Horn
Brass Section
SynthBrass 1
SynthBrass 2
Soprano Sax
Alto Sax
Tenor Sax
Baritone Sax
Oboe
English Horn
Bassoon
Clarinet
Piccolo
Flute
Recorder
Pan Flute
Blown Bottle
Shakuhachi
Whistle
Ocarina
Lead 1 (square)
Lead 2 (sawtooth)
Lead 3 (calliope)
Lead 4 (chiff)
Lead 5 (charang)
Lead 6 (voice)
Lead 7 (fifths)
Lead 8 (bass + lead)
Pad 1 (new age)
Pad 2 (warm)
Pad 3 (polysynth)
Pad 4 (choir)
Pad 5 (bowed)
Pad 6 (metallic)
Pad 7 (halo)
Pad 8 (sweep)
FX 1 (rain)
FX 2 (soundtrack)
FX 3 (crystal)
FX 4 (atmosphere)
FX 5 (brightness)
FX 6 (goblins)
FX 7 (echoes)
FX 8 (sci-fi)
Sitar
Banjo
Shamisen
Koto
Kalimba
Bag pipe
Fiddle
Shanai
Tinkle Bell
Agogo
Steel Drums
Woodblock
Taiko Drum
Melodic Tom
Synth Drum
Reverse Cymbal
Guitar Fret Noise
Breath Noise
Seashore
Bird Tweet
Telephone Ring
Helicopter
Applause
Gunshot
"""