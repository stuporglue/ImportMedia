ImportMedia
===========

Copy Files to a YYYY/MM/DD structure. 

You need [exiftool](http://www.sno.phy.queensu.ca/~phil/exiftool/index.html) to use this program.

About
-----
This program lets you drop images or directories onto its icon, and have the 
images copied into a YYYY/MM/DD structure based on their exif data (if JPEG)
or their ctime.

The python script (import_media.py) should work on Linux or Mac. 

Media are placed in ~/Pictures/

Why?
----
Organizing by Year-Month-Day makes finding files easy. 

I used to use [Shotwell](https://wiki.gnome.org/Apps/Shotwell) to manage my photos and it used a YYYY/MM/DD 
directory structure. Now I use [DigiKam](https://apps.kde.org/digikam/) but still use the same directory
layout.

Changelog
---------

 * 2014-2022 - Python V2 wrapped with Platypus to make an OSX droplet app
 * 2022-2023 - Python V3 for use from the command line on Linux. May still work on Mac. 
