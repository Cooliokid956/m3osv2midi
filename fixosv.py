import os, shutil
from mido import MidiFile

ogdir = "./OSV/"
dir = "./OSVMSGS/"
directory = os.fsencode(dir)

if os.path.exists(dir):
    print("MSGS exists! removing...")
    shutil.rmtree(dir)

shutil.copytree(ogdir, dir)

directory = os.fsencode(dir)

converts = 0
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".mid"): 
        mid = MidiFile(dir + filename)

        for track in mid.tracks:
            for msg in track:
                if msg.type == 'program_change' and ( \
                    msg.program == 70-1
                 or msg.program == 62-1): # English Horn
                    msg.program = 61-1 # French Horn
                    converts += 1
                    print(dir + filename + ": Converted to French. " + str(converts) + " converts")

        mid.save(dir + filename)
        continue
    else:
        continue
