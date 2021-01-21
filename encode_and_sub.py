import os
import sys
from datetime import datetime
from datetime import timedelta
import fnmatch
import argparse
from pathlib import Path
import ntpath

def encode_and_create_subtitles(path, txt_file):
    with open(txt_file) as info_file:
        file_info = info_file.read().split(',')
        initial_time = datetime.fromtimestamp(int(file_info[0]))
        video_duration = int((datetime.fromtimestamp(int(file_info[1])) - initial_time).total_seconds()) + 1

    header = """[Script Info]
Title:
Original Script:
Original Translation:
Original Editing:
Original Timing:
Original Script Checking:
Synch Point:
Script Updated By:
Update Details:
ScriptType: v4.00
Collisions: Normal
PlayResY: 864
PlayDepth: 0
Timer: 100.0000

[V4 Styles]
Style: Default,Consolas,20,65535,65535,65535,-2147483640,-1,0,1,3,0,2,30,30,30,0,0

[Events]
Format: Marked, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def hms(time_delta):
        hours = int(time_delta.total_seconds() / 3600)
        minutes = int((time_delta.total_seconds() // 60) % 60)
        seconds = int(time_delta.total_seconds() % 60)
        return str(hours) + ":" + f'{minutes:02}' + ":" + f'{seconds:02}' + ".00"

    parent_path = Path(path).parent.parent
    filename = os.path.splitext(ntpath.basename(path))[0]
    cam_name = file_info[2] + ' ' * (87 - len(file_info[2]))
    assfile_path = parent_path / (filename + ".ass")
    with open(assfile_path, 'w') as assfile:
        assfile.write(header)
        for i in range(0, video_duration):
            begin = hms(timedelta(0, i))
            end = hms(timedelta(0, i + 1))
            line = "Dialogue: Marked=0," + begin + "," + end + ",*Default,1,0000,0000,0000,," + cam_name
            assfile.write(line + (initial_time + timedelta(0, i)).strftime('%Y-%m-%d %H:%M:%S') + "\n")
    
    mkv_path = parent_path / (initial_time.strftime("%Y-%m-%d-%H-%M-%S") + ".mkv")
    if os.path.isfile(mkv_path):
        os.remove(mkv_path)
    mkv_path_tmp = parent_path / (filename + ".tmp.mkv")
    os.system("ffmpeg -y -framerate 25 -i " + path + " -c:v libx265 -preset fast " + str(mkv_path_tmp))
    os.system("mkvmerge -o " + str(mkv_path) + " " + str(mkv_path_tmp) + " " + str(assfile_path))
    
    os.remove(str(mkv_path_tmp))
    os.remove(str(assfile_path))
    os.remove(path)
    os.remove(txt_file)

for filename in os.listdir(sys.argv[1]):
    filename_path = sys.argv[1] + "/" + filename
    if fnmatch.fnmatch(filename_path, "*.h264"):
        txt_file_path = os.path.splitext(filename_path)[0] + ".txt"
        if os.path.isfile(txt_file_path):
            encode_and_create_subtitles(filename_path, txt_file_path)
