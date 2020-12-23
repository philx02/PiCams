import os
import sys
import fnmatch
from datetime import datetime
from datetime import timedelta

now = datetime.now()
maximum_video_age = timedelta(days=50)

for filename in os.listdir(sys.argv[1]):
    filename_path = sys.argv[1] + "/" + filename
    if fnmatch.fnmatch(filename, "*.mkv"):
        date_string = filename.replace(".mkv", "")
        date_object = datetime.strptime(date_string, "%Y-%m-%d-%H-%M-%S")
        if (now - date_object > maximum_video_age):
            print("Deleting " + filename_path)
            os.remove(filename_path)
