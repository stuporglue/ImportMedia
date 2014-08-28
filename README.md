ImportMedia
===========

Copy Files to a YYYY/MM/DD structure. 

About
-----
This program lets you drop images or directories onto its icon, and have the 
images copied into a YYYY/MM/DD structure based on their exif data (if JPEG)
or their ctime.

The python script (import_media.py) should work on Linux or Mac. There is also
an OSX droplet application provided.

Media are placed in ~/Pictures/MediaSorter

Why?
----
I rsync my [Shotwell](https://wiki.gnome.org/Apps/Shotwell) photo directory to a 
backup server and wanted my wife's photos to be organized in the same structure. 

Organizing by Year-Month-Day makes finding files easy. 

Building
--------
To build the app for OSX you'll need [Platypus](http://www.sveinbjorn.org/platypus), 
a handy script wrapper UI maker which I have used for several projects. 
