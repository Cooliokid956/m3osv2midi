# MOTHER 3 OSV to MIDI

import os, shutil

from mido import MidiFile, MidiTrack, Message, MetaMessage #, merge_tracks # planned for use with guitar strum emulation
from mido.messages.checks import check_channel

def clamp(x, a, b): return max(a,min(x, b))
os.system('cls' if os.name == "nt" else 'clear')
print("MOTHER 3 OSV to MIDI\n")

GS_RESET = Message("sysex", data = [0x41, 0x10,0x42, 0x12, 0x40,0x00,0x7F, 0x00,0x41])
                                    # 65,   16,  66,   18,   64,   0, 127,    0,  65

CHANNEL_EVENTS = ('note_on', 'note_off', 'polytouch', 'control_change', 'program_change', 'aftertouch', 'pitchwheel')
ALTERED_EVENTS = ('note_on', 'note_off', 'control_change', 'program_change')

# settings
LOOPS        = 1
DEFER_DRUMS  = False
INSTANT_CUT  = False
SKIP_REPLACE = False
SKIP_TWEAKS  = False

def TOGGLE_DRUMS(chan, on):
    check_channel(chan)
    xx = 0x11 + chan
    if chan == 9: xx = 0x10
    if chan  > 9: xx -= 1
    yy = 0x1A - chan
    msg = [0x41, 0x10,0x42, 0x12, 0x40,xx, 0x15, (1 if on else 0), yy]
           # 65,   16,  66,   18,   64,xx,   21, (1 if on else 0), yy]

    return Message("sysex", data = msg)

def DRUMS(msg, on):
    if not DEFER_DRUMS: return TOGGLE_DRUMS(msg.channel, on)
    return MetaMessage("marker", text="drums"+("|" if on else "O")+str(msg.channel))

source_dir = "./OSV/"
target_dir = "./OSVMIDI/"

if not os.path.exists(target_dir):
    os.mkdir(target_dir)

inst_replace = {
    (  0,  0) : ( 16,  0), # detuned (?)
    (  0, 11) : ( 16,  0),
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
    (  0,126) : (  0, 18), # Rotary Organ, bank 24 if SC-88
    (  0, 44) : (  0, 47), # timpani
    (  0, 67) : (  0, 27), # Guitar chord
    (  0, 69) : (  0, 27), # Guitar chord
    (  0,127) : (128,  0), # Percussion
}
def get_inst(inst):
    replace = inst_replace.get(inst)
    if replace is None: return inst, False
    else: return replace, True

class Chord:
    def __init__(self, *offsets):
        self.offsets = []
        for offset in offsets:
            if type(offset) is not tuple:
                offset = (offset, 1)
            self.offsets.append(offset)
class Velocity:
    def __init__(self, mult):
        self.mult = mult
inst_tweaks = {
    (  0,  3): [Chord(12, 15, 19)],
    (  0,  6): [Chord(15, 19, 22)],
    (  0,  7): [Chord(17)],
    (  0,  9): [Chord(12)],
    (  0, 11): [Chord(0-12, 4-12, 7-12)], # Major
    (  0, 31): [Chord(-15, -8)],
   #(  0, 34): [Chord(24)],
    (  0, 41): [Chord(12)],
    (  0, 60): [Velocity(0.50)], #, Chord(12)],
    (  0, 61): [Velocity(0.85)], #, Chord(12)],
    (  0, 67): [Chord(0, 3,-5)], # Guitar chord
    (  0, 69): [Chord(0, 4, 7)], # Guitar chord
}

drums_remap = {
    24: (56, 58), # SFX; Applause
    33: (48, 59), # Orchestra;
    35: ( 0, 43), # reverse cymbal

    # SC-88
    25: (56, 38), # pick scrape
}
DEF_BANK = 0 # 16 for Power

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
    ( 24, 18): "RotaryOrg.F"
}

