#!/usr/bin/python
"""
Use depth to extract folds from a triangular surface mesh and fill holes
resulting from shallower areas within a fold.

Inputs:
    faces: triangular surface mesh vertex indices [#faces x 3]
    depths: depth values [#vertices x 1]
    min_depth: depth threshold for defining folds
    min_fold_size: minimum fold size

Output:
    folds: label indices for folds: [#vertices x 1] numpy array
    n_folds:  #folds [int]


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
def segment_surface(faces, seeds, n_vertices, min_seeds, min_patch_size):
    """
    Segment a surface into contiguous patches (seed region growing).

    Inputs:
    ------
    faces: surface mesh vertex indices [#faces x 3]
    seeds: mesh vertex indices for vertices to be segmented
           list or [#seeds x 1] numpy array
    n_vertices: #vertices total (seeds are a subset)
    min_seeds: minimum number of seeds (vertices) per triangle for inclusion
    min_patch_size: minimum size of segmented set of vertices

    Output:
    ------
    segments: label indices for patches: [#seeds x 1] numpy array
    n_segments: #labels
    max_patch_label: index for largest segmented set of vertices
    neighbor_lists: lists of lists of neighboring vertex indices

    Calls:
    -----
    find_neighbors()

    """

    # Initialize segments and seeds (indices of deep vertices)
    segments = np.zeros(n_vertices)
    n_seeds = len(seeds)

    # Remove faces with fewer than min_seeds seeds to speed up computation
    fs = frozenset(seeds)
    faces_seeds = [lst for lst in faces 
                   if len(fs.intersection(lst)) >= min_seeds]
    faces_seeds = np.reshape(np.ravel(faces_seeds), (-1, 3))
    print('    Reduced {} to {} faces.'.format(len(faces),
                                             len(faces_seeds)))

    # Loop until all seed vertices segmented
    print('    Grow {} seed vertices...'.format(n_seeds))
    max_patch_size = 0
    max_patch_label = 1
    n_segments = 0
    counter = 0
    TEMP0 = np.zeros(n_vertices)
    neighbor_lists = [[] for x in range(n_vertices)]
    while n_seeds >= min_patch_size:
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
                neighbor_lists[index] = neighbors

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
        if size_patch >= min_patch_size:
            counter += 1
            n_segments = counter
            segments[Ipatch] = n_segments

            # Display current number and size of patch
            if size_patch > 1:
                print('    Segmented patch {}: {} vertices. {} seeds remaining...'.
                      format(n_segments, size_patch, n_seeds))

            # Find the maximum patch size
            if size_patch > max_patch_size:
                max_patch_size = size_patch
                max_patch_label = counter

    return segments, n_segments, max_patch_label, neighbor_lists

#-----------
# Fill holes
#-----------
def fill_holes(faces, folds, holes, n_holes, neighbor_lists):
    """
    Fill holes in surface mesh patches.

    Inputs:
    ------
    faces: surface mesh vertex indices [#faces x 3] numpy array
    folds: [#vertices x 1] numpy array
    holes: [#vertices x 1] numpy array
    n_holes: [#vertices x 1] numpy array
    neighbor_lists: lists of lists of neighboring vertex indices

    Output:
    ------
    folds: [#vertices x 1] numpy array

    Calls:
    -----
    find_neighbors()

    """

    # Look for vertices that have a fold label and are
    # connected to any of the vertices in the current hole,
    # and assign the hole the maximum label number
    for i in range(1, n_holes + 1):
        indices_holes = np.where(holes == i)[0]
        # Loop until a labeled neighbor is found
        for index in indices_holes:
            # Find neighboring vertices to the hole
            if len(neighbor_lists) > 0:
                neighbors = neighbor_lists[index]
                if not len(neighbors):
                    neighbors = find_neighbors(faces, index)
            else:
                neighbors = find_neighbors(faces, index)
            # If there are any neighboring labels,
            # assign the hole the maximum label
            # of its neighbors and end the while loop
            for folds_neighbor in folds[neighbors]:
                if folds_neighbor > 0:
                    folds[indices_holes] = folds_neighbor
                    break

    return folds

#==============
# Extract folds
#==============
def extract_folds(faces, depths, min_depth, min_depth_hole, min_fold_size):
    """
    Extract folds.

    Inputs:
    ------
    faces: triangular surface mesh vertex indices [#faces x 3]
    depths: depth values [#vertices x 1]
    min_depth: depth threshold for defining folds
    min_fold_size: minimum fold size
    min_depth_holes: minimum depth for decreasing segmentation time of holes

    Output:
    ------
    folds: label indices for folds: [#vertices x 1] numpy array
    n_folds:  #folds [int]
    folds_index_lists:  list of #folds lists of vertex indices

    Calls:
    -----
    segment_surface()
    fill_holes()

    """

    n_vertices = len(depths)

    # Segment folds of a surface mesh
    print("  Segment deep portions of surface mesh into separate folds...")
    t0 = time()
    seeds = np.where(depths > min_depth)[0]
    folds, n_folds, max_fold, neighbor_lists_folds = segment_surface(
        faces, seeds, n_vertices, 3, min_fold_size)
    print('    ...Folds segmented ({:.2f} seconds)'.format(time() - t0))

    # If there are any folds
    if n_folds > 0:

        # Find fold vertices that have not yet been segmented
        # (because they weren't sufficiently deep) and have some minimum depth
        t0 = time()
        seeds = [i for i,x in enumerate(folds)
                 if x==0 and depths[i] > min_depth_hole]

        # Segment holes in the folds
        print('  Segment holes in the folds...')
        holes, n_holes, max_hole, neighbor_lists_holes = segment_surface(
            faces, seeds, n_vertices, 1, 1)

        # If there are any holes
        if n_holes > 0:

            # Combine neighbor lists
            neighbor_lists = [[] for x in range(n_vertices)]
            for index, neighbor_list in enumerate(neighbor_lists_folds):
                if len(neighbor_list) > 0:
                    neighbor_lists[index] = neighbor_list
                if len(neighbor_lists_holes) > 0:
                    if len(neighbor_lists_holes[index]) > 0:
                        [neighbor_lists[index].extend([x])
                         for x in neighbor_lists_holes[index]
                         if x not in neighbor_lists[index]]

                    # Ignore the largest hole (the background) and renumber holes
            holes[holes == max_hole] = 0
            if max_hole < n_holes:
                holes[holes > max_hole] -= 1
            n_holes -= 1
            print('    ...Holes segmented ({:.2f} seconds)'.format(time() - t0))

            t0 = time()
            folds = fill_holes(faces, folds, holes, n_holes, neighbor_lists)
            print('  Filled holes ({:.2f} seconds)'.format(time() - t0))

    # Convert folds array to a list of lists of vertex indices
    index_lists_folds = [np.where(folds == i)[0].tolist() 
                         for i in range(1, n_folds+1)]

    # Return folds, the number of folds, and lists of indices for each fold
    return folds, n_folds, index_lists_folds, neighbor_lists
