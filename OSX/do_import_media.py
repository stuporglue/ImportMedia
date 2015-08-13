#!/usr/bin/env python
import sys
from os.path import expanduser
import os
import signal
import import_media

# Import Photos!
#
# This script imports photos (or other documents) into date based directories
# Copyright 2014 Michael Moore <stuporglue@gmail.com>

#
# SETTINGS
#

# The base directory where photos will be copied into
destdir = expanduser("~" + os.sep + "Pictures" + os.sep + "MediaSorter" + os.sep)

# The directory structure that the pictures will be copied into
dirformat = "%Y" + os.sep + "%m" + os.sep + "%d"

# These mime types will be copied. Other mime types will be ignored
supportedTypes = ['image', 'video']


#
# CODE
# You shouldn't need to modify anything below here if you're just using the program
#
# These types will be copied using their EXIF data if possible (falls back to their c_time)

#jpegTypes = ['jpeg', 'pjpeg', 'mpeg', 'mp4']

# CODE

# Handle Ctrl-c without doing a backtrace
def signal_handler(signal, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Handle incorrect parameters
if len(sys.argv) < 2:
    print "Drop files or directories on me!\n\nI'll put them in " + destdir + ", organized by date."
    exit()

importer = import_media.ImportMedia(sys.argv[1:], destdir)
importer.set_dir_format(dirformat)
importer.set_supported_types(supportedTypes)
importer.do_import()

if importer.has_errors():
    print "Errors were found when copying the following files:" + "\n\t* " + "\n\t* ".join(importer.totalerror)

print str(importer.totalnew) + " new files copied. " + str(importer.totaldup) + " duplicates not copied."
