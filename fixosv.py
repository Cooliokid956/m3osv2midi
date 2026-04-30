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
from mido import MidiFile, MidiTrack, Message, MetaMessage, merge_tracks
from mido.messages.checks import check_channel

from utils import *

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
    return Message("sysex", data = data)
GM_SYSTEM_ON  = SYSEX("7E 7F 09 01")
GM2_SYSTEM_ON = SYSEX("7E 7F 09 03")
GS_RESET      = SYSEX("41 1042 12 40007F 0041")

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
        pre = [0x41, 0x10, 0x42, 0x12]
               # 65,   16,   66,   18
        xx = 0x11 + chan
        if chan == 9: xx = 0x10
        if chan  > 9: xx -= 1
        data = [0x40,xx, 0x15, (1 if on else 0)]
                # 64,xx,   21, (1: on;off is 0)
        sum = 0
        for n in data:
            sum += n & 0x7F
        sum = [(128 - (sum & 127)) & 127]

        data = pre + data + sum

        return [SYSEX(data)]
    elif GM2:
        return [CC(chan, 0, (0x78 if on else 0x79)), CC(chan, 32, 0)]
    return []

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

from tweaks import *

def get_inst(inst):
    replace = inst_replace.get(inst)
    if replace is None: return inst, False
    else: return replace, True

if SC88 or EXTRA_PATCH:
    inst_replace.update({
        (  0,  3) : (  2, 88), # New Age
        (  0,  6) : (  2, 88), # New Age
        (  0, 62) : (  2, 63), # Warm Brass
        (  0, 73) : (  1, 73), # Flute 2
        (  0,101) : (  1,101), # Goblinson
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
        28: (49, 57), # tabla
        29: (49, 58), # tabla
        30: (49, 59), # tabla
        32: (49, 45), # "Big Gong"
        34: (49, 47), # "Bend Gong"
        65: (49, 67), # "Timbales Low"
        66: (49, 69), # "Timbales High"

        31: (49, 29), # snare roll
        39: (49, 30), # snare "9"
    })

from instalias import inst_alias

def get_inst_name(prog):
    return inst_alias.get(prog, f"Unknown ({prog[0]:03.0f}:{prog[1]:03.0f})")

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
            chan_prog = array((-1, 0), 16) if GM2 else array((0, 0), 16)
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
                    if LOOPS > 0:
                        match msg.text:
                            case "loopStart":
                                queue_and_flush(msg)
                                pre_loop_track = track
                                track = MidiTrack()
                                continue
                                # pre_loop_perc_bank = perc_bank
                                # queue_and_flush(PC(9, perc_bank)) # find a better way to do this
                            case "loopEnd":
                                if len(track) > 0:
                                    track[-1].time += pop_time(msg)
                                pre_loop_track.extend(track * (LOOPS + 1))
                                track = pre_loop_track
                                queue_and_flush(msg)
                                continue
                    queue_and_flush(msg)
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
                            if GM2: queue(CC(msg.channel, 0, 0x79, time = 0))
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

                if msg.type in ('note_on', 'note_off'):
                    if orig_prog[msg.channel][1] == 127:
                        channel = 9 if chan_prog[msg.channel][0] == 128 and GM else msg.channel
                        remap = drums_remap.get(msg.note)
                        bank = DEF_BANK
                        if remap is not None:
                            if isinstance(remap, Auxiliary):
                                queue_and_flush(aux.fire(remap, msg))
                                continue
                            elif type(remap) is int: pass
                            else:
                                bank = remap[0]
                                msg.note = remap[1]
                        if bank != (drum_bank if SC88 else chan_prog[channel][1]):
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
                    # header += TOGGLE_DRUMS(peak_chan+i, True)
                    header += TOGGLE_DRUMS(min(peak_chan+i, 15), True) # THIS IS BROKEN!! bandaid fix, proper fix later
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

            # track.append(SYSEX("7E 7F 09 02"))
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
