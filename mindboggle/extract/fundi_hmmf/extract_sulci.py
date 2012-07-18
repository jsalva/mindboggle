#!/usr/bin/python
"""
Use depth to extract sulci from a triangular surface mesh and fill their holes.

Inputs:
    faces: triangular surface mesh vertex indices [#faces x 3]
    depths: depth values [#vertices x 1]
    depth_threshold: depth threshold for defining sulci
    min_sulcus_size: minimum sulcus size

Output:
    sulci: label indices for sulci: [#vertices x 1] numpy array
    n_sulci:  #sulci [int]


Authors:
    Yrjo Hame  .  yrjo.hame@gmail.com
    Arno Klein  .  arno@mindboggle.info  .  www.binarybottle.com

(c) 2012  Mindbogglers (www.mindboggle.info), under Apache License Version 2.0

"""

import numpy as np
from find_neighbors import find_neighbors
from time import time

#========================
# Segment surface patches
#========================
def segment_surface(faces, seeds, N, min_patch_size):
    """
    Segment a surface into contiguous patches (seed region growing).

    Inputs:
    ------
    faces: surface mesh vertex indices [#faces x 3]
    seeds: mesh vertex indices for vertices to be segmented [#seeds x 1]
    N: #vertices total (seeds are a subset)
    min_patch_size: minimum size of segmented set of vertices

    Output:
    ------
    segments: label indices for patches: [#seeds x 1] numpy array
    n_segments: #labels
    max_patch_label: index for largest segmented set of vertices

    Calls:
    -----
    find_neighbors()

    """

    # Initialize segments and seeds (indices of deep vertices)
    segments = np.zeros(N)
    n_seeds = len(seeds)

    # Remove faces that do not contain seeds to speed up computation
    fs = frozenset(seeds)
    faces_seeds = [lst for lst in faces if fs.intersection(lst)]
    faces_seeds = np.reshape(np.ravel(faces_seeds), (-1, 3))
    print('  Reduced {} to {} faces.'.format(len(faces),
                                             len(faces_seeds)))

    # Loop until all seed vertices segmented
    print('  Grow {} seed vertices...'.format(n_seeds))
    max_patch_size = 0
    max_patch_label = 1
    n_segments = 0
    counter = 0
    TEMP0 = np.zeros(N)
    while n_seeds > min_patch_size:
        TEMP = np.copy(TEMP0)

        # Select a seed vertex (selection does not affect result)
        #I = [seeds[round(np.random.rand() * (n_seeds - 1))]]
        I = [seeds[0]]
        # Region grown from seed
        Ipatch = I[:]

        # Grow region about the seed vertex until
        # there are no more connected seed vertices available.
        # Continue loop if there are newly selected neighbors.
        loop = 1
        while loop:
            loop = 0
            TEMP[I] = 1
            Inew = []

            # Find neighbors for each selected seed vertex
            for index in I:
                neighbors = find_neighbors(faces_seeds, index)

                # Select neighbors that have not been previously selected
                if len(neighbors) > 0:
                    neighbors = [x for x in neighbors if TEMP[x] == 0]
                    TEMP[neighbors] = 2
                    Inew.extend(neighbors)

                    # Continue looping
                    loop = 1
            I = Inew
            Ipatch.extend(Inew)

        # Disregard vertices already visited
        seeds = list(frozenset(seeds).difference(Ipatch))
        n_seeds = len(seeds)

        # Assign counter number to segmented patch
        # if patch size is greater than min_patch_size
        size_patch = len(Ipatch)
        if size_patch > min_patch_size:
            counter += 1
            n_segments = counter
            segments[Ipatch] = n_segments
            # Display current number and size of patch
            if size_patch > 1:
                print('  Segmented patch {}: {} vertices. {} seeds remaining...'.
                      format(n_segments, size_patch, n_seeds))

            # Find the maximum patch size
            if size_patch > max_patch_size:
                max_patch_size = size_patch
                max_patch_label = counter

    return segments, n_segments, max_patch_label

#-----------
# Fill holes
#-----------
def fill_holes(faces, sulci, holes, n_holes):
    """
    Fill holes in surface mesh patches.

    Inputs:
    ------
    faces: surface mesh vertex indices [#faces x 3] numpy array
    sulci: [#vertices x 1] numpy array
    holes: [#vertices x 1] numpy array
    n_holes: [#vertices x 1] numpy array

    Output:
    ------
    sulci: [#vertices x 1] numpy array

    Calls:
    -----
    find_neighbors()

    """

    # Look for vertices that have a sulcus label and are
    # connected to any of the vertices in the current hole,
    # and assign the hole the maximum label number
    for i in range(1, n_holes + 1):
        found = 0
        hole_indices = np.where(holes == i)[0]
        # Loop until a labeled neighbor is found
        for hole_index in hole_indices:
            # Find neighboring vertices to the hole
            neighbors = find_neighbors(faces, hole_index)
            # If there are any neighboring labels,
            # assign the hole the maximum label
            # of its neighbors and end the while loop
            for sulci_neighbor in sulci[neighbors]:
                if sulci_neighbor > 0:
                    sulci[hole_indices] = sulci_neighbor
                    break

    return sulci

#==============
# Extract sulci
#==============
def extract_sulci(faces, depths, depth_threshold=0.2, min_sulcus_size=50):
    """
    Extract sulci.

    Inputs:
    ------
    faces: triangular surface mesh vertex indices [#faces x 3]
    depths: depth values [#vertices x 1]
    depth_threshold: depth threshold for defining sulci
    min_sulcus_size: minimum sulcus size

    Output:
    ------
    sulci: label indices for sulci: [#vertices x 1] numpy array
    n_sulci:  #sulci [int]
    sulci_index_lists:  list of #sulci lists of vertex indices

    Calls:
    -----
    segment_surface()
    fill_holes()

    """

    # Segment sulcus surface
    print("  Segment deep portions of surface mesh into separate folds...")
    t0 = time()
    seeds = np.where(depths > depth_threshold)[0]
    sulci, n_sulci, max_sulcus = segment_surface(faces, seeds, N=len(depths),
                                                 min_patch_size=min_sulcus_size)
    print('    ...completed in {0:.2f} seconds'.format(time() - t0))

    # If there are any sulci
    if n_sulci > 0:

        # Segment holes in the folds
        print('  Segment holes in the folds...')
        t0 = time()
        seeds = np.where(sulci == 0)[0]
        holes, n_holes, max_hole = segment_surface(faces, seeds, N=len(sulci),
                                                   min_patch_size=0)
        # If there are any holes
        if n_holes > 0:
        
            # Ignore the largest hole (the background) and renumber holes
            holes[holes == max_hole] = 0
            if max_hole < n_holes:
                holes[holes > max_hole] -= 1
            n_holes -= 1
            print('    ...completed in {0:.2f} seconds'.format(time() - t0))

            print('  Fill holes...')
            t0 = time()
            sulci = fill_holes(faces, sulci, holes, n_holes)
            print('    ...completed in {0:.2f} seconds'.format(time() - t0))

    # Convert sulci array to a list of lists of vertex indices
    sulci_index_lists = [np.where(sulci==i)[0].tolist() for i in range(1, n_sulci+1)]

    # Return sulci, the number of sulci, and index lists
    return sulci, n_sulci, sulci_index_lists
