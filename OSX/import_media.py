import sys
import os
import mimetypes
import time
import shutil
import hashlib
import re
import subprocess

class ImportMedia(object):

    def __init__(self, source=[], dest=''):
        # Source and dest
        self.source = source
        self.dest = dest

        # File tracking
        self.allfiles = []
        self.possibledupes = []
        self.totalerror = []

        # Stats
        self.totalnew = 0
        self.totalprocessed = 0
        self.totaldup = 0
        self.lastprogress = 0

        # Settings
        self.be_verbose = True
        self.dirformat = "%Y" + os.sep + "%m" + os.sep + "%d"
        self.supported_types = ['image', 'video']

        # Setup
        self.get_files()


    # Find all of the files in our source directory
    # Set self.allfiles as an array of source files
    def get_files(self):
        for file_or_dir in self.source:
            if os.path.isfile(file_or_dir):
                self.allfiles.append(file_or_dir)
            elif os.path.isdir(file_or_dir):
                for (root, subFolders, files) in os.walk(file_or_dir):
                    for filename in files:
                        self.allfiles.append(root + os.sep + filename)

        # Reverse the list since most recent photos are probably named later
        # than older ones and we want oure most recents
        self.allfiles = self.allfiles[::-1]


    # Top level import routine. Import all non-dupes first, then import dupes
    def do_import(self):
        self.print_msg("Importing " + str(len(self.allfiles)) + "...")

        # Copy all simple cases
        self.do_copy_routine(self.allfiles)

        # Now copy any files which we need to calculate md5s for. This will be slower, so do it last
        self.do_copy_routine(self.possibledupes, True)


    # For all files in the given list try to copy them.
    # In the default case, skip files which have duplicates
    # Otherwise, tell get_timestamp to handle dupes
    def do_copy_routine(self, filenames, handle_dupes=False):
        for filename in filenames:
            try:
                timestamp = self.get_timestamp(filename)
                if not timestamp:
                    continue

                destpath = self.get_dest_path(timestamp, filename, handle_dupes)

                if destpath:
                    if self.copy_file(filename,destpath):
                        self.totalnew += 1
                    else:
                        self.totaldup += 1
                    self.totalprocessed += 1
                    self.print_status()
            except Exception:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                self.totalerror.append(filename)
                self.totalprocessed += 1
                self.print_status()


    # Get a timestamp from a file, hopefully using exiftool,
    # but falling back to the file ctime if needed
    # Returns False if the file has no type or is not a self.supported_types
    def get_timestamp(self, filename):
        maintype, subtype = mimetypes.guess_type(filename)
        if maintype is not None:
            maintype = maintype.split('/')

            category = maintype[0]

            if category in self.supported_types:
                try:
                    # Try to get exif taken date
                    maybetags = [
                        "DateTimeOriginal",
                        "CreateDate",
                        "TrackCreateDate",
                        "MediaCreateDate",
                        "ModifyDate",
                        "MediaModifyDate"
                    ]

                    for maybetag in maybetags:
                        doutput = subprocess.check_output(["exiftool", "-" + maybetag, filename])
                        if len(doutput) > 0:
                            break

                    dreone = re.sub(r".*: ", '', doutput)
                    draw = re.sub(r"\n", '', dreone)
                    if len(draw) > 0:
                        origTime = draw
                        timestamp = time.strptime(str(origTime), "%Y:%m:%d %H:%M:%S")
                    else:
                        create_date = os.stat(filename)[9]
                        timestamp = time.gmtime(create_date)
                except:
                    theerror = sys.exc_info()[0]
                    print_msg("CAUGHT EXCEPTION: " + theerror)
                    timestamp = time.gmtime(os.stat(filename)[9]) # [9] is st_ctime

                return timestamp
        return False


    # Given a timestamp and a source filename determine the output filename
    # If handle_dupes is not True we simply give up when a dupe is encountered
    def get_dest_path(self, timestamp, filename, handle_dupes=False):
        destpath = os.path.join(
                   self.dest,
                   time.strftime(self.dirformat, timestamp),
                   os.path.basename(filename)
                   )

        # keep modifying destpath with incrementing numbers until we find
        # an unused number or find a duplicate file. If the file is a
        # duplicate, return instead of copying
        if os.path.exists(destpath):
            if not handle_dupes:
                # Early exit for the quick case
                self.possibledupes.append(destpath)
                return False
            basename = os.path.basename(filename)
            filenamepart, extension = os.path.splitext(basename)
            counter = 1
            srchash = self.md5file(filename)

        while os.path.exists(destpath):
            if self.md5file(destpath) == srchash:
                return destpath
            destpath = os.path.join(
                            self.dest, 
                            time.strftime(self.dirformat, timestamp), 
                            filenamepart + "_" + str(counter) + extension
                        )
            counter += 1

        return destpath

    # Try to copy a file. Handle duplicate names
    def copy_file(self, filename, destpath):
        if not os.path.exists(os.path.dirname(destpath)):
            os.makedirs(os.path.dirname(destpath))

        if os.path.exists(destpath):
            return False
        else:
            shutil.copy2(filename, destpath)

        if os.path.basename(filename) != os.path.basename(destpath):
            self.totaldup += 1
            print_msg("\tDifferent file with same name already exists. Renaming to " + os.path.basename(destpath))

        return True

    # Util functions

    # Get the md5 hash of a file
    def md5file(self, filename):
        filehandle = open(filename, mode='rb')
        dahash = hashlib.md5()
        while True:
            data = filehandle.read(8192)
            if not data:
                break
            dahash.update(data)
        filehandle.close()
        return dahash.hexdigest()

    # Print the progress in a format that Platypus understands
    def print_status(self):
        progress = (self.totalprocessed*100/len(self.allfiles))
        if  progress > self.lastprogress:
            self.lastprogress = progress
            self.print_msg('PROGRESS:' + str(progress))

    # Simple logger
    def print_msg(self, msg):
        if self.be_verbose:
            print msg
            sys.stdout.flush()

    # Check our error count
    def has_errors(self):
        return len(self.totalerror) > 0

    # Setters
    def verbose(self, be_verbose=True):
        self.be_verbose = be_verbose

    def set_dir_format(self, theformat):
        self.dirformat = theformat

    def set_supported_types(self, types):
        self.supported_types = types




