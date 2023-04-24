#!/usr/bin/env python3

# Import Media!
#
# This script imports photos (or other documents) into date based directories based on 
# the date found in the media's exif data, falling back to the filesystem timestamp if needed.
#
# Copyright 2014-2023 Michael Moore <stuporglue@gmail.com>

import sys
import os
import signal
import mimetypes
import time
import shutil
import hashlib
import re
import subprocess
from os.path import expanduser
import traceback

home = expanduser("~")

###
### SETTINGS
###

# The base directory where photos will be copied into
destdir = home + '/Pictures/'

# Change here to override
#destdir = "/shared/bigint/Photos/"

# The directory structure that the pictures will be copied into
dirformat = "%Y" + os.sep + "%m" + os.sep + "%d"

# These mime types will be copied. Other mime types will be ignored
supportedTypes = ['image','video']


###
### CODE
###
### You shouldn't need to modify anything below here if you're just using the program
###

# These types will be copied using their EXIF data if possible (falls back to their c_time)

# Handle Ctrl-c without doing a backtrace

# m4v isn't in the db for some reason...
mimetypes.add_type('video/mp4','.m4v',True)

# Why did we need this? Maybe we don't? 
def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Print USAGE statement if no args are given
if len(sys.argv) < 2:
    print("USAGE: import_media.py some_file_or_directory [additional_files_or_directory...]")
    print("")
    print("Media will be put in " + destdir + ", organized by " + dirformat + ".")
    sys.stdout.flush()
    exit()

# When we have a file name collision, we will calculate an md5 and compare it. 
# We are OK with md5 because it is fast and the odds of a collission between 
# different files with the same exif date seems low. 
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
            print("\tIdentical file already exists. Not re-copying.")
            return False
        destpath = destdir + os.sep + time.strftime(dirformat,timestamp) + os.sep + filenamepart + "_" + str(counter) + extension
        counter += 1

    shutil.copy2(filename,destpath)

    if fileexisted:
        print("\tDifferent file with same name already exists. Renaming to " + os.path.basename(destpath))
    return True

# Check all files and send appropriate files off to get copied
def probeFile(filename):
    maintype,subtype= mimetypes.guess_type(filename) 
    if maintype is not None:
        destPath = None
        category,subtype = maintype.split('/')

        if category in supportedTypes:
            print("Copying " + filename)
            sys.stdout.flush()

            try:
                # Try to get exif taken date
                maybetags = [
                        "DateTimeOriginal",
                        "CreateDate",
                        "CreationDate",
                        "DateCreated",
                        "TrackCreateDate",
                        "MediaCreateDate",
                        "GPSDateTime",
                        "ModifyDate",
                        "MediaModifyDate",
                        "FileModifyDate",
                        "TrackModifyDate",
                        "FileInodeChangeDate",
                        "FileAccessDate"
                        ] 

                for maybetag in maybetags:
                    doutput = subprocess.check_output(["exiftool","-" + maybetag,"-extractEmbedded",filename],encoding='UTF-8')
                    if (len(doutput) > 0 and '0000:00:00 00:00:00' not in doutput ):
                        break

                if (len(doutput) > 0 and '0000:00:00 00:00:00' not in doutput):

                    # Strip the tag name off the front
                    dreone = re.sub(r".*: ",'',doutput)
                    
                    # Trim the newline off the end
                    draw = re.sub(r"\n.*",'',dreone)

                    # Remove the timezone info off the end
                    draw = re.sub(r"[+-][0-9]{1,2}:[0-9]{2}$",'',draw)
                    draw = re.sub(r"Z$",'',draw)

                    # Convert dashes or other delimiters to colons
                    draw = re.sub(r"[^0-9 ]",':',draw)
                    
                    if len(draw) > 0:
                        sys.stdout.flush()
                        origTime = draw
                        timestamp = time.strptime(str(origTime),"%Y:%m:%d %H:%M:%S")
                    else:
                        sys.stdout.flush()
                        create_date = os.stat(filename)[9]
                        timestamp = time.gmtime(create_date)
                else:
                    create_date = os.stat(filename)[9]
                    timestamp = time.gmtime(create_date)
            except Exception as e:
                print(e)
                traceback.print_exc()
                theerror = sys.exc_info()[0]
                sys.stderr.write(theerror)
                print("CAUGHT EXCEPTION: " + theerror)
                timestamp = time.gmtime(os.stat(filename)[9]) # [9] is st_ctime

            return copyFile(timestamp,filename)
        else:
            # print("Not a supported mime type for " + filename)
            # sys.stdout.flush()
            pass
    else:
        print("No mimetype found for " + filename)

totalnew = 0
totaldup = 0
totalerror = []
print("Starting Import")
sys.stdout.flush()

# Do 2 loops. One to count files, one to import them
# The count loop is so we can print a progress bar

# Count loop
print("Counting files...")
sys.stdout.flush()
totalfiles = 0
for file_or_dir in sys.argv[1:]:
    if os.path.isfile(file_or_dir):
        totalfiles += 1
    elif os.path.isdir(file_or_dir):
        for (root, subFolders, files) in os.walk(file_or_dir):
            totalfiles += len(files)


print("Print Importing " + str(totalfiles) + "...")
sys.stdout.flush()

# Import loop
progress = 0
totalprocessed = 0
if totalfiles > 0:
    lastprogress = totalprocessed*100/totalfiles
else:
    lastprogress = 100
print('PROGRESS:' + str(lastprogress))
sys.stdout.flush()
for file_or_dir in sys.argv[1:]:
    print("Considering " + file_or_dir + " and its subfolders")
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
                print('PROGRESS:' + str(progress))
                sys.stdout.flush()
        except Exception as e:
            sys.exit(str(e))
            sys.stderr.write(str(e))
            totalerror.append(file_or_dir)
            totalprocessed += 1
    elif os.path.isdir(file_or_dir):
        for (root, subFolders, files) in os.walk(file_or_dir):
            for filename in files:
                try:
                    if probeFile(root + os.sep + filename):
                        totalnew += 1
                    else:
                        totaldup += 1
                    totalprocessed += 1
                    progress = (totalprocessed*100/totalfiles)
                    if  progress > lastprogress:
                        lastprogress = progress
                        print('PROGRESS:' + str(progress))
                        sys.stdout.flush()
                except Exception as e:
                    sys.exit(str(e))
                    sys.stderr.write(str(e))
                    totalerror.append(root + os.sep + filename)
                    totalprocessed += 1
                    if  progress > lastprogress:
                        lastprogress = progress
                        print('PROGRESS:' + str(progress))
                        sys.stdout.flush()

if len(totalerror):
    print("\nErrors were found when copying the following files:")
    print("\t* " + "\n\t* ".join(totalerror))
    sys.stdout.flush()

print(str(totalnew) + " new files copied. " + str(totaldup) + " duplicates not copied.")
sys.stdout.flush()