def main():
    converts = 0
    ntweaks  = 0
    perc_counts = {}
    total_og_len = 0
    total_len = 0

    bomb = 999

    for file in os.listdir(os.fsencode(source_dir)):
        filename = os.fsdecode(file)
        if filename.endswith(".mid"):
            mid = MidiFile(source_dir + filename)

            for og_track in mid.tracks:
                header = [GS_RESET, TOGGLE_DRUMS(9, False)]
                track = MidiTrack()
                altered = False
                bank_switch = False

                orig_prog = []
                chan_prog = []
                prog_record = []
                for i in range(16):
                    orig_prog.append((0, 0))
                    chan_prog.append((0, 0))
                    prog_record.append([])
                rest_time = 0

                tweaked = False

                pre_loop_track = None
                pre_loop_perc_bank = None

                perc_count = 0
                peak_chan = 0

                # pass 1
                for msg in og_track:
                    msg_queue = []
                    def suppress(msg):
                        nonlocal rest_time
                        rest_time += msg.time
                    def queue(msg):
                        nonlocal rest_time; msg.time += rest_time
                        msg_queue.append(msg)
                        rest_time = 0
                        return msg
                    def flush():
                        track.extend(msg_queue)
                        msg_queue.clear()
                    def queue_and_flush(msg):
                        queue(msg); flush()
                    def pop_time(msg):
                        time = msg.time
                        msg.time = 0
                        return time

                    # Altered; begin file entry
                    if not altered and msg.type in ALTERED_EVENTS:
                        altered = True; print(filename[11:-4].ljust(52))

                    # looping
                    if msg.type == 'marker':
                        queue_and_flush(msg)
                        if LOOPS > 0:
                            match msg.text:
                                case "loopStart":
                                    pre_loop_track = track
                                    track = MidiTrack()
                                    # pre_loop_perc_bank = perc_bank
                                    # queue_and_flush(Message("program_change", channel = 9, program = perc_bank)) # find a better way to do this
                                case "loopEnd":
                                    pre_loop_track.extend(track * (LOOPS + 1))
                                    track = pre_loop_track
                        continue

                    if msg.type == 'sysex': suppress(msg); continue#print("sysex:", msg.data); continue

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
                                    inst_name[(orig_prog[msg.channel][0], msg.program)]))
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
                                queue(DRUMS(msg, True))
                                queue_and_flush(msg.copy(program=DEF_BANK)); continue
                            elif chan_prog[msg.channel][0] == 128:
                                queue(DRUMS(msg, False))

                            if chan_prog[msg.channel][0] != new_prog[0]:
                                queue(Message("control_change", channel = msg.channel, control = 0, value = new_prog[0], time = pop_time(msg)))
                            chan_prog[msg.channel] = new_prog
                            msg.program = new_prog[1]
                            if replaced:
                                converts += 1
                                print("%s %s -> %s"
                                     % (str(msg.channel).rjust(2),
                                        inst_name[orig_prog[msg.channel]].ljust(23),
                                        inst_name[new_prog].ljust(23)))

                            queue_and_flush(msg)
                        else: suppress(msg)
                        continue

                    is_drums = msg.type in CHANNEL_EVENTS and chan_prog[msg.channel][0] == 128

                    if msg.type in ('note_on', 'note_off'):
                        if is_drums:
                            if msg.note in (35, 56): # 56 is proper, 35 is different
                                queue(Message(type = "program_change", channel = 14, program = 119, time = pop_time(msg)))
                                queue_and_flush(msg.copy(channel=14, note=60))
                                continue

                            remap = drums_remap.get(msg.note)
                            bank = DEF_BANK
                            if remap is not None:
                                bank = remap[0]
                                msg.note = remap[1]
                            if bank != chan_prog[msg.channel][1]:
                                queue(Message(type = "program_change", channel = msg.channel, program = bank, time = pop_time(msg)))
                                chan_prog[msg.channel] = (128, bank)
                            queue_and_flush(msg)
                            continue

                        tweaks = inst_tweaks.get(orig_prog[msg.channel])
                        cut = False
                        def_queue = True
                        if tweaks is not None and not SKIP_TWEAKS:
                            ntweaks += 1

                            for tweak in tweaks:
                                if not tweaked:
                                    tweaked = True; print(inst_name[orig_prog[msg.channel]], "tweaked")
                                if type(tweak) is Chord:

                                    for offset in tweak.offsets:
                                        note = clamp(msg.note + offset[0], 0, 127)
                                        velocity = int(msg.velocity * offset[1])

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

                    if msg.type in CHANNEL_EVENTS and msg.channel > peak_chan:
                        peak_chan = msg.channel

                # pass 2: deferred percussion
                if DEFER_DRUMS:
                    dyn_perc = []
                    for i, prog_list in enumerate(prog_record):
                        if len(prog_list) > 0:
                            if (128, 0) in prog_list:
                                if len(prog_list) == 1:
                                    perc_count -= 1
                                    header.append(TOGGLE_DRUMS(i, True))
                                    print("Channel %i: static percussion allocated" % i)
                                else:
                                    dyn_perc.append(i)
                    for i in range(perc_count):
                        header.append(TOGGLE_DRUMS(peak_chan+i+1, True))
                        print("Channel %i: dynamic percussion allocated" % (peak_chan+i+1))

                    if perc_counts.get(perc_count) is None: perc_counts[perc_count] = [] # debug
                    perc_counts[perc_count].append(filename) # debug

                    if perc_count + len(dyn_perc) > 0:
                        dyn_perc_chan = {}
                        for i in dyn_perc:
                            orig_prog[i] = (0, 0)
                        for msg in track:
                            if msg.type == "marker" and msg.text[:5] == "drums":
                                on = msg.text[5] == '|'
                                channel = int(msg.text[6:])
                                print("drums", ("on" if on else "off"), "channel %i" % channel)
                                if channel in dyn_perc:
                                    if on:
                                        for i in range(10, 16):
                                            if i not in dyn_perc_chan:
                                                dyn_perc_chan[channel] = i
                                    else: dyn_perc_chan[channel] = None
                                track.remove(msg)

                            if msg.type in CHANNEL_EVENTS and dyn_perc_chan.get(msg.channel):
                                msg.channel = dyn_perc_chan[msg.channel]

                header.extend(track)
                mid.tracks[mid.tracks.index(og_track)] = header

                # for msg in header:
                #     print(msg, end=",  ")

                bomb -= 1
                if not bomb: raise NameError

                print("Message reduction:", f"{(len(track) / len(og_track)):.2%}", "(%i/%i)" % (len(track), len(og_track)))
                total_og_len += len(og_track)
                total_len += len(track)

            mid.save(target_dir + filename)

    print()
    print("Program Overrides:", converts)
    print("Tweaks:", ntweaks)
    print("Message reduction:", f"{(total_len / total_og_len):.2%}", "(%i/%i)" % (total_len, total_og_len))
    # print("Peak dynamic percussion channel counts:", perc_counts)

    print("Conversion success!")

if __name__ == "__main__": main()
