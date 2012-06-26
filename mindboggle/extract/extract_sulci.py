#!/usr/bin/python
"""
Extract sulci from a VTK surface mesh and fill holes in them.

Inputs:
    faces: surface mesh vertex indices [n x 3]
    depths: depth values [m x 1]
    depth_threshold: depth threshold for defining sulci
     
Output:
    sulci: [n_sulci x 1], where n_sulci is the number of sulci

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

"""
#------------------
# Fill sulcus holes
#------------------
def fill_sulcus_holes(faces, sulci):
    ""
    Fill sulcus holes.
    ""
    print('Number of sulci before pruning: ' + str(max(sulci)))

    counter = 0

    while (counter < max(sulci)):
        counter = counter + 1
        ns = sum(sulci == counter)
        if (ns < 50):
            sulci(sulci == counter) = 0
            sulci(sulci > counter) = sulci(sulci > counter) - 1
            counter = counter - 1

    print('Number of sulci after pruning: ' str(max(sulci)))

    Holes = np.zeros(size(sulci))

    seeds = find(sulci == 0)

    seedSize = size(seeds,1)
    counter = 0

    while (seedSize > 0):
        counter = counter + 1
        TEMP = np.zeros(size(sulci))

        rseed = round(rand*(seedSize-1)) + 1

        TEMP(seeds(rseed,1),1) = 2
        newSize = size(find(TEMP>1))

        # grow region until no more connected points available
        while(newSize > 0):
            indsList = find(TEMP == 2)

            TEMP(TEMP == 2) = 1

            for i = 1:size(indsList,1):
                neighs = find_neighbors(faces,indsList(i,1))
                neighs = neighs(sulci(neighs) == 0)
                neighs = neighs(TEMP(neighs) == 0)
                TEMP(neighs) = 2

            newSize = size(find(TEMP>1))

        Holes(TEMP > 0) = counter

        sulci(Holes > 0) = .5
        seeds = find(sulci == 0)

        seedSize = size(seeds,1)

        # display current sulcus size
        print(size(find(Holes == counter),1))

    sulci(sulci < 1) = 0

    for i in range(max(Holes)):
        found = 0
        currInds = find(Holes == i)

        if (size(currInds,1) < 10000):
            j = 0
            while (found == 0):
                j = j + 1
                neighs = find_neighbors(faces, currInds(j,1))
                nIdx = max(sulci(neighs))
                if (nIdx > 0):
                    sulci(currInds) = nIdx
                    found = 1
                    print('Found ' + str(i))

    return sulci

"""

#==============
# Extract sulci
#==============
def extract_sulci(faces, depths, depth_threshold=0.2):
    """
    Extract sulci.

    Inputs:
    faces: surface mesh vertex indices [#faces x 3]
    depths: depth values [#vertices x 1]
    depth_threshold: depth threshold for defining sulci
     
    Parameters:
    depth_increment: depth increment for assigning vertices to sulci
    
    Output:
    sulci: [#vertices x 1]
    
    """

    faces = np.round(10*np.random.rand(5,3)).astype(int)
    depths = np.random.rand(10,1)

    depth_increment = 0.5 

    # Initialize sulci and seeds (indices of deep vertices)
    sulci = np.zeros(len(depths))
    seeds = np.where(depths > depth_threshold)[0]
    n_seeds = len(seeds)

    # Loop until all seed vertices included in sulci
    counter = 0
    while (n_seeds > 0):
        counter += 1

        # Select a random seed vertex (selection does not affect result)
        rseed = np.round(np.random.rand() * (n_seeds - 1))
        TEMP = np.zeros(len(depths))
        TEMP[seeds[rseed]] = 2

        # Grow region about the seed vertex until 
        # there are no more connected vertices available.
        # Continue loop if there are newly selected neighbors.
        while(sum(TEMP > 1) > 0):
            indices = np.where(TEMP == 2)[0]
            TEMP[indices] = 1
            # For each previously selected seed vertex
            for index in indices:
                # Find all neighbors deeper than the depth threshold
                #import sys; sys.exit()
                neighbors = find_neighbors(faces, index)
                if any(neighbors):
                    neighbors = neighbors[depths[neighbors][0] > depth_threshold]
                    # Select the neighbors that have not been previously selected
                    if any(neighbors):
                        neighbors = neighbors[TEMP[neighbors] == 0]
                        TEMP[neighbors] = 2

        # Assign the seed region vertices the loop counter number
        sulci[TEMP > 0] = counter

        # Disregard vertices already assigned to sulci
        depths[sulci > 0] = depth_threshold - depth_increment
        seeds = np.where(depths > depth_threshold)[0]
        n_seeds = len(seeds)

        # Display current number of sulci
        print('Number of sulci:', str(counter))

    #sulci = fill_sulcus_holes(faces, sulci)

    return sulci
