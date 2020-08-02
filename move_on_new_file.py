import argparse
import os
import time
import fnmatch
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

parser = argparse.ArgumentParser(description='Create subtitle.')
parser.add_argument('-f', '--folder', type=str, help='folder to watch for new video')
args = parser.parse_args()

class HandleH264(PatternMatchingEventHandler):
    def __init__(self):
        super().__init__(patterns=['*video*.h264'])

    def on_created(self, event):
        for filename in os.listdir("."):
            if fnmatch.fnmatch(filename, '*video*.h264') and os.path.normpath(filename) != os.path.normpath(event.src_path):
                os.rename(filename, "to_encode/" + filename)

event_handler = HandleH264()
observer = Observer()
#observer.schedule(event_handler, args.folder)
observer.schedule(event_handler, ".")
observer.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()