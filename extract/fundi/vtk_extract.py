# this script extracts fundi/pits/sulci from a VTK file from the output from Joachim's code
# 2011-12-27 Now curvature is from FreeSurfer and is used to threshold the surface

import libfundi, fileio, libvtk # this line imports my own library
import sys, getopt # this line imports pulic libraries

try:
    opts, args = getopt.getopt(sys.argv[1:],'T:S:C:')
except getopt.GetoptError, err:
    print str(err) # will print something like "option -a not recognized"
    print "\n\t Usage: python vtk_extract.py  [-T thickness] [-S 2nd surface] [-C Convexity] VTKFile CurvFile"
    sys.exit(2)

if len(args)!=2:
    print "\n\t Please give at least one input VTK file containing a per-vertex map"
    print "\t Usage: python vtk_extract.py  [-T thickness] [-S 2nd surface] [-C Convexity] VTKFile CurvFile"
    sys.exit()

#print args
#print opts

[VTKFile, CurvFile] = args

print "\tRead in a VTK file:", VTKFile

ConvexFile, SurfFile2, ThickFile  = '', '', ''

for o,p in opts:
    if o in ['-S']:
        SurfFile2 = p
        print "\t Extraction result be mapped onto the 2nd surface:", SurfFile2
        libvtk.surf2VTK(SurfFile2)
    elif o in ['-C']:
        ConvexFile = p
        print "\t convexity file provided:", ConvexFile
    elif o in ['-T']:
        ThickFile = p
        print "\t Thickness file in use:", ThickFile

libfundi.getFundi([VTKFile, CurvFile, SurfFile2, ConvexFile, ThickFile], 'vtk-curv','')