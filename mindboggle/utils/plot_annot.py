#!/usr/bin/python

"""
Use FreeSurfer's tksurfer to visualize .annot surface mesh data

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0
"""

import os, sys

debug = 1

if len(sys.argv) < 6:
    if debug:
        subject = 'HLN-12-3'
        hemisphere = 'lh'
        surface = 'pial'
        annotname = 'labels.DKT31.manual'
        colortable = '/projects/Mindboggle/mindboggle/mindboggle/info/labels.surface.DKT31.txt'
    else:
        sys.exit('Usage: %s subject hemisphere surface-type annotname colortable' %sys.argv[0])
else:
    subject = sys.argv[1]
    hemisphere = sys.argv[2]
    surface = sys.argv[3]
    annotname = sys.argv[4]
    colortable = sys.argv[5]

args = ['tksurfer', subject, hemisphere, surface, '-annotation', annotname,
        '-colortable', colortable]
c = ' '.join(args)
print(c); os.system(c)
