#!/usr/bin/env python 
import sys
print "Loading Program..."
sys.stdout.flush()

# Import Photos!
#
# This script imports photos (or other documents) into date based directories
# Copyright 2014 Michael Moore <stuporglue@gmail.com>

import os
import signal
import mimetypes
import EXIF
import time
import shutil
import hashlib
from os.path import expanduser

#
# SETTINGS
#

# The base directory where photos will be copied into
destdir = expanduser("~" + os.sep + "Pictures" + os.sep + "MediaSorter" + os.sep)

# The directory structure that the pictures will be copied into
dirformat = "%Y" + os.sep + "%m" + os.sep + "%d"

# These mime types will be copied. Other mime types will be ignored
supportedTypes = ['image','video']


#
# CODE
# You shouldn't need to modify anything below here if you're just using the program
#
# These types will be copied using their EXIF data if possible (falls back to their c_time)

jpegTypes = ['jpeg','pjpeg']

# CODE

# Handle Ctrl-c without doing a backtrace
def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Handle incorrect parameters
if len(sys.argv) < 2:
    print "Drop files or directories on me!"
    print "                                "
    print "I'll put them in " + destdir + ", organized by date."
    sys.stdout.flush()
    exit()

# Get the md5 hash of a file
def md5file(filename):
    f = open(filename,mode='rb')
    d = hashlib.md5()
    while True:
        data = f.read(8192)
        if not data:
            break;
        d.update(data)
    f.close()
    return d.hexdigest()

# Try to copy a file. Handle duplicate names
def copyFile(timestamp,filename):
    destpath =  destdir + os.sep + time.strftime(dirformat,timestamp) + os.sep + os.path.basename(filename)

    if not os.path.exists(os.path.dirname(destpath)):
        #print "Directory " + os.path.dirname(destpath) + " does not exist. Trying to create it."
        #sys.stdout.flush()
        os.makedirs(os.path.dirname(destpath))

    # keep modifying destpath with incrementing numbers until we find
    # an unused number or find a duplicate file. If the file is a
    # duplicate, return instead of copying
    if os.path.exists(destpath):
        basename = os.path.basename(filename)
        filenamepart,extension = os.path.splitext(basename)
        counter = 1
        srchash = md5file(filename)

    fileexisted = False
    if os.path.exists(destpath):
        fileexisted = True 
        

    while os.path.exists(destpath):
        if md5file(destpath) == srchash:
            print "\tIdentical file already exists. Not re-copying."
            return False
        destpath = destdir + os.sep + time.strftime(dirformat,timestamp) + os.sep + filenamepart + "_" + str(counter) + extension
        counter += 1

    shutil.copy2(filename,destpath)

    if fileexisted:
        print "\tDifferent file with same name already exists. Renaming to " + os.path.basename(destpath)
    return True

# Check all files and send appropriate files off to get copied
def probeFile(filename):
    maintype,subtype= mimetypes.guess_type(filename) 
    if maintype is not None:
        destPath = None
        category,subtype = maintype.split('/')

        if subtype in jpegTypes:
            try:
                # Try to get exif taken date
                jpg = open(filename,'rb')
                tags = EXIF.process_file(jpg,details=False,stop_tag="EXIF DateTimeOriginal")
                jpg.close()

                if "EXIF DateTimeOriginal" in tags:
                    origTime = tags["EXIF DateTimeOriginal"]
                    timestamp = time.strptime(str(origTime),"%Y:%m:%d %H:%M:%S")
                else:
                    create_date = os.stat(filename)[9]
                    timestamp = time.gmtime(create_date)
            except:
                # print "Error getting EXIF date for " + filename + ". Copying with ctime"
                # sys.stdout.flush()
                timestamp = time.gmtime(os.stat(filename)[9]) # [9] is st_ctime

            return copyFile(timestamp,filename)
        elif category in supportedTypes:
            create_date = os.stat(filename)[9] # [9] is st_ctime
            return copyFile(time.gmtime(create_date),filename)

totalnew = 0
totaldup = 0
totalerror = []
print "Starting Import"
sys.stdout.flush()

# Do 2 loops. One to count files, one to import them
# The count loop is so we can print a progress bar

# Count loop
print "Counting files..."
sys.stdout.flush()
totalfiles = 0
for file_or_dir in sys.argv[1:]:
    if os.path.isfile(file_or_dir):
        totalfiles += 1
    elif os.path.isdir(file_or_dir):
        for (root, subFolders, files) in os.walk(file_or_dir):
            totalfiles += len(files)


print "Print Importing " + str(totalfiles) + "..."
sys.stdout.flush()

# Import loop
totalprocessed = 0
lastprogress = totalprocessed*100/totalfiles
print 'PROGRESS:' + str(lastprogress)
sys.stdout.flush()
for file_or_dir in sys.argv[1:]:
    print "Copying " + file_or_dir
    sys.stdout.flush()
    if os.path.isfile(file_or_dir):
        try:
            if probeFile(file_or_dir):
                totalnew += 1
            else:
                totaldup += 1
            totalprocessed += 1
            progress = (totalprocessed*100/totalfiles)
            if  progress > lastprogress:
                lastprogress = progress
                print 'PROGRESS:' + str(progress)
                sys.stdout.flush()
        except:
            totalerror.append(file_or_dir)
            totalprocessed += 1
    elif os.path.isdir(file_or_dir):
        for (root, subFolders, files) in os.walk(file_or_dir):
            for filename in files:
                print "Copying " + filename
                sys.stdout.flush()
                try:
                    if probeFile(root + os.sep + filename):
                        totalnew += 1
                    else:
                        totaldup += 1
                    totalprocessed += 1
                    progress = (totalprocessed*100/totalfiles)
                    if  progress > lastprogress:
                        lastprogress = progress
                        print 'PROGRESS:' + str(progress)
                        sys.stdout.flush()
                except:
                    totalerror.push(root + os.sep + filename)
                    totalprocessed += 1
                    if  progress > lastprogress:
                        lastprogress = progress
                        print 'PROGRESS:' + str(progress)
                        sys.stdout.flush()

if len(totalerror):
    print "Errors were found when copying the following files:"
    print "\t* " + "\n\t* ".join(totalerror)
    sys.stdout.flush()

print str(totalnew) + " new files copied. " + str(totaldup) + " duplicates not copied."
sys.stdout.flush()
