#!/usr/bin/python
"""
Find neighbors

Authors:
Yrjo Hame  .  yrjo.hame@gmail.com  (original Matlab code)
Arno Klein  .  arno@mindboggle.info  (translated to Python)

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import numpy as np

#---------------
# Find neighbors
#---------------
def find_neighbors(faces, index):
    """
    For a set of surface mesh faces and the index of a surface vertex,
    find unique indices for neighboring vertices.
    """
    # Create list of vertex indices sharing the same faces as "index"
    I = [faces[np.where(faces[:,i] == index)[0]][0].tolist() for i in range(3) \
         if len(np.where(faces[:,i] == index)[0]) > 0]

    # Create single list from nested lists
    I = [int(item) for sublist in I for item in sublist]

    # Find unique indices not equal to "index"
    I = np.unique(I)
    I[I != index]

    return I

